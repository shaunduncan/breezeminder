from mock import Mock
from unittest2 import TestCase

from breezeminder.forms.reminder import ReminderForm


class ReminderFormTestCase(TestCase):

    def setUp(self):
        self.form = ReminderForm()

        self.bal_rem = Mock()
        self.bal_rem.type = 'BAL'
        self.bal_rem.threshold = '12.34'

        self.ride_rem = Mock()
        self.ride_rem.type = 'RIDE'
        self.ride_rem.threshold = '10'

        self.exp_rem = Mock()
        self.exp_rem.type = 'EXP'
        self.exp_rem.threshold = '1'
        self.exp_rem.quantifier = 'Days'

    def test_is_change_from_different_types(self):
        self.form.type.data = self.bal_rem.type
        self.form.balance_threshold.data = self.bal_rem.threshold
        self.assertFalse(self.form.is_changed_from(self.bal_rem))

        self.form.type.data = self.exp_rem.type
        self.assertTrue(self.form.is_changed_from(self.bal_rem))

    def test_is_changed_from_balance(self):
        self.form.type.data = self.bal_rem.type
        self.form.balance_threshold.data = self.bal_rem.threshold
        self.assertFalse(self.form.is_changed_from(self.bal_rem))

        self.form.balance_threshold.data = '13.37'
        self.assertTrue(self.form.is_changed_from(self.bal_rem))

        # Ensure problems are handled
        self.form.balance_threshold.data = 'foo'
        self.bal_rem.threshold = 'bar'
        self.assertFalse(self.form.is_changed_from(self.bal_rem))

    def test_is_changed_from_ride(self):
        self.form.type.data = self.ride_rem.type
        self.form.ride_threshold.data = self.ride_rem.threshold
        self.assertFalse(self.form.is_changed_from(self.ride_rem))

        self.form.ride_threshold.data = '25'
        self.assertTrue(self.form.is_changed_from(self.ride_rem))

        # Ensure problems are handled
        self.form.ride_threshold.data = 'foo'
        self.ride_rem.threshold = 'bar'
        self.assertFalse(self.form.is_changed_from(self.ride_rem))

    def test_is_changed_from_exp(self):
        self.form.type.data = self.exp_rem.type
        self.form.exp_threshold.data = self.exp_rem.threshold
        self.form.exp_quantity.data = self.exp_rem.quantifier
        self.assertFalse(self.form.is_changed_from(self.exp_rem))

        self.form.exp_threshold.data = '25'
        self.form.exp_quantity.data = self.exp_rem.quantifier
        self.assertTrue(self.form.is_changed_from(self.exp_rem))

        self.form.exp_threshold.data = self.exp_rem.threshold
        self.form.exp_quantity.data = 'Decades'
        self.assertTrue(self.form.is_changed_from(self.exp_rem))

        # Ensure problems are handled
        self.form.exp_threshold.data = 'foo'
        self.exp_rem.threshold = 'bar'
        self.assertFalse(self.form.is_changed_from(self.exp_rem))
