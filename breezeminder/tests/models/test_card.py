from BeautifulSoup import BeautifulSoup
from datetime import datetime, timedelta
from mock import patch
from unittest2 import TestCase

from breezeminder.app import app
from breezeminder.models.card import (BreezeCard,
                                      format_numeric_number)
from breezeminder.util.testing import silence_is_golden


EMPTY_CONTENT = '<html><body></body><html>'

FAKE_CONTENT = """
<html>
    <body>
        <table>
            <tr>
                <td>Your card will expire in some date 12-02-1984</td>
            </tr>
            <tr>
                <td>Stored Value</td>
                <td>$100.00</td>
            </td>
        </table>
    </body>
</html>
"""

PRODUCT_CONTENT = """
<html><body><table>
    <!-- Expected Header Row -->
    <tr><td>product name</td></tr>

    <!-- Valid Row -->
    <tr><td>Foo</td><td>12-02-1984</td><td>   100</td></tr>

    <!-- Empty Data -->
    <tr><td></td><td></td><td></td></tr>

    <!-- No Date -->
    <tr><td>Bar</td><td></td><td>   100</td></tr>

    <!-- No Rides -->
    <tr><td>Baz</td><td>12-02-1984</td><td></td></tr>

    <!-- Try to break the num rides -->
    <tr><td>Xyz</td><td></td><td>Hello</td></tr>

    <!-- Terminating Row -->
    <tr><td>That's it</td></tr>

    <!-- A row we won't see -->
    <tr>
        <td>INVISIBLE</td>
        <td>12-02-1984</td>
        <td>100</td>
    </tr>
</table></body></html>
"""

AUTOLOAD_CONTENT = """
<html><body><table>
    <!-- Expected Header Row -->
    <tr><td>pending autoload transactions</td></tr>

    <!-- Valid Row -->
    <tr><td>Foo</td><td>   100</td></tr>

    <!-- Empty Data -->
    <tr><td></td><td></td></tr>

    <!-- Try to break the value -->
    <tr><td>Xyz</td><td>Hello</td></tr>

    <!-- Terminating Row -->
    <tr><td>That's it</td></tr>

    <!-- A row we won't see -->
    <tr>
        <td>INVISIBLE</td>
        <td>100</td>
    </tr>
</table></body></html>
"""

FAKE_CONTENT_INVALID = FAKE_CONTENT.replace('12-02-1984', '')\
                                   .replace('$100.00', '')


class NumberOnlyFormatTestCase(TestCase):

    def test_format_numeric_number(self):
        self.assertEquals('123', format_numeric_number('a1b2c3'))
        self.assertEquals('123', format_numeric_number('   123   '))
        self.assertEquals('123', format_numeric_number('123'))
        self.assertEquals('', format_numeric_number('no_numbers_here'))


