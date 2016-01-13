from django.utils import timezone
from haystack import indexes

from .models import Report


class ReportIndex(indexes.SearchIndex, indexes.Indexable):
    """
    Indexes reports in Elasticsearch using Haystack
    """
    # Haystack requires one field to be used as the primary search term
    text = indexes.CharField(document=True, use_template=True)

    report_id = indexes.IntegerField(model_attr="report_id")

    species = indexes.CharField(model_attr="species__name", null=True)
    species_id = indexes.CharField(model_attr="species__species_id", null=True)
    reported_species = indexes.CharField(model_attr="reported_species__name", null=True)
    actual_species = indexes.CharField(model_attr="actual_species__name", null=True)

    category = indexes.CharField(model_attr="category")
    category_id = indexes.IntegerField(model_attr="category__category_id")

    title = indexes.CharField()
    description = indexes.CharField()
    location = indexes.CharField()
    county = indexes.CharField(model_attr="county__name", null=True)
    county_id = indexes.IntegerField(model_attr="county__pk", null=True)

    edrr_status = indexes.CharField(model_attr="get_edrr_status_display")
    ofpd = indexes.BooleanField(model_attr="created_by__has_completed_ofpd")

    claimed_by = indexes.CharField(model_attr="claimed_by", null=True)
    claimed_by_id = indexes.IntegerField(model_attr="claimed_by__user_id", null=True)

    created_by = indexes.CharField(model_attr="created_by")
    created_by_id = indexes.IntegerField(model_attr="created_by__user_id")
    created_on = indexes.DateField(model_attr="created_on")

    is_archived = indexes.BooleanField(model_attr="is_archived", default=False)
    is_public = indexes.BooleanField(model_attr="is_public", default=False)

    icon_url = indexes.CharField(model_attr="icon_url")
    image_url = indexes.CharField(model_attr="image_url", default=None)
    lat = indexes.FloatField(model_attr="point__y")
    lng = indexes.FloatField(model_attr="point__x")

    def get_model(self):
        """
        Returns the current model
        """
        return Report

    def index_queryset(self, using=None):
        """
        Used when the entire Report index is updated, indexes new document
        """
        return self.get_model().objects.filter(created_on__lte=timezone.now())

    def prepare_email(self, model):
        """
        Prepare the email field
        """
        return None if model.claimed_by is None else model.claimed_by.email.lower()

    def prepare_species(self, model):
        """
        Prepare species field, appends species scientific_name to species_name
        """
        return model.species.name + " " + model.species.scientific_name if model.species else None

    def prepare_title(self, model):
        """
        Prepares the title field, describing the document in terms of the report
        it represents.
        """
        return model.__str__()
