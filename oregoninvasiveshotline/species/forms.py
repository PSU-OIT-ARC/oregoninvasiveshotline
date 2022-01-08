from django import forms

from oregoninvasiveshotline.utils.search import SearchForm


class SpeciesSearchForm(SearchForm):
    order_by = forms.ChoiceField(
        choices=[
            ('name', 'Name'),
            ('scientific_name', 'Scientific Name'),
            ('severity', 'Severity'),
            ('category', 'Category'),
            ('is_confidential', 'Confidential'),
        ],
        required=False
    )
    order = forms.ChoiceField(
        choices=[
            ('ascending', 'Ascending'),
            ('descending', 'Descending'),
        ],
        required=False,
        initial='ascending',
        widget=forms.widgets.RadioSelect
    )

    def get_search_fields(self):
        return ('name', 'scientific_name', 'category__name')

    def search(self, queryset):
        species = super().search(queryset)

        order_by = self.cleaned_data.get('order_by')
        if order_by:
            if self.cleaned_data.get('order') == 'descending':
                order_by = '-{}'.format(order_by)
            species = species.order_by(order_by)

        return species
