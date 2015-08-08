from django.contrib.gis.db import models


class County(models.Model):
    county_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    the_geom = models.MultiPolygonField(srid=4326)

    objects = models.GeoManager()

    class Meta:
        db_table = "county"

    def __str__(self):
        return self.name
