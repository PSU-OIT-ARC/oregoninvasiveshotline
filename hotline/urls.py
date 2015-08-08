from django.conf import settings
from django.conf.urls import include, patterns, url
from django.conf.urls.static import static
from django.contrib import admin
from django.views.generic import TemplateView

from .comments import views as comments
from .notifications import views as notifications
from .reports import views as reports
from .users import views as users
from .species import views as species
from .views import home

admin.autodiscover()

urlpatterns = patterns(
    '',
    # Examples:
    # url(r'^$', 'hotline.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    # the django admin interface is always nice to have
    url(r'^admin/', include(admin.site.urls)),
    # the homepage goes straight to a template. But you may want to change this
    # into a normal view function
    url(r'^$', TemplateView.as_view(template_name="home.html"), name='home'),
    url(r'^adminpanel/?$', species.admin_panel, name='admin_panel'),
    url(r'^adminpanel/species-list/?$', species.SpeciesList.as_view(), name='species_list'),
    url(r'^adminpanel/species-detail/(?P<pk>[0-9]+)/$', species.SpeciesDetailView.as_view(), name='species_detail'),
    url(r'^adminpanel/species-delete/(?P<pk>[0-9]+)/$', species.SpeciesDeleteView.as_view(), name='species_delete'),
    url(r'^adminpanel/species-create/?$', species.SpeciesCreateView.as_view(), name='species_create'),

    url(r'^adminpanel/category-list/?$', species.CategoryList.as_view(), name='category_list'),
    url(r'^adminpanel/category-detail/(?P<pk>[0-9]+)/$', species.CategoryDetailView.as_view(), name='category_detail'),
    url(r'^adminpanel/category-delete/(?P<pk>[0-9]+)/$', species.CategoryDeleteView.as_view(), name='category_delete'),
    url(r'^adminpanel/category-create/?$', species.CategoryCreateView.as_view(), name='category_create'),

    url(r'^adminpanel/severity-list/?$', species.SeverityList.as_view(), name='severity_list'),
    url(r'^adminpanel/severity-detail/(?P<pk>[0-9]+)/$', species.SeverityDetailView.as_view(), name='severity_detail'),
    url(r'^adminpanel/severity-delete/(?P<pk>[0-9]+)/$', species.SeverityDeleteView.as_view(), name='severity_delete'),
    url(r'^adminpanel/severity-create/?$', species.SeverityCreateView.as_view(), name='severity_create'),
    url(r'^$', home, name="home"),
    url(r'^reports/create/?$', reports.create, name='reports-create'),
    url(r'^reports/detail/(?P<report_id>\d+)?$', reports.detail, name='reports-detail'),
    url(r'^reports/claim/(?P<report_id>\d+)?$', reports.claim, name='reports-claim'),
    url(r'^reports/list/?$', reports.list_, name='reports-list'),

    url(r'^comments/edit/(?P<comment_id>\d+)?$', comments.edit, name='comments-edit'),

    url(r'^notifications/create/?$', notifications.create, name='notifications-create'),

    url(r'^users/home/?$', users.home, name='users-home'),
    url(r'^users/detail/(?P<pk>[0-9]+)/$', users.detail.as_view(), name='users-detail'),
    url(r'^users/list/?$', users.list_, name='users-list'),
    url(r'^users/create/?$', users.create, name='users-create'),
    url(r'^users/edit/(?P<user_id>\d+)/?$', users.edit, name='users-edit'),
    url(r'^users/delete/(?P<user_id>\d+)/?$', users.delete, name='users-delete'),
    url(r'^users/authenticate/?$', users.authenticate, name='users-authenticate'),
    url(r'^users/avatar/(?P<user_id>\d+)/?$', users.avatar, name='users-avatar'),

    # these url routes are useful for password reset functionality and logging in and out
    # https://github.com/django/django/blob/master/django/contrib/auth/urls.py
    url(r'^login/$', users.login, name='login'),
    url(r'', include('django.contrib.auth.urls')),

    # these routes allow you to masquerade as a user, and login as them from the command line
    url(r'^cloak/', include('cloak.urls'))
)

if settings.DEBUG:  # pragma: no cover
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static("htmlcov", document_root="htmlcov", show_indexes=True)
