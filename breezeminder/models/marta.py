"""MARTA related data classes"""
from datetime import datetime

from breezeminder.app import app
from breezeminder.models.base import BaseQuerySet
from breezeminder.util.date import timesince


class Route(app.db.Document):
    """
    One describable MARTA bus/train route. Consists of "trips"
    """
    id = app.db.IntField(primary_key=True)
    name = app.db.StringField(required=True, max_length=25)
    description = app.db.StringField()
    type = app.db.IntField(required=True, default=0)
    color = app.db.StringField(required=True, min_length=6,
                               max_length=6, default='000000')

    meta = {
        'collection': 'marta_route',
        'queryset_class': BaseQuerySet,
        'indexes': [
            'name',
            'type'
        ]
    }

    def get_trips(self, schedule=None):
        """
        Gets trips for this route as an unexecuted queryset
        """
        qs = Trip.objects.filter(route=self)

        if schedule:
            qs = qs.filter(schedule=schedule)

        return qs

    def get_shapes(self, schedule=None):
        """
        Gets distinct shapes belonging to trips for this route
        """
        return self.get_trips(schedule=schedule).distinct('shape')

    def get_stops(self, schedule=None):
        """
        Gets distinct stops belonging to trips for this route
        """
        q = app.db.Q(route_id=self.id)

        if schedule:
            q = q & app.db.Q(schedule_id=schedule.id)

        return Stop.objects.in_bulk(
            ScheduledStop.objects.filter(q).only('stop_id').distinct('stop_id')
        ).values()

    def to_json(self, stops=True, full=False, schedule=None):
        """
        Exports this route, with optional data, as csv writable data
        """
        data = {
            'name': self.name,
            'color': self.color,
            'shapes': [list(s.points) for s in self.get_shapes(schedule=schedule)],
        }

        if full:
            data.update({
                'id': self.id,
                'description': self.description,
                'type': self.type
            })

        # Include stop
        if stops:
            data['stops'] = [s.to_json(full=full) for s in self.get_stops(schedule=schedule)]

        return data


class ScheduleQuerySet(BaseQuerySet):

    def for_today(self):
        """Returns the first matching schedule for today or None"""
        dow = datetime.strftime(datetime.now(), '%A').lower()

        try:
            return self.filter(**{dow: True})[0]
        except IndexError:
            return None


class Schedule(app.db.Document):
    """
    Used to indicate trips/routes that run on different days
    """
    id = app.db.IntField(primary_key=True)
    begin = app.db.DateTimeField()
    end = app.db.DateTimeField()
    monday = app.db.BooleanField()
    tuesday = app.db.BooleanField()
    wednesday = app.db.BooleanField()
    thursday = app.db.BooleanField()
    friday = app.db.BooleanField()
    saturday = app.db.BooleanField()
    sunday = app.db.BooleanField()

    meta = {
        'collection': 'marta_schedule',
        'queryset_class': ScheduleQuerySet
    }


class Shape(app.db.Document):
    """ Holds a single mappable shape or collection of points """
    id = app.db.IntField(primary_key=True)
    points = app.db.ListField(app.db.GeoPointField(), required=True)

    meta = {
        'collection': 'marta_shape',
        'queryset_class': BaseQuerySet
    }


class Stop(app.db.Document):
    """ A single MARTA stop """
    id = app.db.IntField(primary_key=True)
    code = app.db.StringField()
    name = app.db.StringField(required=True)
    description = app.db.StringField()
    point = app.db.GeoPointField(required=True)

    meta = {
        'collection': 'marta_stop',
        'queryset_class': BaseQuerySet
    }

    def to_json(self, full=False):
        """JSON exportable representation of this object"""
        data = {
            'id': self.id,
            'pt': self.point,
            'name': self.name.upper(),
        }

        if full:
            data.update({
                'code': self.code,
                'description': self.description
            })

        return data


