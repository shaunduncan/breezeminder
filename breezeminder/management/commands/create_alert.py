from datetime import datetime
from flask.ext.script import Command, Option

from breezeminder.models.alerts import Alert


class CreateAlert(Command):
    """ Creates a BreezeMinder site alert """

    def get_options(self):
        return [
            Option('-m', '--message', dest='message', required=True,
                   help='Content of message to display'),
            Option('-s', '--start', dest='start', required=True,
                   help='Start date/time of alert. Format MM-DD-YYYY HH:MM. Time optional'),
            Option('-e', '--end', dest='end', required=True,
                   help='End date/time of alert. Format MM-DD-YYYY HH:MM. Time optional'),
            Option('-l', '--level', dest='level', default='info',
                   choices=['info', 'success', 'warning', 'error'],
                   help='The level to display for this alert'),
            Option('--inactive', dest='inactive', default=False, action='store_true',
                   help='Create the alert, but do not activate it')
        ]

    def _prepare_datetime(self, value):
        parts = value.split()
        if len(parts) > 1:
            return datetime.strptime(value.strip(), '%m-%d-%Y %H:%M')
        else:
            return datetime.strptime(parts[0].strip(), '%m-%d-%Y')

    def run(self, **kwargs):
        message = kwargs['message'].strip()
        start = self._prepare_datetime(kwargs['start'])
        end = self._prepare_datetime(kwargs['end'])
        is_active = not kwargs.get('inactive', False)
        level = kwargs.get('level', 'info').lower()

        alert = Alert.objects.create(message=message,
                                     start=start,
                                     end=end,
                                     is_active=is_active,
                                     level=level)

        print 'Created alert: %s' % alert.id
