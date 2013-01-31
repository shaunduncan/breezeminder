from breezeminder.settings.common import *

DEBUG = True

SERVER_PORT = 5000
SERVER_LISTEN = '0.0.0.0'

MOCK_FETCH = DEBUG
MOCK_FILE = '../lib/example_output.html'

JUGGERNAUT = "http://127.0.0.1:8080/application.js"

REMEMBER_COOKIE_DOMAIN = 'localhost.localdomain'
REMEMBER_COOKIE_DURATION = timedelta(minutes=30)

ALLOW_NO_REFERRER = True

# Local caching for testing
CACHE_TYPE = 'filesystem'
CACHE_DIR = '/tmp/bmcache'
CACHE_DISABLED = False

# This should probably be watched. We don't want to flood the servers
ALLOW_USER_REFRESH = DEBUG
REFRESH_LIMITING = not DEBUG
REFRESH_INTERVAL = timedelta(seconds=10)

CARD_RETRY_DELAY = 10
CARD_RATE_LIMIT = '10/m'
CARD_STALE_THRESH = timedelta(minutes=1)

CELERYBEAT_SCHEDULE = {
    'send-outgoing-mail-task': {
        'task': 'tasks.send_outgoing_mail',
        'schedule': REFRESH_INTERVAL,
    },

    # Run the immediate mail queue every 30 seconds
    'send-immediate-mail-task': {
        'task': 'tasks.send_immediate_mail',
        'schedule': timedelta(seconds=30)
    },

    # Run the periodic check for stale cards
    'check-card-pull-task': {
        'task': 'tasks.check_card_pulls',
        'schedule': timedelta(seconds=5),
    },

    # Run the pull of realtime marta data
    'pull-marta-realtime-data-task': {
        'task': 'tasks.pull_marta_realtime_data',
        'schedule': timedelta(seconds=10),
    }
}
CELERYBEAT_SCHEDULE = {'pull-marta-realtime-data-task': CELERYBEAT_SCHEDULE['pull-marta-realtime-data-task']}
