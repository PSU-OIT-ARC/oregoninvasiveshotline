from datetime import timedelta
from unittest.mock import patch

from django.utils import timezone
from django.test import TestCase, TransactionTestCase
from django.contrib.gis.geos import Point
from django.core.exceptions import NON_FIELD_ERRORS
from django.core import mail
from django.db import transaction

from model_mommy.mommy import make, prepare
from arcutils.test.user import UserMixin

from oregoninvasiveshotline.tests.base import ServiceTestCaseMixin
from oregoninvasiveshotline.comments.models import Comment
from oregoninvasiveshotline.species.models import Category, Severity, Species
from oregoninvasiveshotline.notifications.models import UserNotificationQuery
from oregoninvasiveshotline.users.models import User
from oregoninvasiveshotline.reports.forms import InviteForm, ManagementForm, ReportForm, ReportSearchForm
from oregoninvasiveshotline.reports.models import Invite, Report

from .base import SuppressPostSaveMixin

ORIGIN = Point(0, 0)


class ReportSearchFormTest(UserMixin, ServiceTestCaseMixin, TestCase):

    def setUp(self):
        self.user = self.create_user(
            username="foo@example.com",
            password="foo",
            is_active=True,
            is_staff=True
        )
        self.report = Report()

    def tearDown(self):
        if self.report.pk is not None:
            self.report.delete()

    def test_filter_by_open_and_claimed_reports(self):
        # test combined filters
        claimed_open_report = make(
            Report, claimed_by=self.user, is_archived=False, point=ORIGIN)
        claimed_archived_report = make(
            Report, claimed_by=self.user, is_archived=True, point=ORIGIN)
        unclaimed_report = make(Report, claimed_by=None, point=ORIGIN)

        form = ReportSearchForm({
            "q": "",
            "claimed_by": "me",
            "is_archived": "notarchived"
        }, user=self.user)
        results = form.search()

        # Since form.search() returns a SearchQuerySet, we create from that a
        # list of reports so we can see if our desired reports are in the list.
        reports = list()
        for r in results:
            reports.append(r.object)

        self.assertIn(claimed_open_report, reports)
        self.assertNotIn(claimed_archived_report, reports)
        self.assertNotIn(unclaimed_report, reports)
        self.assertEqual(len(reports), 1)

    def test_filter_by_claimed_by_me_reports(self):
        claimed_open_report = make(
            Report, claimed_by=self.user, is_archived=False, point=ORIGIN)
        claimed_archived_report = make(
            Report, claimed_by=self.user, is_archived=True, point=ORIGIN)
        unclaimed_report = make(Report, claimed_by=None, point=ORIGIN)

        form = ReportSearchForm({
            "q": "",
            "claimed_by": "me",
        }, user=self.user)
        results = form.search()

        reports = list()
        for r in results:
            reports.append(r.object)

        self.assertIn(claimed_open_report, reports)
        self.assertIn(claimed_archived_report, reports)
        self.assertNotIn(unclaimed_report, reports)
        self.assertEqual(len(reports), 2)

    def test_filter_by_unclaimed_reports(self):
        claimed_report = make(Report, claimed_by=self.user, point=ORIGIN)
        unclaimed_report = make(Report, claimed_by=None, point=ORIGIN)

        form = ReportSearchForm({
            "q": "",
            "claimed_by": "nobody",
        }, user=self.user)
        results = form.search()

        reports = list()
        for r in results:
            reports.append(r.object)

        self.assertIn(unclaimed_report, reports)
        self.assertNotIn(claimed_report, reports)
        self.assertEqual(len(reports), 1)

    def test_filter_by_archived_reports(self):
        archived_report = make(Report, is_archived=True, point=ORIGIN)
        unarchived_report = make(Report, is_archived=False, point=ORIGIN)

        form = ReportSearchForm({
            "q": "",
            "is_archived": "archived",
        }, user=self.user)
        results = form.search()

        reports = list()
        for r in results:
            reports.append(r.object)

        self.assertIn(archived_report, reports)
        self.assertNotIn(unarchived_report, reports)
        self.assertEqual(len(reports), 1)

    def test_filter_by_unarchived_reports(self):
        archived_report = make(Report, is_archived=True, point=ORIGIN)
        unarchived_report = make(Report, is_archived=False, point=ORIGIN)

        form = ReportSearchForm({
            "q": "",
            "is_archived": "notarchived",
        }, user=self.user)
        results = form.search()

        reports = list()
        for r in results:
            reports.append(r.object)

        self.assertIn(unarchived_report, reports)
        self.assertNotIn(archived_report, reports)
        self.assertEqual(len(reports), 1)

    def test_filter_by_public_reports(self):
        pub_report = make(Report, is_public=True, point=ORIGIN)
        priv_report = make(Report, is_public=False, point=ORIGIN)

        form = ReportSearchForm({
            "q": "",
            "is_public": "public",
        }, user=self.user)
        results = form.search()

        reports = list()
        for r in results:
            reports.append(r.object)

        self.assertIn(pub_report, reports)
        self.assertNotIn(priv_report, reports)
        self.assertEqual(len(reports), 1)

    def test_filter_by_not_public_reports(self):
        pub_report = make(Report, is_public=True, point=ORIGIN)
        priv_report = make(Report, is_public=False, point=ORIGIN)

        form = ReportSearchForm({
            "q": "",
            "is_public": "notpublic",
        }, user=self.user)
        results = form.search()

        reports = list()
        for r in results:
            reports.append(r.object)

        self.assertIn(priv_report, reports)
        self.assertNotIn(pub_report, reports)
        self.assertEqual(len(reports), 1)

    def test_filter_by_reports_user_was_invited_to(self):
        inviter = self.create_user(username="inviter@example.com")
        invited_report = make(Report, created_by=inviter, point=ORIGIN)
        other_report = make(Report, point=ORIGIN)
        make(Invite, user=self.user, created_by=inviter, report=invited_report)

        form = ReportSearchForm({
            "q": "",
            "source": "invited",
        }, user=self.user)
        results = form.search()

        reports = list()
        for r in results:
            reports.append(r.object)

        self.assertIn(invited_report, reports)
        self.assertNotIn(other_report, reports)
        self.assertEqual(len(reports), 1)

    def test_filter_by_reports_user_reported(self):
        my_report = make(Report, created_by=self.user, point=ORIGIN)
        other_report = make(Report, point=ORIGIN)

        form = ReportSearchForm({
            "q": "",
            "source": "reported",
        }, user=self.user, report_ids=[my_report.pk])
        results = form.search()

        reports = list()
        for r in results:
            reports.append(r.object)

        self.assertIn(my_report, reports)
        self.assertNotIn(other_report, reports)
        self.assertEqual(len(reports), 1)

    def test_order_by_field_sorts_reports(self):
        now = timezone.now()
        make(Report, created_on=now - timedelta(days=1), point=ORIGIN)
        make(Report, created_on=now, point=ORIGIN)
        make(Report, created_on=now + timedelta(days=1), point=ORIGIN)

        form = ReportSearchForm({
            "order_by": "-created_on",
        }, user=self.user)
        results = form.search()

        reports = list()
        for r in results:
            reports.append(r.object)

        self.assertTrue(reports, Report.objects.all().order_by("-created_on"))

    def test_inactive_users_only_see_public_fields(self):
        self.user.is_active = False
        self.user.save()
        form = ReportSearchForm(self, user=self.user)
        form_fields = sorted(tuple(form.fields.keys()))
        public_fields = sorted(form.public_fields)
        self.assertEqual(form_fields, public_fields)

    def test_inactive_users_only_see_public_reports_and_reports_they_created(self):
        self.user.is_active = False
        self.user.save()
        pub_report = make(Report, is_public=True, point=ORIGIN)
        priv_report = make(Report, is_public=False, point=ORIGIN)
        my_report = make(Report, created_by=self.user, point=ORIGIN)

        # Since we aren't creating reports through a view, manually assign the
        # created report to report_ids (already covered in view tests)
        form = ReportSearchForm({"q": ""}, user=self.user, report_ids=[my_report.pk])
        results = form.search()

        # Since form.search() returns a SearchQuerySet, we create from that a
        # list of reports so we can see if our desired reports are in the list.
        reports = list()
        for r in results:
            reports.append(r.object)

        # Ensure that only pub_report and my_report are in the list of reports
        self.assertIn(pub_report, reports)
        self.assertIn(my_report, reports)
        self.assertNotIn(priv_report, reports)
        self.assertEqual(len(reports), 2)


