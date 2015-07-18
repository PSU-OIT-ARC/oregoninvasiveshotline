from django.core.urlresolvers import reverse
from django.test import TestCase
from model_mommy.mommy import make

from hotline.images.models import Image
from hotline.reports.models import Report
from hotline.users.models import User

from .forms import CommentForm
from .models import Comment


class CommentFormTest(TestCase):
    def test_report_and_created_by_initialized_for_new_comment(self):
        user = make(User)
        report = make(Report)
        form = CommentForm(user=user, report=report)
        self.assertEqual(form.instance.created_by, user)
        self.assertEqual(form.instance.report, report)

    def test_visibility_field_removed_for_non_experts(self):
        user = make(User, is_manager=False, is_staff=False)
        report = make(Report)
        form = CommentForm(user=user, report=report)
        self.assertNotIn("visibility", form.fields)
        self.assertEqual(form.instance.visibility, Comment.PROTECTED)


class CommentEditViewTest(TestCase):
    def test_get(self):
        report = make(Report, created_by__is_active=False)
        session = self.client.session
        session['report_ids'] = [report.pk]
        session.save()
        comment = make(Comment, report=report, created_by=report.created_by)
        response = self.client.get(reverse("comments-edit", args=[comment.pk]))
        self.assertEqual(response.status_code, 200)

    def test_anonymous_users_are_forced_to_login(self):
        comment = make(Comment)
        response = self.client.get(reverse("comments-edit", args=[comment.pk]))
        self.assertEqual(response.status_code, 302)

    def test_not_allowed_to_edit(self):
        report = make(Report)
        comment = make(Comment, report=report)
        user = report.created_by
        user.set_password("foo")
        user.save()
        self.client.login(email=user.email, password="foo")
        response = self.client.get(reverse("comments-edit", args=[comment.pk]))
        self.assertEqual(response.status_code, 403)

    def test_post(self):
        report = make(Report, created_by__is_active=False)
        session = self.client.session
        session['report_ids'] = [report.pk]
        session.save()
        comment = make(Comment, report=report, created_by=report.created_by)
        data = {
            "body": "hello",
            "form-TOTAL_FORMS": "0",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
        }
        response = self.client.post(reverse("comments-edit", args=[comment.pk]), data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Comment.objects.get(pk=comment.pk).body, "hello")

    def test_post_with_image(self):
        # make a report for a user who is allowed to login and control
        # visibility
        report = make(Report, created_by__is_active=True, created_by__is_staff=True)
        user = report.created_by
        user.set_password("foo")
        user.save()
        self.client.login(email=user.email, password="foo")

        comment = make(Comment, report=report, created_by=report.created_by)
        data = {
            "body": "hello",
            "visibility": Comment.PUBLIC,
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-image_data_uri": "data:image/gif;base64,R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs=",
            "form-0-name": "Hello world",
            "form-0-visibility": Image.PUBLIC,
        }
        response = self.client.post(reverse("comments-edit", args=[comment.pk]), data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Comment.objects.get(pk=comment.pk).body, "hello")
        self.assertEqual(Image.objects.filter(comment=comment, visibility=Image.PUBLIC).count(), 1)
