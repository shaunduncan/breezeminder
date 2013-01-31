import re
from datetime import datetime
from dateutil.relativedelta import relativedelta

from breezeminder.app import app
from breezeminder.models.base import (BaseDocument,
                                      BaseQuerySet)


class ReminderQuerySet(BaseQuerySet):
    pass


class ReminderHistoryQuerySet(BaseQuerySet):

    def last_reminder(self, reminder, card):
        try:
            return self.filter(reminder=reminder, card=card)[0]
        except IndexError:
            return None


class ReminderTypeQuerySet(BaseQuerySet):

    @app.cache.memoize(timeout=3600)
    def all_tuples(self, field='name'):
        return [(t.key, getattr(t, field)) for t in self.all()]


class ReminderType(BaseDocument):
    key = app.db.StringField(required=True)
    name = app.db.StringField(required=True)
    description = app.db.StringField()
    order = app.db.IntField(required=True, default=0)

    meta = {
        'collection': 'reminder_types',
        'queryset_class': ReminderTypeQuerySet,
        'ordering': ['+order'],
        'indexes': [
            {
                'fields': ['key'],
                'unique': True
            }
        ]
    }

    def __str__(self):
        return self.key

    def __eq__(self, obj):
        if isinstance(obj, basestring):
            return self.key == obj
        else:
            return self == obj


