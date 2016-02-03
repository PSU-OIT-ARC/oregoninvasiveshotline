import logging
import os
import posixpath

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.gis.db import models
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string

from oregoninvasiveshotline.images.models import Image
from oregoninvasiveshotline.utils import generate_thumbnail
from oregoninvasiveshotline.visibility import Visibility

from .utils import generate_icon, icon_file_name


log = logging.getLogger(__name__)


class Report(models.Model):

    class Meta:
        db_table = 'report'
        ordering = ['-created_on']

    objects = models.GeoManager()

    report_id = models.AutoField(primary_key=True)
    # It may seem odd to have FKs to the species AND category, but in the case
    # where the user doesn't know what species it is, we fall back to just a
    # category (with the reported_species field NULL'd out)
    reported_category = models.ForeignKey("species.Category")
    reported_species = models.ForeignKey("species.Species", null=True, default=None, related_name="+")

    description = models.TextField(verbose_name="Please provide a description of your find")
    location = models.TextField(
        verbose_name="Please provide a description of the area where species was found",
        help_text="""
            For example name the road, trail or specific landmarks
            near the site whether the species was found. Describe the geographic
            location, such as in a ditch, on a hillside or in a streambed. If you
            happen to have taken GPS coordinates, enter them here.
        """
    )
    has_specimen = models.BooleanField(default=False, verbose_name="Do you have a physical specimen?")

    point = models.PointField(srid=4326)
    county = models.ForeignKey('counties.County', null=True)

    created_by = models.ForeignKey("users.User", related_name="reports")
    created_on = models.DateTimeField(auto_now_add=True)

    claimed_by = models.ForeignKey("users.User", null=True, default=None, related_name="claimed_reports")

    # these are copied over from the original site
    edrr_status = models.IntegerField(verbose_name="EDRR Status", choices=[
        (None, '',),
        (0, 'No Response/Action Required',),
        (1, 'Local expert notified',),
        (2, 'Population assessed',),
        (3, 'Population treated',),
        (4, 'Ongoing monitoring',),
        (5, 'Controlled at site'),
    ], default=None, null=True, blank=True)

    # the actual species confirmed by an expert
    actual_species = models.ForeignKey("species.Species", null=True, default=None, related_name="reports")

    is_archived = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False, help_text="This report can be viewed by the public")

    @property
    def title(self):
        return self.species.title if self.species else self.category.name

    @property
    def icon_color(self):
        species = self.species
        return settings.ICON_DEFAULT_COLOR if species is None else species.severity.color

    @property
    def icon_file_name(self):
        """Get base file name for this report's icon.

        This is used by :meth:`icon_path` and :meth:`icon_url` to
        generate icon file system paths and URLs; generally, you'd use
        one of those instead of using this directly.

        """
        return icon_file_name(self.category.icon, self.icon_color)

    @property
    def icon_path(self):
        """Path to (generated) icon for this report."""
        return os.path.join(settings.MEDIA_ROOT, settings.ICON_DIR, self.icon_file_name)

    @property
    def icon_url(self):
        """Get icon URL for this report."""
        return posixpath.join(settings.MEDIA_URL, settings.ICON_DIR, self.icon_file_name)

    def generate_icon(self, force=False):
        """Generate a map-style icon for this Report.

        Normally, a report icon will be generated only if it doesn't
        already exist on disk, but generation can be ``force``d.

        When a report is saved, its icon will be re-generated if
        necessary.

        """
        icon_path = self.icon_path
        if force or not os.path.exists(icon_path):
            inner_icon_path = self.category.icon and self.category.icon.path
            icon = generate_icon(icon_path, inner_icon_path, self.icon_color)
            return icon

    @property
    def image_url(self):
        """Get URL for "first" public image attached to this report.

        If the report has at least one public image, the thumbnail URL
        for the newest image will be returned. Otherwise, the report's
        comments are checked for public images.

        If the thumbnail for the selected image doesn't exist, it will
        be created as a side effect.

        If no image is found, ``None`` will be returned.

        """
        # Try to get a directly-attached image first
        q = Image.objects.filter(report=self)
        q = q.filter(visibility=Visibility.PUBLIC).order_by('-created_on')
        image = q.first()

        if image is None:
            # Fall back to images attached to this report's comments
            q = Image.objects.filter(comment__in=self.comment_set.values_list('pk', flat=True))
            q = q.filter(visibility=Visibility.PUBLIC).order_by('-created_on')
            image = q.first()

        if image is None:
            return None

        sub_dir = 'generated_thumbnails'
        output_dir = os.path.join(settings.MEDIA_ROOT, sub_dir)
        media_url = posixpath.join(settings.MEDIA_URL, sub_dir)

        file_name = '{image.pk}.png'.format(image=image)
        output_path = os.path.join(output_dir, file_name)
        if not os.path.exists(output_path):
            generate_thumbnail(image.image.path, output_path, width=64, height=64)
        return posixpath.join(media_url, file_name)

    @property
    def species(self):
        """Return actual species if set; fall back to reported species."""
        return self.actual_species or self.reported_species

    @property
    def category(self):
        """Return actual category if set; fall back to reported category."""
        return self.actual_species.category if self.actual_species else self.reported_category

    @property
    def is_misidentified(self):
        """Is reported species different from actual species?"""
        if self.reported_species and self.actual_species:
            return self.reported_species != self.actual_species
        return False

    def get_absolute_url(self):
        return reverse('reports-detail', args=(self.pk,))

    def __str__(self):
        return 'Report: {0.title}'.format(self)


@receiver([post_save], sender=Report)
def receiver__generate_icon(sender, instance, **kwargs):
    """Create or update icon for Report on save."""
    instance.generate_icon()


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
    def create(cls, *, email, report, inviter, message, request):
        """
        Create and send an invitation to the person with the given email address

        Returns True if the invite was sent, otherwise False (meaning the user
        has already been invited before)
        """
        user_model = get_user_model()
        try:
            user = user_model.objects.get(email__iexact=email)
        except user_model.DoesNotExist:
            user = user_model.objects.create(email=email, is_active=False)

        if Invite.objects.filter(user=user, report=report).exists():
            return False

        invite = Invite(user=user, created_by=inviter, report=report)

        send_mail(
            "Invasive Species Hotline Submission Review Request",
            render_to_string("reports/_invite_expert.txt", {
                "inviter": inviter,
                "message": message,
                "url": user.get_authentication_url(request, next=reverse("reports-detail", args=[report.pk]))
            }),
            "noreply@pdx.edu",
            [email]
        )

        invite.save()
        return True
