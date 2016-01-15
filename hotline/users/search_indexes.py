from haystack import indexes

from .models import User


class UserIndex(indexes.SearchIndex, indexes.Indexable):
    """
    Indexes a user model defined by the fields below in Elasticsearch,
    using Haystack
    """
    text = indexes.CharField(document=True, use_template=True)
    first_name = indexes.CharField(model_attr="first_name")
    last_name = indexes.CharField(model_attr="last_name")
    email = indexes.CharField(model_attr="email")
    is_active = indexes.BooleanField(model_attr="is_active")
    is_staff = indexes.BooleanField(model_attr="is_staff")

    def get_model(self):
        """
        Returns the current model
        """
        return User

    def index_queryset(self, using=None):
        """
        Used when the entire User index is updated, indexes new documents
        """
        return self.get_model().objects.all()
