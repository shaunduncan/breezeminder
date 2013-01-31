import os

from flask import Flask
from flaskext.cache import Cache
from flaskext.mail import Mail

from breezeminder.util import logger
from breezeminder.util.mongo import PortAwareMongoEngine


def get_app():
    app = Flask('breezeminder')

    settings_file = os.environ.get('BREEZEMINDER_SETTINGS', 'breezeminder.settings.local')
    app.config.from_object(settings_file)
    app.config['BREEZEMINDER_ENV'] = settings_file.split('.')[-1].upper()
    app.config['SHOW_ADS'] = app.config.get('ADSENSE_CLIENT', None) is not None

    app.secret_key = app.config['SECRET_KEY']

    app.db = PortAwareMongoEngine(app)

    logger.configure_logging(app)
    return app


# The core stuff
app = get_app()
cache = Cache(app)
mail = Mail(app)

# Assign modules to the app
app.cache = cache
app.mail = mail
