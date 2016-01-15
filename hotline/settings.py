from django.conf import global_settings

from arcutils.settings import init_settings

init_settings()

PASSWORD_HASHERS = list(global_settings.PASSWORD_HASHERS)
PASSWORD_HASHERS.insert(1, 'hotline.utils.RubyPasswordHasher')
