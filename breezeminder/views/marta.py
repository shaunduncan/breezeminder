import json

from datetime import datetime, timedelta

from flask import (flash,
                   make_response,
                   render_template,
                   request)

from breezeminder.app import app
from breezeminder.forms.marta import MartaRouteStatusForm
from breezeminder.models.marta import (Route,
                                       Schedule,
                                       Stop,
                                       ScheduledStop,
                                       Bus)
from breezeminder.util.views import same_origin, nocache


@nocache
def status():
    form = MartaRouteStatusForm(request.form)

    context = {
        'title': 'Check MARTA Bus Status',
        'description': 'Check the current status of MARTA Buses on any route',
        'form': form
    }

    if request.method == 'POST' and form.validate():
        try:
            context['route'] = Route.objects.get(name=form.route.data)
            print context['route']
        except Route.DoesNotExist:
            flash('Oops! An error occurred looking up route %s' % form.route.data, 'error')

    return render_template('marta/realtime.html', **context)


@same_origin
def route_details(route_id):
    route = Route.objects.get_or_404(name=route_id)
    schedule = Schedule.objects.for_today()

    resp = make_response(json.dumps(route.to_json(schedule=schedule)))
    resp.cache_control.no_cache = True
    resp.headers['Content-Type'] = 'application/json'

    return resp


@same_origin
def route_realtime(route_id):
    # Only get "recent" buses
    current = datetime.now() - timedelta(hours=1)
    qs = Bus.objects.filter(route=route_id,
                            status_time__gte=current,
                            is_stale=False)
    data = [bus.to_json() for bus in qs]

    resp = make_response(json.dumps(data))
    resp.cache_control.no_cache = True
    resp.headers['Content-Type'] = 'application/json'

    return resp


@same_origin
def route_upcoming(route_id):
    route = Route.objects.get_or_404(name=route_id)
    schedule = Schedule.objects.for_today()

    data = {}
    start = ScheduledStop.arrival_now()

    # Filter the next arrivals for 1hour
    # This should limit the results enough so we don't do more work
    qs = ScheduledStop.objects.filter(route_id=route.id,
                                      schedule_id=schedule.id,
                                      arrival__gt=start,
                                      arrival__lt=start + 3600)

    # Optionally accept a stop argument
    if 'stop' in request.args:
        try:
            stop = Stop.objects.get(id=request.args['stop'])
        except (Stop.DoesNotExist, Stop.MultipleObjectsReturned, ValueError):
            pass
        else:
            qs = qs.filter(stop_id=stop.id)

    # Process ordered by arrival - grouped by stop
    for stop in qs.only('stop_id', 'arrival').order_by('arrival'):
        if stop.stop_id not in data:
            data[stop.stop_id] = {
                'refresh': stop.arrival - start,
                'times': []
            }

        if len(data[stop.stop_id]['times']) >= 3:
            continue

        data[stop.stop_id]['times'].append(
            ScheduledStop.seconds_to_timestring(stop.arrival)
        )

    resp = make_response(json.dumps(data))
    resp.cache_control.no_cache = True
    resp.headers['Content-Type'] = 'application/json'

    return resp


app.add_url_rule('/marta/', 'marta.status', status, methods=['GET', 'POST'])
app.add_url_rule('/marta/route/<route_id>.json', 'marta.route.details', route_details)
app.add_url_rule('/marta/realtime/<route_id>.json', 'marta.route.realtime', route_realtime)
app.add_url_rule('/marta/upcoming/<route_id>.json', 'marta.route.upcoming', route_upcoming)
