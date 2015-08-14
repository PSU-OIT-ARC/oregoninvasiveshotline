import base64
import hashlib
import itertools
import os
import subprocess
import tempfile

from django.conf import settings
from django.contrib.gis.db import models
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.template import Context
from django.template.loader import get_template, render_to_string

from hotline.users.models import User


class Report(models.Model):
    # cache the template since Django is so slow at rendering templates and NFS
    # makes it even worse
    TEMPLATE = get_template("reports/_popover.html")

    report_id = models.AutoField(primary_key=True)
    # It may seem odd to have FKs to the species AND category, but in the case
    # where the user doesn't know what species it is, we fall back to just a
    # category (with the reported_species field NULL'd out)
    reported_category = models.ForeignKey("species.Category")
    reported_species = models.ForeignKey("species.Species", null=True, default=None, related_name="+")

    description = models.TextField(verbose_name="Please provide a description of your find")
    location = models.TextField(verbose_name="Please provide a description of the area where species was found")
    has_specimen = models.BooleanField(default=False, verbose_name="Do you have a physical specimen?")

    point = models.PointField(srid=4326)
    county = models.ForeignKey('counties.County', null=True)

    created_by = models.ForeignKey("users.User", related_name="reports")
    created_on = models.DateTimeField(auto_now_add=True)

    claimed_by = models.ForeignKey("users.User", null=True, default=None, related_name="claimed_reports")

    # these are copied over from the original site
    edrr_status = models.IntegerField(verbose_name="EDDR Status", choices=[
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
        ordering = ['-pk']

    def __str__(self):
        if self.species:
            return str(self.species)

        return self.category.name

    def to_json(self):
        image_url = self.image_url()
        return {
            "lat": self.point.y,
            "lng": self.point.x,
            "icon": self.icon_url(),
            "title": str(self),
            "image_url": image_url,
            "content": self.__class__.TEMPLATE.render(Context({
                "report": self,
                "image_url": image_url,
            })),
        }

    def icon_url(self):
        """
        This view generates on the fly a PNG image from a SVG, which can be used as
        an icon on the Google map. The reason for this SVG to PNG business is that
        SVGs are easily customized, but not all browsers support SVG on Google
        maps, so we convert the SVG to a PNG.

        The icon is composed of a background color based on the specie's severity,
        and an image from the specie's category.

        If you are going to change the design or size of the icon, you will need to
        update `hotline/static/js/main.js:generateIcon` as well
        """
        # TODO caching so we don't hit the filesystem all the time
        category = self.category
        # figure out which color to use for the background
        color = "#999" if self.species is None else self.species.severity.color
        icon_size = "30x45"
        # the file path for the generated icon will be based on the parameters that
        # can change the appearance of the map icon
        key = hashlib.md5("|".join(map(str, [category.icon.path if category.icon else "", color])).encode("utf8")).hexdigest()
        icon_location = os.path.join(settings.MEDIA_ROOT, "generated_icons", key + ".png")
        # if the PNG doesn't exist, create it
        if not os.path.exists(icon_location):
            with tempfile.NamedTemporaryFile("wt", suffix=".svg") as f:
                f.write(render_to_string("reports/icon.svg", {
                    # we encode the category PNG inside the SVG, to avoid file path
                    # problems that come from generating the PNG from imagemagick
                    "img": base64.b64encode(open(category.icon.path, "rb").read()) if category.icon else None,
                    "color": color
                }))
                f.flush()
                subprocess.call(["convert", "-background", "none", "-crop", icon_size + "+0+0", f.name, icon_location])

        return settings.MEDIA_URL + "/generated_icons/%s.png" % key

    def image_url(self):
        """
        Returns the URL to the thumbnail generated for the first public image
        attached to this report or None.

        If the thumbnail doesn't exist, it is created
        """
        for image in itertools.chain(self.image_set.all(), *(comment.image_set.all() for comment in self.comment_set.all())):
            if image.visibility == image.PUBLIC:
                output_path = os.path.join(settings.MEDIA_ROOT, "generated_thumbnails", str(image.pk) + ".png")
                thumbnail_size = "64x64"
                if not os.path.exists(output_path):
                    subprocess.call([
                        "convert",
                        image.image.path,
                        "-thumbnail",
                        # the > below means don't enlarge images that fit in the 64x64 box
                        thumbnail_size + ">",
                        "-background",
                        "transparent",
                        "-gravity",
                        "center",
                        # fill the 64x64 box with the background color (which
                        # is transparent) so all the thumbnails are exactly the
                        # same size
                        "-extent",
                        thumbnail_size,
                        output_path
                    ])
                return settings.MEDIA_URL + os.path.relpath(output_path, settings.MEDIA_ROOT)

        return None

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
    def create(cls, *, email, report, inviter, message, request):
        """
        Create and send an invitation to the person with the given email address

        Returns True if the invite was sent, otherwise False (meaning the user
        has already been invited before)
        """
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            user = User(email=email, is_active=False)
            user.save()

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


from .indexes import *  # noqa isort:skip
