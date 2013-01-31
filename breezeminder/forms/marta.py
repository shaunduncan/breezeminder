from wtforms import Form, SelectField
from wtforms.validators import Required

from breezeminder.models.marta import Route


def _route_choices():
    # Only type='3' for buses at the moment
    ids = []
    for route in Route.objects.filter(type='3').only('name'):
        try:
            name = int(route.name)
        except ValueError:
            name = route.name
        ids.append(name)
    return [(str(x), str(x)) for x in sorted(ids)]


class MartaRouteStatusForm(Form):
    route = SelectField('Route', choices=_route_choices(), validators=[Required()])
