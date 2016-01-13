from django import forms
from haystack.forms import SearchForm

from .models import Species


class SpeciesSearchForm(SearchForm):
    """
    This form handles searching for a species in the species list view.
    """
    q = forms.CharField(required=False, widget=forms.widgets.TextInput(attrs={
        "placeholder": "Enter a keyword, then click \"Search\""
    }), label="Search")

    sort_by = forms.ChoiceField(choices=[
        ("name", "Name"),
        ("scientific_name", "Scientific Name"),
        ("severity", "Severity"),
        ("category", "Category"),
        ("is_confidential", "Confidential"),
    ], required=False)

    order = forms.ChoiceField(choices=[
        ("ascending", "Ascending"),
        ("descending", "Descending"),
    ], required=False, initial="ascending", widget=forms.widgets.RadioSelect)

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def no_query_found(self):
        """Return all species when no query is found."""
        return self.searchqueryset.all().models(Species)

    def search(self):
        results = super().search().models(Species)

        if not self.is_valid():
            return self.no_query_found()

        sort_by = self.cleaned_data.get("sort_by")
        order = self.cleaned_data.get("order")
        if sort_by:
            if order == "descending":
                sort_by = "-" + sort_by
            results = results.order_by(sort_by)

        return results
