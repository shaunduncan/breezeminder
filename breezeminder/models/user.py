import re

from flask.ext.login import UserMixin
from hashlib import md5, sha1

from breezeminder.app import app
from breezeminder.models.base import (BaseDocument,
                                      BaseQuerySet)


PHONE_TYPES = [
    ('H', 'Home'),
    ('C', 'Cell'),
    ('W', 'Work'),
]


_phone_num_pat = re.compile(r'(\d{3})(\d{3})(\d{4})')


class PhoneNumber(app.db.EmbeddedDocument):
    type = app.db.StringField(required=True, choices=PHONE_TYPES)
    carrier = app.db.ReferenceField('WirelessCarrier', dbref=False)
    number = app.db.StringField(required=True, max_length=10)

    @property
    def sms_address(self):
        if self.carrier is not None:
            return '%s@%s' % (self.number, self.carrier.sms_domain)

    def format(self):
        return _phone_num_pat.sub('(\\1) \\2-\\3', self.number)


class UserQuerySet(BaseQuerySet):
    pass


class User(BaseDocument, UserMixin):
    email = app.db.EmailField(required=True, unique=True)
    password = app.db.StringField(required=True, max_length=80)
    first_name = app.db.StringField()
    last_name = app.db.StringField()
    is_admin = app.db.BooleanField(required=True, default=False)
    is_verified = app.db.BooleanField(required=True, default=False)
    cell_phone = app.db.EmbeddedDocumentField('PhoneNumber')
    cell_verify_code = app.db.StringField()  # Hash ObjectId()
    cell_verified = app.db.BooleanField(required=True, default=False)

    meta = {
        'collection': 'users',
        'queryset_class': UserQuerySet,
        'indexes': [
            ('email', 'password', 'is_verified'),
            {
                'fields': ['cell_verify_code'],
                'sparse': True,
                'unique': True
            },
            {
                'fields': ['email'],
                'unique': True
            }
        ]
    }

    @property
    def gravatar_hash(self):
        return md5(self.email.strip().lower()).hexdigest()

    @classmethod
    def hash_password(self, password):
        salted = '%s%s' % (app.config.get('SECRET_KEY', ''), password)
        return sha1(salted).hexdigest()

    @property
    def needs_to_verify_phone(self):
        return getattr(self.cell_phone, 'number', '') and \
                self.cell_verify_code and \
                not self.cell_verified

    @property
    def can_receive_sms(self):
        return getattr(self.cell_phone, 'number', '') and self.cell_verified

    def send_cell_verification(self):
        if getattr(self.cell_phone, 'number', ''):
            from breezeminder.models.messaging import Messaging
            Messaging.objects.create(recipients=[self.cell_phone.sms_address],
                                     sender=app.config['DEFAULT_MAIL_SENDER'],
                                     subject='BREEZEMINDER VERIFY CODE',
                                     message='Your verification code is %s' % self.cell_verify_code,
                                     is_plain=True,
                                     is_immediate=True)

    def verify(self):
        self.is_verified = True
        self.save()

    def set_password(self, password):
        """ Properly handles the hashing """
        self.password = self.hash_password(password)

    def check_reminders(self, card=None, **kwargs):
        """
        Check a user's reminders against a specified card or all
        user cards if not supplied
        """
        from breezeminder.models.card import BreezeCard
        from breezeminder.models.reminder import Reminder

        reminders = Reminder.objects.filter(owner=self)
        check_cards = []

        if card is not None:
            check_cards.append(card)
        else:
            check_cards = BreezeCard.objects.filter(owner=self)

        for card in check_cards:
            for reminder in reminders:
                reminder.remind(card, **kwargs)
