from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from model_mommy.mommy import make

from .notifications.models import UserNotificationQuery
from .reports.models import Invite, Report
from .users.models import User
from .utils import get_tab_counts


class GetTabCountsTest(TestCase):
    def test_subscribed(self):
        user = make(User)
        make(UserNotificationQuery, user=user)
        make(UserNotificationQuery)
        context = get_tab_counts(user, [])
        self.assertEqual(context['subscribed'], 1)

    def test_invited_to(self):
        user = make(User)
        make(Invite, user=user, report=make(Report))
        make(Invite, report=make(Report))
        context = get_tab_counts(user, [])
        self.assertEqual(context['invited_to'], 1)

    def test_reported(self):
        user = make(User)
        make(Report, created_by=user)
        make(Report)
        report_id = make(Report).pk
        context = get_tab_counts(user, [report_id])
        self.assertEqual(context['reported'], 2)

    def test_open_and_claimed(self):
        make(Report)
        user = AnonymousUser()
        context = get_tab_counts(user, [])
        self.assertEqual(context['open_and_claimed'], 0)

        user = make(User)
        make(Report, claimed_by=user)
        context = get_tab_counts(user, [])
        self.assertEqual(context['open_and_claimed'], 1)

    def test_unclaimed_reports(self):
        make(Report, claimed_by=make(User))
        make(Report)
        user = AnonymousUser()
        context = get_tab_counts(user, [])
        self.assertEqual(context['unclaimed_reports'], 0)

        user = make(User, is_active=False)
        context = get_tab_counts(user, [])
        self.assertEqual(context['unclaimed_reports'], 0)

        user = make(User, is_active=True)
        context = get_tab_counts(user, [])
        self.assertEqual(context['unclaimed_reports'], 1)


class RubyPasswordHasherTest(TestCase):
    def test_verify(self):
        with self.settings(PASSWORD_HASHERS=('django.contrib.auth.hashers.PBKDF2PasswordHasher', 'hotline.utils.RubyPasswordHasher')):
            user = make(User)
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
