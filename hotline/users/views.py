from arcutils import will_be_deleted_with
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.core.signing import BadSignature
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from hotline.reports.models import Invite, Report

from .forms import UserForm
from .models import User
from .perms import can_list_users, permissions


def authenticate(request):
    sig = request.GET.get("sig", "")
    try:
        user = User.authenticate(sig)
    except BadSignature:
        messages.error(request, "Bad Signature")
        return redirect("home")

    if user.is_active or Invite.objects.filter(user=user).exists():
        user.backend = settings.AUTHENTICATION_BACKENDS[0]
        login(request, user)

    # populate the report_ids session variable with all the reports the user made
    request.session['report_ids'] = list(Report.objects.filter(created_by=user).values_list('pk', flat=True))

    return redirect(request.GET.get("next") or settings.LOGIN_REDIRECT_URL)


def home(request):
    """
    Just redirect to the detail view for the user. This page exists solely
    because settings.LOGIN_REDIRECT_URL needs to redirect to a "simple" URL
    (i.e. we can't use variables in the URL)
    """
    user = request.user
    if user.is_anonymous() and not request.session.get('report_ids'):
        messages.error(request, "You are not allowed to be here")
        return redirect("home")

    invited_to = [invite.report for invite in Invite.objects.filter(user_id=user.pk).select_related("report")]
    reported = Report.objects.filter(Q(pk__in=request.session.get("report_ids", [])) | Q(created_by_id=user.pk))
    open_and_claimed = Report.objects.filter(claimed_by_id=user.pk, is_public=False, is_archived=False).exclude(claimed_by=None)

    unclaimed_reports = []
    if user.is_authenticated() and user.is_elevated:
        unclaimed_reports = Report.objects.filter(claimed_by=None, is_public=False, is_archived=False)

    return render(request, "users/home.html", {
        "invited_to": invited_to,
        "reported": reported,
        "open_and_claimed": open_and_claimed,
        "unclaimed_reports": unclaimed_reports,
    })


@permissions.can_view_user
def detail(request, user_id):
    """
    A nice homepage for user the user. By passing the user_id as a parameter,
    this allows admins to view the user's detail page, without having to
    masquerade as them.
    """
    user = get_object_or_404(User, pk=user_id)

    return render(request, "users/detail.html", {
        # we use the name "the_user" to avoid clashing with the authentication
        # context processor which populates the "user" template variable
        "the_user": user,
        # we hide the masquerade button if the user can't do it, or they are
        # looking at their own detail page
        "can_cloak": request.user.can_cloak_as(user) and user.pk != request.user.pk
    })


@permissions.can_list_users
def list_(request):
    """
    List out all the users in the system
    """
    users = User.objects.all()
    paginator = Paginator(users, settings.ITEMS_PER_PAGE)
    page = request.GET.get('page')
    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        users = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        users = paginator.page(paginator.num_pages)

    return render(request, "users/list.html", {
        "users": users,
    })


@permissions.can_delete_user
def delete(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.method == "POST":
        user.delete()
        messages.success(request, "User deleted!")
        return redirect("users-list")

    related_objects = will_be_deleted_with(user)

    return render(request, "users/delete.html", {
        # we don't call this template variable "user" because that collides
        # with the "user" variable which references the currently logged in
        # user
        "object": user,
        "related_objects": related_objects,
    })


@permissions.can_create_user
def create(request):
    """
    Create a new user
    """
    return _edit(request)


@permissions.can_edit_user
def edit(request, user_id):
    """
    Edit an existing user.
    """
    user = get_object_or_404(User, pk=user_id)
    return _edit(request, user)


def _edit(request, user=None):
    """
    Handle creating or editing a user
    """
    if request.POST:
        form = UserForm(request.POST, user=request.user, instance=user)
        if form.is_valid():
            is_new = user is None or user.pk is None
            user = form.save()
            if is_new:
                messages.success(request, "Created!")
            else:
                messages.success(request, "Edited!")

            if can_list_users(request.user):
                return redirect("users-list")
            return redirect("users-home")
    else:
        form = UserForm(user=request.user, instance=user)

    return render(request, 'users/edit.html', {
        "form": form,
    })
