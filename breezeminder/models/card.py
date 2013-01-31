import re
import requests

from BeautifulSoup import BeautifulSoup
from copy import deepcopy
from datetime import datetime

from breezeminder.app import app
from breezeminder.models.base import (BaseDocument,
                                      BaseQuerySet)
from breezeminder.util.crypto import encrypt, decrypt


BREEZECARD_ENDPOINT = 'https://balance.breezecard.com/breezeWeb/cardnumber_qa.do'

_numeric_only_pat = re.compile(r'[^0-9]')


def format_numeric_number(value):
    return _numeric_only_pat.sub('', value)


class BreezeCardQuerySet(BaseQuerySet):
    def create_fresh_card(self, number, owner):
        from breezeminder.tasks import pull_card_data

        # Create the card and schedule it to be pulled
        card = BreezeCard(owner=owner, number=_numeric_only_pat.sub('', number))
        card.save()

        pull_card_data.delay(card.id)
        return card


class CardDataQuerySet(BaseQuerySet):
    pass


class InvalidCardDataQuerySet(BaseQuerySet):
    pass


class BreezeCard(BaseDocument):
    """ Self-explanatory class """
    _number = app.db.StringField(required=True)
    last_four = app.db.StringField(required=True, min_length=4, max_length=4)
    expiration_date = app.db.DateTimeField()
    stored_value = app.db.DecimalField(default=0.0)
    owner = app.db.ReferenceField('User', required=True, dbref=False,
                                  reverse_delete_rule=app.db.CASCADE)
    products = app.db.ListField(app.db.EmbeddedDocumentField('Product'))
    pending = app.db.ListField(app.db.EmbeddedDocumentField('PendingTransaction'))
    last_loaded = app.db.DateTimeField()
    has_data = app.db.BooleanField(required=True, default=False)
    _shorturl = app.db.StringField()

    meta = {
        'collection': 'breezecards',
        'queryset_class': BreezeCardQuerySet,
        'indexes': [
            {
                'fields': ['_number'],
                'unique': True,
            },
            'owner',
            'expiration_date',
            'last_loaded',
        ]
    }

    @property
    def shorturl(self):
        check_cache_key = 'bitly-%s' % self.pk_hash

        if self._shorturl is None and app.cache.get(check_cache_key) is None:
            # Shorten the absolute URL for this card
            import bitly_api
            abs_url = 'https://breezeminder.com/cards/view/%s' % self.pk_hash

            # Grab from bitly
            try:
                bitly = bitly_api.Connection(app.config['BITLY_USERNAME'],
                                             app.config['BITLY_API_KEY'])
                data = bitly.shorten(abs_url, preferred_domain='j.mp')

                app.logger.debug('Bitly returned data: %s' % data)
                self._shorturl = data['url']
                self.save()
            except:
                # Log the exception and do not try again for an hour
                app.logger.exception('An exception occurred contacting bitly')
                app.cache.set(check_cache_key, True, timeout=3600)

        return self._shorturl or ''

    @property
    def number(self):
        # Note, decrypt() is memoized for 1 hour
        return decrypt(self._number)

    @property
    def number_masked(self):
        return '%s%s' % ('*' * 12, self.last_four)

    @property
    def next_refresh(self):
        return self.last_loaded + app.config['REFRESH_INTERVAL']

    @property
    def can_refresh(self):
        if not app.config['REFRESH_LIMITING'] and self.next_refresh < datetime.now():
            return True
        return False

    def set_number(self, value):
        value = format_numeric_number(value)
        self.last_four = value[-4:]
        self._number = encrypt(value)

    def __setattr__(self, attr, value):
        if attr == 'number':
            self.set_number(value)
        else:
            super(BreezeCard, self).__setattr__(attr, value)

    def fetch_remote_data(self):
        app.logger.info('Fetching remote data for card %s' % self.number_masked)

        payload = {
            'cardnumber': format_numeric_number(self.number),
            'submitButton.x': '0',
            'submitButton.y': '0'
        }

        # Try to post with retry one time, then fail if error
        resp = requests.post(BREEZECARD_ENDPOINT, data=payload, verify=False,
                             config={'max_retries': 1})
        app.logger.debug('Card fetch for %s returned %s' % (self.number_masked, resp.content.strip()))

        return resp.content.strip()

    def pull_data(self, auto_save=True, check_reminders=False):
        """ Pulls fresh remote data, parses and stores it """
        now = datetime.now()
        last_state = deepcopy(self)

        if app.config.get('MOCK_FETCH', False):
            with open(app.config['MOCK_FILE'], 'r') as f:
                content = f.read()
        else:
            content = self.fetch_remote_data()

        if not self._valid_pull(content):
            # Should store error documents
            invalid = InvalidCardData.objects.create(card=self, fetch_date=now, document=content)
            app.logger.error('Invalid card pull response. See document %s' % invalid.id)
            return

        # Cache the result FTW!
        data = CardData(card=self, fetch_date=now, document=content)

        # Pull out the parts you need with BeautifulSoup
        soup = BeautifulSoup(content)

        # Run the various extractions
        self.expiration_date = self._parse_expiration_date(soup)
        self.stored_value = self._parse_stored_value(soup)

        # Get/make the products
        self.products = []
        for product_data in self._parse_products(soup):
            self.products.append(Product(**product_data))

        self.pending = []
        for pending_data in self._parse_pending_transactions(soup):
            self.pending.append(PendingTransaction(**pending_data))

        self.last_loaded = datetime.now()
        self.has_data = True

        if auto_save:
            # Remove stale card data
            for stale_data in CardData.objects.filter(card=self, fetch_date__lt=now):
                app.logger.info('Removing stale card data saved on %s' % stale_data.fetch_date)
                stale_data.delete()

            self.save()
            data.save()

            if check_reminders:
                self.owner.check_reminders(card=self, last_state=last_state)

    def _valid_pull(self, content):
        """ Looks for 'enter card serial number' in content """
        return 'enter card serial number' not in content.lower()

    def _parse_expiration_date(self, soup):
        try:
            found = soup.find('td', text=re.compile(r'your card will expire', re.I))
            datestring = re.findall(r'\d{2}-\d{2}-\d{4}', found)[0]
            exp_date = datetime.strptime(datestring, '%m-%d-%Y')
            app.logger.debug('Parsing exp date for card %s found %s' % (self.number_masked, exp_date))

            return exp_date
        except Exception, e:
            app.logger.exception('Failed to parse expiration date')
            return None

    def _parse_stored_value(self, soup):
        try:
            cell = soup.find('td', text=re.compile(r'stored value', re.I))
            value = cell.parent.findNextSiblings()[0].text.replace('$', '').strip()
            app.logger.debug('Parsing stored value for card %s found %s' % (self.number_masked, value))
            
            return value or None
        except Exception, e:
            app.logger.exception('Failed to parse card stored value')
            return None

    def _parse_products(self, soup):
        products = []
        try:
            cell = soup.find('td', text=re.compile(r'product name', re.I))
            start_row = cell.parent.parent

            for product_row in start_row.findNextSiblings():
                children = product_row.findChildren('td')
                if len(children) == 3:
                    app.logger.debug('Possible product row located')
                    product = {
                        'name': children[0].text.strip(),
                        'remaining_rides': None,
                        'expiration_date': None,
                    }

                    if 'no active product' in product['name'].lower():
                        app.logger.debug('No products listed')
                        continue

                    # Try to grab remaining rides
                    try:
                        product['remaining_rides'] = int(children[2].text.strip())
                    except:
                        app.logger.debug('Remaining rides not found, likely N/A vlaue')

                    try:
                        text_node = children[1].text.strip()
                        datestring = re.findall(r'\d{2}-\d{2}-\d{4}', text_node)[0]
                        product['expiration_date'] = datetime.strptime(datestring, '%m-%d-%Y')
                    except:
                        app.logger.debug('Product expiration date could not be parsed correctly')

                    products.append(product)
                else:
                    app.logger.debug('Reached the end of products list')
                    break
        except Exception, e:
            app.logger.exception('Failed to parse card products')
            pass

        app.logger.debug('Parsing products for card %s found %s' % (self.number_masked, products))
        return products

    def _parse_pending_transactions(self, soup):
        pending = []
        try:
            cell = soup.find('td', text=re.compile(r'pending autoload transactions', re.I))
            start_row = cell.parent.parent

            for pending_row in start_row.findNextSiblings():
                children = pending_row.findChildren('td')
                if len(children) == 2:
                    transaction = {
                        'name': children[0].text.strip(),
                        'value': children[1].text.strip()
                    }

                    # Skip if it's just a header or we've reached the end
                    if transaction['name'].lower() in ['product name', '&nbsp;']:
                        continue

                    # Grab the value
                    try:
                        transaction['value'] = float(transaction['value'].replace('$', ''))
                    except Exception, e:
                        app.logger.exception('Failed to convert value to decimal')
                        transaction['value'] = 0.0

                    pending.append(transaction)
                else:
                    app.logger.debug('End of pending transactions list')
                    break
        except Exception, e:
            app.logger.exception('Failed to parse pending transactions')
            pass

        return pending


