import functools

from flask import abort, make_response, request, redirect
from urlparse import urlparse

from breezeminder.app import app


def redirect_next():
    next = request.args.get('next') or '/'
    return redirect(next)


def nocache(fn):
    @functools.wraps(fn)
    def do_nocache(*args, **kwargs):
        resp = make_response(fn(*args, **kwargs))
        resp.cache_control.no_cache = True
        return resp
    return do_nocache


def same_origin(fn):
    @functools.wraps(fn)
    def check_origin(*args, **kwargs):
        if not app.config.get('ALLOW_NO_REFERRER', False):
            # Only allow local referers
            try:
                info = urlparse(request.referrer)
                app.logger.debug('Checking same origin %s == %s' % (request.host, info.netloc))

                same_origin = request.host == info.netloc
            except:
                same_origin = False

            if not same_origin:
                app.logger.info("Failed access to json data - not same origin")
                abort(404)
        else:
            app.logger.debug('Referrer checking disabled')

        return fn(*args, **kwargs)
    return check_origin
