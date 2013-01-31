from breezeminder.app import app
from breezeminder.models.base import (BaseDocument,
                                      BaseQuerySet)


class WirelessCarrierQuerySet(BaseQuerySet):
    pass


class WirelessCarrier(BaseDocument):
    name = app.db.StringField(required=True, max_length=50)
    sms_domain = app.db.StringField(required=True, max_length=100)

    meta = {
        'collection': 'wireless',
        'queryset_class': WirelessCarrierQuerySet,
        'ordering': ['+name']
    }