class BreezeCardTestCase(TestCase):

    def setUp(self):
        self.soup = BeautifulSoup(FAKE_CONTENT)
        self.bad_soup = BeautifulSoup(FAKE_CONTENT_INVALID)
        self.empty_soup = BeautifulSoup(EMPTY_CONTENT)
        self.test_date = {
            'month': 12,
            'day': 2,
            'year': 1984
        }

        self.card = BreezeCard(last_loaded=datetime(year=self.test_date['year'],
                                                    month=self.test_date['month'],
                                                    day=self.test_date['day']))
        self.card_number = '1111222233334444'
        self.card.set_number(self.card_number)

    def test_number_masked(self):
        self.assertEquals('************4444', self.card.number_masked)

    def test_next_refresh(self):
        mock_config = {'REFRESH_INTERVAL': timedelta(days=1)}

        with patch.dict(app.config, values=mock_config, clear=True):
            self.assertEquals(self.card.next_refresh,
                              datetime(year=self.test_date['year'],
                                       month=self.test_date['month'],
                                       day=self.test_date['day'] + 1))

    def test_can_refresh_with_limiting(self):
        mock_config = {
            'REFRESH_INTERVAL': timedelta(days=1),
            'REFRESH_LIMITING': True
        }

        with patch.dict(app.config, values=mock_config, clear=True):
            self.assertFalse(self.card.can_refresh)

    def test_can_refresh_without_limiting(self):
        mock_config = {
            'REFRESH_INTERVAL': timedelta(days=1),
            'REFRESH_LIMITING': False
        }

        # Test with date before now
        with patch.dict(app.config, values=mock_config, clear=True):
            self.assertTrue(self.card.can_refresh)

        # Test with date after now
        with patch.dict(app.config, values=mock_config, clear=True):
            old_val = self.card.last_loaded
            self.card.last_loaded = datetime(year=2999, month=1, day=1)
            self.assertFalse(self.card.can_refresh)
            self.card.last_loaded = old_val

    def test_set_number(self):
        # Check 4 characters
        num = '1234'
        self.card.set_number(num)
        self.assertEquals(num, self.card.number)
        self.assertEquals(num, self.card.last_four)

        # Edge case - less than four numbers
        num = '1'
        self.card.set_number(num)
        self.assertEquals(num, self.card.number)
        self.assertEquals(num, self.card.last_four)

        # With more than four numbers
        num = '11112222'
        self.card.set_number(num)
        self.assertEquals(num, self.card.number)
        self.assertEquals('2222', self.card.last_four)

        # With many non-numeric
        num = 'abc1X2X3xyz'
        self.card.set_number(num)
        self.assertEquals('123', self.card.number)
        self.assertEquals('123', self.card.last_four)

        # No Numbers
        num = 'foo_bar_baz'
        self.card.set_number(num)
        self.assertEquals('', self.card.number)
        self.assertEquals('', self.card.last_four)

    @silence_is_golden
    def test_parse_expiration_date(self, *args):
        self.assertEquals(self.card._parse_expiration_date(self.soup),
                          datetime(year=1984, month=12, day=2))
        self.assertIsNone(self.card._parse_expiration_date(self.bad_soup))
        self.assertIsNone(self.card._parse_expiration_date(self.empty_soup))

    @silence_is_golden
    def test_parse_stored_value(self, *args):
        self.assertEquals(self.card._parse_stored_value(self.soup), '100.00')
        self.assertIsNone(self.card._parse_stored_value(self.bad_soup))
        self.assertIsNone(self.card._parse_stored_value(self.empty_soup))

    @silence_is_golden
    def test_parse_products(self, *args):
        prod_soup = BeautifulSoup(PRODUCT_CONTENT)
        products = self.card._parse_products(prod_soup)
        expect_date = datetime(year=1984, month=12, day=2)
        self.assertEquals(5, len(products))
        self.assertEquals(products[0], {'name': 'Foo',
                                        'remaining_rides': 100,
                                        'expiration_date': expect_date})
        self.assertEquals(products[1], {'name': '',
                                        'remaining_rides': None,
                                        'expiration_date': None})
        self.assertEquals(products[2], {'name': 'Bar',
                                        'remaining_rides': 100,
                                        'expiration_date': None})
        self.assertEquals(products[3], {'name': 'Baz',
                                        'remaining_rides': None,
                                        'expiration_date': expect_date})
        self.assertEquals(products[4], {'name': 'Xyz',
                                        'remaining_rides': None,
                                        'expiration_date': None})

        empty_products = self.card._parse_products(self.empty_soup)
        self.assertEquals(0, len(empty_products))

    @silence_is_golden
    def test_parse_pending_transactions(self, *args):
        trans_soup = BeautifulSoup(AUTOLOAD_CONTENT)
        autoloads = self.card._parse_pending_transactions(trans_soup)
        self.assertEquals(3, len(autoloads))
        self.assertEquals(autoloads[0], {'name': 'Foo',
                                         'value': 100})
        self.assertEquals(autoloads[1], {'name': '',
                                         'value': 0.0})
        self.assertEquals(autoloads[2], {'name': 'Xyz',
                                         'value': 0.0})

        empty_autoloads = self.card._parse_pending_transactions(self.empty_soup)
        self.assertEquals(0, len(empty_autoloads))
