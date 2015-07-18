from django import forms

from hotline.reports.perms import can_adjust_visibility

from .models import Comment


class CommentForm(forms.ModelForm):
    SUBMIT_FLAG = "COMMENT"

    class Meta:
        model = Comment
        fields = [
            'body',
            'visibility',
        ]

    def __init__(self, *args, user, report, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['body'].label = ""
        self.fields['body'].widget.attrs['placeholder'] = "Comment body..."
        self.fields['body'].widget.attrs['rows'] = 3

        if self.instance.pk is None:
            self.instance.report = report
            self.instance.created_by = user

        if not can_adjust_visibility(user, report):
            self.fields.pop('visibility')
            self.instance.visibility = Comment.PROTECTED
