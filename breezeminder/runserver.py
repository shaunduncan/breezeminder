import logging
import sys

from werkzeug import run_simple
from werkzeug.contrib.profiler import ProfilerMiddleware, MergeStream

# Application setup, mostly
from breezeminder.app import app, auth, context, filters
from breezeminder import views, models


def profile_run():
    print "* Profiling"
    f = open('./profiler.log', 'w')
    profiled_app = ProfilerMiddleware(app, MergeStream(sys.stderr, f))
    run_simple(app.config['SERVER_LISTEN'],
               app.config['SERVER_PORT'],
               profiled_app,
               use_reloader=app.config['DEBUG'],
               use_debugger=app.config['DEBUG'])


def run():
    app.logger.setLevel(getattr(logging, app.config['LOGGING_LEVEL']))
    app.logger.info('Running BreezeMinder %s' % app.config['BREEZEMINDER_ENV'])
    app.run(host=app.config['SERVER_LISTEN'],
            port=app.config['SERVER_PORT'],
            debug=app.config['DEBUG'],
            use_reloader=app.config['DEBUG'])


if __name__ == "__main__":
    if "profile" in sys.argv:
        profile_run()
    else:
        run()
