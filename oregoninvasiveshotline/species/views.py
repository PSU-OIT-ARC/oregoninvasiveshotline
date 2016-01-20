from django.conf import settings
from django.contrib.messages.views import SuccessMessageMixin
from django.core.urlresolvers import reverse, reverse_lazy
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from arcutils.db import will_be_deleted_with

from oregoninvasiveshotline.perms import permissions
from oregoninvasiveshotline.species.forms import SpeciesSearchForm
from oregoninvasiveshotline.species.models import Category, Severity, Species


@permissions.is_active
def list_(request):
    form = SpeciesSearchForm(request.GET, user=request.user)
    species = form.search()

    paginator = Paginator(species, settings.ITEMS_PER_PAGE)

    active_page = request.GET.get('page')
    try:
        species = paginator.page(active_page)
    except PageNotAnInteger:
        species = paginator.page(1)
    except EmptyPage:
        species = paginator.page(paginator.num_pages)

    return render(request, 'species/list.html', {
        "all_species": species,
        "form": form,
    })


class SpeciesCreateView(SuccessMessageMixin, CreateView):
    model = Species
    fields = ['name', 'scientific_name', 'remedy', 'resources', 'is_confidential', 'category', 'severity']
    success_message = "Species created successfully."
    template_name_suffix = '_detail_form'

    def get_success_url(self):
        return reverse("species-list")


class SpeciesDetailView(SuccessMessageMixin, UpdateView):
    model = Species
    fields = ['name', 'scientific_name', 'remedy', 'resources', 'is_confidential', 'category', 'severity']
    success_message = "Species updated successfully."
    template_name_suffix = '_detail_form'

    def get_success_url(self):
        success_url = self.request.get_full_path()
        return success_url


class SpeciesDeleteView(SuccessMessageMixin, DeleteView):
    model = Species
    success_message = "Species deleted successfully."
    success_url = reverse_lazy('species-list')

    template_name = "delete.html"
    template_name_suffix = ""

    def get_context_data(self, **kwargs):
        obj = super(DeleteView, self).get_object()
        context = super(SpeciesDeleteView, self).get_context_data(**kwargs)
        context['will_be_deleted_with'] = will_be_deleted_with(obj)

        return context


class CategoryList(ListView):
    model = Category


class CategoryCreateView(SuccessMessageMixin, CreateView):
    model = Category
    fields = ['name', 'icon']
    template_name_suffix = '_detail_form'
    success_message = "Category created successfully."

    def get_success_url(self):
        return reverse("categories-list")


class CategoryDeleteView(SuccessMessageMixin, DeleteView):
    model = Category
    success_message = "Category deleted successfully."
    success_url = reverse_lazy('categories-list')

    template_name = "delete.html"
    template_name_suffix = ""

    def get_context_data(self, **kwargs):
        obj = super(DeleteView, self).get_object()
        context = super(CategoryDeleteView, self).get_context_data(**kwargs)
        context['will_be_deleted_with'] = will_be_deleted_with(obj)

        return context


class CategoryDetailView(SuccessMessageMixin, UpdateView):
    model = Category
    fields = ['name', 'icon']
    success_message = "Category updated successfully."
    template_name_suffix = '_detail_form'

    def get_success_url(self):
        return reverse("categories-list")


class SeverityList(ListView):
    model = Severity


class SeverityCreateView(SuccessMessageMixin, CreateView):
    model = Severity
    fields = ['name', 'color']
    success_message = "Severity created successfully."
    template_name_suffix = '_detail_form'

    def get_success_url(self):
        return reverse("severities-list")


class SeverityDeleteView(SuccessMessageMixin, DeleteView):
    model = Severity
    success_url = reverse_lazy('severities-list')
    success_message = "Severity deleted successfully."

    template_name = "delete.html"
    template_name_suffix = ""

    def get_context_data(self, **kwargs):
        obj = super(DeleteView, self).get_object()
        context = super(SeverityDeleteView, self).get_context_data(**kwargs)
        context['will_be_deleted_with'] = will_be_deleted_with(obj)

        return context


class SeverityDetailView(SuccessMessageMixin, UpdateView):
    model = Severity
    fields = ['name', 'color']
    success_message = "Severity updated successfully."
    template_name_suffix = '_detail_form'

    def get_success_url(self):
        return reverse("severities-list")


@permissions.is_staff
def admin_panel(request):
    return render(request, 'species/admin_panel.html')