class ReportFormTest(UserMixin, ServiceTestCaseMixin, TransactionTestCase):

    def test_reported_species_is_not_required(self):
        form = ReportForm({})
        self.assertFalse(form.is_valid())
        self.assertFalse(form.has_error("reported_species"))

    def test_save_creates_user_if_it_doesnt_exist(self):
        # the user doesn't exist, so he should be created when the form is saved
        form = ReportForm({
            "email": "foo@example.com",
            "first_name": "Foo",
            "last_name": "Bar",
            "prefix": "Mr.",
            "suffix": "PHD",
        })
        self.assertFalse(form.is_valid())
        report = prepare(Report, pk=1, point=ORIGIN)
        pre_count = User.objects.count()

        with patch("oregoninvasiveshotline.reports.forms.forms.ModelForm.save") as save:
            form.instance = report
            form.save()
            self.assertTrue(save.called)

        self.assertEqual(User.objects.count(), pre_count+1)
        self.assertEqual(report.created_by.email, "foo@example.com")
        self.assertEqual(report.created_by.is_active, False)
        self.assertEqual(report.created_by.last_name, "Bar")

        # the user already exists, so no record should be created
        pre_count = User.objects.count()
        form = ReportForm({
            "email": "FOO@eXaMplE.com",  # using odd casing here to ensure `icontains` is used
        })
        self.assertFalse(form.is_valid())
        pre_count = User.objects.count()
        with patch("oregoninvasiveshotline.reports.forms.forms.ModelForm.save") as save:
            form.instance = report
            form.save()
            self.assertTrue(save.called)

        self.assertEqual(User.objects.count(), pre_count)

    def test_comment_is_added(self):
        form = ReportForm({
            "email": "foo@example.com",
            "first_name": "Foo",
            "last_name": "Bar",
            "questions": "hello world",
        })
        self.assertFalse(form.is_valid())
        report = make(Report, point=ORIGIN)
        with patch("oregoninvasiveshotline.reports.forms.forms.ModelForm.save"):
            form.instance = report
            form.save()

        self.assertEqual(Comment.objects.get(report=report).body, "hello world")

    def test_notify_sends_emails_to_subscribers(self):
        user = self.create_user(username='foo@example.com')

        # Subscribe to the same thing twice to ensure that only one
        # email is sent to the user when a report matches.
        make(UserNotificationQuery, query='q=foobarius', user=user)
        make(UserNotificationQuery, query='q=foobarius', user=user)

        # This report does *not* have the words "foobarius" in it, so no
        # email should be sent.
        form = ReportForm({
            "email": "foo@example.com",
            "first_name": "Foo",
            "last_name": "Bar",
        })
        self.assertFalse(form.is_valid())
        report = make(Report, point=ORIGIN)
        with patch("oregoninvasiveshotline.reports.forms.forms.ModelForm.save"):
            # notification task is out-of-band and uses 'on_commit' barrier
            # so the path being tested is wrapped in a transaction
            with transaction.atomic():
                form.instance = report
                form.save()

        # mailbox should contain one report submission email
        self.assertEqual(len(mail.outbox), 1)

        # This report *does* have the word "foobarius" in it, so it
        # should trigger an email to be sent.
        report = make(Report, reported_category__name='foobarius', point=ORIGIN)
        with patch("oregoninvasiveshotline.reports.forms.forms.ModelForm.save"):
            # notification task is out-of-band and uses 'on_commit' barrier
            # so the path being tested is wrapped in a transaction
            with transaction.atomic():
                form.instance = report
                form.save()

        # mailbox should contain two report submission emails and a
        # subscription notification
        self.assertEqual(len(mail.outbox), 3)

        # If we notify about the same report, no new email should be sent.
        with patch("oregoninvasiveshotline.reports.forms.forms.ModelForm.save"):
            # notification task is out-of-band and uses 'on_commit' barrier
            # so the path being tested is wrapped in a transaction
            with transaction.atomic():
                form.instance = report
                form.save()

        # mailbox should contain three report submission emails and a
        # subscription notification
        self.assertEqual(len(mail.outbox), 4)


