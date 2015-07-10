import json
import tempfile
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse
from django.test import TestCase
from model_mommy.mommy import make, prepare

from hotline.comments.models import Comment
from hotline.images.models import Image
from hotline.species.models import Category, Species
from hotline.users.models import User

from .forms import ReportForm
from .models import Invite, Report


class ReportTest(TestCase):
    def test_species(self):
        reported_species = make(Species)
        actual_species = make(Species)

        self.assertEqual(make(Report, actual_species=None, reported_species=reported_species).species, reported_species)
        self.assertEqual(make(Report, actual_species=actual_species, reported_species=reported_species).species, actual_species)
        self.assertEqual(make(Report, actual_species=None, reported_species=None).species, None)

    def test_category(self):
        reported_species = make(Species)
        actual_species = make(Species)

        self.assertEqual(
            make(Report, actual_species=None, reported_species=None, reported_category=reported_species.category).category,
            reported_species.category
        )
        self.assertEqual(make(Report, actual_species=actual_species, reported_species=reported_species).category, actual_species.category)

    def test_is_misidentified(self):
        reported_species = make(Species)
        actual_species = make(Species)

        # if they didn't identify the species, then it can't be misidentified
        self.assertEqual(make(Report, actual_species=None, reported_species=None).is_misidentified, False)
        # if the reported and actual species are the same, it's not misidentified
        self.assertEqual(make(Report, actual_species=actual_species, reported_species=actual_species).is_misidentified, False)
        # if the species differ, then it is misidentified
        self.assertEqual(make(Report, actual_species=actual_species, reported_species=reported_species).is_misidentified, True)


class CreateViewTest(TestCase):
    def test_get(self):
        c1 = make(Category)
        c2 = make(Category)
        s1 = make(Species, category=c1)
        s2 = make(Species, category=c1)
        make(Species, category=c2)
        response = self.client.get(reverse("reports-create"))
        self.assertEqual(response.status_code, 200)
        # make sure the category_id_to_species_id gets populated
        self.assertEqual(set(json.loads(response.context['category_id_to_species_id'])[str(c1.pk)]), set([s1.pk, s2.pk]))

    def test_post(self):
        data = {
            "location": "back ally",
            "point": "SRID=4326;POINT(-6.7236328125 8.61328125)",
            "reported_category": make(Category).pk,
            "description": "It was HUGE",
            "questions": "question",
            "prefix": "Dr.",
            "first_name": "John",
            "last_name": "Evil",
            "suffix": "PHD",
            "email": "john@example.com",
        }

        response = self.client.post(reverse("reports-create"), data)
        self.assertRedirects(response, reverse("reports-detail", args=[Report.objects.order_by("-pk").first().pk]))
        session = self.client.session
        # make sure the report_ids in the session gets updated
        self.assertIn(Report.objects.order_by("-pk").first().pk, session['report_ids'])


