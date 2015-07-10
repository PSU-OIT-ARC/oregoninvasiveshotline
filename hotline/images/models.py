from django.db import models


class Image(models.Model):
    image_id = models.AutoField(primary_key=True)
    image = models.ImageField(upload_to="images")
    name = models.CharField(max_length=255)
    created_by = models.ForeignKey("users.User")
    created_on = models.DateTimeField(auto_now_add=True)
    visibility = models.IntegerField(choices=[
        (0, "Private"),  # only managers/admins/invited experts can see
        (1, "Protected"),  # private + the person reporting it can see
        (2, "Public"),  # the public can see (on a public report)
    ], default=1)

    # create a nullable FK to every object that can have images
    report = models.ForeignKey("reports.Report", null=True, default=None)
    comment = models.ForeignKey("comments.Comment", null=True, default=None)
    species = models.ForeignKey("species.Species", null=True, default=None)

    class Meta:
        db_table = "image"
