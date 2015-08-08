import os
import shutil
import tempfile

from django.conf import settings
from elasticmodels import SearchRunner


class TestRunner(SearchRunner):
    """
    Set whatever test settings need to be in place when you run tests
    """
    def run_tests(self, *args, **kwargs):
        settings.TEST = True
        media_root = tempfile.mkdtemp()
        # these directories are needed for generated icons and thumbnails
        os.mkdir(os.path.join(media_root, "generated_icons"))
        os.mkdir(os.path.join(media_root, "generated_thumbnails"))
        settings.MEDIA_ROOT = media_root
        settings.CELERY_ALWAYS_EAGER = True
        settings.PASSWORD_HASHERS = (
            'django.contrib.auth.hashers.MD5PasswordHasher',
        )

        to_return = super().run_tests(*args, **kwargs)
        shutil.rmtree(media_root)

        return to_return
