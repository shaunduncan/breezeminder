import datetime
import json
import re

from unidecode import unidecode

from breezeminder.app import app


_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')


@app.template_filter('slugify')
def slugify(text, delim=u'-'):
    """Generates an ASCII-only slug."""
    result = []
    for word in _punct_re.split(text.lower()):
        result.extend(unidecode(word).split())
    return unicode(delim.join(result))


@app.template_filter('strftime')
def safe_strftime(value, format="%m/%d/%Y", default=''):
    if value is not None:
        return value.strftime(format)
    return default


@app.template_filter('money')
def money(value):
    try:
        return '$%.2f' % round(float(value), 2)
    except:
        return '$0.00'


@app.template_filter('timesince')
def timesince(dt, default="just now"):
    """
    Returns string representing "time since" e.g.
    3 days ago, 5 hours ago etc.
    """

    now = datetime.datetime.now()
    diff = now - dt

    periods = (
        (diff.days / 365, "year", "years"),
        (diff.days / 30, "month", "months"),
        (diff.days / 7, "week", "weeks"),
        (diff.days, "day", "days"),
        (diff.seconds / 3600, "hour", "hours"),
        (diff.seconds / 60, "minute", "minutes"),
        (diff.seconds, "second", "seconds"),
    )

    for period, singular, plural in periods:
        if period:
            return "%d %s ago" % (period, singular if period == 1 else plural)

    return default


@app.template_filter('jsonencode')
def jsonencode(data):
    return json.dumps(data) 
