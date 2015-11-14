from haystack import indexes

from .models import Report


class ReportIndex(indexes.SearchIndex, indexes.Indexable):
    """
    This class has been refactored to use haystack on a basic level (was
    elasticmodels) but will need some more custom functionality. An analyzer
    should override the default analyzer for ES to use an nGram filter that
    breaks words using the standard tokenizer.

    There is nothing fancy going on other than indexing Report models with
    haystack.

    Uses 'species.name' as the primary search term
    """

    category = indexes.CharField(model_attr="category.name")
    category_id = indexes.IntegerField(model_attr="category.pk")

    text = indexes.CharField(document=True, use_template=True, model_attr="species.name")
    species_id = indexes.CharField(model_attr="species.pk")

    description = indexes.CharField()  # needs analyzer (analyzer=name)
    location = indexes.CharField()     # needs analyzer (analyzer=name)

    county = indexes.CharField(model_attr="county.name")
    edrr_status = indexes.CharField(model_attr="get_edrr_status_display")
    ofpd = indexes.BooleanField(model_attr="created_by.has_completed_ofpd")

    claimed_by = indexes.CharField(model_attr="claimed_by.email")
    claimed_by_id = indexes.IntegerField(model_attr="claimed_by.pk")

    created_by_id = indexes.IntegerField(model_attr="created_by_id")
    created_on = indexes.DateField()

    def get_model(self):
        return Report
