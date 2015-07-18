from django import forms
from django.conf import settings
from django.forms import ModelForm
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from hotline.species.models import Species, Category, Severity