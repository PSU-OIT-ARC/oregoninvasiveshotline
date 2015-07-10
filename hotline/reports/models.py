from django.contrib.gis.db import models


class Report(models.Model):
    report_id = models.AutoField(primary_key=True)
    # It may seem odd to have FKs to the species AND category, but in the case
    # where the user doesn't know what species it is, we fall back to just a
    # category (with the reported_species field NULL'd out)
    reported_category = models.ForeignKey("species.Category")
    reported_species = models.ForeignKey("species.Species", null=True, default=None, related_name="+")

    description = models.TextField(verbose_name="Please provide a description of your find")
    location = models.TextField(verbose_name="Please provide a description of the area where species was found")
    has_specimen = models.BooleanField(default=False)

    point = models.PointField(srid=4326)

    created_by = models.ForeignKey("users.User", related_name="reports")
    created_on = models.DateTimeField(auto_now_add=True)

    claimed_by = models.ForeignKey("users.User", null=True, default=None, related_name="claimed_reports")

    # these are copied over from the original site
    edrr_status = models.IntegerField(choices=[
        (0, '',),
        (1, 'No Response/Action Required',),
        (2, 'Local expert notified',),
        (3, 'Population assessed',),
        (4, 'Population treated',),
        (5, 'Ongoing monitoring',),
        (6, 'Controlled at site'),
    ], default=0)

    # the actual species confirmed by an expert
    actual_species = models.ForeignKey("species.Species", null=True, default=None, related_name="reports")

    is_archived = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False, help_text="This report can be viewed by the public")

    objects = models.GeoManager()

    class Meta:
        db_table = "report"

    @property
    def species(self):
        """
        Returns the actual species if it exists, and falls back on the reported_species
        """
        return self.actual_species or self.reported_species

    @property
    def category(self):
        """
        Returns the Category of the actual species, falling back to the reported_category
        """
        return self.actual_species.category if self.actual_species else self.reported_category

    @property
    def is_misidentified(self):
        """
        Returns True if the reported_species differs from the actual species (and both fields are filled out)
        """
        return bool(self.reported_species and self.actual_species and self.reported_species != self.actual_species)


class Invite(models.Model):
    """
    Abitrary people can be invited (via email) to leave comments on a report
    """
    invite_id = models.AutoField(primary_key=True)
    # the person invited (a User object will be created for them)
    user = models.ForeignKey("users.User", related_name="invites")
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey("users.User", related_name="+")
    report = models.ForeignKey(Report)

    class Meta:
        db_table = "invite"

    @classmethod
    def create(cls, *, email, report, inviter, message):
        """
        Create and send an invitation to the person with the given email address
        """
        pass
