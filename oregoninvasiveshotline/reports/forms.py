from collections import namedtuple

from django.core.validators import validate_email
from django.db import transaction
from django import forms

from oregoninvasiveshotline.utils.search import SearchForm
from oregoninvasiveshotline.comments.models import Comment
from oregoninvasiveshotline.counties.models import County
from oregoninvasiveshotline.species.models import Category, Severity, Species
from oregoninvasiveshotline.users.models import User
from oregoninvasiveshotline.reports.models import Invite, Report
from oregoninvasiveshotline.reports.tasks import (
    notify_report_submission,
    notify_report_subscribers,
    notify_invited_reviewer
)


def get_category_choices():
    categories = Category.objects.all().order_by('name')
    category_choices = []
    category_choices.extend((c.pk, c.name) for c in categories)
    return category_choices


def get_county_choices():
    county_choices = []
    for county in County.objects.all().order_by('state', 'name'):
        county_choices.append((county.pk, county.label))
    return county_choices


class ReportSearchForm(SearchForm):
    """
    Search for reports.

    This form handles searching of reports by both managers and
    anonymous users.

    Form data can be used to create a :class:`UserNotificationQuery`
    object in the database, which captures the input to this form as
    a QueryDict string. So be careful if you start renaming fields,
    since that will break any :class:`UserNotificationQuery` rows that
    rely on that field.
    """
    public_fields = ['q', 'order_by', 'source', 'categories', 'counties']

    source = forms.ChoiceField(
        required=False,
        label='',
        choices=[
            ('', '- Extra Criteria -'),
            ('invited', 'Invited to Review'),
            ('reported', 'Reported by Me')
        ]
    )
    categories = forms.MultipleChoiceField(
        required=False,
        label='',
        choices=get_category_choices,
        widget=forms.SelectMultiple(attrs={'title': 'Categories'})
    )
    counties = forms.MultipleChoiceField(
        required=False,
        label='',
        choices=get_county_choices,
        widget=forms.SelectMultiple(attrs={'title': 'Counties'})
    )
    is_archived = forms.ChoiceField(
        required=False,
        initial='notarchived',
        label='',
        choices=[
            ('', '- Archived? -'),
            ('archived', 'Archived'),
            ('notarchived', 'Not archived'),
        ]
    )
    is_public = forms.ChoiceField(
        required=False,
        label='',
        choices=[
            ('', '- Public? -'),
            ('public', 'Public'),
            ('notpublic', 'Not public'),
        ])
    claimed_by = forms.ChoiceField(
        required=False,
        label='',
        choices=[
            ('', '- Claimed By -'),
            ('me', 'Me'),
            ('nobody', 'Nobody'),
        ])
    order_by = forms.ChoiceField(
        required=False,
        choices=[
            ('species', 'Species'),
            ('category', 'Category'),
            ('-created_on', 'Newest'),
        ],
        widget=forms.widgets.RadioSelect
    )

    def get_search_fields(self):
        return (
            'county__name',
            'reported_category__name',
            'reported_species__name',
            'reported_species__scientific_name',
            'actual_species__category__name',
            'actual_species__name',
            'actual_species__scientific_name',
            'report_id'
        )

    def __init__(self, *args, user, report_ids=(), **kwargs):
        super().__init__(*args, **kwargs)

        # Only certain fields on this form can be used by members of the public
        if not user.is_active:
            for name in list(self.fields):
                if name not in self.public_fields:
                    self.fields.pop(name)

        if user.is_anonymous:
            if report_ids:
                source_field = self.fields['source']
                source_choices = source_field.choices
                source_field.choices = [
                    (value, label)
                    for (value, label) in source_choices if value != 'invited']
            else:
                self.fields.pop('source')


