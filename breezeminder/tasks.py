import json
import requests

from datetime import datetime
from dateutil.parser import parse as parse_date
from flask.ext.celery import Celery
from juggernaut import Juggernaut
from mongoengine.queryset import Q

from breezeminder.app import app

from breezeminder.models.card import BreezeCard
from breezeminder.models.messaging import Messaging
from breezeminder.models.marta import Bus


celery = Celery(app)
celery.config_from_object(app.config)


# 15 Minute default
DEFAULT_RETRY = 15 * 60


@celery.task(name='tasks.check_card_pulls', ignore_result=True)
def check_card_pulls():
    """ Find cards that aren't scheduled for a pull """
    logger = check_card_pulls.get_logger()

    threshold = datetime.now() - app.config['REFRESH_INTERVAL'] - app.config['CARD_STALE_THRESH']
    logger.info('Checking stale cards never loaded or loaded before %s' % threshold)

    # Cards that were never loaded or are 'stale'
    qs = Q(last_loaded=None) | Q(last_loaded__lte=threshold)

    for card in BreezeCard.objects.filter(qs):
        logger.debug('Scheduling stale card %s' % card.number_masked)
        pull_card_data.delay(card.id)


@celery.task(name='tasks.pull_card_data',
             ignore_result=True,
             rate_limit=app.config.get('CARD_RATE_LIMIT', '10/m'),
             default_retry_delay=app.config.get('CARD_RETRY_DELAY', DEFAULT_RETRY))
def pull_card_data(card_id):
    # THIS TASK USES TEMPLATES. Make sure they are imported
    from breezeminder.app import context, filters

    logger = pull_card_data.get_logger()
    logger.info('Starting card pull task for card %s' % card_id)

    # Process the card
    try:
        card = BreezeCard.objects.get(id=card_id)
        if card.last_loaded is not None and card.next_refresh >= datetime.now():
            logger.error('Card pull was scheduled but it is not due yet')
        else:
            card.pull_data(check_reminders=True)
            logger.info('Card pull complete')

            # Reschedule the next pull
            logger.info('Rescheduling card %s for %s' % (card_id, card.next_refresh))
            pull_card_data.apply_async((card_id, ), eta=card.next_refresh)
    except BreezeCard.DoesNotExist:
        logger.exception('Could not locate BreezeCard by id %s - WILL NOT RETRY' % card_id)
    except Exception, exc:
        logger.exception('Pull card data task for id %s went full retard. Retry.' % card_id)
        pull_card_data.retry((card_id, ), exc=exc)


@celery.task(name='tasks.pull_marta_realtime_data',
             ignore_result=True,
             rate_limit=app.config.get('MARTA_RATE_LIMIT', '6/m'),
             default_retry_delay=app.config.get('MARTA_RETRY_DELAY', 10))
def pull_marta_realtime_data():
    logger = pull_marta_realtime_data.get_logger()
    logger.info('Starting MARTA realtime pull')
    stale = set(Bus.objects.filter(is_stale=False).values_list('id'))

    try:
        data = json.loads(requests.get(app.config['MARTA_ENDPOINT']).content)
        socket = Juggernaut()
        queue = app.config.get('MARTA_SOCKET_QUEUE', 'marta')
        push = []

        for info in data:
            defaults = {
                'id': info['VEHICLE'],
                'direction': info['DIRECTION'],
                'route': info['ROUTE'],
                'location': (float(info['LATITUDE']), float(info['LONGITUDE'])),
                'status_time': parse_date(info['MSGTIME']),
                'timepoint': info['TIMEPOINT'],
                'stop_id': info.get('STOPID', ''),
                'is_stale': False
            }

            try:
                defaults['adherence'] = int(info['ADHERENCE'])
            except (ValueError, KeyError):
                defaults['adherence'] = 0

            bus, created = Bus.objects.get_or_create(id=defaults['id'],
                                                     defaults=defaults)

            if not created:
                stale.discard(bus.id)
                current = defaults['status_time'] > bus.status_time
                updated = bus.update_maybe(**defaults)

                if updated and current:
                    bus.save()
                    push.append(bus.to_json())
            else:
                push.append(bus.to_json())

        # Notify
        try:
            # Push new updates
            if push:
                logger.info('Publishing %s bus updates to queue %s' % (len(push), queue))
                socket.publish(queue, push)

            # Notify of staleness
            if stale:
                stale = list(stale)
                logger.info('Publishing %s stale bus notices to %s/stale' % (len(stale), queue))
                socket.publish('%s/stale' % queue, stale)
                Bus.objects.filter(id__in=stale).update(set__is_stale=True)

        except:
            logger.exception("Can't push realtime MARTA notifications")
    except:
        logger.exception('Failed to pull MARTA realtime data')
    else:
        logger.info('MARTA realtime pull finished')


def _process_mail_queue(logger, immediate=False, batch=100):
    queue_type = 'immediate' if immediate else 'queued'

    logger.info('Starting processing %s messages. Batched %s' % (queue_type, batch))

    messages = Messaging.objects.filter(is_sent=False, is_immediate=immediate)

    # Try sending out a batch
    try:
        processed = 0
        for message in messages.order_by('created')[:batch]:
            with app.mail.connect() as conn:
                message.send(conn)
                processed += 1
        logger.info('Processed %s messages' % processed)
    except Exception, e:
        logger.exception('The mail processing queue went full retard')


@celery.task(name='tasks.send_outgoing_mail', ignore_result=True)
def send_outgoing_mail(batch=100):
    _process_mail_queue(send_outgoing_mail.get_logger(), batch=batch)


@celery.task(name='tasks.send_immediate_mail', ignore_result=True)
def send_immediate_mail(batch=100):
    _process_mail_queue(send_immediate_mail.get_logger(), immediate=True, batch=batch)
