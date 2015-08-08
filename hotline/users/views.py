import random

from arcutils import will_be_deleted_with
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login as django_login
from django.contrib.auth.views import login as django_login_view
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.core.signing import BadSignature
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView
from hotline.reports.models import Invite, Report

from .forms import LoginForm, UserForm
from .models import User
from .perms import can_list_users, permissions


def login(request, *args, **kwargs):
    """
    This delegates most of the work to `django.contrib.auth.views.login`, but
    we need to display an extra form, that allows users to login with just an
    email address. To do that without rewriting all the django login code, we
    tap into the TemplateResponse.context_data and add the extra form
    """
    response = django_login_view(request, *args, **kwargs)
    # if our special "OTHER_LOGIN" flag is present, we process our login form
    if request.method == "POST" and request.POST.get("form") == "OTHER_LOGIN":
        # make it look like the django login form wasn't filled out
        response.context_data['form'] = response.context_data['form'].__class__(request)
        # now do the regular form processing stuff...
        other_form = LoginForm(request.POST)
        if other_form.is_valid():
            other_form.save(request=request)
            messages.success(request, "Check your email! You have been sent the login link.")
            return redirect(request.get_full_path())
    else:
        other_form = LoginForm()

    # patch in the other_form variable, so the template can render it.
    # Sometimes the django_login_view returns an HttpResponseRedirect, which
    # doesn't have context_data, hence the check
    if hasattr(response, "context_data"):
        response.context_data['other_form'] = other_form

    return response


def authenticate(request):
    sig = request.GET.get("sig", "")
    try:
        user = User.authenticate(sig)
    except BadSignature:
        messages.error(request, "Bad Signature")
        return redirect("home")

    if user.is_active or Invite.objects.filter(user=user).exists():
        user.backend = settings.AUTHENTICATION_BACKENDS[0]
        django_login(request, user)

    # populate the report_ids session variable with all the reports the user made
    request.session['report_ids'] = list(Report.objects.filter(created_by=user).values_list('pk', flat=True))

    return redirect(request.GET.get("next") or settings.LOGIN_REDIRECT_URL)


def avatar(request, user_id, colors="AliceBlue AntiqueWhite Aqua Aquamarine Azure Beige Bisque Black BlanchedAlmond Blue BlueViolet Brown BurlyWood CadetBlue Chartreuse Chocolate Coral CornflowerBlue Cornsilk Crimson Cyan DarkBlue DarkCyan DarkGoldenRod DarkGray DarkGreen DarkKhaki DarkMagenta DarkOliveGreen DarkOrange DarkOrchid DarkRed DarkSalmon DarkSeaGreen DarkSlateBlue DarkSlateGray DarkTurquoise DarkViolet DeepPink DeepSkyBlue DimGray DodgerBlue FireBrick FloralWhite ForestGreen Fuchsia Gainsboro GhostWhite Gold GoldenRod Gray Green GreenYellow HoneyDew HotPink IndianRed Indigo Ivory Khaki Lavender LavenderBlush LawnGreen LemonChiffon LightBlue LightCoral LightCyan LightGoldenRodYellow LightGray LightGreen LightPink LightSalmon LightSeaGreen LightSkyBlue LightSlateGray LightSteelBlue LightYellow Lime LimeGreen Linen Magenta Maroon MediumAquaMarine MediumBlue MediumOrchid MediumPurple MediumSeaGreen MediumSlateBlue MediumSpringGreen MediumTurquoise MediumVioletRed MidnightBlue MintCream MistyRose Moccasin NavajoWhite Navy OldLace Olive OliveDrab Orange OrangeRed Orchid PaleGoldenRod PaleGreen PaleTurquoise PaleVioletRed PapayaWhip PeachPuff Peru Pink Plum PowderBlue Purple RebeccaPurple Red RosyBrown RoyalBlue SaddleBrown Salmon SandyBrown SeaGreen SeaShell Sienna Silver SkyBlue SlateBlue SlateGray Snow SpringGreen SteelBlue Tan Teal Thistle Tomato Turquoise Violet Wheat White WhiteSmoke Yellow YellowGreen".split(" ")):  # noqa
    """
    Generates an SVG to use as the user's default avatar, using some random
    colors based on the user's PK
    """
    user = get_object_or_404(User, pk=user_id)
    background_color, text_color = random.Random(user.pk).sample(colors, 2)

    return render(request, "users/avatar.svg", {
        "user": user,
        "background_color": background_color,
        "text_color": text_color,
    }, content_type="image/svg+xml")


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
    if user.is_authenticated() and user.is_active:
        unclaimed_reports = Report.objects.filter(claimed_by=None, is_public=False, is_archived=False)

    return render(request, "users/home.html", {
        "invited_to": invited_to,
        "reported": reported,
        "open_and_claimed": open_and_claimed,
        "unclaimed_reports": unclaimed_reports,
    })


class detail(DetailView):
    
    model = User
    fields = ["email", "first_name", "last_name", "prefix", "suffix", "is_manager", "is_staff", 
             "is_active", "date_joined", "affiliations", "biography", "photo"]
    
    def get_context_data(self, **kwargs):
        obj = super(DetailView, self).get_object()
        context = super(detail, self).get_context_data(**kwargs)
        context['current_user'] = self.request.user

        return context


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

    
    