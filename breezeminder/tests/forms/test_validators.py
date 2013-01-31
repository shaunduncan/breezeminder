from mock import Mock
from unittest2 import TestCase
from wtforms import ValidationError

from breezeminder.forms.validators import (Numeric,
                                           CardNumber,
                                           ExactLength,
                                           PhoneNumber,
                                           PositiveNumber,
                                           Conditional)


class ValidatorTestCase(TestCase):

    def setUp(self):
        self.form = Mock()
        self.field = Mock()
        self.valids = []
        self.invalids = []

    def test_for_valids(self):
        for val in self.valids:
            self.field.data = val
            self.assertIsNone(self.validator(self.form, self.field))

    def test_for_invalids(self):
        for val in self.invalids:
            self.field.data = val
            with self.assertRaises(ValidationError):
                self.validator(self.form, self.field)


class NumericTestCase(ValidatorTestCase):

    def setUp(self):
        super(NumericTestCase, self).setUp()
        self.validator = Numeric()
        self.valids = ['123', 'foo1bar2baz3', '@@@123', ' 1 2 3 ']
        self.invalids = ['foo', 'bar', 'baz']


class CardNumberTestCase(ValidatorTestCase):

    def setUp(self):
        super(CardNumberTestCase, self).setUp()
        self.validator = CardNumber()
        self.valids = ['1111222233334444',
                          '1111a2222b3333c4444d',
                          ' 1 1 1 1 2 2 2 2 3 3 3 3 4 4 4 4']
        self.invalids = ['123', 'foo', '111222333444']


class ExactLengthTestCase(ValidatorTestCase):

    def setUp(self):
        super(ExactLengthTestCase, self).setUp()
        self.validator = ExactLength(length=3)
        self.valids = ['123', 'foo', 'bar', 'baz', '@@@']
        self.invalids = ['a', 'foobar', 'thiswillfaileverytime']


class PhoneNumberTestCase(ValidatorTestCase):

    def setUp(self):
        super(PhoneNumberTestCase, self).setUp()
        self.validator = PhoneNumber()
        self.valids = ['4042004824',
                       '6782229899',
                       '4042001234']
        self.invalids = ['4045551234',
                         '+14042004824',  # This SHOULD be valid, just not now
                         '1887898788',
                         '4041118980',
                         '911',
                         '411',
                         '4049111234',
                         '9113774878']


class PositiveNumberTestCase(ValidatorTestCase):

    def setUp(self):
        super(PositiveNumberTestCase, self).setUp()
        self.validator = PositiveNumber()
        self.valids = ['1', '0', '100', '1000', '+1']
        self.invalids = ['foo', '-1', '-1000']


def fake_raising_validator(*args):
    raise ValidationError('FooBar')


class ConditionalTestCase(TestCase):

    def setUp(self):
        self.form = Mock()
        self.form.field = Mock()
        self.field = Mock()
        self.validator = Conditional('field',
                                     'foo',
                                     validators=[fake_raising_validator])
        self.validator_ne = Conditional('field',
                                        'foo',
                                        validators=[fake_raising_validator],
                                        not_equals=True)

    def test_not_equals_invokes_validator(self):
        self.form.field.data = 'bar'

        with self.assertRaises(ValidationError):
            self.validator_ne(self.form, self.field)

    def test_equals_invokes_validator(self):
        self.form.field.data = 'foo'

        with self.assertRaises(ValidationError):
            self.validator(self.form, self.field)

    def test_validator_not_invoked(self):
        self.form.field.data = 'foo'
        self.assertIsNone(self.validator_ne(self.form, self.field))

        self.form.field.data = 'bar'
        self.assertIsNone(self.validator(self.form, self.field))
