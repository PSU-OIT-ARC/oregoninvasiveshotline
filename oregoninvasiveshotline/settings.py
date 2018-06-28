from django.conf import global_settings

from arcutils.settings import init_settings
from emcee.backends.aws import processors


init_settings(settings_processors=[processors.set_secret_key,
                                   processors.set_sentry_dsn,
                                   processors.set_smtp_parameters,
                                   processors.set_database_parameters,
                                   processors.set_elasticsearch_parameters])

PASSWORD_HASHERS = list(global_settings.PASSWORD_HASHERS)
PASSWORD_HASHERS.insert(1, 'oregoninvasiveshotline.hashers.RubyPasswordHasher')
