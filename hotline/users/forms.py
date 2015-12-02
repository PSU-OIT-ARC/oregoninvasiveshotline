from django import forms
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from haystack.forms import SearchForm

from hotline.utils import resize_image

from .search_indexes import UserIndex
from .models import User


class UserSearchForm(SearchForm):
    is_manager = forms.BooleanField(initial=True, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset().order_by("last_name", "first_name")
        if self.cleaned_data.get('is_manager'):
            queryset = queryset.filter(is_active=True)

        return queryset


class LoginForm(forms.Form):
    """
    This form allows users to login via the authentication_url
    """
    email = forms.EmailField()

    def clean_email(self):
        email = self.cleaned_data['email']
        if not User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with that email address does not exist")

        return email

    def save(self, request):
        """
        Send an email to the user with a link that allows them to login
        """
        user = User.objects.get(email__iexact=self.cleaned_data['email'])
        send_mail(
            "OregonInvasivesHotline.org - Login Link",
            render_to_string("users/_login.txt", {
                "user": user,
                "url": user.get_authentication_url(request, next=reverse("users-home"))
            }),
            "noreply@pdx.edu",
            [user.email]
        )


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            'email',
            'first_name',
            'last_name',
            'phone',
            'biography',
            'affiliations',
            'photo',
            'is_active',
            'is_staff',
        )

    def __init__(self, *args, user, **kwargs):
        """
        `user` is the person using the form, not the person the form is actually going edit
        """
        super().__init__(*args, **kwargs)

        # add a password field to the form if the user is being created. This
        # allows an admin to set an initial password
        if self.instance.pk is None:
            self.fields['password'] = forms.CharField(widget=forms.widgets.PasswordInput)

        if user.pk == self.instance.pk:
            # these fields you shouldn't be allowed to alter if you're editing
            # yourself, for safety reasons
            self.fields.pop("is_active")
            self.fields.pop("is_staff")

        if not user.is_staff:
            # only staff members can control the is_staff field
            self.fields.pop("is_staff", None)

        # only active users should be allowed to fill out these fields
        if not user.is_active:
            self.fields.pop("photo")
            self.fields.pop("biography")
            self.fields.pop("affiliations")

        # stupid chrome...http://stackoverflow.com/a/30976223/2733517
        for name, field in self.fields.items():
            field.widget.attrs['autocomplete'] = "new-password"

    def save(self, *args, **kwargs):
        """
        Save the form, and set the password, if it has been set
        """
        password = self.cleaned_data.pop("password", None)
        if password is not None:
            self.instance.set_password(password)

        instance = super().save(*args, **kwargs)

        # if we got a new photo resize it and convert it to a png
        if self.cleaned_data.get("photo"):
            output_path = instance.photo.path + ".png"
            resize_image(instance.photo.path, output_path, width=256, height=256)
            self.instance.photo = instance.photo.name + ".png"
            self.instance.save()

        return instance
