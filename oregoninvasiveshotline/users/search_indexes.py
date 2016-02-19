from haystack import indexes

from .models import User


class UserIndex(indexes.SearchIndex, indexes.Indexable):

    text = indexes.CharField(document=True, use_template=True)
    email = indexes.CharField(model_attr='email')
    first_name = indexes.CharField(model_attr='first_name', null=True)
    last_name = indexes.CharField(model_attr='last_name', null=True)

    # Data fields (stored by not indexed)
    full_name = indexes.CharField(model_attr='full_name', indexed=False)
    is_active = indexes.BooleanField(model_attr='is_active', indexed=False)
    is_staff = indexes.BooleanField(model_attr='is_staff', indexed=False)

    def get_model(self):
        return User

    def index_queryset(self, using=None):
        return self.get_model().objects.all()