class ManagementFormTest(SuppressPostSaveMixin, TestCase):

    def test_species_and_category_initialized(self):
        species = make(Species)
        report = make(Report, reported_species=species, reported_category=species.category, point=ORIGIN)
        form = ManagementForm(instance=report)
        self.assertEqual(form.initial['category'], species.category)
        self.assertEqual(form.initial['actual_species'], species)

    def test_field_widget_ids_match_expected_id_from_javascript(self):
        """
        The javascript for the category/species selector expects the ids for
        the category and species fields to be something particular
        """
        report = make(Report, point=ORIGIN)
        form = ManagementForm(instance=report)
        self.assertEqual(form.fields['category'].widget.attrs['id'], 'id_reported_category')
        self.assertEqual(form.fields['actual_species'].widget.attrs['id'], 'id_reported_species')

    def test_either_a_new_species_is_entered_xor_an_existing_species_is_selected(self):
        report = make(Report, point=ORIGIN)
        data = {
            "new_species": "Yeti",
            "actual_species": make(Species).pk
        }
        form = ManagementForm(data, instance=report)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error(NON_FIELD_ERRORS, code="species_contradiction"))

        data = {
            "new_species": "Yeti",
        }
        form = ManagementForm(data, instance=report)
        self.assertFalse(form.is_valid())
        self.assertFalse(form.has_error(NON_FIELD_ERRORS, code="species_contradiction"))

    def test_if_new_species_is_entered_severity_is_required(self):
        report = make(Report, point=ORIGIN)
        data = {
            "new_species": "Yeti",
        }
        form = ManagementForm(data, instance=report)
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error("severity", code="required"))

    def test_new_species_is_saved(self):
        report = make(Report, point=ORIGIN)
        category = make(Category)
        severity = make(Severity)
        data = {
            "new_species": "Yeti",
            "category": category.pk,
            "severity": severity.pk
        }
        form = ManagementForm(data, instance=report)
        self.assertTrue(form.is_valid())
        form.save()
        species = Species.objects.get(name="Yeti", category=category)
        self.assertEqual(report.actual_species, species)

    def test_is_public_field_disabled_for_is_confidential_species(self):
        report = make(Report, actual_species__is_confidential=True, point=ORIGIN)
        form = ManagementForm(instance=report, data={
            # even though this was submitted with a True-y value, the form
            # should override it so it is always False
            "is_public": 1,
            "edrr_status": 0,
            "category": make(Category).pk,
        })
        self.assertTrue(form.fields['is_public'].widget.attrs['disabled'])
        self.assertTrue(form.is_valid())
        form.save()
        # even though the data spoofed the is_public flag as True, it should still be false
        self.assertFalse(report.is_public)

    def test_settings_the_actual_species_to_a_confidential_species_raises_an_error_if_the_report_is_public_too(self):
        report = make(Report, point=ORIGIN)
        form = ManagementForm(instance=report, data={
            "actual_species": make(Species, is_confidential=True).pk,
            "is_public": 1,
            "edrr_status": 0,
            "category": make(Category).pk,
        })
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error(NON_FIELD_ERRORS, "species-confidential"))


