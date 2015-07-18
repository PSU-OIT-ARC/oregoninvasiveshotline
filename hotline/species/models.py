import json
from collections import defaultdict

from django.db import models


def category_id_to_species_id_json():
    species = Species.objects.all().select_related("category").values_list("category__pk", "pk").order_by("category__pk")
    category_id_to_species_id = defaultdict(list)
    for category_id, species_id in species:
        category_id_to_species_id[category_id].append(species_id)

    return json.dumps(category_id_to_species_id)


class Category(models.Model):
    """Simply a container for species"""
    category_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)

    class Meta:
        db_table = "category"
        ordering = ['name']

    def __str__(self):
        return self.name


class Severity(models.Model):
    """
    This could be an enum, but in the original DB it was a table with 3 rows
    for "native" "non-native" "invasive"
    """
    severity_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)

    class Meta:
        db_table = "severity"
        ordering = ['name']

    def __str__(self):
        return self.name


class Species(models.Model):
    """
    A species that can be reported on
    """
    species_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    scientific_name = models.CharField(max_length=255)
    remedy = models.TextField()
    resources = models.TextField()

    is_confidential = models.BooleanField(default=False, help_text="""
        A species can be marked as confidential if making a report about it public would cause harm
    """)

    severity = models.ForeignKey(Severity)
    category = models.ForeignKey(Category)

    class Meta:
        db_table = "species"
        ordering = ['name']

    def __str__(self):
        return "%s%s" % (self.name, " (%s)" % self.scientific_name if self.scientific_name else "")
