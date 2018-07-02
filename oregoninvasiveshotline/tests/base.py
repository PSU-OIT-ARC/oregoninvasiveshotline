import logging

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission, Group
from django.contrib.auth import get_user_model
from django.db import transaction
from django.apps import apps

from arcutils.test.user import UserMixin

from . import utils

logger = logging.getLogger(__name__)


class ServiceTestCaseMixin(object):
    def _pre_setup(self):
        super(ServiceTestCaseMixin, self)._pre_setup()

        utils.clear_search_indexes()


class TestCaseMixin(UserMixin, ServiceTestCaseMixin):
    """
    TBD
    """
