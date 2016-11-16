import os.path
from os import getenv
from collections import defaultdict
import requests.certs

# Certificate file for communication with other systems.
TLS_CERT_FILE = requests.certs.where()
print(('Loading TLS certificates from %s' % TLS_CERT_FILE))

import requests.certs

RFC1123_DATE_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'
PILLAR_SERVER_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SCHEME = 'https'
STORAGE_DIR = getenv('PILLAR_STORAGE_DIR', '/data/storage/pillar')
PORT = 5000
HOST = '0.0.0.0'
DEBUG = False

SECRET_KEY = '123'

# Authentication settings
BLENDER_ID_ENDPOINT = 'http://blender_id:8000/'

PILLAR_SERVER_ENDPOINT = 'http://pillar:5001/api/'

CDN_USE_URL_SIGNING = True
CDN_SERVICE_DOMAIN_PROTOCOL = 'https'
CDN_SERVICE_DOMAIN = '-CONFIG-THIS-'
CDN_CONTENT_SUBFOLDER = ''
CDN_URL_SIGNING_KEY = '-SECRET-'

CDN_STORAGE_USER = '-SECRET'
CDN_STORAGE_ADDRESS = 'push-11.cdnsun.com'
CDN_SYNC_LOGS = '/data/storage/logs'
CDN_RSA_KEY = '/data/config/cdnsun_id_rsa'
CDN_KNOWN_HOSTS = '/data/config/known_hosts'

UPLOADS_LOCAL_STORAGE_THUMBNAILS = {
    's': {'size': (90, 90), 'crop': True},
    'b': {'size': (160, 160), 'crop': True},
    't': {'size': (160, 160), 'crop': False},
    'm': {'size': (320, 320), 'crop': False},
    'l': {'size': (1024, 1024), 'crop': False},
    'h': {'size': (2048, 2048), 'crop': False}
}

BIN_FFPROBE = '/usr/bin/ffprobe'
BIN_FFMPEG = '/usr/bin/ffmpeg'
BIN_SSH = '/usr/bin/ssh'
BIN_RSYNC = '/usr/bin/rsync'

GCLOUD_APP_CREDENTIALS = 'google_app.json'
GCLOUD_PROJECT = '-SECRET-'

ADMIN_USER_GROUP = '5596e975ea893b269af85c0e'
SUBSCRIBER_USER_GROUP = '5596e975ea893b269af85c0f'
BUGSNAG_API_KEY = ''

ALGOLIA_USER = '-SECRET-'
ALGOLIA_API_KEY = '-SECRET-'
ALGOLIA_INDEX_USERS = 'dev_Users'
ALGOLIA_INDEX_NODES = 'dev_Nodes'

SEARCH_BACKEND = 'algolia'  # algolia, elastic

ZENCODER_API_KEY = '-SECRET-'
ZENCODER_NOTIFICATIONS_SECRET = '-SECRET-'
ZENCODER_NOTIFICATIONS_URL = 'http://zencoderfetcher/'

ENCODING_BACKEND = 'zencoder'  # local, flamenco

# Validity period of links, per file storage backend. Expressed in seconds.
# Shouldn't be more than a year, as this isn't supported by HTTP/1.1.
FILE_LINK_VALIDITY = defaultdict(
    lambda: 3600 * 24 * 30,  # default of 1 month.
    gcs=3600 * 23,  # 23 hours for Google Cloud Storage.
)

# Roles with full GET-access to all variations of files.
FULL_FILE_ACCESS_ROLES = {'admin', 'subscriber', 'demo'}

# Client and Subclient IDs for Blender ID
BLENDER_ID_CLIENT_ID = 'SPECIAL-SNOWFLAKE-57'
BLENDER_ID_SUBCLIENT_ID = 'PILLAR'


# See https://docs.python.org/2/library/logging.config.html#configuration-dictionary-schema
LOGGING = {
    'version': 1,
    'formatters': {
        'default': {'format': '%(asctime)-15s %(levelname)8s %(name)s %(message)s'}
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'stream': 'ext://sys.stderr',
        }
    },
    'loggers': {
        'pillar': {'level': 'INFO'},
        'werkzeug': {'level': 'INFO'},
    },
    'root': {
        'level': 'WARNING',
        'handlers': [
            'console',
        ],
    }
}

SHORT_LINK_BASE_URL = 'https://blender.cloud/r/'
SHORT_CODE_LENGTH = 6  # characters

# People are allowed this many bytes per uploaded file.
FILESIZE_LIMIT_BYTES_NONSUBS = 32 * 2 ** 20
# Unless they have one of those roles.
ROLES_FOR_UNLIMITED_UPLOADS = {'subscriber', 'demo', 'admin'}


#############################################
# Old pillar-web config:

# Mapping from /{path} to URL to redirect to.
REDIRECTS = {}

GIT = 'git'

# Setting this to True can be useful for development.
# Note that it doesn't add the /p/home/{node-id} endpoint, so you will have to
# change the URL of the home project if you want to have direct access to nodes.
RENDER_HOME_AS_REGULAR_PROJECT = False


# Authentication token for the Urler service. If None, defaults
# to the authentication token of the current user.
URLER_SERVICE_AUTH_TOKEN = None


# Blender Cloud add-on version. This updates the value in all places in the
# front-end.
BLENDER_CLOUD_ADDON_VERSION = '1.4'

EXTERNAL_SUBSCRIPTIONS_MANAGEMENT_SERVER = 'https://store.blender.org/api/'

# Certificate file for communication with other systems.
TLS_CERT_FILE = requests.certs.where()
