import itertools
from collections import namedtuple

from django import forms
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.core.validators import validate_email
from django.db.models import Q
from django.template.loader import render_to_string
from elasticmodels.forms import SearchForm

from hotline.comments.models import Comment
from hotline.counties.models import County
from hotline.notifications.models import UserNotificationQuery
from hotline.species.models import Category, Severity, Species
from hotline.users.models import User

from .indexes import ReportIndex
from .models import Invite, Report


class ReportSearchForm(SearchForm):
    """
    This form handles searching of reports by managers and anonymous users alike.

    Form data that is submitted can be used to create a "UserNotificationQuery"
    object in the database, which captures the input to this form as a
    QueryDict string. So be careful if you start renaming fields, since that
    will break any UserNotificationQuery rows that rely on that field.
    """
    q = None  # the default SearchForm has a q field with we don't want to use

    querystring = forms.CharField(required=False, widget=forms.widgets.TextInput(attrs={
        "placeholder": "county:Washington AND category:Aquatic"
    }), label="Search")

    sort_by = forms.ChoiceField(choices=[
        ("_score", "Relevance"),
        ("species.raw", "Species"),
        ("category.raw", "Category"),
        ("-created_on", "Date"),
    ], required=False, widget=forms.widgets.RadioSelect)

    is_archived = forms.ChoiceField(choices=[
        ("", "Any"),
        ("archived", "Archived"),
        ("notarchived", "Not archived"),
    ], required=False, initial="notarchived")

    is_public = forms.ChoiceField(choices=[
        ("", "Any"),
        ("public", "Public"),
        ("notpublic", "Not public"),
    ], required=False)

    claimed_by = forms.ChoiceField(choices=[
        ("", "Any"),
        ("me", "Me"),
        ("nobody", "Nobody"),
    ], required=False)

    def __init__(self, *args, user, report_ids=(), **kwargs):
        self.user = user
        self.report_ids = report_ids
        super().__init__(*args, index=ReportIndex, **kwargs)

        # only certain fields on this form can be used by members of the public
        public_fields = ['querystring', 'sort_by']
        if not user.is_active:
            for name in self.fields.keys():
                if name not in public_fields:
                    self.fields.pop(name)

        # create a MultipleChoiceField listing the species, for each category
        groups = itertools.groupby(
            Species.objects.all().select_related("category").order_by("category__name", "category__pk", "name"),
            key=lambda obj: obj.category
        )
        self.categories = []
        for category, species in groups:
            self.categories.append(category)
            choices = [(s.pk, str(s)) for s in species]
            self.fields['category-%d' % category.pk] = forms.MultipleChoiceField(
                choices=choices,
                required=False,
                label="",
                widget=forms.widgets.CheckboxSelectMultiple
            )

    def iter_categories(self):
        """
        Just makes it easier to look through the category fields
        """
        for category in self.categories:
            yield category, self['category-%d' % category.pk]

    def get_queryset(self):
        # We do a monster join here so we get all the data we need on all the methods we
        # call on the report
        queryset = super().get_queryset().prefetch_related(
            "image_set",
            "comment_set__image_set"
        ).select_related(
            "reported_category",
            "reported_species",
            "actual_species",
            "actual_species__severity",
            "reported_species__severity",
            "actual_species__category",
            "reported_species__category"
        )

        if not self.user.is_active:
            # only show public reports, or reports that they were invited to,
            # or reports that are in their session variable
            queryset = queryset.filter(
                Q(is_public=True) |
                Q(pk__in=Invite.objects.filter(user_id=self.user.pk)) |
                Q(pk__in=self.report_ids)
            )

        # the is_archived field has an initial value on the form, which we want
        # to pre-filter with
        is_archived = self.cleaned_data.get("is_archived")
        if is_archived == "archived":
            queryset = queryset.filter(is_archived=True)
        elif is_archived == "notarchived":
            queryset = queryset.filter(is_archived=False)

        return queryset

    def search(self):
        results = super().search()
        if self.cleaned_data.get("querystring"):
            query = results.query(
                "query_string",
                query=self.cleaned_data.get("querystring", ""),
                lenient=True,
            )

            # if the query isn't valid, fall back on a simple_query_string
            # query
            if not self.is_valid_query(query):
                results = results.query(
                    "simple_query_string",
                    query=self.cleaned_data.get("querystring", ""),
                    lenient=True,
                )
            else:
                results = query

        sort_by = self.cleaned_data.get("sort_by")
        if sort_by:
            results = results.sort(sort_by)

        # collect all the species and filter by that
        species = []
        for category in self.categories:
            species.extend(map(int, self.cleaned_data.get("category-%d" % category.pk, [])))
        if species:
            results = results.filter("terms", species_id=species)

        is_public = self.cleaned_data.get("is_public", "")
        if is_public is not "":
            results = results.filter("term", is_public=is_public == "public")

        is_archived = self.cleaned_data.get("is_archived", "")
        if is_archived is not "":
            results = results.filter("term", is_archived=is_archived == "archived")

        claimed_by = self.cleaned_data.get("claimed_by")
        if claimed_by == "me":
            results = results.filter("term", claimed_by=self.user.email)
        elif claimed_by == "nobody":
            results = results.filter("missing", field="claimed_by")

        return results


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


class SettingsForm(forms.ModelForm):
    """
    Handles setting some flags on the report

    The is_public flag is only enabled if the actual species associated with
    the report is *not* marked as is_confidential
    """
    SUBMIT_FLAG = "SETTINGS"

    class Meta:
        model = Report
        fields = [
            'is_public',
            'is_archived',
            'edrr_status',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.actual_species and self.instance.actual_species.is_confidential:
            self.fields['is_public'].widget.attrs['disabled'] = True
            self.fields['is_public'].help_text = "This species is marked as confidential, so you cannot make this report public."

    def clean_is_public(self):
        if self.instance.actual_species and self.instance.actual_species.is_confidential:
            return False
        return self.cleaned_data['is_public']


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

        if bool(new_species) & bool(actual_species):
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
        elif not self.cleaned_data.get("actual_species"):
            self.instance.actual_species = None

        return super().save(*args, **kwargs)
