from collections import namedtuple

from django import forms
from django.core.validators import validate_email

from hotline.comments.models import Comment
from hotline.species.models import Category, Severity, Species
from hotline.users.models import User

from .models import Invite, Report


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


class PublicForm(forms.ModelForm):
    SUBMIT_FLAG = "PUBLIC"

    class Meta:
        model = Report
        fields = [
            'is_public'
        ]


class ArchiveForm(forms.ModelForm):
    SUBMIT_FLAG = "ARCHIVE"

    class Meta:
        model = Report
        fields = [
            'is_archived'
        ]


class InviteForm(forms.Form):
    """
    Form to invite people to comment on a report
    """
    SUBMIT_FLAG = "INVITE"

    emails = forms.CharField()
    body = forms.CharField(widget=forms.Textarea, required=False)

    def clean_emails(self):
        emails = set([email.strip() for email in self.cleaned_data['emails'].split(",") if email.strip()])
        for email in emails:
            try:
                validate_email(email)
            except forms.ValidationError:
                raise forms.ValidationError('"%(email)s" is an invalid email', params={"email": email})

        return emails

    def save(self, user, report):
        invited = []
        already_invited = []
        for email in self.cleaned_data['emails']:
            if Invite.create(email=email, report=report, inviter=user, message=self.cleaned_data.get('body')):
                invited.append(email)
            else:
                already_invited.append(email)

        return namedtuple("InviteReport", "invited already_invited")(invited, already_invited)


class ConfirmForm(forms.ModelForm):
    """
    Allows the expert to confirm the report by choosing a species (or creating
    a new species)
    """
    SUBMIT_FLAG = "CONFIRM"

    new_species = forms.CharField(required=False, label="")
    severity = forms.ModelChoiceField(queryset=Severity.objects.all(), label="", required=False)
    category = forms.ModelChoiceField(queryset=Category.objects.all(), empty_label="")

    class Meta:
        model = Report
        fields = [
            'actual_species'
        ]

    def __init__(self, *args, instance, **kwargs):
        initial = kwargs.pop("initial", {})
        if instance.actual_species is None:
            initial['actual_species'] = instance.reported_species
            initial['category'] = instance.reported_category
        else:
            initial['category'] = instance.actual_species.category

        super().__init__(*args, instance=instance, initial=initial, **kwargs)

        self.fields['category'].widget.attrs['id'] = "id_reported_category"
        self.fields['actual_species'].widget.attrs['id'] = "id_reported_species"
        self.fields['new_species'].widget.attrs['placeholder'] = "Species common name"

        self.fields['actual_species'].empty_label = ""
        self.fields['actual_species'].required = False

    def clean(self):
        new_species = self.cleaned_data.get("new_species")
        actual_species = self.cleaned_data.get("actual_species")
        severity = self.cleaned_data.get("severity")

        if not (bool(new_species) ^ bool(actual_species)):
            raise forms.ValidationError("Either choose a species or create a new one.", code="species_contradiction")

        if new_species and not severity:
            self.add_error("severity", forms.ValidationError("This field is required", code="required"))

        return self.cleaned_data

    def save(self, *args, **kwargs):
        new_species = self.cleaned_data.get("new_species")
        severity = self.cleaned_data.get("severity")

        if new_species:
            species = Species(name=new_species, severity=severity, category=self.cleaned_data['category'])
            species.save()
            self.instance.actual_species = species

        return super().save(*args, **kwargs)
