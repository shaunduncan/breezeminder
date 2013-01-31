from flask.ext.script import Command, Option

from breezeminder.models.alerts import Alert


class DisableAlert(Command):
    """ Disables a BreezeMinder site alert """

    def get_options(self):
        return [
            Option('--id', dest='id', required=True,
                   help='ID/Primary Key of the alert to disable'),
            Option('--delete', dest='delete', default=False, action='store_true',
                   help='Instead of disabling the alert, permanently delete it')
        ]

    def run(self, **kwargs):
        id = kwargs['id']

        try:
            alert = Alert.objects.get(id=id)
        except Alert.DoesNotExist:
            print 'Alert with ID %s does not exist' % id
        else:
            if kwargs.get('delete', False):
                alert.delete()
                print 'Alert %s deleted successfully' % id
            else:
                alert.disable()
                print 'Alert %s disabled successfully' % id
