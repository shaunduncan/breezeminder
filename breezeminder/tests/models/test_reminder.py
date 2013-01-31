from copy import deepcopy
from datetime import datetime
from dateutil.relativedelta import relativedelta
from mock import Mock
from unittest2 import TestCase

from breezeminder.models.reminder import Reminder
from breezeminder.util.testing import silence_is_golden


class ReminderTestCase(TestCase):

    def setUp(self):
        self.bal_rem = Reminder(type='BAL', threshold=19.99)
        self.exp_rem = Reminder(type='EXP', threshold=2, quantifier='weeks')
        self.ride_rem = Reminder(type='RIDE', threshold=5)
        self.round_trip_rem = Reminder(type='ROUND_TRIP', threshold=3)

        # Mock a card
        self.card = Mock()
        self.card.expiration_date = datetime(year=1984, month=12, day=2)
        self.card.stored_value = 1
        self.card.products = []

        # Add some products
        for i in range(1,4):
            prod = Mock()
            prod.name = 'Product-%s' % i
            prod.expiration_date = datetime(year=1984, month=12, day=i)
            prod.remaining_rides = i
            self.card.products.append(prod)

    def test_description(self):
        self.assertIn('Stored Value', self.bal_rem.description(html=False))
        self.assertIn('$19.99', self.bal_rem.description(html=False))

        self.assertIn('falls below 5', self.ride_rem.description(html=False))

        self.assertIn('2 weeks away', self.exp_rem.description(html=False))

    @silence_is_golden
    def test_check_reminder_invalids(self, *args):
        self.bal_rem.valid_until = datetime(year=1984, month=12, day=2)
        self.assertFalse(self.bal_rem.check_reminder(Mock()))

    @silence_is_golden
    def test_check_balance_reminder(self, *args):
        self.card.stored_value = 9.99
        self.assertTrue(self.bal_rem._check_balance_reminder(self.card))

        # Check we only remind ONCE if there isn't a change
        last_state = deepcopy(self.card)
        self.assertFalse(self.bal_rem._check_balance_reminder(self.card, last_state))

        # And that we remind if there is a change
        self.card.stored_value = 9.98
        self.assertTrue(self.bal_rem._check_balance_reminder(self.card, last_state))

        self.card.stored_value = 29.99
        self.assertFalse(self.bal_rem._check_balance_reminder(self.card))
        
        self.card.stored_value = 'foo'
        self.assertFalse(self.bal_rem._check_balance_reminder(self.card))

    @silence_is_golden
    def test_check_expiration_reminder(self, *args):
        now = datetime.now()

        for quant in ['Days', 'Weeks', 'Months']:
            self.exp_rem.quantifier = quant
            self.exp_rem.threshold = 1

            # Expired cards always return False
            self.assertFalse(self.exp_rem._check_expiration_reminder(self.card))

            # Upcoming expirations will return True
            self.card.expiration_date = now + relativedelta(**{quant.lower(): 1})
            self.assertTrue(self.exp_rem._check_expiration_reminder(self.card))

            # ...so long as they are X quantity away exactly
            self.card.expiration_date = now + relativedelta(**{quant.lower(): 1}) - relativedelta(days=1)
            self.assertFalse(self.exp_rem._check_expiration_reminder(self.card))

            # Expirations that don't meet criteria of reminder are false
            self.card.expiration_date = now + relativedelta(hours=1)
            self.assertFalse(self.exp_rem._check_expiration_reminder(self.card))

            # Make sure products are checked
            self.card.expiration_date = datetime(year=2999, month=12, day=31)
            for prod in self.card.products:
                prod.expiration_date = now + relativedelta(**{quant.lower(): 1})
            self.assertTrue(self.exp_rem._check_expiration_reminder(self.card))

    @silence_is_golden
    def test_check_round_trip_reminder(self, *args):
        # Check that they should remind
        for prod in self.card.products:
            prod.remaining_rides = 2
        self.assertTrue(self.round_trip_rem._check_round_trip_reminder(self.card))

        # Check they remind ONCE without change
        last_state = deepcopy(self.card)
        self.assertFalse(self.round_trip_rem._check_round_trip_reminder(self.card, last_state=last_state))

        # Check they remind if there is one change
        self.card.products[0].remaining_rides = 1
        self.assertTrue(self.round_trip_rem._check_round_trip_reminder(self.card, last_state=last_state))

        # Check that they should not remind
        for prod in self.card.products:
            prod.remaining_rides = 9999
        self.assertFalse(self.round_trip_rem._check_round_trip_reminder(self.card))

    @silence_is_golden
    def test_check_ride_reminder(self, *args):
        # Check that they should remind
        for prod in self.card.products:
            prod.remaining_rides = 3
        self.assertTrue(self.ride_rem._check_ride_reminder(self.card))

        # Check that they should remind ONCE if there is no change
        last_state = deepcopy(self.card)
        self.assertFalse(self.ride_rem._check_ride_reminder(self.card, last_state=last_state))

        # But we should remind for at least ONE change
        self.card.products[0].remaining_rides = 2
        self.assertTrue(self.ride_rem._check_ride_reminder(self.card, last_state=last_state))

        # Check that they should not remind
        for prod in self.card.products:
            prod.remaining_rides = 9999
        self.assertFalse(self.ride_rem._check_ride_reminder(self.card))
