from flaskext.mail import Message

from breezeminder.app import app
from breezeminder.models.base import (BaseDocument,
                                      BaseQuerySet)


class MessagingQuerySet(BaseQuerySet):
    pass


class Messaging(BaseDocument):
    """
    Specifically used to log/schedule outgoing messages so they
    don't get sent at random times during the day.
    """

    subject = app.db.StringField()
    message = app.db.StringField()
    sender = app.db.StringField(required=True, default=app.config['DEFAULT_MAIL_SENDER'])
    recipients = app.db.ListField(app.db.StringField(), required=True)
    is_plain = app.db.BooleanField(required=True, default=False)
    is_sent = app.db.BooleanField(required=True, default=False)
    is_immediate = app.db.BooleanField(required=True, default=False)

    meta = {
        'collection': 'messaging',
        'queryset_class': MessagingQuerySet,
        'indexes': [
            ('is_sent', 'is_immediate'),
            'created'
        ]
    }

    def _get_masked_recipients(self):
        masked = []
        for recipient in self.recipients:
            addr, domain = recipient.split('@')
            masked_addr = '*' * len(addr)
            masked.append('@'.join([masked_addr, domain]))
        return masked

    def send(self, conn=None):
        """ Sends a message and marks it as sent """
        msg = Message(recipients=self.recipients,
                      sender=self.sender,
                      subject=self.subject)
        
        if self.is_plain:
            msg.body = self.message
        else:
            msg.html = self.message

        # Obfuscate the log
        masked_recipients = self._get_masked_recipients()

        app.logger.info('MAIL: %s: %s' % (masked_recipients, self.subject))
        app.logger.debug('Sending mail to %s: %s\n%s' % (masked_recipients,
                                                         self.subject,
                                                         self.message))

        if conn is None:
            with app.mail.connect() as conn:
                conn.send(msg)
        else:
            conn.send(msg)

        # Mark as sent
        self.is_sent = True
        self.save()
