from django import forms
from django.conf import settings
from django.forms import ModelForm
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from hotline.species.models import Species, Category, Severity


class CreateSpeciesForm(forms.Form):
    species_name = forms.CharField(required=True)
    
    def save(self):
        species_name = self.cleaned_data.get('species_name')
        
        new_species = Species(name=species_name, scientific_name=species_name, remedy=species_name, resources= species_name )

        new_species.save()
        

class edit_species(forms.Form):
    stuff = "stuff"
    
class delete_species(forms.Form):
    stuff = "stuff"
    
class create_severity(forms.Form):
    stuff = "stuff"

class edit_severity(forms.Form):
    stuff = "stuff"
    
class delete_severity(forms.Form):
    stuff = "stuff"
    
class CreateCategoryForm(forms.Form):
    category_name = forms.CharField(required=True)
    
    def save(self):
        category_name = self.cleaned_data.get('category_name')
        
        new_category = Category(name=category_name)

        new_category.save()

class edit_category(forms.Form):
    stuff = "stuff"
    
class delete_category(forms.Form):
    stuff = "stuff"

