import os
import pkg_resources
from fnmatch import fnmatch
from ipaddress import ip_address

from django.conf import global_settings
from django.contrib.messages import constants as messages
from django.core.urlresolvers import reverse_lazy

from local_settings import LocalSetting, SecretSetting, load_and_check_settings


PACKAGE = os.path.basename(os.path.dirname(__file__))
PACKAGE_DIR = pkg_resources.resource_filename(PACKAGE, '')


# Local settings

DEBUG = LocalSetting(False)

DATABASES = {
    'default': {
        'NAME': LocalSetting(PACKAGE),
        'USER': LocalSetting(''),
        'PASSWORD': SecretSetting(),
        'HOST': LocalSetting(''),
    },
}

ELASTICSEARCH_CONNECTIONS = {
    'default': {
        'hosts': [LocalSetting(default='http://localhost:9200')],
        'index_name': LocalSetting(),
    }
}

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
        'URL': 'http://localhost:9200/',
        'INDEX_NAME': '{PACKAGE}-{ENV}',
    }
}

SECRET_KEY = SecretSetting()

globals().update(load_and_check_settings(globals()))

# / Local settings


LOGIN_URL = reverse_lazy('login')
LOGIN_REDIRECT_URL = reverse_lazy('users-home')

MESSAGE_TAGS = {
    messages.ERROR: 'danger',
}

PASSWORD_HASHERS = list(global_settings.PASSWORD_HASHERS)
PASSWORD_HASHERS.insert(1, 'hotline.utils.RubyPasswordHasher')


if DEBUG:
    INTERNAL_IPS = type('INTERNAL_IPS', (), {
        '__contains__': lambda self, addr: ip_address(addr).is_private,
    })()


if globals().get('TEST'):
    import logging
    logging.disable(logging.ERROR)
    from mommy_spatial_generators import MOMMY_SPATIAL_FIELDS
    MOMMY_CUSTOM_FIELDS_GEN = MOMMY_SPATIAL_FIELDS
