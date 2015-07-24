from django import forms
from django.core.mail import send_mass_mail
from django.db.models import Q
from django.template.loader import render_to_string

from hotline.reports.models import Invite
from hotline.reports.perms import can_adjust_visibility
from hotline.users.models import User

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

    def save(self, *args, request, **kwargs):
        is_new = self.instance.pk is None
        to_return = super().save(*args, **kwargs)
        if is_new:
            # when a new comment is made, send out an email to the relevant
            # people
            # any managers or staff who commented on this should get notified
            to_notify = set(
                Comment.objects.filter(report=self.instance.report).filter(
                    Q(created_by__is_staff=True) | Q(created_by__is_manager=True)
                ).values_list(
                    "created_by__email",
                    flat=True
                )
            )
            # whoever claimed the report should get notified
            if self.instance.report.claimed_by:
                to_notify.add(self.instance.report.claimed_by.email)

            # all invited experts should be notified
            to_notify |= set(Invite.objects.filter(report=self.instance.report).values_list("user__email", flat=True))

            # notify the person who submitted the report if it is PUBLIC or PROTECTED
            if self.instance.visibility in [Comment.PROTECTED, Comment.PUBLIC]:
                to_notify.add(self.instance.report.created_by.email)

            # don't notify yourself
            to_notify.discard(self.instance.created_by.email)

            letters = []
            for email in to_notify:
                letters.append((
                    "OregonInvasivesHotline.org - New Comment on Report",
                    render_to_string("reports/_new_comment.txt", {
                        "user": self.instance.created_by,
                        "body": self.instance.body,
                        "url": User(email=email).get_authentication_url(request, next=self.instance.get_absolute_url())
                    }),
                    "noreply@pdx.edu",
                    [email]
                ))

            send_mass_mail(letters)

        return to_return