class InvalidCardData(BaseDocument):
    """
    A date stored fetch cache for 'bad' or invalid data pulls. Merely for debugging purposes
    """
    card = app.db.ReferenceField('BreezeCard', required=True, dbref=False,
                                 reverse_delete_rule=app.db.CASCADE)
    fetch_date = app.db.DateTimeField(required=True)
    _document = app.db.StringField()

    meta = {
        'collection': 'invalid_card_data',
        'queryset_class': InvalidCardDataQuerySet
    }

    @property
    def document(self):
        # Note, decrypt() is memoized
        return decrypt(self._document)

    def __setattr__(self, attr, value):
        if attr == 'document':
            self._document = encrypt(value)
        else:
            super(InvalidCardData, self).__setattr__(attr, value)

        
class CardData(BaseDocument):
    """
    A date stored fetch cache for results of retrieving breeze card details.
    Maintined in its own collection to reduce overhead/size of breeze
    card collection.
    """
    card = app.db.ReferenceField('BreezeCard', required=True, dbref=False,
                                 reverse_delete_rule=app.db.CASCADE)
    fetch_date = app.db.DateTimeField(required=True)
    _document = app.db.StringField()

    meta = {
        'collection': 'breezecard_data',
        'queryset_class': CardDataQuerySet,
        'indexes': [('card', 'fetch_date')],
        'ordering': ['-fetch_date']
    }

    @property
    def document(self):
        # Note, decrypt() is memoized
        return decrypt(self._document)

    def __setattr__(self, attr, value):
        if attr == 'document':
            self._document = encrypt(value)
        else:
            super(CardData, self).__setattr__(attr, value)


class Product(app.db.EmbeddedDocument):
    name = app.db.StringField()
    expiration_date = app.db.DateTimeField()
    remaining_rides = app.db.IntField()

    def __eq__(self, other):
        try:
            return self.name == other.name
        except:
            return False


class PendingTransaction(app.db.EmbeddedDocument):
    name = app.db.StringField()
    value = app.db.DecimalField(default=0.0)

    def __eq__(self, other):
        try:
            return self.name == other.name
        except:
            return False
