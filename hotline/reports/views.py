import json
from collections import defaultdict

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.functional import curry

from hotline.comments.forms import CommentForm
from hotline.comments.models import Comment
from hotline.comments.perms import can_create_comment
from hotline.species.models import Species

from .forms import ReportForm
from .models import Invite, Report
from .perms import can_view_private_report


def create(request):
    """
    Render the public form for submitting reports
    """
    if request.POST:
        form = ReportForm(request.POST, request.FILES)
        if form.is_valid():
            report = form.save()
            messages.success(request, "Report submitted successfully")
            request.session.setdefault("report_ids", []).append(report.pk)
            request.session.modified = True
            # TODO send email
            return redirect("reports-detail", report.pk)
    else:
        form = ReportForm()

    species = Species.objects.all().select_related("category").values_list("category__pk", "pk").order_by("category__pk")
    category_id_to_species_id = defaultdict(list)
    for category_id, species_id in species:
        category_id_to_species_id[category_id].append(species_id)

    return render(request, "reports/create.html", {
        "form": form,
        "category_id_to_species_id": json.dumps(category_id_to_species_id)
    })


def detail(request, report_id):
    """
    This is a complex view that handles displaying all the information about a
    Report. It needs to take into account the user's role on the Report to
    determine whether to display the comment form, and which comments to
    display, etc
    """
    report = get_object_or_404(Report, pk=report_id)

    if request.user.is_anonymous() and report.pk in request.session.get("report_ids", []):
        if report.created_by.is_active:
            # make them login before they can view this page, since they are
            # allowed to login. This prevents an anonymous user from being able
            # to masquerade as an active user
            return login_required(lambda request: None)(request)
        else:
            # for the life of this request, the user can masquerade as the
            # person who submitted the report. This is kind of dangerous
            # because by submitted a report using a spoofed email address, you
            # can become that user (but only for the life of this request)
            request.user = report.created_by

    if not report.is_public and not can_view_private_report(request.user, report):
        raise PermissionDenied()

    # process the comment form only if they are allowed to leave comments
    if can_create_comment(request.user, report):
        PartialCommentForm = curry(CommentForm, user=request.user, report=report)
        if request.POST:
            form = PartialCommentForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                messages.success(request, "Comment Added!")
                return redirect(request.get_full_path())
        else:
            form = PartialCommentForm()
    else:
        form = None

    # filter down the comments based on the user's permissions
    comments = Comment.objects.filter(report=report)
    if request.user.is_anonymous():
        comments = comments.filter(visibility=Comment.PUBLIC)
    elif request.user.is_elevated or Invite.objects.filter(user=request.user, report=report).exists():
        # no need to filter for these folks
        pass
    else:
        # the logged in user is the person who reported
        comments = comments.filter(Q(visibility=Comment.PUBLIC) | Q(visibility=Comment.PROTECTED))

    return render(request, "reports/detail.html", {
        "comments": comments,
        "report": report,
        "form": form,
    })
