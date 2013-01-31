from wtforms import (Form,
                     BooleanField,
                     HiddenField,
                     FormField,
                     TextField,
                     PasswordField,
                     SelectField)
from wtforms.validators import (email,
                                equal_to,
                                required)
from werkzeug.datastructures import MultiDict

from breezeminder.app import app
from breezeminder.forms.validators import (Conditional,
                                           Unique,
                                           PhoneNumber)
from breezeminder.models.user import User
from breezeminder.models.wireless import WirelessCarrier


YES_NO_CHOICES = [
    ('Y', 'Yes'),
    ('N', 'No')
]


@app.cache.memoize(timeout=3600)
def _wireless_providers():
    carriers = [('', '')]
    for carrier in WirelessCarrier.objects.all().order_by('+name'):
        carriers.append((carrier.pk_hash, carrier.name))

    return carriers


class LoginForm(Form):
    email = TextField('Email Address',
                      validators=[required(),
                                  email(message='You must enter a valid email address')])
    password = PasswordField('Password', validators=[required()])


class PasswordChangeForm(Form):
    current_password = PasswordField('Current Password',
                                     validators=[required()])
    password = PasswordField('New Password',
                             validators=[required(),
                                         equal_to('confirm', message='Passwords must match')])
    confirm = PasswordField('Confirm Password', validators=[required()])


class ResetPasswordForm(Form):
    email = TextField('Email Address',
                      validators=[required(),
                                  email(message='You must enter a valid email address')])


class RegisterForm(Form):
    first_name = TextField('First Name')
    last_name = TextField('Last Name')
    email = TextField('Email Address',
                      validators=[required(),
                                  email(message='You must enter a valid email address'),
                                  Unique(User, 'email', ignorecase=True, message='This email is already registered')])
    password = PasswordField('Password',
                             validators=[required(),
                                         equal_to('confirm', message='Passwords must match')])
    confirm = PasswordField('Confirm Password', validators=[required()])
    agree_terms = BooleanField('I agree to the <a href="/terms" title="Terms of Service">terms of service</a>',
                               validators=[required(message='You must agree to the terms and conditions')])
    read_privacy = BooleanField('I have read and understand the BreezeMinder <a href="/privacy" title="Privacy Policy">privacy policy</a>',
                                validators=[required(message="You must read the privacy policy. It's important!")])
                            

class VerifyCellForm(Form):
    verify_code = TextField('Verification Code', validators=[required()])


class ProfileForm(Form):
    first_name = TextField('First Name')
    last_name = TextField('Last Name')
    phone_type = HiddenField('Type', default='C')
    phone_carrier = SelectField('Wireless Carrier', choices=_wireless_providers(),
                                validators=[
                                    Conditional('phone_number', '', validators=[required()], not_equals=True)
                                  ])
    phone_number = TextField('Number',
                             validators=[
                                 PhoneNumber(),
                                 Conditional('phone_carrier', '', validators=[required()], not_equals=True)
                              ])

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        if self.phone_carrier is not None:
            self.phone_carrier.choices = _wireless_providers()

    def populate_user(self, user):
        user.first_name = self.first_name.data
        user.last_name = self.last_name.data

        if self.phone_number.data:
            import re
            from breezeminder.models.user import PhoneNumber
            from breezeminder.models.wireless import WirelessCarrier
            from breezeminder.util.shortcodes import shortcode

            try:
                old_number = getattr(user.cell_phone, 'number', '')
                user.cell_phone = PhoneNumber(type=self.phone_type.data,
                                              carrier=WirelessCarrier.objects.get(pk_hash=self.phone_carrier.data),
                                              number=re.sub(r'[^0-9]', '', self.phone_number.data))

                if user.cell_phone.number != old_number or not user.cell_verified:
                    user.cell_verified = False
                    user.cell_verify_code = shortcode(user.cell_phone.number)
            except:
                app.logger.exception('Saving user wireless number failed')

    @staticmethod
    def from_user(user):
        data = {
            'first_name': user.first_name,
            'last_name': user.last_name
        }

        # The phone field
        if user.cell_phone:
            data['phone_type'] = user.cell_phone.type
            data['phone_carrier'] = user.cell_phone.carrier.pk_hash
            data['phone_number'] = user.cell_phone.number

        # Remove any None values
        for key in data.copy():
            if data[key] is None:
                del data[key]

        return ProfileForm(MultiDict(data))
