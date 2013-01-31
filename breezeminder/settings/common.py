from datetime import timedelta

SITE_NAME="BreezeMinder"
DOMAIN = 'breezeminder.com'
COMPANY_FULL_NAME = 'Krakendoodle, LLC'
COMPANY_NAME = 'Krakendoodle'
DEBUG = True
LOGGING_LEVEL = 'DEBUG'

JUGGERNAUT = "http://breezeminder.com:8080/application.js"

SESSION_TIMEOUT = timedelta(minutes=30)

REMEMBER_COOKIE_NAME = 'breezeminder'
REMEMBER_COOKIE_DURATION = timedelta(days=30)
REMEMBER_COOKIE_DOMAIN = '.breezeminder.com'

ALLOW_NO_REFERRER = False

GOOGLE_MAPS_APIKEY = "Use_Your_Own_Value_Here"

MARTA_BY_ROUTE_ENDPOINT = 'http://developer.itsmarta.com/BRDRestService/BRDRestService.svc/GetBusByRoute/%s'
MARTA_ENDPOINT = 'http://developer.itsmarta.com/BRDRestService/BRDRestService.svc/GetAllBus'
MARTA_RATE_LIMIT = '6/m'
MARTA_RETRY_DELAY = 30
MARTA_REALTIME_QUEUE = 'marta'

if DEBUG:
    SERVER_PORT = 5000
    SERVER_LISTEN = 'localhost'
else:
    SERVER_PORT = 80
    SERVER_LISTEN = '0.0.0.0'

SECRET_KEY = "ThisIsTheCommon.pySecretKey"

CACHE_TYPE = 'memcached'
CACHE_MEMCACHED_SERVERS = ('127.0.0.1:11211', )
CACHE_DEFAULT_TIMEOUT = 3600
CACHE_DISABLED = DEBUG

# Supply your own bit.ly username/api key
BITLY_USERNAME = 'use_your_own'
BITLY_API_KEY = 'use_your_own'

ANALYTICS_CODE = ''

MONGODB_DB = SITE_NAME.lower()
MONGODB_PORT = 27017

# Flask-Mail settings
MAIL_DEBUG = DEBUG
MAIL_SERVER = 'localhost'
MAIL_PORT = 25
MAIL_USE_TLS = False
MAIL_USE_SSL = False
MAIL_USERNAME = ''
MAIL_PASSWORD = ''
DEFAULT_MAIL_SENDER = 'no-reply@%s' % DOMAIN
DEFAULT_MAX_EMAILS = None
MAIL_FAIL_SILENTLY = MAIL_DEBUG
MAIL_SUPPRESS_SEND = False

# This should probably be watched. We don't want to flood the servers
ALLOW_USER_REFRESH = False
REFRESH_LIMITING = False
REFRESH_INTERVAL = timedelta(minutes=30)

CARD_RETRY_DELAY = 15 * 60
CARD_RATE_LIMIT = '10/m'
CARD_STALE_THRESH = timedelta(minutes=10)

LOG_FILE = '/tmp/%s.log' % SITE_NAME.lower()

BROKER_TRANSPORT = "redis"
BROKER_HOST = "localhost"
BROKER_PORT = 6379
BROKER_VHOST = "0"

CELERY_LOG_FILE = '/tmp/%s.celery.log' % SITE_NAME.lower()
CELERY_LOG_LEVEL = LOGGING_LEVEL
CELERYD_LOG_LEVEL = CELERY_LOG_LEVEL
CELERYBEAT_LOG_LEVEL = CELERY_LOG_LEVEL
CELERY_RESULT_BACKEND = "redis"
CELERY_REDIS_HOST = "localhost"
CELERY_REDIS_PORT = 6379
CELERY_REDIS_DB = 0
CELERY_IGNORE_RESULT = True
CELERY_IMPORTS = ('breezeminder.tasks', )
CELERYD_CONCURRENCY = 1
CELERY_ALWAYS_EAGER = False
CELERY_DEFAULT_QUEUE = 'breezeminder'

from celery.schedules import crontab
CELERYBEAT_SCHEDULE = {
    # Run the mail queue every five minutes during reasonable hours
    'send-outgoing-mail-task': {
        'task': 'tasks.send_outgoing_mail',
        'schedule': crontab(minute='*/5', hour='7-22')
    },

    # Run the immediate mail queue every 30 seconds
    'send-immediate-mail-task': {
        'task': 'tasks.send_immediate_mail',
        'schedule': timedelta(seconds=30)
    },

    # Run the periodic check for stale cards
    'check-card-pull-task': {
        'task': 'tasks.check_card_pulls',
        'schedule': timedelta(seconds=30),
    },

    # Run the pull of realtime marta data
    'pull-marta-realtime-data-task': {
        'task': 'tasks.pull_marta_realtime_data',
        'schedule': timedelta(seconds=10),
    }
}
