from django import forms
from django.utils.translation import ugettext_lazy as _

from oregoninvasiveshotline.users.models import User

from .models import UserNotificationQuery


class UserNotificationQueryForm(forms.ModelForm):

    class Meta:
        model = UserNotificationQuery
        fields = ['name']


class UserSubscriptionAdminForm(forms.ModelForm):

    class Meta:
        model = UserNotificationQuery
        fields = ('user', 'name', 'query')
        labels = {
            'name': _('Subscription Name'),
        }
        help_texts = {
            'name': _('''
                Note: Changing the owner of a subscription will notify the user
                that you have assigned a subscription to them'''),
            'query': _('''
                Altering the query string is disabled. Try creating a new
                subscription by clicking "Search Reports" and subscribing to
                a new search'''),
        }
        querysets = {
            'user': User.objects.filter(is_active=True),
        }
        widgets = {
            'name': forms.widgets.TextInput(attrs={
                'placeholder': 'For easier review, give the subscription a name. For example, "Mammals in Clark County"',
            }),
            'query': forms.widgets.TextInput(attrs={
                'readonly': True,
            }),
        }


class UserSubscriptionDeleteForm(forms.Form):

    subscriptions = forms.ModelMultipleChoiceField(
        required=True, widget=forms.CheckboxSelectMultiple, queryset=None)

    def __init__(self, *args, user, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        initial = UserNotificationQuery.objects.filter(user=user)
        self.fields['subscriptions'].queryset = initial

    def iter_items(self):
        subscriptions = list(self['subscriptions'])
        for model, choice in zip(self.fields['subscriptions'].queryset, subscriptions):
            yield model, choice

    def save(self, *args, **kwargs):
        for field in self.cleaned_data['subscriptions']:
            field.delete()
