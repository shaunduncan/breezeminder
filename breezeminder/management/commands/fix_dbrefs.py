from flask.ext.script import Command, Option

from breezeminder.models.card import (BreezeCard,
                                      InvalidCardData,
                                      CardData)
from breezeminder.models.reminder import (Reminder,
                                          ReminderHistory)
from breezeminder.models.user import User


class FixDbrefs(Command):
    """ Updates Outdated Mongo DBRefs """

    def get_options(self):
        return [
            Option('--go', dest='go', default=False, action='store_true',
                   help="Run for realz")
        ]

    def run(self, **kwargs):
        go = kwargs.get('go', False)

        print 'Updating BreezeCard Refs'
        count = 0
        for bc in BreezeCard.objects.all():
            count += 1
            bc.owner = bc.owner
            if go:
                bc.save()
        print '%d Updated\n' % count

        print 'Updating InvalidCardData Refs'
        count = 0
        for icd in InvalidCardData.objects.all():
            count += 1
            icd.card = icd.card
            if go:
                icd.save()
        print '%d Updated\n' % count

        print 'Updating CardData Refs'
        count = 0
        for cd in CardData.objects.all():
            count += 1
            cd.card = cd.card
            if go:
                cd.save()
        print '%d Updated\n' % count

        print 'Updating Reminder Refs'
        count = 0
        for r in Reminder.objects.all():
            count += 1
            r.owner = r.owner
            r.type = r.type
            if go:
                r.save()
        print '%d Updated\n' % count

        print 'Updating ReminderHistory Refs'
        count = 0
        for rh in ReminderHistory.objects.all():
            count += 1
            rh.reminder = rh.reminder
            rh.card = rh.card
            rh.owner = rh.owner
            if go:
                rh.save()
        print '%d Updated\n' % count

        print 'Updating User.PhoneNumber Refs'
        count = 0
        for u in User.objects.all():
            if u.cell_phone:
                count += 1
                u.cell_phone.carrier = u.cell_phone.carrier
                if go:
                    u.save()
        print '%d Updated\n' % count
