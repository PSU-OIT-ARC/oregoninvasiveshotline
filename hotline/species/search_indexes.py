from haystack import indexes

from .models import Species


class SpeciesIndex(indexes.SearchIndex, indexes.Indexable):
    """ uses `name` as the primary search term """

    text = indexes.CharField(document=True, use_template=True, model_attr="name")
    scientific_name = indexes.CharField(model_attr="scientific_name")
    remedy = indexes.CharField(model_attr="remedy")
    resources = indexes.CharField(model_attr="resources")

    is_confidential = indexes.BooleanField(model_attr="is_confidential")

    severity = indexes.CharField(model_attr="severity")
    category = indexes.CharField(model_attr="category")

    def get_model(self):
        return Species