class ReportForm(forms.ModelForm):

    email = forms.EmailField()
    prefix = forms.CharField(required=False)
    first_name = forms.CharField()
    last_name = forms.CharField()
    suffix = forms.CharField(required=False)
    phone = forms.CharField(required=False)
    has_completed_ofpd = forms.BooleanField(required=False)
    questions = forms.CharField(
        required=False,
        widget=forms.Textarea,
        label=(
            'Do you have additional questions for the invasive species expert who will review '
            'this report?'
        ),
    )

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
        widgets = {
            'point': forms.widgets.HiddenInput
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['reported_species'].empty_label = 'Unknown'
        self.fields['reported_species'].required = False

        has_completed_ofpd_label = User._meta.get_field('has_completed_ofpd').verbose_name
        self.fields['has_completed_ofpd'].label = has_completed_ofpd_label

    def clean_email(self):
        # NOTE: Technically, email addresses are case-sensitive, but in
        #       practice we can ignore that.
        email = self.cleaned_data['email']
        email = email.lower()
        return email

    def save(self, *args, **kwargs):
        report = self.instance

        # NOTE: If the user doesn't exist, a new inactive account is
        #       automatically created here, which seems to me like a
        #       tremendously bad idea (still trying to work out how to
        #       fix this).
        email = self.cleaned_data['email']
        defaults = {
            'email': email.lower(),
            'prefix': self.cleaned_data.get('prefix', ''),
            'first_name': self.cleaned_data.get('first_name'),
            'last_name': self.cleaned_data.get('last_name'),
            'suffix': self.cleaned_data.get('suffix', ''),
            'phone': self.cleaned_data.get('phone', ''),
            'has_completed_ofpd': self.cleaned_data.get('has_completed_ofpd'),
            'is_active': False,
        }
        user, _ = User.objects.get_or_create(email__iexact=email, defaults=defaults)

        report.created_by = user
        report.county = County.objects.filter(the_geom__intersects=report.point).first()

        super().save(*args, **kwargs)

        questions = self.cleaned_data.get('questions')
        if questions:
            Comment.objects.create(
                report=report, created_by=user, body=questions, visibility=Comment.PROTECTED)

        transaction.on_commit(lambda: notify_report_submission.delay(report.pk, user.pk))
        transaction.on_commit(lambda: notify_report_subscribers.delay(report.pk))

        return report


class InviteForm(forms.Form):
    """
    Form to invite people to comment on a report
    """
    SUBMIT_FLAG = "INVITE"

    emails = forms.CharField(label="Email addresses (comma separated)")
    body = forms.CharField(widget=forms.Textarea, required=False)

    def clean_emails(self):
        emails = set([email.strip() for email in self.cleaned_data['emails'].split(",") if email.strip()])
        for email in emails:
            try:
                validate_email(email)
            except forms.ValidationError:
                raise forms.ValidationError('"%(email)s" is an invalid email', params={"email": email})

        return emails

    def save(self, inviter, report):
        """
        Send an invitation to the specified ``email`` address.

        If an invite has already been sent to the ``email`` address for
        the specified ``report``, nothing will be done. Otherwise, an
        ``Invite`` record is created and an email is sent.

        Returns:
            bool: True if the invite was sent; False if an invite has
                already been sent to the email address for the specified
                report.
        """
        invited = []
        already_invited = []

        for email in self.cleaned_data['emails']:
            user, _ = User.objects.get_or_create(email__iexact=email,
                                                 defaults={'email': email.lower(),
                                                           'is_active': False})
            (invite, created) = Invite.objects.get_or_create(user=user,
                                                             report=report,
                                                             defaults={'created_by': inviter})
            if created:
                transaction.on_commit(lambda: notify_invited_reviewer.delay(invite.pk, self.cleaned_data.get('body')))
                invited.append(email)
            else:
                already_invited.append(email)

        # make the invite into a comment
        Comment.objects.create(report=report,
                               visibility=Comment.PRIVATE,
                               body=self.cleaned_data.get("body"),
                               created_by=inviter)
                               
        return namedtuple("InviteReport", "invited already_invited")(invited, already_invited)


class ManagementForm(forms.ModelForm):
    """
    Allows the expert to confirm the report by choosing a species (or creating
    a new species)
    """
    SUBMIT_FLAG = "MANAGEMENT"
    confidential_error_text = "This species is marked as confidential, so you cannot make this report public."

    new_species = forms.CharField(required=False, label="")
    severity = forms.ModelChoiceField(queryset=Severity.objects.all(), label="", required=False)
    category = forms.ModelChoiceField(queryset=Category.objects.all(), empty_label="")

    class Meta:
        model = Report
        fields = [
            'actual_species',
            'is_public',
            'is_archived',
            'edrr_status',
        ]

    def __init__(self, *args, instance, **kwargs):
        initial = kwargs.pop("initial", {})
        if instance.actual_species is None:
            initial['actual_species'] = instance.reported_species
            initial['category'] = instance.reported_category
        else:
            initial['category'] = instance.actual_species.category

        super().__init__(*args, instance=instance, initial=initial, **kwargs)

        # we have to use these specific IDs so the JS in species_selector.js works
        self.fields['category'].widget.attrs['id'] = "id_reported_category"
        self.fields['actual_species'].widget.attrs['id'] = "id_reported_species"

        self.fields['new_species'].widget.attrs['placeholder'] = "Species common name"

        self.fields['actual_species'].empty_label = ""
        self.fields['actual_species'].required = False

        if self.instance.actual_species and self.instance.actual_species.is_confidential:
            self.fields['is_public'].widget.attrs['disabled'] = True
            self.fields['is_public'].help_text = self.confidential_error_text

    def clean_is_public(self):
        if self.instance.actual_species and self.instance.actual_species.is_confidential:
            return False
        return self.cleaned_data['is_public']

    def clean(self):
        new_species = self.cleaned_data.get("new_species")
        actual_species = self.cleaned_data.get("actual_species")
        severity = self.cleaned_data.get("severity")

        if bool(new_species) & bool(actual_species):
            raise forms.ValidationError("Either choose a species or create a new one.", code="species_contradiction")

        if new_species and not severity:
            self.add_error("severity", forms.ValidationError("This field is required", code="required"))

        if actual_species and actual_species.is_confidential and self.cleaned_data.get("is_public"):
            raise forms.ValidationError(self.confidential_error_text, code="species-confidential")

        return self.cleaned_data

    def save(self, *args, **kwargs):
        new_species = self.cleaned_data.get("new_species")
        severity = self.cleaned_data.get("severity")

        if new_species:
            species = Species(name=new_species, severity=severity, category=self.cleaned_data['category'])
            species.save()
            self.instance.actual_species = species
        elif not self.cleaned_data.get("actual_species"):
            self.instance.actual_species = None

        return super().save(*args, **kwargs)
