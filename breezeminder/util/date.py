import datetime


def timesince(dt, default="Just Now"):
    """
    Returns string representing "time since" e.g.
    3 days ago, 5 hours ago etc.
    """
    now = datetime.datetime.now()
    diff = now - dt

    periods = (
        (diff.days / 365, "Year", "Years"),
        (diff.days / 30, "Month", "Months"),
        (diff.days / 7, "Week", "Weeks"),
        (diff.days, "Day", "Days"),
        (diff.seconds / 3600, "Hour", "Hours"),
        (diff.seconds / 60, "Minute", "Minutes"),
        (diff.seconds, "Second", "Seconds"),
    )

    for period, singular, plural in periods:
        if period:
            return "%d %s Ago" % (period, singular if period == 1 else plural)
    return default
