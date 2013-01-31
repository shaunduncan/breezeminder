from wtforms import (Form,
                     TextField,
                     TextAreaField)
from wtforms.validators import Required, Email


class ContactForm(Form):
    email = TextField('Your Email', validators=[Required(), Email()])
    subject = TextField('Subject', validators=[Required()])
    message = TextAreaField('Message', validators=[Required()])
