from django.core.urlresolvers import reverse
from django.db import models

from hotline.visibility import Visibility


class Comment(Visibility, models.Model):
    """
    Comments can be left on reports
    """
    comment_id = models.AutoField(primary_key=True)
    body = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    edited_on = models.DateField(auto_now=True)

    visibility = models.IntegerField(choices=Visibility.choices, default=Visibility.PRIVATE, help_text="Controls who can see this comment")

    created_by = models.ForeignKey("users.User")
    report = models.ForeignKey("reports.Report")

    class Meta:
        db_table = "comment"
        ordering = ["created_on", "pk"]

    def get_absolute_url(self):
        return reverse("reports-detail", args=[self.report_id]) + "#comment-" + str(self.pk)
