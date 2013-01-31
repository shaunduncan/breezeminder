from datetime import datetime, timedelta
from flask import (flash,
                   make_response,
                   redirect,
                   render_template,
                   request,
                   url_for)
from flask.ext.login import (current_user,
                             fresh_login_required)

from breezeminder.app import app
from breezeminder.forms.card import CreateCardForm
from breezeminder.models.card import BreezeCard
from breezeminder.models.reminder import Reminder
from breezeminder.util.views import nocache


@fresh_login_required
@nocache
def cards():
    cards = BreezeCard.objects.filter(owner=current_user._get_current_object())

    context = {
        'title': 'Manage Your Cards',
        'description': 'Manage your MARTA Breeze Cards',
        'cards': cards
    }

    return render_template('user/cards/index.html', **context)


@fresh_login_required
@nocache
def view_card(pk_hash):
    owner = current_user._get_current_object()
    card = BreezeCard.objects.get_or_404(pk_hash=pk_hash,
                                         owner=owner)

    # See if there are recent reminders
    reminder_log = []
    for reminder in Reminder.objects.filter(owner=owner):
        last_sent = reminder.last_reminded(card)
        reminder_log.append({
            'reminder': reminder,
            'last_sent': getattr(last_sent, 'sent_date', None)
        })

    context = {
        'title': 'Breeze Card %s' % card.number_masked,
        'description': 'Manage MARTA Breeze Card ending in %s' % card.last_four,
        'card': card,
        'reminder_log': reminder_log
    }
    return render_template('user/cards/view.html', **context)


@fresh_login_required
def card_ical(pk_hash):
    from icalendar import Calendar, Event
    from pytz import timezone

    card = BreezeCard.objects.get_or_404(pk_hash=pk_hash,
                                         owner=current_user._get_current_object())

    cache_key = 'ical-%s' % card.pk_hash
    ical_str = app.cache.get(cache_key)

    if ical_str is None:
        # Basics
        now = datetime.now()
        tzinfo = timezone('US/Eastern')
        now.replace(tzinfo=tzinfo)

        cal = Calendar()
        cal.add('prodid', '-//BreezeMinder//breezeminder.com//EN')
        cal.add('version', '2.0')

        # Basic formats
        card_exp_desc = '''Your Breeze Card ending in %s expires. To see details
visit https://%s%s or visit http://www.breezecard.com to reload your card or
purchase a new product.'''.replace('\n', ' ')

        product_exp_desc = '''Product %s on Breeze Card ending in %s expires.
To see details visit https://%s%s or visit http://www.breezecard.com to
reload your card or purchase a new product.'''.replace('\n', ' ')

        # Get card expiration
        try:
            event = Event()
            event.add('summary', 'Breeze Card %s Expiration Date' % card.number_masked)
            event.add('description', card_exp_desc % (card.last_four,
                                                      app.config['DOMAIN'],
                                                      url_for('user.cards.view', pk_hash=card.pk_hash)))
            event.add('dtstart', card.expiration_date.date())
            event.add('dtend', card.expiration_date.date() + timedelta(days=1))
            event.add('dtstamp', now)
            event.add('uid', '%s@%s' % (card.pk_hash, app.config['DOMAIN']))
            cal.add_component(event)
        except Exception:
            app.logger.exception('Cannot add card %s to ical' % card.last_four)

        # Get product expirations
        for product in card.products:
            try:
                event = Event()
                event.add('summary', 'Breeze Card Product %s Expiration Date' % product.name)
                event.add('description', product_exp_desc % (product.name,
                                                             card.last_four,
                                                             app.config['DOMAIN'],
                                                             url_for('user.cards.view', pk_hash=card.pk_hash)))
                event.add('dtstart', product.expiration_date.date())
                event.add('dtend', product.expiration_date.date() + timedelta(days=1))
                event.add('dtstamp', now)
                event.add('uid', '%s-%s-%s@%s' % (card.pk_hash,
                                                  product.name.replace(' ', '').lower(),
                                                  str(product.expiration_date.date()),
                                                  app.config['DOMAIN']))
                cal.add_component(event)
            except Exception:
                app.logger.exception('Cannot add product %s of card %s to ical' % (product.name, card.last_four))
        ical_str = cal.to_ical()
        app.cache.set(cache_key, ical_str, timeout=3600)

    # Create the resposne
    resp = make_response(render_template('core/content_only.html', content=ical_str))
    resp.cache_control.no_cache = True
    resp.headers['Content-Type'] = 'text/calendar'
    resp.headers['Content-Disposition'] = 'attachment; filename="breeze-card-%s.ics"' % card.last_four

    return resp


@fresh_login_required
@nocache
def reload_card(pk_hash):
    card = BreezeCard.objects.get_or_404(pk_hash=pk_hash,
                                         owner=current_user._get_current_object())

    if app.config.get('ALLOW_USER_REFRESH', False):
        if not app.config['REFRESH_LIMITING'] or (app.config['REFRESH_LIMITING'] and
                card.last_loaded + app.config['REFRESH_INTERVAL'] <= datetime.now()):
            card.pull_data()
            flash('Card information updated successfully', 'success')
        else:
            flash('Card information cannot be refreshed until after %s' % 
                    (card.last_loaded + app.config['REFRESH_INTERVAL']).strftime('%m/%d/%Y %I:%M %p'))

    return redirect(url_for('user.cards.view', pk_hash=card.pk_hash))


@fresh_login_required
@nocache
def add_card():
    form = CreateCardForm(request.form)
    if request.method == 'POST' and form.validate():
        try:
            card = BreezeCard.objects.create_fresh_card(form.cardnumber.data.strip(),
                                                        current_user._get_current_object())
            flash('Card added successfully', 'success')
            return redirect(url_for('user.cards'))
        except Exception, e:
            if 'duplicate' in str(e):
                flash('This card is already registered', 'error')
            else:
                flash('Your card was saved successfully, but it may not be immediately available', 'warning')
                app.logger.exception('Something has gone terribly wrong when creating a card')
                return redirect(url_for('user.cards'))

    context = {
        'title': 'Add New Breeze Card',
        'description': 'Add a new MARTA Breeze Card to your BreezeMinder.com account',
        'form': form
    }
    return render_template('user/cards/add.html', **context)


@fresh_login_required
@nocache
def delete_card(pk_hash):
    card = BreezeCard.objects.get_or_404(pk_hash=pk_hash,
                                         owner=current_user._get_current_object())
    card.delete()
    flash('Card removed successfully', 'success')
    return redirect(url_for('user.cards'))


app.add_url_rule('/cards/', 'user.cards', cards)
app.add_url_rule('/cards/view/<pk_hash>', 'user.cards.view', view_card)
app.add_url_rule('/cards/ical/<pk_hash>', 'user.cards.ical', card_ical)
app.add_url_rule('/cards/reload/<pk_hash>', 'user.cards.reload', reload_card, methods=['GET', 'POST'])
app.add_url_rule('/cards/add/', 'user.cards.add', add_card, methods=['GET', 'POST'])
app.add_url_rule('/cards/delete/<pk_hash>', 'user.cards.delete', delete_card)
