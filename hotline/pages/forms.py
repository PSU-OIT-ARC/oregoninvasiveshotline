from django import forms
from django.contrib.flatpages.forms import FlatpageForm
from django.contrib.flatpages.models import FlatPage
from django.contrib.flatpages.views import flatpage
from django.contrib.sites.models import Site
from django.core.urlresolvers import resolve
from django.http import Http404

from . import HIDDEN_PAGE_PREFIX


class FlatterPageForm(FlatpageForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # no one uses the sites framework these days, so remove the field, and
        # we'll set the self.instance.sites variable in the save method
        self.fields.pop("sites")
        # when we're editing the "hidden pages", we don't want to let the user
        # edit the URL or title
        if self.instance.url.startswith(HIDDEN_PAGE_PREFIX):
            self.fields.pop("url")
            self.fields.pop("title")

    def clean_url(self):
        """
        Ensures that the route doesn't collide with another URL on the site,
        and it doesn't start with the HIDDEN_PAGE_PREFIX
        """
        url = super().clean_url()
        # if a 404 is raised when we try to resolve the URL, or it resolves
        # back to the flatpage we're editing, the URL is ok
        try:
            if resolve(url).func == flatpage and FlatPage.objects.filter(url=url).first() == self.instance:
                raise Http404()
        except Http404:
            pass  # the URL doesn't cause a collision, so we're good to go
        else:
            raise forms.ValidationError("A page with that URL route already exists", code="duplicate_url")

        if url.startswith(HIDDEN_PAGE_PREFIX):
            raise forms.ValidationError("URLs cannot start with _", code="forbidden_name")

        return url

    def save(self, *args, **kwargs):
        to_return = super().save(*args, **kwargs)
        self.instance.sites = Site.objects.all()
        self.instance.save()
        return to_return
