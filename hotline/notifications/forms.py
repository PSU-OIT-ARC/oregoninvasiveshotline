from django import forms

from .models import UserNotificationQuery


class UserNotificationQueryForm(forms.ModelForm):
    class Meta:
        model = UserNotificationQuery
        fields = ['name']
