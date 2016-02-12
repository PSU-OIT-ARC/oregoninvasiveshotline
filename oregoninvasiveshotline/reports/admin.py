from django.contrib import admin
from django.contrib.gis.admin.options import GeoModelAdmin

from .models import Report


class CustomGeoModelAdmin(GeoModelAdmin):
    """A custom administration options class for Geographic models"""

    # Use a non-default URL so openlayers can be used over HTTPS
    openlayers_url = 'https://cdnjs.cloudflare.com/ajax/libs/openlayers/2.13.1/OpenLayers.js'


admin.site.register(Report, CustomGeoModelAdmin)
