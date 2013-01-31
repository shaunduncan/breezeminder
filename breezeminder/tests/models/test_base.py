from mock import Mock, patch
from mongoengine.queryset import DoesNotExist
from random import shuffle
from unittest2 import TestCase
from werkzeug.exceptions import NotFound

from breezeminder.models.base import BaseQuerySet


class BaseQuerySetTestCase(TestCase):

    def setUp(self):
        self.qs = BaseQuerySet(Mock(), Mock())
        self.qs._document = Mock(spec=['_fields'])
        self.qs._document._fields = ['foo', 'bar', 'baz']

    def test_get_or_404(self):
        with patch('breezeminder.models.base.BaseQuerySet.get',
                   Mock(return_value=None)) as mocked:
            self.assertIsNone(self.qs.get_or_404())

        with patch('breezeminder.models.base.BaseQuerySet.get',
                   Mock(side_effect=DoesNotExist)) as mocked:
            self.assertRaises(NotFound, self.qs.get_or_404)

    def test_check_pk_hash(self):
        """ Ensure `check_pk_hash` removes a kwarg pk_hash and unhashes it """
        result = self.qs._check_pk_hash(pk_hash='z', id='10000')
        self.assertNotIn('pk_hash', result)
        self.assertNotEqual(result['id'], '10000')
        self.assertEquals(1, len(result))

    def test_is_property(self):
        # Valid checks
        for field in ['blah', '+blah', '-blah']:
            self.assertTrue(self.qs._is_property(field))

        # Invalid checks
        for field in ['foo', 'bar', 'baz']:
            self.assertFalse(self.qs._is_property(field))

    def test_attr_sort(self):
        items = [ Mock(spec=self.qs._document._fields) for i in range(3) ]
        for idx, item in enumerate(items):
            for field in self.qs._document._fields:
                setattr(item, field, 'field%s' % idx)
        shuffle(items)

        for field in self.qs._document._fields:
            result_asc = self.qs._attr_sort(items, '+%s' % field)
            self.assertTrue(getattr(result_asc[0], field) <= \
                            getattr(result_asc[1], field) <= \
                            getattr(result_asc[2], field))

            result_desc = self.qs._attr_sort(items, '-%s' % field)
            self.assertTrue(getattr(result_desc[0], field) >= \
                            getattr(result_desc[1], field) >= \
                            getattr(result_desc[2], field))
