from datetime import datetime
from wtforms import (Form,
                     IntegerField,
                     DecimalField,
                     FormField,
                     SelectField)
from wtforms.validators import Required, Optional
from werkzeug.datastructures import MultiDict

from breezeminder.models.reminder import ReminderType
from breezeminder.forms.validators import (ActiveStateOptional,
                                           Conditional,
                                           PositiveNumber)
from breezeminder.forms.fields import BootstrapSelectMultipleField


def _create_tuple_range(start, stop):
    return [(int(x), str(x)) for x in xrange(start, stop)]


DATE_QUANTIFIERS = ['Days', 'Weeks', 'Months']
DATE_RANGE_CHOICES = [(x, x) for x in DATE_QUANTIFIERS]
DATE_THRESHOLD_CHOICES = _create_tuple_range(1, 11)

# For Date Selects, allow empties
MONTH_CHOICES = [(-1, 'Month')]
DAY_CHOICES = [(-1, 'Day')]
YEAR_CHOICES = [(-1, 'Year')]

# Extend all valid ranges
MONTH_CHOICES.extend(_create_tuple_range(1, 13))
DAY_CHOICES.extend(_create_tuple_range(1, 32))
YEAR_CHOICES.extend(_create_tuple_range(datetime.now().year,
                                        datetime.now().year + 10))

REMINDER_TYPES = ReminderType.objects.all_tuples()
NOTIFICATION_CHOICES = [
    ('EMAIL', 'Email'),
    ('SMS', 'Text Message')
]


class _DateForm(Form):
    month = SelectField('Month',
                        coerce=int,
                        choices=MONTH_CHOICES,
                        validators=[Optional()])
    day = SelectField('Day',
                      coerce=int,
                      choices=DAY_CHOICES,
                      validators=[Optional()])
    year = SelectField('Year',
                       coerce=int,
                       choices=YEAR_CHOICES,
                       validators=[Optional()])


class ReminderForm(Form):
    type = SelectField('When',
                       choices=REMINDER_TYPES,
                       validators=[Required()])

    # Type BAL, conditionally Required if type is BAL
    balance_threshold = DecimalField('Falls Below',
                                     places=2,
                                     validators=[
                                         ActiveStateOptional(),
                                         Conditional('type', 'BAL', validators=[Required(), PositiveNumber()])
                                      ])

    # Type RIDES, conditionally Required if type is RIDE
    ride_threshold = IntegerField('Falls Below',
                                   validators=[
                                       ActiveStateOptional(),
                                       Conditional('type', 'RIDE', validators=[Required(), PositiveNumber()])
                                    ])

    # Type ROUND_TRIP, conditionally Require if type is ROUND_TRIP
    round_trip_threshold = IntegerField('Falls Below',
                                        validators=[
                                            ActiveStateOptional(),
                                            Conditional('type', 'ROUND_TRIP', validators=[Required(), PositiveNumber()])
                                         ])

    # Type EXP, conditionally Required if type is EXP
    exp_threshold = SelectField('Is',
                                choices=DATE_THRESHOLD_CHOICES, coerce=int,
                                validators=[
                                    Conditional('type', 'EXP', validators=Required())
                                ])
    exp_quantity = SelectField('Quantity',
                               choices=DATE_RANGE_CHOICES,
                               validators=[
                                   Conditional('type', 'EXP', validators=Required())
                                ])
   
    # Options
    valid_until = FormField(_DateForm, separator='/', label='Remind Me Until')
    notifications = BootstrapSelectMultipleField('Send Me',
                                                 choices=NOTIFICATION_CHOICES,
                                                 validators=[Required()])

    def _disable_optional(self, field):
        field.flags.optional = False
        for idx, obj in enumerate(field.validators):
            if isinstance(obj, ActiveStateOptional):
                obj.deactivate()
                break

    def _enable_optional(self, field):
        field.flags.optional = True
        for idx, obj in enumerate(field.validators):
            if isinstance(obj, ActiveStateOptional):
                obj.activate()
                break

    def _pre_validate(self):
        """ Removes any Optional flags for conditional fields """
        if self.type.data == 'BAL':
            self._disable_optional(self.balance_threshold)
        elif self.type.data == 'RIDE':
            self._disable_optional(self.ride_threshold)
        elif self.type.data == 'ROUND_TRIP':
            self._disable_optional(self.round_trip_threshold)
        elif self.type.data == 'EXP':
            pass

    def _post_validate(self):
        """ Re-enables optional flags """
        self._enable_optional(self.balance_threshold)
        self._enable_optional(self.ride_threshold)
        self._enable_optional(self.round_trip_threshold)

    def validate(self, *args, **kwargs):
        self._pre_validate()
        retval = super(ReminderForm, self).validate(*args, **kwargs)
        self._post_validate()

        return retval

    def is_changed_from(self, reminder):
        if reminder.type != self.type.data:
            return True

        try:
            if self.type.data == 'BAL':
                return float(reminder.threshold) != float(self.balance_threshold.data)

            if self.type.data == 'RIDE':
                return int(reminder.threshold) != int(self.ride_threshold.data)

            if self.type.data == 'ROUND_TRIP':
                return int(reminder.threshold) != int(self.round_trip_threshold.data)

            if self.type.data == 'EXP':
                if int(reminder.threshold) != int(self.exp_threshold.data):
                    return True
                elif reminder.quantifier != self.exp_quantity.data:
                    return True
        except:
            pass

        return False

    def populate_reminder(self, reminder):
        # This will bubble up if any problems pop up
        reminder.type = ReminderType.objects.get(key=self.type.data)

        try:
            reminder.valid_until = datetime(month=self.valid_until.month.data,
                                            day=self.valid_until.day.data,
                                            year=self.valid_until.year.data)
        except:
            reminder.valid_until = None

        # Set the notifications
        reminder.send_sms = 'SMS' in self.notifications.data
        reminder.send_email = 'EMAIL' in self.notifications.data

        # Set threshold based on type
        if reminder.type == 'BAL':
            reminder.threshold = float('%.2f' % round(self.balance_threshold.data, 2))
        elif reminder.type == 'RIDE':
            reminder.threshold = self.ride_threshold.data
        elif reminder.type == 'ROUND_TRIP':
            reminder.threshold = self.round_trip_threshold.data
        elif reminder.type == 'EXP':
            reminder.threshold = self.exp_threshold.data
            reminder.quantifier = self.exp_quantity.data

        return reminder

    @staticmethod
    def from_reminder(reminder):
        data = {
            'type': reminder.type.key,
            'notifications': []
        }

        if reminder.valid_until:
            for part in ['month', 'day', 'year']:
                data['valid_until/%s' % part] = getattr(reminder.valid_until, part, None)

        if reminder.type == 'BAL':
            data['balance_threshold'] = '%.2f' % round(reminder.threshold, 2)
        elif reminder.type == 'RIDE':
            data['ride_threshold'] = reminder.threshold
        elif reminder.type == 'ROUND_TRIP':
            data['round_trip_threshold'] = reminder.threshold
        elif reminder.type == 'EXP':
            data['exp_threshold'] = reminder.threshold
            data['exp_quantity'] = reminder.quantifier

        if reminder.send_sms:
            data['notifications'].append('SMS')
        if reminder.send_email:
            data['notifications'].append('EMAIL')

        # Remove any None values
        for key in data.copy():
            if data[key] is None:
                del data[key]

        return ReminderForm(MultiDict(data))
