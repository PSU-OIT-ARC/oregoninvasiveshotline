from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render

from arcutils.db import will_be_deleted_with

from oregoninvasiveshotline.perms import permissions
from oregoninvasiveshotline.utils import get_tab_counts

from .forms import UserNotificationQueryForm, UserSubscriptionAdminForm, UserSubscriptionDeleteForm
from .models import UserNotificationQuery


@permissions.is_active
def create(request):
    query = request.GET.copy()
    query.pop('tabs', None)
    query = query.urlencode()
    instance = UserNotificationQuery(user=request.user, query=query)
    if request.method == 'POST':
        form = UserNotificationQueryForm(request.POST, instance=instance)
        if form.is_valid():
            instance = form.save()
            messages.success(request, 'New search subscription "{0.name}" added'.format(instance))
            return HttpResponseRedirect(reverse('reports-list') + '?' + request.GET.urlencode())
    else:
        form = UserNotificationQueryForm(instance=instance)
    return render(request, 'notifications/create.html', {
        'form': form,
    })


@permissions.is_staff
def edit(request, subscription_id):
    subscription = UserNotificationQuery.objects.get(pk=subscription_id)
    if request.method == 'POST':
        form = UserSubscriptionAdminForm(request.POST, instance=subscription)
        old_owner = subscription.user
        if form.is_valid():
            instance = form.save()
            new_owner = instance.user
            if new_owner != old_owner:
                # If the owner has changed, send the new owner an email updating
                # them of their newly assigned subscription
                instance.notify_new_owner(subscription, request)
                messages.success(request, 'Subscription updated. {0.full_name} has been notified'.format(new_owner))
            else:
                messages.success(request, 'Subscription updated')
            return redirect('notifications-all')
    else:
        form = UserSubscriptionAdminForm(instance=subscription)
    return render(request, 'notifications/edit.html', {
        'form': form,
    })


@permissions.is_active
def list_(request):
    user = request.user
    report_ids = request.session.get('report_ids', [])
    tab_context = get_tab_counts(user, report_ids)
    if request.method == 'POST':
        form = UserSubscriptionDeleteForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Saved')
            return redirect('notifications-list')
    else:
        form = UserSubscriptionDeleteForm(user=request.user)
    context = {'form': form}
    context.update(tab_context)
    return render(request, 'notifications/list.html', context)


@permissions.is_staff
def all(request):
    subscriptions = UserNotificationQuery.objects.all()

    active_page = request.GET.get('page')
    paginator = Paginator(subscriptions, settings.ITEMS_PER_PAGE)

    try:
        subscriptions = paginator.page(active_page)
    except PageNotAnInteger:
        subscriptions = paginator.page(1)
    except EmptyPage:
        subscriptions = paginator.page(paginator.num_pages)

    return render(request, 'notifications/all.html', {
        'subscriptions': subscriptions,
    })


@permissions.is_staff()
def delete(request, subscription_id):
    subscription = get_object_or_404(UserNotificationQuery, pk=subscription_id)
    if request.method == 'POST':
        subscription.delete()
        messages.success(request, 'Subscription deleted!')
        return redirect('notifications-all')

    related_objects = list(will_be_deleted_with(subscription))

    return render(request, 'delete.html', {
        'object': subscription,
        'will_be_deleted_with': related_objects,
    })
