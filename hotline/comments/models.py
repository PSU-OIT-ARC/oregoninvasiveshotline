from django.db import models


class Comment(models.Model):
    """
    Comments can be left on reports
    """
    PRIVATE = 0
    PROTECTED = 1
    PUBLIC = 2

    comment_id = models.AutoField(primary_key=True)
    body = models.TextField()
    created_on = models.DateField(auto_now_add=True)
    edited_on = models.DateField(auto_now=True)

    visibility = models.IntegerField(choices=[
        (0, "Private - only managers and invited experts can see"),
        (1, "Protected - only managers, invited experts and the report submitter can see"),  # private + the person reporting it can see
        (2, "Public - everyone can see (when this report is made public)"),  # the public can see (on a public report)
    ], default=0, help_text="Controls who can see this comment")

    created_by = models.ForeignKey("users.User")
    report = models.ForeignKey("reports.Report")

    class Meta:
        db_table = "comment"
