from datetime import datetime, timedelta
from unittest2 import TestCase

from breezeminder.app.filters import (slugify,
                                      safe_strftime,
                                      money,
                                      timesince)


class JinjaFilterTestCase(TestCase):

    def test_slugify(self):
        self.assertEquals('my-foo-bar', slugify('my @foo bar!!!'))
        self.assertEquals('my-foo-bar', slugify('MY______Foo@bAR'))

    def test_safe_strftime(self):
        self.assertEquals('', safe_strftime(None))
        self.assertEquals('12/02/1984', safe_strftime(datetime(year=1984,
                                                               month=12,
                                                               day=2)))

    def test_money(self):
        # Test formatting/rounding
        self.assertEquals('$12.34', money('12.34'))
        self.assertEquals('$12.35', money('12.34999'))
        self.assertEquals('$12.34', money('12.34111'))

        # Test edge cases
        self.assertEquals('$0.00', money(None))
        self.assertEquals('$0.00', money('Foo'))

    def test_timesince(self):
        # Testable using timedelta
        for period in ['seconds', 'minutes', 'hours', 'days', 'weeks']:
            expecting = '1 %s ago' % period[:-1]
            dt = datetime.now() - timedelta(**{period: 1})
            self.assertEquals(expecting, timesince(dt)) 

        # Try to see if 5 weeks ago 
        now = datetime.now()
        dt = now - timedelta(weeks=5)

        if dt.month == now.month:
            dt = now - timedelta(weeks=6)

        self.assertEquals('1 month ago', timesince(dt))
