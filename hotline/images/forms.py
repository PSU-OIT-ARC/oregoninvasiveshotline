from arcutils.forms import BaseModelFormSet
from django import forms
from django.forms.models import modelformset_factory
from django.utils.functional import curry

from hotline.reports.perms import can_adjust_visibility

from .fields import ClearableImageInput
from .models import Image


class ImageForm(forms.ModelForm):
    class Meta:
        model = Image
        fields = [
            'image',
            'name',
            'visibility',
        ]

        widgets = {
            'image': ClearableImageInput,
            'name': forms.TextInput(attrs={"placeholder": "Caption"})
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].label = ""
        self.fields['name'].label = ""
        self.fields['visibility'].label = ""

        if user is None or not can_adjust_visibility(user, self.instance.report):
            self.fields.pop('visibility')
            self.instance.visibility = Image.PROTECTED


class BaseImageFormSet(BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def save_new(self, form, commit=True):
        """Saves and returns an existing model instance for the given form."""
        form.instance.created_by = self.user
        setattr(form.instance, self.fk.__class__.__name__.lower(), self.fk)
        super().save_new(form, commit)

    def save(self, user, fk, commit=True):
        self.user = user
        self.fk = fk
        super().save(commit)


def get_image_formset(*args, **kwargs):
    """
    This is annoying, but because ImageForm takes arguments in the __init__
    method, we have to alter the formset's form on the fly

    http://stackoverflow.com/a/813647/2733517
    """
    ImageFormSet = modelformset_factory(Image, form=ImageForm, formset=BaseImageFormSet, can_delete=True)
    ImageFormSet.form = staticmethod(curry(ImageForm, *args, **kwargs))
    return ImageFormSet
