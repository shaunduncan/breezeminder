from datetime import timedelta

from breezeminder.settings.common import *

SITE_NAME="BreezeMinder"
DEBUG = False
LOGGING_LEVEL = 'INFO'

SERVER_PORT = 5000
SERVER_LISTEN = '0.0.0.0'

CACHE_TYPE = 'memcached'
CACHE_MEMCACHED_SERVERS = ('127.0.0.1:11211', )
CACHE_DEFAULT_TIMEOUT = 3600
CACHE_DISABLED = False

MONGODB_DB = 'breezeminder'
MONGODB_PORT = 27017

MOCK_FETCH = False

# Flask-Mail settings
MAIL_DEBUG = False
MAIL_SERVER = 'localhost'
MAIL_PORT = 25
MAIL_USE_TLS = False
MAIL_USE_SSL = False
MAIL_USERNAME = ''
MAIL_PASSWORD = ''
DEFAULT_MAIL_SENDER = 'no-reply@breezeminder.com'
DEFAULT_MAX_EMAILS = None
MAIL_FAIL_SILENTLY = MAIL_DEBUG
MAIL_SUPPRESS_SEND = False

LOG_FILE = '/tmp/breezeminder.log'

REFRESH_INTERVAL = timedelta(hours=3)

# Let's use redis instead of mongo for our celery queuing
BROKER_TRANSPORT = "redis"
BROKER_HOST = "localhost"  # Maps to redis host.
BROKER_PORT = 6379         # Maps to redis port.
BROKER_VHOST = "0"         # Maps to database number.

CELERY_LOG_FILE = '/tmp/breezeminder-celery.log'
CELERY_LOG_LEVEL = LOGGING_LEVEL
CELERYD_LOG_LEVEL = CELERY_LOG_LEVEL
CELERYBEAT_LOG_LEVEL = CELERY_LOG_LEVEL

CARD_RETRY_DELAY = 15 * 60
CARD_RATE_LIMIT = 1
