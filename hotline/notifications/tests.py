from unittest.mock import Mock, patch

from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase

from model_mommy.mommy import make

from arcutils.test.user import UserMixin

from hotline.reports.models import Report

from .models import UserNotificationQuery


class CreateViewTest(TestCase, UserMixin):

    def setUp(self):
        self.user = self.create_user(
            username="foo@example.com",
            password="foo",
            is_active=True,
            is_staff=False
        )

    def test_only_active_users_can_view_page(self):
        self.client.login(email=self.user.email, password="foo")
        self.user.is_active = False
        self.user.save()
        response = self.client.get(reverse("notifications-create"))
        self.assertEqual(response.status_code, 403)

    def test_get(self):
        self.client.login(email=self.user.email, password="foo")
        response = self.client.get(reverse("notifications-create"))
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        self.client.login(email=self.user.email, password="foo")
        pre_count = UserNotificationQuery.objects.count()
        response = self.client.post(reverse("notifications-create") + "?q=foo", {
            "name": "bar"
        })
        self.assertRedirects(response, reverse("reports-list") + "?q=foo")
        self.assertEqual(UserNotificationQuery.objects.count(), pre_count+1)


class ListViewTest(TestCase, UserMixin):

    def test_get(self):
        user = self.create_user(
            username="foo@example.com",
            password="foo",
            is_active=True
        )
        make(UserNotificationQuery, user=user, query="?q=foo")
        self.client.login(email=user.email, password="foo")
        response = self.client.get(reverse("notifications-list"))
        self.assertEqual(response.status_code, 200)


class UserNotificationQueryTest(TestCase, UserMixin):

    @patch("hotline.notifications.models.threading.Thread")
    def test_notify_sends_emails_to_subscribers(self, thread):
        user = self.create_user(username="foo@example.com")
        # we subscribe to the same thing twice, just to ensure that only one
        # email is sent to the user, when a report matches
        make(UserNotificationQuery, query="q=foobarius", user=user)
        make(UserNotificationQuery, query="q=foobarius", user=user)

        # this report doesn't have the words "foobarius" in it, so no email
        # should be sent
        report = make(Report)
        UserNotificationQuery.notify(report, request=Mock())
        # since we mocked up the threading library, we need a way to call the
        # Thread's target function within this main thread. This is a hacky way
        # to do that
        thread.call_args[1]['target'](*thread.call_args[1]['args'])
        self.assertEqual(len(mail.outbox), 0)

        # this report does have the word foobarius in it, so it should trigger
        # an email to be sent
        report = make(Report, reported_category__name="foobarius")
        request = Mock(build_absolute_uri=Mock(return_value=""))
        UserNotificationQuery.notify(report, request=request)
        thread.call_args[1]['target'](*thread.call_args[1]['args'])
        self.assertEqual(len(mail.outbox), 1)

        # if we call it again, no new email should be sent
        UserNotificationQuery.notify(report, request=request)
        thread.call_args[1]['target'](*thread.call_args[1]['args'])
        self.assertEqual(len(mail.outbox), 1)
