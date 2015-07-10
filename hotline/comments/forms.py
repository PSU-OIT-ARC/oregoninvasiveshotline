from django import forms

from hotline.images.fields import MultiFileField
from hotline.images.models import Image
from hotline.reports.models import Invite

from .models import Comment


class CommentForm(forms.ModelForm):
    images = MultiFileField(required=False)

    class Meta:
        model = Comment
        fields = [
            'body',
            'visibility',
        ]

    def __init__(self, *args, user, report, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['body'].label = ""
        self.fields['body'].widget.attrs['placeholder'] = "Add a comment..."
        self.fields['body'].widget.attrs['rows'] = 3

        if self.instance.pk is None:
            self.instance.report = report
            self.instance.created_by = user

        if not (user.is_elevated or Invite.objects.filter(user=user, report=report).exists()):
            self.fields.pop('visibility')
            self.instance.visibility = Comment.PROTECTED

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # now save every image that was attached to this comment
        for image in self.cleaned_data.get('images', []):
            i = Image(image=image, created_by=self.instance.created_by, comment=self.instance)
            i.save()

        return self.instance
