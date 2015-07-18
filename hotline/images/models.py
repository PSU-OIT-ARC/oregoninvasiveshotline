from django.db import models

from hotline.visibility import Visibility


class Image(Visibility, models.Model):
    image_id = models.AutoField(primary_key=True)
    image = models.ImageField(upload_to="images")
    name = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey("users.User")
    created_on = models.DateTimeField(auto_now_add=True)
    visibility = models.IntegerField(choices=Visibility.choices, default=Visibility.PROTECTED)

    # create a nullable FK to every object that can have images
    report = models.ForeignKey("reports.Report", null=True, default=None)
    comment = models.ForeignKey("comments.Comment", null=True, default=None)
    species = models.ForeignKey("species.Species", null=True, default=None)

    class Meta:
        db_table = "image"
        ordering = ['pk']
