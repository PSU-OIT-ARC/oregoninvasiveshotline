import os
import shutil
import tempfile

from django.conf import settings
from django.test.runner import DiscoverRunner


class TestRunner(DiscoverRunner):

    def setup_test_environment(self, **kwargs):
        settings.MEDIA_ROOT = media_root = tempfile.mkdtemp()

        # These directories are needed for generated icons and thumbnails
        os.mkdir(os.path.join(media_root, 'icons'))
        os.mkdir(os.path.join(media_root, 'generated_icons'))
        os.mkdir(os.path.join(media_root, 'generated_thumbnails'))

        super().setup_test_environment(**kwargs)

    def teardown_test_environment(self, **kwargs):
        shutil.rmtree(settings.MEDIA_ROOT)
        super().teardown_test_environment(**kwargs)
