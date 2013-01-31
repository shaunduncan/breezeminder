from wtforms import Form, TextField
from wtforms.validators import required

from breezeminder.forms.validators import UniqueCardNumber


_card_taken_message = 'This number already belongs to another user'


class CreateCardForm(Form):
    cardnumber = TextField('Card Number',
                           validators=[required(),
                                       UniqueCardNumber(message=_card_taken_message)])
