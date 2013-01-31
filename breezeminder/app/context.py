from datetime import datetime
from flask import (get_flashed_messages,
                   request)
from flask.ext.login import current_user

from breezeminder.app import app
from breezeminder.models.alerts import Alert


@app.context_processor
def core_context():
    now = datetime.now()

    context = {
        'messages': get_flashed_messages(with_categories=True),
        'config': app.config,
        'request': request,
        'current_user': current_user,
        'now': now,
        'is_mobile': (request.user_agent.platform in ('android', 'iphone') or
                        'blackberry' in request.user_agent.string),
        'alerts': Alert.objects.filter(start__lt=now, end__gt=now)
    }
    # Any functions needed?
    return context
