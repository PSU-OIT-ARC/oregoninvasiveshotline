import datetime

from django.utils import timezone
from django.core.urlresolvers import reverse
from django.db import models

from oregoninvasiveshotline.visibility import Visibility


class Comment(Visibility, models.Model):
    """
    Comments can be left on reports
    """
    comment_id = models.AutoField(primary_key=True)
    body = models.TextField()
    created_on = models.DateTimeField(default=timezone.now)
    edited_on = models.DateField(default=datetime.date.today)

    visibility = models.IntegerField(choices=Visibility.choices, default=Visibility.PROTECTED, help_text="Controls who can see this comment")

    created_by = models.ForeignKey("users.User")
    report = models.ForeignKey("reports.Report")

    class Meta:
        db_table = "comment"
        ordering = ["created_on", "pk"]

    def get_absolute_url(self):
        return reverse("reports-detail", args=[self.report_id]) + "#comment-" + str(self.pk)

    def __str__(self):
        return 'Comment on: report "{0.report}"'.format(self)
