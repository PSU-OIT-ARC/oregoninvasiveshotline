from django.conf.urls import include, url

from . import views


urlpatterns = [
    url(r'^list/?$', views.list_, name='pages-list'),
    url(r'^create/?$', views.edit, name='pages-create'),
    url(r'^edit/(?P<page_id>\d+)?$', views.edit, name='pages-edit'),
    url(r'^delete/(?P<page_id>\d+)?$', views.delete, name='pages-delete'),
]
