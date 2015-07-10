import tempfile
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
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

    def test_images_are_saved_to_comment(self):
        user = make(User, is_manager=False, is_staff=False)
        report = make(Report)
        form = CommentForm({
            "body": "hi",
        }, user=user, report=report)
        self.assertTrue(form.is_valid())
        form.save()
        with tempfile.NamedTemporaryFile() as f:
            form.cleaned_data['images'] = [SimpleUploadedFile(f.name, f.read())]
            with patch("hotline.comments.forms.forms.ModelForm.save"):
                form.save()

        self.assertEqual(Image.objects.filter(comment=form.instance).count(), 1)
