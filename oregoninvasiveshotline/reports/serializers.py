from django.template.loader import render_to_string

from haystack.models import SearchResult
import pytz

from rest_framework import serializers

from .models import Report


class ReportSerializer(serializers.Serializer):

    pk = serializers.IntegerField()
    category = serializers.CharField()
    content = serializers.SerializerMethodField()
    county = serializers.CharField()

    # encountered error with translation of datetime object in production
    # the given value was an unaware datetime with values which do not
    # exist in the local timezone. (2am is skipped when we go DST).
    #
    # so, ensure that this field understands the incoming data are in UTC.
    created_on = serializers.DateTimeField(format='%b %d, %Y',
                                           default_timezone=pytz.utc)

    edrr_status = serializers.SerializerMethodField()
    icon_url = serializers.CharField(required=False)
    image_url = serializers.CharField(required=False)
    lat = serializers.SerializerMethodField()
    lng = serializers.SerializerMethodField()
    species = serializers.CharField()
    title = serializers.CharField()

    def get_content(self, instance):
        return render_to_string('reports/_popover.html', {
            'report': instance,
            'image_url': instance.image_url,
        })

    def get_edrr_status(self, instance):
        return instance.get_edrr_status_display()

    def get_lat(self, instance):
        if isinstance(instance, Report):
            point = instance.point
            return point.y if point else None
        elif isinstance(instance, SearchResult):
            return instance.lat
        else:
            raise TypeError(instance.__class__)

    def get_lng(self, instance):
        if isinstance(instance, Report):
            point = instance.point
            return point.x if point else None
        elif isinstance(instance, SearchResult):
            return instance.lng
        else:
            raise TypeError(instance.__class__)
