import threading

from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db import models
from django.http import QueryDict
from django.template.loader import render_to_string


class UserNotificationQuery(models.Model):
    user_notification_query_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, verbose_name="""
        To make it easier to review your subscriptions, give the search you
        just performed a name. For example "Aquatic plants in Multnomah county"
    """)
    user = models.ForeignKey("users.User")
    query = models.TextField(help_text="""
        This is a a string for a QueryDict of the GET parameters to pass to the
        ReportSearchForm that match reports the user should be notified about
    """)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_notification_query"

    @classmethod
    def notify(cls, report, request):
        """
        When a new report is submitted, we need to notify everyone who has
        subscribed to a query on the ReportSearchForm that matches the report.

        This function spawns a thread to send the emails, since this is a
        fairly slow process
        """
        def runnable(cls, report, request):
            from hotline.reports.forms import ReportSearchForm  # get around a circular import
            users = set()
            for query in cls.objects.all().select_related("user").exclude(
                    user__pk__in=Notification.objects.filter(report=report).values_list("user_id", flat=True)
            ):
                if query.user.pk not in users:
                    form = ReportSearchForm(QueryDict(query.query), user=query.user)
                    if form.is_valid() and form.search().filter("term", _id=report.pk).count() >= 1:
                        send_mail("New Online Hotline submission for review", render_to_string("notifications/email.txt", {
                            "user": query.user,
                            "name": query.name,
                            "url": query.user.get_authentication_url(request=request, next=reverse("reports-detail", args=[report.pk])),
                            "report": report,
                        }), "noreply@pdx.edu", [query.user.email])
                        Notification(user=query.user, report=report).save()
                        users.add(query.user.pk)

        threading.Thread(target=runnable, args=(cls, report, request)).start()


class Notification(models.Model):
    """
    This just tells you which users have been notified about which reports, so
    they don't get emailed twice about the same report
    """
    notification_id = models.AutoField(primary_key=True)
    user = models.ForeignKey("users.User")
    report = models.ForeignKey("reports.Report")
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notification"