class Reminder(BaseDocument):
    owner = app.db.ReferenceField('User', required=True, dbref=False,
                                  reverse_delete_rule=app.db.CASCADE)
    type = app.db.ReferenceField('ReminderType', required=True, dbref=False)
    threshold = app.db.DecimalField(required=True, default=0.0)
    quantifier = app.db.StringField()
    valid_until = app.db.DateTimeField()
    send_email = app.db.BooleanField(required=True, default=True)
    send_sms = app.db.BooleanField(required=True, default=True)

    meta = {
        'collection': 'reminders',
        'queryset_class': ReminderQuerySet,
        'indexes': ['type', 'valid_until']
    }

    def __init__(self, **kwargs):
        if 'type' in kwargs and isinstance(kwargs['type'], basestring):
            kwargs['type'] = ReminderType.objects.get(key=kwargs['type'])
        super(Reminder, self).__init__(**kwargs)

    def last_reminded(self, card=None):
        """
        Grabs the last reminder. Proxy for `ReminderHistory.objects.last_reminder`.
        If a card is supplied, return the latest reminder for that specifically.
        If no card is supplied, for each card owned by the owner of this reminder,
        return the result of this method
        """
        if card:
            return ReminderHistory.objects.last_reminder(self, card)
        else:
            # We have to find last reminded for all owner cards
            from breezeminder.models.card import BreezeCard
            reminders = []

            for card in BreezeCard.objects.filter(owner=self.owner):
                reminder = self.last_reminded(card)
                if reminder:
                    reminders.append(reminder)

            return reminders

    def description(self, html=True):
        """
        Returns a descriptive form of this reminder.
        
        Examples
            Balance falls below $25.00
            Remaining Rides falls below 3
            Expiration Date is 2 days away
        """
        if self.type == 'EXP':
            action = 'is'
            quantity = '%i %s away' % (int(self.threshold), self.quantifier)
        elif self.type.key.startswith('AVAIL_'):
            action = ''
            quantity = ''
        else:
            fmt = '$%.2f' if self.type == 'BAL' else '%s'
            action = 'falls below'
            quantity = fmt % self.threshold

        if html:
            format = '<b>%s</b> %s <b>%s</b>'
        else:
            format = '%s %s %s'

        return format % (self.type.name, action, quantity)

    def check_reminder(self, card, last_state=None):
        """ Entry point for lazily checking reminders based on type """

        # Don't proceed if we've passed the time we are limiting to
        if self.valid_until and datetime.now() >= self.valid_until:
            return False

        if self.type == 'BAL':
            return self._check_balance_reminder(card, last_state)
        elif self.type == 'RIDE':
            return self._check_ride_reminder(card, last_state)
        elif self.type == 'ROUND_TRIP':
            return self._check_round_trip_reminder(card, last_state)
        elif self.type == 'EXP':
            return self._check_expiration_reminder(card)
        elif self.type == 'AVAIL_BAL':
            if last_state:
                return self._check_available_balance_reminder(card, last_state)
        elif self.type == 'AVAIL_PROD':
            if last_state:
                return self._check_available_product_reminder(card, last_state)
        else:
            message = 'Reminders for type %s are not implemented' % self.type
            app.logger.exception(message)
            raise NotImplementedError(message)

    def _check_available_balance_reminder(self, card, last_state):
        """ Check if card stored value has increased """
        if card.stored_value is not None and last_state.stored_value is not None:
            try:
                if float(card.stored_value) > float(last_state.stored_value):
                    return True
            except:
                app.logger.exception('Exception checking available balance')
                pass

        return False

    def _check_available_product_reminder(self, card, last_state):
        """ Check if card has new products """
        current_prod = card.products if card.products else []
        old_prod = last_state.products if last_state.products else []

        for product in current_prod:
            if product not in old_prod:
                return True

        # Check autoloads
        current_pending = card.pending if card.pending else []
        old_pending = last_state.pending if last_state.pending else []

        for pending in current_pending:
            if pending in old_pending:
                return True

        return False

    def _check_balance_reminder(self, card, last_state=None):
        """ Check card stored value """
        if card.stored_value is not None:
            try:
                current_value = float(card.stored_value)

                # Pedantic - make sure the last value isn't identical
                if last_state is not None and last_state.stored_value is not None:
                    last_value = float(last_state.stored_value)
                    if current_value == last_value:
                        app.logger.info('No change in stored value %s since last reminder: %s' % (current_value, card.last_four))
                        return False

                return current_value > 0 and current_value <= float(self.threshold)
            except:
                app.logger.exception('Exception checking balance')
                pass

        return False

    def _exp_delta(self):
        try:
            return relativedelta(**{self.quantifier.lower(): int(self.threshold)})
        except:
            message = 'Expiration reminders not implemented for %s' % self.quantifier
            app.logger.exception(message)
            raise NotImplementedError(message)

    def _will_expire(self, exp_date, delta):
        # Will expire will happen if now + thresh is the same date as the expiration
        now = datetime.now().date()
        return now + delta == exp_date.date() and exp_date.date() >= now

    def _check_expiration_reminder(self, card):
        """ Checks the card expiration and product expirations """
        remind = False
        delta = self._exp_delta()

        # Check expiration date of card
        if card.expiration_date is not None:
            remind = remind or self._will_expire(card.expiration_date, delta)

        # Check each product
        for product in card.products:
            if product.expiration_date is not None:
                remind = remind or self._will_expire(product.expiration_date, delta)

        return remind

    def _check_round_trip_reminder(self, card, last_state=None):
        """ Checks products for remaining round trips that have fallen below threshold """
        remind = False
        threshold = int(self.threshold)

        for product in card.products:
            if product.remaining_rides is None:
                continue

            try:
                # This does take into consideration half trips
                round_trips = product.remaining_rides / 2.0
                should_remind = round_trips < threshold

                # Pedantic - check last state products for name match
                # and number of round trips
                if last_state:
                    last_trips = None

                    # Find a matching product to compare
                    for last in last_state.products:
                        if last.name != product.name or last.remaining_rides is None:
                            continue
                        last_trips = last.remaining_rides / 2.0
                        break

                    if last_trips is not None:
                        pedantic_remind = last_trips != round_trips and should_remind

                        app.logger.info('Ensuring a change in %s round trips for %s: %s' % (round_trips, product.name, pedantic_remind))
                        remind = remind or pedantic_remind
                        continue

                # The default case
                remind = remind or should_remind
            except:
                app.logger.exception('Exception checking round trips')
                pass

        return remind

    def _check_ride_reminder(self, card, last_state=None):
        """ Checks products for remaining rides that have fallen below threshold """
        remind = False
        threshold = int(self.threshold)
        for product in card.products:
            if product.remaining_rides is None:
                continue

            try:
                remaining_rides = int(product.remaining_rides)
                should_remind = remaining_rides <= threshold

                # Pedantic - check last state products for name match
                # and number of remaining rides
                if last_state:
                    last_rides = None

                    for last in last_state.products:
                        if last.name != product.name or last.remaining_rides is None:
                            continue
                        last_rides = int(last.remaining_rides)
                        break

                    if last_rides is not None:
                        pedantic_remind = last_rides != remaining_rides and should_remind

                        app.logger.info('Ensuring a change in %s rides for %s: %s' % (remaining_rides, product.name, pedantic_remind))
                        remind = remind or pedantic_remind
                        continue

                remind = remind or should_remind
            except:
                app.logger.exception('Exception checking rides')
                pass

        return remind

    def check_all_cards(self, force=False):
        from breezeminder.models.card import BreezeCard
        for card in BreezeCard.objects.filter(owner=self.owner):
            self.remind(card, force=force)

    def remind(self, card, force=False, last_state=None):
        # Get last reminded for card
        last_reminder_sent = self.last_reminded(card)
        if not force and last_reminder_sent and (datetime.now() - last_reminder_sent.sent_date).days < 1:
            # Don't proceed if we've already sent out a reminder today
            app.logger.info('%s Reminder for card %s has already been sent today. Last sent: %s' % (self.type,
                                                                                                    card.last_four,
                                                                                                    last_reminder_sent))
            return

        app.logger.info('Begin %s reminder check for %s' % (self.type, card.last_four))

        if not self.check_reminder(card, last_state=last_state):
            app.logger.info('Card %s does not need a %s reminder' % (card.last_four, self.type))
            return

        from flask import render_template
        from breezeminder.app import context, filters
        from breezeminder.models.messaging import Messaging

        app.logger.info('Reminding user %s of %s at or below threshold' % (self.owner.id, self.type))

        subject = '[BreezeMinder] %s reminder' % self.type.name
        messages = []
        context = {
            'card': card,
            'reminder': self,
            'last_state': last_state
        }

        # Build list of expiring content
        if self.type == 'EXP':
            delta = self._exp_delta()
            expiring = {
                'card': self._will_expire(card.expiration_date, delta)
            }

            expiring['products'] = [ p for p in card.products if self._will_expire(p.expiration_date, delta) ]
            context['expiring'] = expiring

        if self.send_email:
            template = 'messages/email/reminders/%s.html' % self.type.key.lower()
            with app.test_request_context():
                content = render_template(template, **context)

            # Queue message for celery
            Messaging.objects.create(recipients=[self.owner.email],
                                     sender=app.config['DEFAULT_MAIL_SENDER'],
                                     subject=subject,
                                     message=content)

        if self.send_sms:
            recipients=[]
            if self.owner.can_receive_sms:
                recipients.append(self.owner.cell_phone.sms_address)

            if len(recipients) > 0:
                template = 'messages/sms/reminders/%s.html' % self.type.key.lower()
                with app.test_request_context():
                    content = render_template(template, **context)

                # Make mobile friendly by removing excess whitespace
                content = re.sub('\s{2,}', ' ', content)

                subject = '%s reminder' % self.type.name

                # Queue message for celery
                Messaging.objects.create(recipients=recipients,
                                         sender=app.config['DEFAULT_MAIL_SENDER'],
                                         subject=subject.upper(), 
                                         message=content,
                                         is_plain=True)

        # Record History, but don't bring down the house
        try:
            with app.test_request_context():
                web_message = render_template('messages/web/reminders/%s.html' % self.type.key.lower(), **context)

            ReminderHistory.objects.create(reminder=self,
                                           card=card,
                                           message=web_message,
                                           sent_date=datetime.now(),
                                           owner=self.owner)
        except:
            app.logger.exception('Could not save a reminder history object')

        # Bump the last reminder
        self.save()


class ReminderHistory(BaseDocument):
    reminder = app.db.ReferenceField('Reminder', required=True, dbref=False,
                                     reverse_delete_rule=app.db.CASCADE)
    card = app.db.ReferenceField('BreezeCard', required=True, dbref=False,
                                 reverse_delete_rule=app.db.CASCADE)
    owner = app.db.ReferenceField('User', required=True, dbref=False,
                                  reverse_delete_rule=app.db.CASCADE)
    sent_date = app.db.DateTimeField(required=True)
    message = app.db.StringField()

    meta = {
        'collection': 'reminder_history',
        'queryset_class': ReminderHistoryQuerySet,
        'indexes': ['sent_date'],
        'ordering': ['-sent_date']
    }
