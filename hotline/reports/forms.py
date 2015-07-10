from django import forms

from hotline.comments.models import Comment
from hotline.images.fields import MultiFileField
from hotline.images.models import Image
from hotline.users.models import User

from .models import Report


class ReportForm(forms.ModelForm):
    """
    Form for the public to submit reports
    """
    questions = forms.CharField(label="Do you have additional questions for the invasive species expert who will review this report?", widget=forms.Textarea)
    first_name = forms.CharField()
    last_name = forms.CharField()
    prefix = forms.CharField(required=False)
    suffix = forms.CharField(required=False)
    email = forms.EmailField()
    images = MultiFileField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['reported_species'].empty_label = "Unknown"
        self.fields['reported_species'].required = False

    def save(self, *args, **kwargs):
        # first thing we need to do is create or find the right User object
        try:
            user = User.objects.get(email__iexact=self.cleaned_data['email'])
        except User.DoesNotExist:
            user = User(
                email=self.cleaned_data['email'],
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                prefix=self.cleaned_data.get('prefix', ""),
                suffix=self.cleaned_data.get('suffix', ""),
                is_active=False
            )
            user.save()

        self.instance.created_by = user
        super().save(*args, **kwargs)

        # now save every image that was attached to this report
        for image in self.cleaned_data.get('images', []):
            i = Image(image=image, created_by=user, report=self.instance)
            i.save()

        # if the submitter left a question, add it as a comment
        if self.cleaned_data.get("questions"):
            c = Comment(report=self.instance, created_by=user, body=self.cleaned_data['questions'], visibility=Comment.PROTECTED)
            c.save()

        return self.instance

    class Meta:
        model = Report
        fields = [
            'reported_category',
            'reported_species',
            'description',
            'location',
            'point',
            'has_specimen',
        ]
