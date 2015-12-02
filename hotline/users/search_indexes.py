from haystack import indexes

from .models import User


class UserIndex(indexes.SearchIndex, indexes.Indexable):
    """ uses 'first_name' as the primary search term """

    # The following fields should use the "name" analyzer once it
    # has been implemented in /hotline/reports/search_indexes.py:
    text = indexes.CharField(document=True, use_template=True, model_attr="first_name")
    last_name = indexes.CharField(model_attr="last_name")
    email = indexes.CharField(model_attr="email")

    def get_model(self):
        return User
