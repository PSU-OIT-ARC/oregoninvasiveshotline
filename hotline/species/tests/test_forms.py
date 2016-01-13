from django.test import TestCase
from model_mommy.mommy import make

from hotline.users.models import User

from ..forms import SpeciesSearchForm
from ..models import Species
from ..search_indexes import SpeciesIndex


class SpeciesSearchFormTest(TestCase):
    """
    Some unit tests to ensure forms in the species app work as they should.

    """
    def setUp(self):
        super(SpeciesSearchFormTest, self).setUp()
        make(Species, name="stuff")
        self.user = User(first_name="foo", last_name="bar", email="foobar@example.com", is_staff=True)
        self.user.set_password("foobar")
        self.user.save()
        self.client.login(username="foobar@example.com", password="foobar")
        self.index = SpeciesIndex()
        self.index.clear()

    def tearDown(self):
        self.index.clear()

    def test_get_initial_queryset(self):
        form = SpeciesSearchForm(user=self.user, data={'q': ''})
        results = form.search()
        self.assertEqual(len(results), SpeciesIndex.objects.all().models(Species).count())

    def test_valid_form(self):
        form = SpeciesSearchForm({'q': 'other'}, user=self.user)
        self.assertTrue(form.is_valid())

    def test_form_with_empty_querystring_returns_everything(self):
        form = SpeciesSearchForm({'q': ''}, user=self.user)
        self.assertTrue(form.is_valid())
        results = form.search()
        self.assertEqual(len(results), SpeciesIndex.objects.all().models(Species).count())

    def test_search_returns_correct_object(self):
        # test object
        name = "other"
        make(Species, name=name)
        # set it all up
        form = SpeciesSearchForm({'q': 'other'}, user=self.user)
        # make sure the form is valid
        self.assertTrue(form.is_valid())
        results = form.search()[0]
        # Check to see that the id of the test object "other"
        # is in the list of ids returned by the search function
        self.assertEqual(results.name, name)

    def test_sort_by_field_sorts_species(self):
        albatross = make(Species, name="albatross", scientific_name="diomedeidae")
        buffalo = make(Species, name="buffalo", scientific_name="bison")
        cat = make(Species, name="cat", scientific_name="felis catus")

        form = SpeciesSearchForm({
            'q': '',
            'sort_by': 'name',
            'order': 'descending',
        }, user=self.user)
        results = form.search()

        species = list()
        for s in results:
            species.append(s.object)

        self.assertTrue(species, Species.objects.all().order_by('-name'))