class Trip(app.db.Document):
    id = app.db.IntField(primary_key=True)
    route = app.db.ReferenceField('Route', required=True, dbref=False,
                                  reverse_delete_rule=app.db.CASCADE)
    schedule = app.db.ReferenceField('Schedule', dbref=False)
    shape = app.db.ReferenceField('Shape', dbref=False)
    headsign = app.db.StringField()
    direction = app.db.StringField()
    block = app.db.StringField()

    meta = {
        'collection': 'marta_trip',
        'queryset_class': BaseQuerySet,
        'indexes': [
            'route',
            'schedule',
            'shape'
        ]
    }

    @property
    def stops(self):
        pass


class ScheduledStopQuerySet(BaseQuerySet):

    def near(self, latitude, longitude, distance=25):
        """Returns a queryset within distance of feet from lat/lon"""
        point = (latitude, longitude)
        distance = distance / 20903520.0

        return self.filter(location__within_spherical_distance=[point, distance])



class ScheduledStop(app.db.Document):
    route_id = app.db.IntField(required=True)
    schedule_id = app.db.IntField(required=True)
    trip_id = app.db.IntField(required=True)
    stop_id = app.db.IntField(required=True)
    arrival = app.db.IntField(required=True)
    location = app.db.GeoPointField(required=True)
    sequence = app.db.IntField(required=True, default=0)
    shape_distance = app.db.DecimalField(required=True, default=0)
    pickup_type = app.db.StringField()
    dropoff_type = app.db.StringField()
    headsign = app.db.StringField()
    direction = app.db.StringField()
    block = app.db.StringField()

    meta = {
        'collection': 'marta_scheduled_stop',
        'queryset_class': BaseQuerySet,
        'indexes': [
            (
                'route_id',
                'schedule_id',
                'trip_id',
                'arrival'
            ),
            'stop_id',
            'sequence'
        ]
    }

    @staticmethod
    def timestring_to_seconds(value):
        """Converts 24h formatted time string like 00:00:00 into number of seconds"""
        parts = value.split(':')
        return (int(parts[0]) * 60 * 60) + (int(parts[1]) * 60) + int(parts[2])

    @staticmethod
    def seconds_to_timestring(value, ampm=True, with_seconds=False):
        s = str(value % 60)
        m = str((value / 60) % 60)

        # Control the display for AM/PM type
        if ampm:
            h = (value / 3600) % 60
            extra = ' AM' if h < 12 else ' PM'
            h = str(h % 12)

            if h == '0':
                h = '12'
        else:
            h = h.rjust(2, '0')
            extra = ''

        parts = [h, m.rjust(2, '0')]

        if with_seconds:
            parts.append(s.rjust(2, '0'))

        return ':'.join(parts) + extra

    @staticmethod
    def arrival_now():
        return ScheduledStop.timestring_to_seconds(datetime.now().strftime('%H:%M:%S'))


class Bus(app.db.Document):
    id = app.db.StringField(primary_key=True)
    direction = app.db.StringField(required=True)
    route = app.db.StringField(required=True)
    location = app.db.GeoPointField(required=True)
    adherence = app.db.IntField(required=True, default=0)
    status_time = app.db.DateTimeField(required=True)
    timepoint = app.db.StringField()
    stop_id = app.db.StringField()
    is_stale = app.db.BooleanField(default=False)

    meta = {
        'collection': 'marta_bus',
        'queryset_class': BaseQuerySet,
        'indexes': ['route', 'is_stale']
    }

    def update_maybe(self, **kwargs):
        updated = False
        for k, v in kwargs.iteritems():
            if getattr(self, k) == v:
                continue
            setattr(self, k, v)
            updated = True
        return updated

    def to_json(self):
        return {
            'id': self.id,
            'direction': self.direction,
            'route': self.route,
            'location': self.location,
            'status_time': datetime.strftime(self.status_time, '%m/%d/%Y %I:%M:%S %p'),
            'timepoint': self.timepoint,
            'adherence': self.adherence,
            'time_since': timesince(self.status_time)
        }
