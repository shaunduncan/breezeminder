from datetime import timedelta

from breezeminder.settings.common import *

SITE_NAME="BreezeMinder"
DEBUG = False
LOGGING_LEVEL = 'INFO'

REMEMBER_COOKIE_DURATION = timedelta(days=1)
SESSION_TIMEOUT = timedelta(minutes=15)

SERVER_PORT = 80
SERVER_LISTEN = '0.0.0.0'

# Uncomment and fill in with AdSense client ID to enable ads
# ADSENSE_CLIENT = ''

SECRET_KEY = "ThisShouldBeChangedToYourOwnValue!"

CACHE_TYPE = 'memcached'
CACHE_MEMCACHED_SERVERS = ('127.0.0.1:11211', )
CACHE_DEFAULT_TIMEOUT = 3600
CACHE_DISABLED = False

ANALYTICS_CODE = """
<script type="text/javascript">
    var _gaq = _gaq || [];
    _gaq.push(['_setAccount', 'UA-33427452-1']);
    _gaq.push(['_setDomainName', 'breezeminder.com']);
    _gaq.push(['_trackPageview']);

    (function() {
        var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
        ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
        var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
    })();

</script>
"""

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

LOG_FILE = '/var/log/breezeminder/app.log'

REFRESH_INTERVAL = timedelta(hours=8)
CARD_RETRY_DELAY = 15 * 60
CARD_RATE_LIMIT = '10/m'
CARD_STALE_THRESH = timedelta(minutes=10)

# Let's use redis instead of mongo for our celery queuing
BROKER_TRANSPORT = "redis"
BROKER_HOST = "localhost"  # Maps to redis host.
BROKER_PORT = 6379         # Maps to redis port.
BROKER_VHOST = "0"         # Maps to database number.

CELERY_LOG_FILE = '/var/log/breezeminder/celery.log'
CELERY_LOG_LEVEL = LOGGING_LEVEL
CELERYD_LOG_LEVEL = CELERY_LOG_LEVEL
CELERYBEAT_LOG_LEVEL = CELERY_LOG_LEVEL

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
        'schedule': timedelta(minutes=5),
    },

    # Run the pull of realtime marta data
    'pull-marta-realtime-data-task': {
        'task': 'tasks.pull_marta_realtime_data',
        'schedule': timedelta(seconds=10),
    }
}
