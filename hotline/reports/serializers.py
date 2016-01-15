from django.template import Context
from django.template.loader import get_template
from rest_framework import serializers
from .models import Report


class ReportSerializer(serializers.Serializer):
    """
    Serializes reports to JSON objects

    Currently this module is used to serialize essential report data to JSON
    so it can be passed to the template and used in our Google Maps JS logic.
    """

    pk = serializers.IntegerField()
    content = serializers.SerializerMethodField()
    county = serializers.CharField()
    created_on = serializers.DateField(format="%b %d, %Y")
    edrr_status = serializers.CharField()
    icon = serializers.CharField(source="icon_url")
    icon_url = serializers.CharField(required=False)
    image_url = serializers.CharField(required=False)
    lat = serializers.SerializerMethodField()
    lng = serializers.SerializerMethodField()
    title = serializers.CharField()
    species = serializers.CharField()
    category = serializers.CharField()

    def get_content(self, instance):
        """
        Returns an HTML element containing the image URL of the report,
        and the report object itself.
        """
        return get_template("reports/_popover.html").render(Context({
            "report": instance,
            "image_url": instance.image_url,
        }))

    def get_lat(self, instance):
        """
        Return the latitude of the ReportIndex, or the Y position
        of the Report model's point field.
        """
        try:
            lat = instance.lat
        except AttributeError:
            lat = instance.point.y
        return lat

    def get_lng(self, instance):
        """
        Returns the longitude of the ReportIndex, or the X position
        of the Report model's point field.
        """
        try:
            lng = instance.lng
        except AttributeError:
            lng = instance.point.x
        return lng
