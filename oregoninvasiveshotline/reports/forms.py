from collections import namedtuple

from django import forms
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.core.validators import validate_email
from django.template.loader import render_to_string

from haystack.forms import SearchForm
from haystack.query import AutoQuery, SQ, SearchQuerySet

from oregoninvasiveshotline.comments.models import Comment
from oregoninvasiveshotline.counties.models import County
from oregoninvasiveshotline.notifications.models import UserNotificationQuery
from oregoninvasiveshotline.species.models import Category, Severity, Species
from oregoninvasiveshotline.users.models import User

from .models import Invite, Report


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

    """Search for reports.

    This form handles searching of reports by both managers and
    anonymous users.

    Form data can be used to create a :class:`UserNotificationQuery`
    object in the database, which captures the input to this form as
    a QueryDict string. So be careful if you start renaming fields,
    since that will break any :class:`UserNotificationQuery` rows that
    rely on that field.

    """

    public_fields = ['q', 'order_by', 'source', 'categories', 'counties']

    q = forms.CharField(
        required=False,
        label='Search',
        widget=forms.widgets.TextInput(attrs={
            'type': 'search',
            'placeholder': 'Enter a category, county, species, or other keyword'
        })
    )

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
        required=False, label='', choices=get_category_choices,
        widget=forms.SelectMultiple(attrs={'title': 'Categories'}))
    counties = forms.MultipleChoiceField(
        required=False, label='', choices=get_county_choices,
        widget=forms.SelectMultiple(attrs={'title': 'Counties'}))

    order_by = forms.ChoiceField(
        required=False,
        choices=[
            ('_score', 'Relevance'),
            ('species', 'Species'),
            ('category', 'Category'),
            ('-created_on', 'Newest'),
        ],
        widget=forms.widgets.RadioSelect
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

    def __init__(self, *args, user, report_ids=(), **kwargs):
        sqs = SearchQuerySet().models(Report)

        # Ensure anonymous/public users cannot see non-public reports in all
        # cases.
        if not user.is_active:
            if report_ids:
                sqs = sqs.filter(SQ(id__in=report_ids) | SQ(is_public=True))
            else:
                sqs = sqs.filter(is_public=True)

        super().__init__(*args, searchqueryset=sqs, **kwargs)

        self.user = user
        self.report_ids = report_ids

        # Only certain fields on this form can be used by members of the
        # public.
        if not user.is_active:
            for name in self.fields.keys():
                if name not in self.public_fields:
                    self.fields.pop(name)

        if user.is_anonymous():
            if report_ids:
                source_field = self.fields['source']
                source_choices = source_field.choices
                source_field.choices = [
                    (value, label) for (value, label) in source_choices if value != 'invited']
            else:
                self.fields.pop('source')

    def no_query_found(self):
        """Return all reports when query is invalid."""
        return self.searchqueryset.all()

    def search(self):
        if not self.is_valid():
            return self.no_query_found()

        sqs = self.searchqueryset
        user = self.user
        report_ids = self.report_ids
        form_data = self.cleaned_data
        term = form_data.get('q')
        order_by = form_data.get('order_by')

        if term:
            auto_query = AutoQuery(term)
            query = (
                SQ(title=auto_query) |
                SQ(category=auto_query) |
                SQ(county=auto_query) |
                SQ(species=auto_query) |
                SQ(text=auto_query)
            )
            if term.isdecimal():
                query = SQ(report_id=auto_query) | query
            sqs = sqs.filter(query)
        else:
            # Don't show the relevance ordering option when there's no
            # search term.
            self.fields['order_by'].choices = self.fields['order_by'].choices[1:]

        counties = form_data.get('counties')
        if counties:
            sqs = sqs.filter(county_id__in=counties)

        categories = form_data.get('categories')
        if categories:
            sqs = sqs.filter(category_id__in=categories)

        is_archived = form_data.get('is_archived')
        if is_archived == 'archived':
            sqs = sqs.filter(is_archived=True)
        elif is_archived == 'notarchived':
            sqs = sqs.exclude(is_archived=True)

        is_public = form_data.get('is_public')
        if is_public == 'public':
            sqs = sqs.filter(is_public=True)
        elif is_public == 'notpublic':
            sqs = sqs.exclude(is_public=True)

        claimed_by = form_data.get('claimed_by')
        if claimed_by == 'me':
            sqs = sqs.filter(claimed_by_id=user.pk)
        elif claimed_by == 'nobody':
            sqs = sqs.filter(_missing_='claimed_by_id')

        source = form_data.get('source')
        if source == 'invited':
            user_invites = Invite.objects.filter(user_id=user.pk)
            sqs = sqs.filter(id__in=user_invites.values_list('report_id', flat=True))
        elif source == 'reported':
            if user.is_active:
                sqs = sqs.filter(created_by_id=user.pk)
            if report_ids:
                sqs = sqs.filter(id__in=report_ids)

        if order_by:
            sqs = sqs.order_by(order_by)
        elif not term:
            sqs = sqs.order_by('-created_on')

        return sqs


class ReportForm(forms.ModelForm):
    """
    Form for the public to submit reports
    """
    questions = forms.CharField(
        label="Do you have additional questions for the invasive species expert who will review this report?",
        widget=forms.Textarea,
        required=False
    )
    first_name = forms.CharField()
    last_name = forms.CharField()
    prefix = forms.CharField(required=False)
    suffix = forms.CharField(required=False)
    email = forms.EmailField()
    phone = forms.CharField(required=False)
    has_completed_ofpd = forms.BooleanField(required=False)

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
        self.fields['reported_species'].empty_label = "Unknown"
        self.fields['reported_species'].required = False
        self.fields['has_completed_ofpd'].label = User._meta.get_field("has_completed_ofpd").verbose_name

    def save(self, *args, request, **kwargs):
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
                phone=self.cleaned_data.get('phone', ""),
                has_completed_ofpd=self.cleaned_data.get("has_completed_ofpd"),
                is_active=False
            )
            user.save()

        self.instance.created_by = user
        self.instance.county = County.objects.filter(the_geom__intersects=self.instance.point).first()
        super().save(*args, **kwargs)

        # if the submitter left a question, add it as a comment
        if self.cleaned_data.get("questions"):
            c = Comment(report=self.instance, created_by=user, body=self.cleaned_data['questions'], visibility=Comment.PROTECTED)
            c.save()

        send_mail(
            "OregonInvasivesHotline.org - Thank you for your submission",
            render_to_string("reports/_submission.txt", {
                "user": user,
                "url": user.get_authentication_url(request, next=reverse("reports-detail", args=[self.instance.pk]))
            }),
            "noreply@pdx.edu",
            [user.email]
        )

        UserNotificationQuery.notify(self.instance, request)

        return self.instance


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

    def save(self, user, report, request):
        invited = []
        already_invited = []
        for email in self.cleaned_data['emails']:
            if Invite.create(email=email, report=report, inviter=user, message=self.cleaned_data.get('body'), request=request):
                invited.append(email)
            else:
                already_invited.append(email)

        # make the invite into a comment
        Comment(body=self.cleaned_data.get("body"), created_by=user, visibility=Comment.PRIVATE, report=report).save()
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
