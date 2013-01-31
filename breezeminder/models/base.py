from bson.objectid import ObjectId
from datetime import datetime
from flask import abort
from operator import attrgetter
from mongoengine.queryset import QuerySet, DoesNotExist

from breezeminder.app import app
from breezeminder.util.shorturls import default_base


class BaseQuerySet(QuerySet):
    """
    Subclass of :class:`mongoengine.queryset.QuerySet` with some specific
    useful utilities
    """

    _property_ordering = []

    def get_or_404(self, *args, **kwargs):
        """ Wrapper to check if `get` returned an object or abort with 404 """
        try:
            return self.get(*args, **kwargs)
        except DoesNotExist:
            abort(404)

    def _check_pk_hash(self, **kwargs):
        """
        Checks a kwargs dict for pk_hash (a reserved kwarg) and converts
        it to an appropriate id mapping by unhashing it
        """
        if 'pk_hash' in kwargs:
            kwargs['id'] = BaseDocument.unhash(kwargs.pop('pk_hash'))
        return kwargs

    def filter(self, *args, **kwargs):
        """ Override specifically to check for pk_hash """
        kwargs = self._check_pk_hash(**kwargs)
        return super(BaseQuerySet, self).filter(*args, **kwargs)

    def get(self, *args, **kwargs):
        """ Override specifically to check for pk_hash """
        kwargs = self._check_pk_hash(**kwargs)
        return super(BaseQuerySet, self).get(*args, **kwargs)

    def __iter__(self):
        """
        Specific implementation to allow for sorting by non-mongo
        class properties (i.e. @property, etc)
        """
        super_iter = super(BaseQuerySet, self).__iter__()
        if len(self._property_ordering) == 0:
            return super_iter
        else:
            resultset = []

            try:
                for i in range(self.count()):
                    resultset.append(self.next())
            except:
                pass

            resultset = self._attr_sort(resultset, *self._property_ordering)
            return iter(resultset)

    def _attr_sort(self, items, *columns):
        """ General purpose mult-key attribute sorting """
        comparers = []
        for col in columns:
            attr = col.strip()
            direction = 1  # Default ASC

            if col.startswith('-'):
                attr = col[1:].strip()
                direction = -1
            elif col.startswith('+'):
                attr = col[1:].strip()

            comparers.append((attrgetter(attr), direction))

        def comparer(left, right):
            for func, direction in comparers:
                result = cmp(func(left), func(right))
                if result:
                    return direction * result
            else:
                return 0

        return sorted(items, cmp=comparer)

    def _is_property(self, field):
        """ Checks if class attribute a true property and not mongo field """
        if field.startswith('+') or field.startswith('-'):
            field = field[1:]
        return field not in self._document._fields

    def order_by(self, *args):
        """ Override to check for non mongo property ordering """
        self._property_ordering = []  # FIXME: This should probably be done in rewind()
        simple = True

        for key in args:
            if self._is_property(key):
                simple = False
                break

        if simple:
            return super(BaseQuerySet, self).order_by(*args)
        else:
            self._property_ordering = args
            return self


class HashableMixin(object):
    """ Mixin to provide re-usable id attribute hashing """

    @property
    def pk_hash(self):
        return default_base.from_decimal(int(str(self.id), 16))

    @classmethod
    def hash(self, value):
        return default_base.from_decimal(int(str(value), 16))

    @classmethod
    def unhash(self, value):
        if value is not None and value:
            return "%x" % default_base.to_decimal(value)
        else:
            return None


class BaseDocument(app.db.Document, HashableMixin):
    created = app.db.DateTimeField(required=True)
    updated = app.db.DateTimeField(required=True)

    meta = {
        'abstract': True
    }

    def save(self, *args, **kwargs):
        if not self.created:
            self.created = datetime.now()
        self.updated = datetime.now()

        super(BaseDocument, self).save(*args, **kwargs)


class BaseEmbeddedDocument(app.db.EmbeddedDocument, HashableMixin):
    """ Specifically created so embedded documents can have an object id """
    id = app.db.ObjectIdField(required=True)

    def __init__(self, *args, **kwargs):
        super(BaseEmbeddedDocument, self).__init__(*args, **kwargs)

        if self.id is None:
            self.id = ObjectId()
