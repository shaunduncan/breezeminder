from wtforms import fields

from breezeminder.forms import widgets


class BootstrapRadioField(fields.RadioField):
    """
    A specific implementation of `wtforms.fields.RadioField` that
    uses a `breezeminder.forms.widgets.BootstrapButtonWidget` as its
    widget implementation.
    """

    widget = widgets.BootstrapButtonWidget()

    def __init__(self, *args, **kwargs):
        if 'btn_class' in kwargs:
            self.widget.btn_class = kwargs.pop('btn_class')
        super(BootstrapRadioField, self).__init__(*args, **kwargs)


class BootstrapSelectField(fields.SelectField):
    """
    A specific implementation of `wtforms.fields.SelectField` that
    uses a `breezeminder.forms.widgets.BootstrapButtonWidget` as its
    widget implementation.
    """

    widget = widgets.BootstrapButtonWidget()

    def __init__(self, *args, **kwargs):
        if 'btn_class' in kwargs:
            self.widget.btn_class = kwargs.pop('btn_class')
        super(BootstrapSelectField, self).__init__(*args, **kwargs)


class BootstrapSelectMultipleField(fields.SelectMultipleField):
    """
    A specific implementation of `wtforms.fields.SelectMultipleField` that
    uses a `breezeminder.forms.widgets.BootstrapButtonWidget` as its
    widget implementation.
    """

    widget = widgets.BootstrapButtonWidget(multiple=True)

    def __init__(self, *args, **kwargs):
        if 'btn_class' in kwargs:
            self.widget.btn_class = kwargs.pop('btn_class')
        super(BootstrapSelectMultipleField, self).__init__(*args, **kwargs)


# TODO: Should a BooleanField provide an implementation? It would work like two-option Radio Field
