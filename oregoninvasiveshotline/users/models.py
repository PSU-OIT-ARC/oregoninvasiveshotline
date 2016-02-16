from urllib.parse import urlencode

from django.contrib.auth.models import AbstractBaseUser, UserManager
from django.core.signing import Signer
from django.core.urlresolvers import reverse
from django.db import models


class User(AbstractBaseUser):

    class Meta:
        db_table = 'user'
        ordering = ['first_name', 'last_name']

    USERNAME_FIELD = 'email'

    objects = UserManager()

    user_id = models.AutoField(primary_key=True)
    email = models.EmailField(max_length=255, unique=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=255, default="", blank=True)
    prefix = models.CharField(max_length=255)
    suffix = models.CharField(max_length=255)
    date_joined = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, blank=True, verbose_name="Is Manager (can login and manage reports)")
    is_staff = models.BooleanField(default=False, blank=True, verbose_name="Is Admin (can do anything)")
    affiliations = models.TextField(blank=True)
    biography = models.TextField(blank=True)
    photo = models.ImageField(upload_to="images", blank=True)
    has_completed_ofpd = models.BooleanField(default=False, blank=True, verbose_name="""
        Check this box if you have completed the Oregon
        Forest Pest Detector training, offered by Oregon State
        Extension.""")


    def get_authentication_url(self, request, next=None):
        signer = Signer("user-authentication")
        sig = signer.sign(self.email)
        querystring = urlencode({
            "sig": sig,
            "next": next or '',
        })
        return request.build_absolute_uri(reverse("users-authenticate")) + "?" + querystring

    @classmethod
    def authenticate(cls, sig):
        signer = Signer("user-authentication")
        email = signer.unsign(sig)
        return cls.objects.get(email=email)

    @property
    def full_name(self):
        """A nicer way to get the user's full name."""
        return self.get_full_name()

    def get_full_name(self):
        if self.first_name:
            name = self.first_name
            if self.last_name:
                name = '{name} {self.last_name}'.format_map(locals())
            return name
        return self.email

    def get_short_name(self):
        if self.first_name:
            name = self.first_name
            if self.last_name:
                last_initial = self.last_name[0]
                name = '{name} {last_initial}.'.format_map(locals())
            return name
        return self.email

    def get_proper_name(self):
        if self.first_name:
            parts = (self.prefix, self.first_name, self.last_name)
            name = ' '.join(p for p in parts if p)
            if self.suffix:
                name = '{name}, {self.suffix}'.format_map(locals())
            return name
        return self.email

    def get_avatar_url(self):
        if self.photo:
            return self.photo.url
        return reverse("users-avatar", args=[self.pk])

    # we don't need granular permissions; all staff will have access to
    # everything
    def has_perm(self, perm, obj=None):
        return self.is_staff

    def has_module_perms(self, app_label):
        return self.is_staff

    def can_cloak_as(self, other_user):
        """
        This method is used by the `cloak` package to determine if a user is
        allowed to cloak as another user
        """
        return self.is_staff

    def __str__(self):
        return self.get_full_name()
