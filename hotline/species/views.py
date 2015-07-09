from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from hotline.species.models import Species, Category, Severity
from hotline.species.forms import CreateSpeciesForm, CreateCategoryForm
from django.contrib import messages
from django.core.urlresolvers import reverse

def admin_panel(request):
    
    if request.method == "POST":
        
        species_form = CreateSpeciesForm(request.POST)
        category_form = CreateCategoryForm(request.POST)
        
        if species_form.is_valid():
            messages.success(request, "Species successfully added.")
            species_form.save()
            return HttpResponseRedirect(reverse('admin_panel'))
        
        if category_form.is_valid():
            messages.success(request, "Category successfully added.")
            category_form.save()
            return HttpResponseRedirect(reverse('admin_panel'))
   
        
    
    species_form = CreateSpeciesForm()
    category_form = CreateCategoryForm()
    
    context = {'species_form': species_form, 'category_form': category_form}
    
    return render(request, 'species/admin_panel.html', context)