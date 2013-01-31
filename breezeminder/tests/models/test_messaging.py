from unittest2 import TestCase

from breezeminder.models.messaging import Messaging


class MessagingTestCase(TestCase):

    def setUp(self):
        self.message = Messaging(subject='Foo',
                                 message='Bar',
                                 sender='no-reply@foo.com',
                                 recipients=['foo@bar.com', 'bar@baz.com'])

    def test__get_masked_recipients(self):
        masked = self.message._get_masked_recipients()
        self.assertEqual('***@bar.com', masked[0])
        self.assertEqual('***@baz.com', masked[1])
