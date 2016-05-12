from unittest.mock import Mock, patch

from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase

from model_mommy.mommy import make

from arcutils.test.user import UserMixin

from oregoninvasiveshotline.reports.models import Report
from oregoninvasiveshotline.species.models import Category

from .models import UserNotificationQuery


class CreateViewTest(TestCase, UserMixin):

    def setUp(self):
        self.user = self.create_user(
            username='foo@example.com',
            password='foo',
            is_active=True,
            is_staff=False
        )

    def test_only_active_users_can_view_page(self):
        self.client.login(email=self.user.email, password='foo')
        self.user.is_active = False
        self.user.save()
        response = self.client.get(reverse('notifications-create'))
        self.assertEqual(response.status_code, 403)

    def test_get(self):
        self.client.login(email=self.user.email, password='foo')
        response = self.client.get(reverse('notifications-create'))
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        self.client.login(email=self.user.email, password='foo')
        pre_count = UserNotificationQuery.objects.count()
        response = self.client.post(reverse('notifications-create') + '?q=foo', {
            'name': 'bar'
        })
        self.assertRedirects(response, reverse('reports-list') + '?q=foo')
        self.assertEqual(UserNotificationQuery.objects.count(), pre_count+1)


class ListViewTest(TestCase, UserMixin):

    def test_get(self):
        user = self.create_user(username='foo@example.com', password='foo', is_active=True)
        make(UserNotificationQuery, user=user, query='?q=foo')
        self.client.login(email=user.email, password='foo')
        response = self.client.get(reverse('notifications-list'))
        self.assertEqual(response.status_code, 200)


class UserNotificationQueryTest(TestCase, UserMixin):

    @patch('oregoninvasiveshotline.notifications.models.threading.Thread')
    def test_notify_sends_emails_to_subscribers(self, thread):
        user = self.create_user(username='foo@example.com')

        # Subscribe to the same thing twice to ensure that only one
        # email is sent to the user when a report matches.
        make(UserNotificationQuery, query='q=foobarius', user=user)
        make(UserNotificationQuery, query='q=foobarius', user=user)

        # This report does *not* have the words "foobarius" in it, so no
        # email should be sent.
        report = make(Report)
        UserNotificationQuery.notify(report, request=Mock())
        thread.call_args[1]['target']()
        self.assertEqual(len(mail.outbox), 0)

        # This report *does* have the word "foobarius" in it, so it
        # should trigger an email to be sent.
        report = make(Report, reported_category__name='foobarius')
        request = Mock(build_absolute_uri=Mock(return_value=''))
        UserNotificationQuery.notify(report, request=request)
        thread.call_args[1]['target']()
        self.assertEqual(len(mail.outbox), 1)

        # If we notify about the same report, no new email should be
        # sent.
        UserNotificationQuery.notify(report, request=request)
        thread.call_args[1]['target']()
        self.assertEqual(len(mail.outbox), 1)


class UserNotificationQueryPrettyQuery(TestCase, UserMixin):

    def test_pretty_query(self):
        user = self.create_user(username='foo@example.com')
        Category.objects.create(name='Ocean Animal')
        Category.objects.create(name='Pencil')
        subscription = UserNotificationQuery.objects.create(
            query='q=foobarius&categories=1&categories=2', user=user,
        )
        expected_output = {
            'Categories': 'Ocean Animal, Pencil',
            'Keyword': 'foobarius'
        }
        self.assertEqual(subscription.pretty_query, expected_output)
