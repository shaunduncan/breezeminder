import re
import sys

from copy import deepcopy
from datetime import datetime
from BeautifulSoup import BeautifulSoup
from flask import render_template

from breezeminder.app import app, context, filters
from breezeminder.models.card import BreezeCard, Product
from breezeminder.models.messaging import Messaging
from breezeminder.models.user import User
from breezeminder.models.reminder import (Reminder,
                                          ReminderType,
                                          ReminderHistory)


def get_user(recip):
    return User.objects.get(email=recip)


def handle_expiration_date(message):
    reminder_type = ReminderType.objects.get(key='EXP')
    user = get_user(message.recipients[0])
    soup = BeautifulSoup(message.message)

    # Figure out the threshold of the reminder
    siblings = soup.p.findNextSiblings()
    thresh, quant = siblings[0].find('b').text.split(' ')
    last_four = re.findall(r'[0-9]{4}', siblings[0].text)[0]
    card = BreezeCard.objects.get(owner=user, last_four=last_four)

    # Try and find a reminder
    print 'Locating EXP reminder for %s (%s): %s, %s' % (user.email,
                                                         last_four,
                                                         thresh,
                                                         quant.capitalize())

    reminder = Reminder.objects.get(type=reminder_type,
                                    owner=user,
                                    threshold=thresh,
                                    quantifier=quant.capitalize())

    # Now we have a reminder, we have to FAKE a card state
    fake_card = deepcopy(card)
    fake_card.products = []

    for exp in siblings[1].findAll('li'):
        matches = re.findall(r'Product (.*) will expire on (.*)', exp.text)
        product, exp_date = matches[0]
        exp_date = datetime.strptime(exp_date, '%m/%d/%Y')

        fake_card.products.append(
            Product(name=product, expiration_date=exp_date)
        )

    # Render the template
    context = {
        'card': fake_card,
        'reminder': reminder,
        'expiring': {
            'card': False,
            'products': fake_card.products
        }
    }

    with app.test_request_context():
        output = render_template('messages/web/reminders/exp.html', **context)
        return ReminderHistory(reminder=reminder,
                               card=card,
                               message=output,
                               sent_date=message.created,
                               owner=user)


def handle_stored_value(message):
    reminder_type = ReminderType.objects.get(key='BAL')
    user = get_user(message.recipients[0])
    soup = BeautifulSoup(message.message)

    # Figure out the threshold of the reminder
    siblings = soup.p.findNextSiblings()
    thresh, card_val = map(lambda x: str(float(x.text.replace('$', ''))),
                           siblings[0].findAll('b'))

    last_four = re.findall(r'[0-9]{4}', siblings[0].text)[0]
    card = BreezeCard.objects.get(owner=user, last_four=last_four)

    # Try and find a reminder
    print 'Locating BAL reminder for %s (%s): %s' % (user.email,
                                                     last_four,
                                                     thresh)

    reminder = Reminder.objects.get(type=reminder_type,
                                    owner=user,
                                    threshold=thresh)

    # Now we have a reminder, we have to FAKE a card state
    fake_card = deepcopy(card)
    fake_card.stored_value = card_val

    context = {
        'card': fake_card,
        'reminder': reminder
    }

    with app.test_request_context():
        output = render_template('messages/web/reminders/bal.html', **context)
        return ReminderHistory(reminder=reminder,
                               card=card,
                               message=output,
                               sent_date=message.created,
                               owner=user)


def handle_remaining_rides(message):
    reminder_type = ReminderType.objects.get(key='RIDE')
    user = get_user(message.recipients[0])
    soup = BeautifulSoup(message.message)

    # Figure out the threshold of the reminder
    siblings = soup.p.findNextSiblings()
    thresh, _, foo = siblings[0].find('b').text.partition(' ')
    last_four = re.findall(r'[0-9]{4}', siblings[0].text)[0]
    card = BreezeCard.objects.get(owner=user, last_four=last_four)

    # Try and find a reminder
    print 'Locating RIDE reminder for %s (%s): %s' % (user.email,
                                                      last_four,
                                                      thresh)

    reminder = Reminder.objects.get(type=reminder_type,
                                    owner=user,
                                    threshold=thresh)

    # Now we have a reminder, we have to FAKE a card state
    fake_card = deepcopy(card)
    fake_card.products = []

    for state in siblings[1].findAll('li'):
        matches = re.findall(r'(.*) has (.*) remaining rides', state.text)
        product, rides = matches[0]

        fake_card.products.append(
            Product(name=product, remaining_rides=rides)
        )

    # Render the template
    context = {
        'card': fake_card,
        'reminder': reminder
    }

    with app.test_request_context():
        output = render_template('messages/web/reminders/ride.html', **context)
        return ReminderHistory(reminder=reminder,
                               card=card,
                               message=output,
                               sent_date=message.created,
                               owner=user)


fn_map = {
    'expiration_date': handle_expiration_date,
    'stored_value': handle_stored_value,
    'remaining_rides': handle_remaining_rides
}


messages = []

# Get a list of potential candidates
for m in Messaging.objects.all():
    if 'help@breezeminder.com' in m.recipients:
        continue

    if (m.subject.startswith('[BM Feedback]') or
        m.subject.startswith('Welcome to BreezeMinder') or
        m.subject.startswith('BREEZEMINDER VERIFY')):
            continue

    if m.subject.startswith('[BreezeMinder]'):
        messages.append(m)

history = []

for message in messages:
    msg_type = message.subject.replace('[BreezeMinder] ', '').replace(' reminder', '')
    msg_type = msg_type.replace(' ','_').lower()

    try:
        history.append(fn_map[msg_type](message))
    except Exception, e:
        print e

args = sys.argv[1:]
if '--go' in args:
    print 'SAVING %s HISTORY ITEMS' % len(history)
    for h in history:
        h.save()
else:
    print 'WILL SAVE %s HISTORY ITEMS WITH --go' % len(history)