class InviteFormTest(UserMixin, ServiceTestCaseMixin, TestCase):

    def test_clean_emails(self):
        # test a few valid emails
        form = InviteForm({
            "emails": "foo@pdx.edu,bar@pdx.edu  ,  fog@pdx.edu,foo@pdx.edu"
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(sorted(form.cleaned_data['emails']), sorted(["foo@pdx.edu", "bar@pdx.edu", "fog@pdx.edu"]))

        # test blank
        form = InviteForm({
            "emails": ""
        })
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error("emails"))

        # test invalid email
        form = InviteForm({
            "emails": "invalid@@pdx.ads"
        })
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error("emails"))

        # test valid and invalid
        form = InviteForm({
            "emails": "valid@pdx.edu, invalid@@pdx.ads"
        })
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error("emails"))
        self.assertIn("invalid@@", str(form.errors))

    def test_save(self):
        inviter = self.create_user()
        report = make(Report, point=ORIGIN)

        form = InviteForm({
            'emails': 'foo@pdx.edu',
            'body': 'body',
        })
        self.assertTrue(form.is_valid())
        invite_report = form.save(inviter, report)
        self.assertEqual(invite_report.invited, ['foo@pdx.edu'])
        self.assertEqual(invite_report.already_invited, [])

        form = InviteForm({
            'emails': 'foo@pdx.edu, bar@pdx.edu',
            'body': 'body',
        })
        self.assertTrue(form.is_valid())
        invite_report = form.save(inviter, report)
        self.assertEqual(invite_report.invited, ['bar@pdx.edu'])
        self.assertEqual(invite_report.already_invited, ['foo@pdx.edu'])
