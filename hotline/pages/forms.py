from django import forms
from django.conf import settings
from django.contrib.flatpages.forms import FlatpageForm
from django.contrib.flatpages.models import FlatPage

from . import HIDDEN_PAGE_PREFIX


class FlatterPageForm(FlatpageForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # We don't use the sites framework. This removes the field from
        # the form. In clean(), we hard code the value for the sites
        # field so that it's always set on create and edit.
        self.fields.pop('sites')
        # Don't allow user to edit URL or title of hidden pages.
        if self.instance.url.startswith(HIDDEN_PAGE_PREFIX):
            self.fields.pop('url')
            self.fields.pop('title')

    def clean_url(self):
        url = super().clean_url()
        q = FlatPage.objects.filter(url=url)
        if self.instance.pk is not None:
            q = q.exclude(pk=self.instance.pk)
        if q.exists():
            raise forms.ValidationError(
                'A page with the URL "%s" already exists' % url, code='duplicate_url')
        if url.startswith(HIDDEN_PAGE_PREFIX):
            raise forms.ValidationError(
                'URLs cannot start with %s' % HIDDEN_PAGE_PREFIX, code='forbidden_name')
        return url

    def clean(self):
        self.cleaned_data['sites'] = [settings.SITE_ID]
        return super().clean()
