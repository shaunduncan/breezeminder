from breezeminder.app import app
from breezeminder.models.base import (BaseDocument,
                                      BaseQuerySet)


class AlertQuerySet(BaseQuerySet):
    pass


class Alert(BaseDocument):
    message = app.db.StringField(required=True)
    is_active = app.db.BooleanField(required=True, default=True)
    start = app.db.DateTimeField(required=True)
    end = app.db.DateTimeField(required=True)
    level = app.db.StringField(default='info')

    meta = {
        'collection': 'alerts',
        'queryset_class': AlertQuerySet,
        'indexes': [
            ('start', 'end')
        ]
    }

    def disable(self):
        self.is_active = False
        self.save()

    def enable(self):
        self.is_active = True
        self.save()
