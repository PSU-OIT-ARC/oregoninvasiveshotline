from django.test import TestCase

from arcutils.test.user import UserMixin


class RubyPasswordHasherTest(TestCase, UserMixin):
    def test_verify(self):
        with self.settings(PASSWORD_HASHERS=('django.contrib.auth.hashers.PBKDF2PasswordHasher',
                                             'oregoninvasiveshotline.hashers.RubyPasswordHasher')):
            user = self.create_user(username="foo@pdx.edu", password="foobar")
            # this is foobar hashed with sha512
            hash = "c3ab8ff13720e8ad9047dd39466b3c8974e592c2fa383d4a3960714caef0c4f2"
            user.password = "RubyPasswordHasher$1$$" + hash
            user.save()
            self.assertTrue(user.check_password("foobar"))
            self.assertFalse(user.check_password("2"))
            # this should still work, despite the fact that the
            # RubyPasswordHasher didn't implement all the methods (because it
            # isn't the first password hasher)
            user.set_password("foobar2")
