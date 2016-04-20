import threading

from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db import models
from django.http import QueryDict
from django.template.loader import render_to_string

from arcutils.settings import get_setting


class UserNotificationQuery(models.Model):

    class Meta:
        db_table = 'user_notification_query'

    user_notification_query_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('users.User')
    name = models.CharField(
        max_length=255,
        verbose_name=(
            'To make it easier to review your subscriptions, give the search you just performed '
            'a name. For example: "Aquatic plants in Multnomah county".'
        )
    )
    query = models.TextField(
        help_text=(
            'This is a string for a QueryDict of the GET parameters to pass to the '
            'ReportSearchForm that match reports the user should be notified about.'
        )
    )
    created_on = models.DateTimeField(auto_now_add=True)

    @classmethod
    def notify_new_owner(cls, subscription, request):
        """Notify the new owner of a subscription when ownership has changed"""

        subject = get_setting('NOTIFICATIONS.notify_new_owner__subject')
        from_email = get_setting('NOTIFICATIONS.from_email')
        new_owner = subscription.user
        next_url = reverse('reports-list') + '?' + subscription.query

        if new_owner.is_active:
            url = request.build_absolute_uri(next_url)
        else:
            url = new_owner.get_authentication_url(request, next=next_url)

        body = render_to_string('notifications/notify_new_owner.txt', {
            'assigner': request.user,
            'name': subscription.name,
            'url': url,
        })
        send_mail(subject, body, from_email, [new_owner.email])

    @classmethod
    def notify(cls, report, request):
        """Notify users subscribed to a query that matches ``report``.

        This function spawns a thread to send the emails, since this is
        a fairly slow process.

        """
        from oregoninvasiveshotline.reports.forms import ReportSearchForm  # Avoid circular import

        subject = get_setting('NOTIFICATIONS.subject')
        from_email = get_setting('NOTIFICATIONS.from_email')
        excluded_users = Notification.objects.filter(report=report).values_list('user_id', flat=True)
        q = cls.objects.all().select_related('user')
        q = q.exclude(user__pk__in=excluded_users)
        user_notification_queries = q.all()
        notified_users = set()

        def runnable():
            for user_notification_query in user_notification_queries:
                user = user_notification_query.user
                if user.pk not in notified_users:
                    query = user_notification_query.query
                    form = ReportSearchForm(QueryDict(query), user=user)
                    if form.is_valid() and form.search().filter(id=report.pk).count():
                        next_url = reverse('reports-detail', args=[report.pk])
                        if user.is_active:
                            url = request.build_absolute_uri(next_url)
                        else:
                            url = user.get_authentication_url(request=request, next=next_url)
                        body = render_to_string('notifications/email.txt', {
                            'user': user,
                            'name': user_notification_query.name,
                            'url': url,
                            'report': report,
                        })
                        send_mail(subject, body, from_email, [user.email])
                        Notification(user=user, report=report).save()
                        notified_users.add(user.pk)

        threading.Thread(target=runnable).start()

    def __str__(self):
        return self.name


class Notification(models.Model):

    """Keeps track of notifications to users.

    This keeps track of which users have been notified about which
    reports, so they don't get emailed twice about the same report.

    """

    class Meta:
        db_table = 'notification'

    notification_id = models.AutoField(primary_key=True)
    user = models.ForeignKey('users.User')
    report = models.ForeignKey('reports.Report')
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return 'Notification for: report "{0.report.title}"'.format(self)
