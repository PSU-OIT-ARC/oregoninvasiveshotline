from elasticmodels import DateField, Index, IntegerField, StringField
from elasticsearch_dsl import MetaField, analyzer, token_filter, tokenizer

from .models import Report

# override the default analyzer for ES to use an ngram filter that breaks words using
# the standard tokenizer. Allow words to be broken up with underscores
name = analyzer(
    "name",
    # the standard analyzer splits the words nicely by default
    tokenizer=tokenizer("standard"),
    filter=[
        # technically, the standard filter doesn't do anything but we include
        # it anyway just in case ES decides to make use of it
        "standard",
        # obviously, lowercasing the tokens is a good thing
        "lowercase",
        # this enumates a 3-4 ngram, but also includes the whole token itself
        # (which prevents us from having to create multifields)
        token_filter(
            "simple_edge",
            type="pattern_capture",
            patterns=["(?=(...))(?=(....))"]
        )
    ]
)


class ReportIndex(Index):
    category = StringField(
        attr="category.name",
        # need a non_analyzed field for sorting
        fields={
            'raw': StringField(index="not_analyzed"),
        },
    )
    category_id = IntegerField(attr="category.pk")

    species = StringField(
        attr="species.name",
        # need a non_analyzed field for sorting
        fields={
            'raw': StringField(index="not_analyzed"),
        }
    )
    species_id = IntegerField(attr="species.pk")

    description = StringField(analyzer=name)
    location = StringField(analyzer=name)
    county = StringField(analyzer="standard", attr="county.name")

    claimed_by = StringField(index="not_analyzed", attr="claimed_by.email")
    claimed_by_id = IntegerField(attr="claimed_by.pk")

    created_on = DateField()

    def get_queryset(self, *args, **kwargs):
        return super().get_queryset().select_related(
            "reported_species",
            "reported_category",
            "actual_species",
            "claimed_by",
            "county",
        ).defer("county__the_geom")

    def prepare_email(self, model):
        return None if model.claimed_by is None else model.claimed_by.email.lower()

    def prepare_species(self, model):
        return model.species.name + " " + model.species.scientific_name if model.species else None

    class Meta:
        doc_type = "report"
        model = Report
        fields = [
            'is_public',
            'is_archived',
        ]
        all = MetaField(analyzer='name')
