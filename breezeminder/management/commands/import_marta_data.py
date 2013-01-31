import csv
import os
import sys

from dateutil.parser import parse as parse_date
from flask.ext.script import Command, Option

from breezeminder.models.marta import (Route,
                                       Schedule,
                                       Shape,
                                       Stop,
                                       Trip,
                                       ScheduledStop)


class ImportMartaData(Command):
    """ Imports MARTA GTFS Data """
    FILES = {
        'routes': None,
        'calendar': None,
        'shapes': None,
        'stops': None,
        'trips': None,
        'stop_times': None,
    }

    PROCESSING_ORDER = [
        'routes',
        'calendar',
        'shapes',
        'stops',
        'trips',
        'stop_times',
    ]

    def get_options(self):
        return [
            Option('-d', '--dir', dest='data_dir', required=True,
                   help='Directory containing MARTA export files'),
            Option('--delete', dest='delete', action='store_true', default=False,
                   help='Delete all model contents first'),
        ]

    def run(self, **kwargs):
        self.dirname = os.path.expanduser(kwargs['data_dir'])
        if not os.path.exists(self.dirname):
            sys.exit('Directory does not exist')

        if kwargs.get('delete', False):
            print 'CLEARING EXISTING DATA'
            self.do_clear()

        self.do_import(**kwargs)

    def do_clear(self):
        Trip.objects.delete()
        Stop.objects.delete()
        Shape.objects.delete()
        Schedule.objects.delete()
        Route.objects.delete()
        ScheduledStop.objects.delete()

    def do_import(self, **kwargs):
        print 'READING FILE CONTENT'
        for filename in self.FILES:
            fullname = os.path.join(self.dirname, '%s.txt' % filename)
            print fullname
            if not os.path.exists(fullname):
                sys.exit('File %s does not exist' % fullname)

            self.FILES[filename] = csv.DictReader(open(fullname, 'r'))

        print 'PROCESSING DATA'
        for name in self.PROCESSING_ORDER:
            print 'Running create_%s' % name
            getattr(self, 'create_%s' % name)(self.FILES[name], **kwargs)

    def allcaps(self, string):
        return ' '.join(map(lambda x: x.capitalize(), string.split(' ')))

    def create_routes(self, data, **kwargs):
        for row in data:
            try:
                id = int(row['route_id'])
            except ValueError:
                print 'WARNING: Could not process route id of %s' % row
                continue

            try:
                type = int(row['route_type'])
            except ValueError:
                type = 0

            try:
                Route(id=id,
                      name=self.allcaps(row['route_short_name']),
                      description=self.allcaps(row['route_long_name']),
                      type=type,
                      color=row['route_color']).save()
            except:
                print 'Route exists'
                continue

    def create_calendar(self, data, **kwargs):
        for row in data:
            try:
                id = int(row['service_id'])
            except ValueError:
                print 'WARNING: Could not process service id of %s' % row
                continue

            begin, end = None, None

            if row['start_date']:
                begin = parse_date(row['start_date'])

            if row['end_date']:
                end = parse_date(row['end_date'])

            defaults = {
                'begin': begin,
                'end': end
            }

            for dow in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
                defaults[dow] = str(row[dow]) == '1'

            try:
                Schedule(id=id, **defaults).save()
            except:
                print 'Schedule exists'
                continue

    def create_shapes(self, data, **kwargs):
        shapes = {}
        for row in data:
            try:
                id = int(row['shape_id'])
            except ValueError:
                print 'WARNING: Could not process shape id of %s' % row
                continue

            if id not in shapes:
                shapes[id] = []

            try:
                lat = float(row['shape_pt_lat'])
                lng = float(row['shape_pt_lon'])
            except ValueError:
                print 'WARNING: Could not process shape coordinates of %s' % row
                continue

            shapes[id].append((lat, lng))

        for id, points in shapes.iteritems():
            try:
                Shape(id=id, points=points).save()
            except:
                print 'Shape exists'
                continue

    def create_stops(self, data, **kwargs):
        self.stop_locations = {}

        for row in data:
            try:
                id = int(row['stop_id'])
            except ValueError:
                print 'WARNING: could not process stop id of %s' % row

            try:
                lat = float(row['stop_lat'])
                lng = float(row['stop_lon'])
            except ValueError:
                print 'WARNING: Could not process stop coordinates of %s' % row
                continue

            self.stop_locations[id] = (lat, lng)

            defaults = {
                'code': row['stop_code'],
                'name': self.allcaps(row['stop_name']),
                'description': self.allcaps(row['stop_desc']),
                'point': (lat, lng)
            }

            try:
                Stop(id=id, **defaults).save()
            except:
                print 'Stop exists'
                continue

    def create_stop_times(self, data, **kwargs):
        count = 0
        for row in data:
            if count % 1000 == 0:
                print 'Checkpoint %d' % count
            count += 1

            try:
                trip_id = int(row['trip_id'])
                stop_id = int(row['stop_id'])
            except ValueError:
                print 'WARNING: Could not parse the ids of scheduled stop %s' % row
                continue

            try:
                route_id = self.trip_mapping[trip_id]['route_id']
                schedule_id = self.trip_mapping[trip_id]['schedule_id']
                direction = self.trip_mapping[trip_id]['direction']
                headsign = self.trip_mapping[trip_id]['headsign']
                block = self.trip_mapping[trip_id]['block']
            except (AttributeError, KeyError):
                print 'WARNING: Trip not mapped for stop %s' % row
                continue

            try:
                seq = int(row['stop_sequence'])
            except ValueError:
                seq = 0

            try:
                dist = float(row['shape_dist_traveled'])
            except ValueError:
                dist = 0.0

            # Arrival
            parts = row['arrival_time'].split(':')
            time = (int(parts[0]) * 3600) + (int(parts[1]) * 60) + int(parts[2])

            try:
                ScheduledStop(route_id=route_id,
                              schedule_id=schedule_id,
                              trip_id=trip_id,
                              stop_id=stop_id,
                              arrival=time,
                              location=self.stop_locations[stop_id],
                              shape_distance=dist,
                              pickup_type=row['pickup_type'],
                              dropoff_type=row['drop_off_type'],
                              direction=direction,
                              headsign=headsign,
                              sequence=seq).save()
            except:
                print 'ScheduledStop exists'
                continue

    def create_trips(self, data, **kwargs):
        self.trip_mapping = {}

        count = 0
        for row in data:
            if count % 500 == 0:
                print 'Checkpoint %s' % count
            count += 1

            try:
                route_id = int(row['route_id'])
                svc_id = int(row['service_id'])
                trip_id = int(row['trip_id'])
                shape_id = int(row['shape_id'])

                self.trip_mapping[trip_id] = {
                    'route_id': route_id,
                    'schedule_id': svc_id,
                    'direction': row['direction_id'],
                    'headsign': row['trip_headsign'],
                    'block': row['block_id'],
                }
            except ValueError:
                print 'WARNING: Could not parse route/service/trip/shape id of trip %s' % row
                continue

            try:
                route = Route.objects.get(id=route_id)
            except Route.DoesNotExist:
                print 'WARNING: No route for id %s' % route_id
                continue

            try:
                schedule = Schedule.objects.get(id=svc_id)
            except Schedule.DoesNotExist:
                print 'WARNING: No schedule for id %s' % svc_id
                schedule = None

            try:
                shape = Shape.objects.get(id=shape_id)
            except Shape.DoesNotExist:
                print 'WARNING: No shape for id %s' % shape_id
                shape = None

            defaults = {
                'route': route,
                'schedule': schedule,
                'shape': shape,
                'headsign': self.allcaps(row['trip_headsign']),
                'direction': row['direction_id'],
                'block': row['block_id']
            }

            try:
                Trip(id=trip_id, **defaults).save()
            except:
                print 'Trip exists'
                continue
