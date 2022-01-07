# -*- coding: utf-8 -*-
import os.path

from django.utils.translation import ugettext_lazy as _
from django.conf import global_settings
from django.urls import reverse_lazy

from emcee.runner.config import YAMLCommandConfiguration
from emcee.runner import configs, config
from emcee.app.config import YAMLAppConfiguration, load_app_configuration
from emcee.app import app_configs, app_config, processors

configs.load(YAMLCommandConfiguration)
app_configs.load(YAMLAppConfiguration)


BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
FILE_ROOT = os.path.abspath(os.path.join(BASE_PATH, '..'))

ROOT_URLCONF = "oregoninvasiveshotline.urls"
WSGI_APPLICATION = "oregoninvasiveshotline.wsgi.application"
SITE_ID = 1

# Email/correspondence settings
SERVER_EMAIL = "do-not-reply@oregoninvasiveshotline.org"
DEFAULT_FROM_EMAIL = SERVER_EMAIL
ADMINS = [["PSU Web & Mobile Team", "webteam@pdx.edu"]]
MANAGERS = [["PSU Web & Mobile Team", "webteam@pdx.edu"]]
EMAIL_SUBJECT_PREFIX = "[Oregon Invasive Hotline] "
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Los_Angeles'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_ETAGS = True
USE_I18N = True
USE_L10N = True
USE_TZ = True

# CSRF Defaults
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True

STATIC_ROOT = os.path.join(FILE_ROOT, 'static')
STATIC_URL = '/static/'
MEDIA_ROOT = os.path.join(FILE_ROOT, 'media')
MEDIA_URL = '/media/'

# Logging configuration
FIRST_PARTY_LOGGER = {
    'handlers': ['console'],
    'propagate': False,
    'level': 'INFO'
}
THIRD_PARTY_LOGGER = {
    'handlers': ['console'],
    'propagate': False,
    'level': 'WARN'
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(asctime)s %(levelname)s [%(name)s] %(message)s'
        }
    },
    'filters': {},
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    'loggers': {
        'oregoninvasiveshotline': FIRST_PARTY_LOGGER,
        'celery.task': FIRST_PARTY_LOGGER,
        'django': THIRD_PARTY_LOGGER,
        'elasticsearch': THIRD_PARTY_LOGGER,
    },
    'root': THIRD_PARTY_LOGGER
}

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "users-home"

AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.AllowAllUsersModelBackend"]
AUTH_USER_MODEL = "users.User"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"}
]

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [os.path.join(BASE_PATH, 'templates')],
    'APP_DIRS': True,
    'OPTIONS': {
        'builtins': [
            "django.contrib.staticfiles.templatetags.staticfiles",
            "bootstrapform.templatetags.bootstrap",
            "oregoninvasiveshotline.templatetags.arc"
        ],
        'context_processors': [
            "django.template.context_processors.debug",
            "django.template.context_processors.request",
            "django.contrib.auth.context_processors.auth",
            "django.contrib.messages.context_processors.messages",
            "django.template.context_processors.media",
            "django.template.context_processors.static",
            "django.template.context_processors.tz",
            "oregoninvasiveshotline.context_processors.defaults"
        ]
    }
}]

INSTALLED_APPS = [
    "oregoninvasiveshotline.apps.MainAppConfig",
    "oregoninvasiveshotline.permissions",
    "oregoninvasiveshotline.comments",
    "oregoninvasiveshotline.counties",
    "oregoninvasiveshotline.images",
    "oregoninvasiveshotline.notifications",
    "oregoninvasiveshotline.pages",
    "oregoninvasiveshotline.reports",
    "oregoninvasiveshotline.species",
    "oregoninvasiveshotline.users",

    # Third party
    "bootstrapform",
    "rest_framework",

    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.flatpages",
    "django.contrib.gis"
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.http.ConditionalGetMiddleware"
]

DATABASES = {
    'default': {
        'ENGINE': "django.contrib.gis.db.backends.postgis",
        'NAME': "invasives",
        'USER': "invasives",
        'PASSWORD': "invasives",
        'ATOMIC_REQUESTS': True
    }
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        "rest_framework.authentication.SessionAuthentication"
    ],
    'DEFAULT_RENDERER_CLASSES': [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer"
    ]
}

# Application-specific configuration
CONTACT_EMAIL = "imapinvasivesoregon@gmail.com"
ITEMS_PER_PAGE = 25
ICON_DEFAULT_COLOR = "#999999"
ICON_DIR = "generated_icons"
ICON_TYPE = "png"

GOOGLE_ANALYTICS_TRACKING_ID = None
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY', '')

NOTIFICATIONS = {
    'from_email': "webmaster@localhost",
    'login_link__subject': "Oregon Invasives Hotline - Login Link",
    'new_report__subject': "Oregon Invasives Hotline - Thank you for your report",
    'notify_new_owner__subject': "A subscription has been assigned to you on Oregon Invasives Hotline",
    'notify_new_submission__subject': "New Oregon Invasives Hotline submission for review",
    'notify_new_comment__subject': "Oregon Invasives Hotline - New Comment on Report",
    'invite_reviewer__subject': "Oregon Invasives Hotline - Submission Review Request"
}


settings = load_app_configuration(app_config, globals())
processors.set_secret_key(config, settings)
processors.set_database_parameters(config, settings)
processors.set_smtp_parameters(config, settings)
processors.set_sentry_dsn(config, settings, traces_sample_rate=0.1)

if config.env in ['stage', 'prod']:
    from emcee.backends.aws.ssm import ssm

    # Configure Google Maps API key
    GOOGLE_ANALYTICS_TRACKING_ID = "UA-57378202-5"
    GOOGLE_API_KEY = ssm('GOOGLE_API_KEY',
                         ssm_prefix=config.infrastructure.ssm_prefix,
                         region=config.infrastructure.region)

    # Instruct Django to inspect HTTP header to help determine
    # whether the request was made securely
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    # Set compatibility password hasher
    PASSWORD_HASHERS = global_settings.PASSWORD_HASHERS + [
        'oregoninvasiveshotline.hashers.RubyPasswordHasher'
    ]