class DetailViewTest(TestCase):
    def test_anonymous_users_cant_view_non_public_reports(self):
        report = make(Report, is_public=False)
        response = self.client.get(reverse("reports-detail", args=[report.pk]))
        self.assertEqual(response.status_code, 403)

    def test_anonymous_users_with_proper_session_state_can_view_non_public_reports(self):
        report = make(Report, is_public=False, created_by__is_active=False)
        session = self.client.session
        session['report_ids'] = [report.pk]
        session.save()
        response = self.client.get(reverse("reports-detail", args=[report.pk]))
        self.assertEqual(response.status_code, 200)

    def test_anonymous_users_with_proper_session_state_should_be_prompted_to_login_if_the_report_was_created_by_an_active_user(self):
        report = make(Report, is_public=False, created_by__is_active=True)
        session = self.client.session
        session['report_ids'] = [report.pk]
        session.save()
        response = self.client.get(reverse("reports-detail", args=[report.pk]))
        self.assertRedirects(response, reverse("login") + "?next=" + reverse("reports-detail", args=[report.pk]))

    def test_comment_form_dependent_on_the_can_create_comment_check(self):
        report = make(Report, is_public=True)
        with patch("hotline.reports.views.can_create_comment", return_value=True) as perm_check:
            with patch("hotline.reports.views.CommentForm"):
                response = self.client.get(reverse("reports-detail", args=[report.pk]))
        self.assertTrue(perm_check.called)
        self.assertNotEqual(None, response.context['form'])

        with patch("hotline.reports.views.can_create_comment", return_value=False) as perm_check:
            with patch("hotline.reports.views.CommentForm"):
                response = self.client.get(reverse("reports-detail", args=[report.pk]))
        self.assertTrue(perm_check.called)
        self.assertEqual(None, response.context['form'])

    def test_display_of_comments_for_each_permission_level(self):
        report = make(Report, is_public=True, created_by__is_active=False)
        public = make(Comment, report=report, visibility=Comment.PUBLIC)
        protected = make(Comment, report=report, visibility=Comment.PROTECTED)
        private = make(Comment, report=report, visibility=Comment.PRIVATE)

        # anonymous users should only be able to see public comments
        response = self.client.get(reverse("reports-detail", args=[report.pk]))
        self.assertIn(public.body, response.content.decode())
        self.assertNotIn(protected.body, response.content.decode())
        self.assertNotIn(private.body, response.content.decode())

        # the person who made the report should be allowed to see PROTECTED and PUBLIC comments
        session = self.client.session
        session['report_ids'] = [report.pk]
        session.save()
        response = self.client.get(reverse("reports-detail", args=[report.pk]))
        self.assertIn(public.body, response.content.decode())
        self.assertIn(protected.body, response.content.decode())
        self.assertNotIn(private.body, response.content.decode())

        # staffers should see everything
        user = prepare(User, is_manager=True)
        user.set_password("foo")
        user.save()
        self.client.login(email=user.email, password="foo")
        response = self.client.get(reverse("reports-detail", args=[report.pk]))
        self.assertIn(public.body, response.content.decode())
        self.assertIn(protected.body, response.content.decode())
        self.assertIn(private.body, response.content.decode())

        # invited experts should see everything
        self.client.logout()
        user = prepare(User, is_manager=False, is_staff=False, is_active=True)
        user.set_password("foo")
        user.save()
        self.client.login(email=user.email, password="foo")
        make(Invite, user=user, report=report)
        response = self.client.get(reverse("reports-detail", args=[report.pk]))
        self.assertIn(public.body, response.content.decode())
        self.assertIn(protected.body, response.content.decode())
        self.assertIn(private.body, response.content.decode())

    def test_create_comment(self):
        report = make(Report)
        user = prepare(User, is_manager=True)
        user.set_password("foo")
        user.save()
        self.client.login(email=user.email, password="foo")
        data = {
            "body": "foo",
            "visibility": Comment.PUBLIC,
        }
        response = self.client.post(reverse("reports-detail", args=[report.pk]), data)
        self.assertRedirects(response, reverse("reports-detail", args=[report.pk]))
        self.assertEqual(1, Comment.objects.filter(report=report).count())


class ReportFormTest(TestCase):
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
        pre_count = User.objects.count()
        with patch("hotline.reports.forms.forms.ModelForm.save") as save:
            form.save()
            self.assertTrue(save.called)

        self.assertEqual(User.objects.count(), pre_count+1)
        user = User.objects.last()
        self.assertEqual(user.email, "foo@example.com")
        self.assertEqual(user.is_active, False)
        self.assertEqual(user.last_name, "Bar")
        self.assertEqual(user.pk, form.instance.created_by.pk)

        # the user already exists, so no record should be created
        pre_count = User.objects.count()
        form = ReportForm({
            "email": "FOO@eXaMplE.com",  # using odd casing here to ensure `icontains` is used
        })
        self.assertFalse(form.is_valid())
        pre_count = User.objects.count()
        with patch("hotline.reports.forms.forms.ModelForm.save") as save:
            form.save()
            self.assertTrue(save.called)

        self.assertEqual(User.objects.count(), pre_count)
        self.assertEqual(user.pk, form.instance.created_by.pk)

    def test_images_are_saved_to_report(self):
        form = ReportForm({
            "email": "foo@example.com",
            "first_name": "Foo",
            "last_name": "Bar",
        })
        self.assertFalse(form.is_valid())
        report = make(Report)
        form.instance = report
        with tempfile.NamedTemporaryFile() as f:
            form.cleaned_data['images'] = [SimpleUploadedFile(f.name, f.read())]
            with patch("hotline.reports.forms.forms.ModelForm.save"):
                form.save()

        self.assertEqual(Image.objects.filter(report=report).count(), 1)

    def test_comment_is_added(self):
        form = ReportForm({
            "email": "foo@example.com",
            "first_name": "Foo",
            "last_name": "Bar",
            "questions": "hello world",
        })
        self.assertFalse(form.is_valid())
        report = make(Report)
        form.instance = report
        with patch("hotline.reports.forms.forms.ModelForm.save"):
            form.save()

        self.assertEqual(Comment.objects.get(report=report).body, "hello world")
