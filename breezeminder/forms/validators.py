import re
from wtforms import ValidationError
from wtforms.validators import Optional

from breezeminder.models.card import BreezeCard
from breezeminder.util.crypto import encrypt


class ModelValidator(object):

    def __init__(self, klass, field, message=None):
        self.klass = klass
        self.field = field
        self.message = message


class ActiveStateValidator(object):
    active = True

    def activate(self):
        self.active = True

    def deactivate(self):
        self.active = False


class Unique(ModelValidator, ActiveStateValidator):
    """ Check for value uniqueness """
    active = True

    def __init__(self, klass, field, message=None, ignorecase=False):
        self.ignorecase = ignorecase
        if not message:
            message = 'This value must be unique'
        super(Unique, self).__init__(klass, field, message=message)

    def __call__(self, form, field):
        if not self.active:
            return

        if self.ignorecase:
            filter = {'%s__iexact' % self.field: field.data.strip()}
            check = self.klass.objects.filter(**filter).count() > 0
        else:
            check = field.data.strip() in self.klass.objects.distinct(self.field)

        if check:
            raise ValidationError(self.message)


class Numeric(ActiveStateValidator):
    def __init__(self, length=None, message=None):
        if not message:
            if length is not None:
                message = 'This value must be a %i digit number' % length
            else:
                message = 'This value must be a number'
        self.message = message
        self.length = length

    def __call__(self, form, field):
        if not self.active:
            return

        value = re.sub(r'[^0-9]', '', field.data.strip())
        if not value.isdigit() or (self.length is not None and len(value) != self.length):
            raise ValidationError(self.message)


class CardNumber(Numeric):
    """ Check a card number is 16 digits """

    def __init__(self, message=None):
        super(CardNumber, self).__init__(16, message)

    def __call__(self, form, field):
        if not self.active:
            return

        value = re.sub(r'[^0-9]', '', field.data.strip())
        if len(value) != 16:
            raise ValidationError(self.message)


class UniqueCardNumber(CardNumber):
    """ Encrypts a number to check it for uniqueness """

    def __init__(self, message=None):
        super(UniqueCardNumber, self).__init__()
        if message is None:
            message = 'This card belongs to another user'
        self.card_message = message

    def __call__(self, form, field):
        if not self.active:
            return

        super(UniqueCardNumber, self).__call__(form, field)
        try:
            check = BreezeCard.objects.get(_number=encrypt(field.data.strip()))
            if check is not None:
                raise ValidationError(self.card_message)
        except:
            pass


class ExactLength(ActiveStateValidator):
    """ Checks that a field is an exact length """

    def __init__(self, length, message=None):
        self.length = length
        if message is None:
            message = 'This field must have a length of %s characters' % length
        self.message = message

    def __call__(self, form, field):
        if not self.active:
            return

        if len(field.data.strip()) != self.length:
            raise ValidationError(self.message)


class PhoneNumber(Numeric):
    """ Check a phone number is 10 digits """
    valid_phone_pattern = re.compile(r'^([2-9][0-9]{2}){2}[0-9]{4}$')
    invalid_patterns = [
        re.compile(r'^\d{3}555\d{4}$'),  # Non 555 numbers
        re.compile(r'^(\d11\d{7}|\d{4}11\d{4})$'),  # Non N11 numbers
    ]

    def __init__(self, message=None):
        super(PhoneNumber, self).__init__(10, message)

    def __call__(self, form, field):
        if not self.active:
            return

        value = re.sub(r'[^0-9]', '', field.data.strip())

        # Check empty and valid length
        if (not value) or len(value) != 10:
            raise ValidationError(self.message)

        # Check valid pattern
        if not self.valid_phone_pattern.match(value):
            raise ValidationError(self.message)

        # Check all patterns that must pass
        for pat in self.invalid_patterns:
            if pat.match(value):
                raise ValidationError(self.message)


class PositiveNumber(ActiveStateValidator):
    """ Checks that a value is positive. Expects an integer or float field """
    def __init__(self, message=None):
        if message is None:
            message = 'This value must be greater than 0'
        self.message = message

    def __call__(self, form, field):
        if not self.active:
            return

        try:
            if int(field.data) < 0:
                raise ValidationError(self.message)
        except:
            raise ValidationError(self.message)


class Conditional(ActiveStateValidator):
    """
    Conditionally apply a validator if the value of another field if
    that field's value matches the one we're looking for. Specify the
    form field name as a string and the value that should invoke a passed
    list of validators. The validators kwarg could be either a list or single
    validator.

    There's also an expectation that conditional validators will completely
    override any optional validator.
    """
    active = True

    def __init__(self, field, value, validators=[], not_equals=False):
        self.field = field
        self.value = value
        self.not_equals = not_equals
        if not isinstance(validators, list):
            validators = [validators]
        self.validators = validators

    def __call__(self, form, field):
        if not self.active:
            return

        field_data = getattr(form, self.field).data.strip()

        # Don't invoke validators if 
        # 1) We want non-equal values and the values are equal
        # 2) We want equal values and the values are not equal
        if (self.not_equals and field_data == self.value) or \
                ((not self.not_equals) and field_data != self.value):
            return

        for validator in self.validators:
            validator(form, field)


class ActiveStateOptional(Optional, ActiveStateValidator):
    """ Allows disabling """
    
    def __call__(self, form, field):
        if not self.active:
            return

        super(ActiveStateOptional, self).__call__(form, field)
