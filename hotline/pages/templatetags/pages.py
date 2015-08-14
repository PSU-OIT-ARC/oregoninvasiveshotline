from django import template
from django.contrib.flatpages.models import FlatPage
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe

from .. import HIDDEN_PAGE_PREFIX

register = template.Library()


@register.simple_tag(takes_context=True)
def getcontent(context, url, default=None):
    url = "%s%s/" % (HIDDEN_PAGE_PREFIX, url)

    try:
        page = FlatPage.objects.get(url=url)
    except FlatPage.DoesNotExist:
        page = FlatPage(url=url, content=default, title=url.strip("/"))
        if default is not None:
            page.save()
            page.sites = Site.objects.all()
            page.save()

    if context.get('user', None) and getattr(context['user'], "is_staff", False) and page.pk:
        edit_url = reverse("pages-edit", args=[page.pk]) + "?next=" + getattr(context.get("request"), "get_full_path", lambda: "")()
        page.content += "<a class='getcontent-edit' href='%s'>Edit</a>" % edit_url

    return mark_safe(page.content)
