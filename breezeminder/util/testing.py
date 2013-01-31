import functools
from mock import patch

from breezeminder.app import app


def silence_is_golden(fn):
    # PATCH ALL THE THINGS!
    @patch.object(app.logger, 'debug')
    @patch.object(app.logger, 'info')
    @patch.object(app.logger, 'error')
    @patch.object(app.logger, 'exception')
    @functools.wraps(fn)
    def without_logger_noise(*args, **kwargs):
        return fn(*args, **kwargs)

    return without_logger_noise
