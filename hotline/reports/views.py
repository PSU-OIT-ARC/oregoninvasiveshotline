from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.functional import curry

from hotline.comments.forms import CommentForm
from hotline.comments.models import Comment
from hotline.comments.perms import can_create_comment
from hotline.images.forms import get_image_formset
from hotline.images.models import Image
from hotline.species.models import category_id_to_species_id_json

from .forms import ArchiveForm, ConfirmForm, InviteForm, PublicForm, ReportForm
from .models import Invite, Report
from .perms import can_manage_report, can_view_private_report, permissions


def create(request):
    """
    Render the public form for submitting reports
    """
    ImageFormSet = get_image_formset()

    if request.POST:
        form = ReportForm(request.POST, request.FILES)
        formset = ImageFormSet(request.POST, request.FILES, queryset=Image.objects.none())
        if form.is_valid() and formset.is_valid():
            report = form.save()
            formset.save(user=report.created_by, fk=report)
            messages.success(request, "Report submitted successfully")
            request.session.setdefault("report_ids", []).append(report.pk)
            request.session.modified = True
            # TODO send email
            return redirect("reports-detail", report.pk)
    else:
        formset = ImageFormSet(queryset=Image.objects.none())
        form = ReportForm()

    return render(request, "reports/create.html", {
        "form": form,
        "category_id_to_species_id": category_id_to_species_id_json(),
        "formset": formset
    })


def detail(request, report_id):
    """
    This is a complex view that handles displaying all the information about a
    Report. It needs to take into account the user's role on the Report to
    determine whether to display the comment form, and which comments to
    display, etc. It also handles the management of the report by the expert
    who claimed it
    """
    report = get_object_or_404(Report, pk=report_id)

    # this is the logic to determine authorization
    if request.user.is_anonymous():
        # We first check to see if the report is in their session. If it is, we
        # make sure the user who created the report isn't a "real" user,
        # otherwise, this would allow anonymous people to submit reports using
        # the email addresses of real users, and masquerade as them
        if report.pk in request.session.get("report_ids", []):
            if report.created_by.is_active:
                # if the user is active, we force them to login to prevent
                # anonymous users from masquerading as real users
                return login_required(lambda request: None)(request)
            else:
                # otherwise, we let the anonymous user masquerade as the user
                # who submitted this report
                request.user = report.created_by
        elif report.is_public:
            # if the report is public, there are no other permission checks required
            pass
        else:
            raise PermissionDenied()
    else:
        # the user is authenticated. If they aren't allowed to view this
        # report, that's a PermissionDenied
        if not can_view_private_report(request.user, report):
            raise PermissionDenied()

    # there are a bunch of forms that can be filled out on this page, by
    # default, they can't be filled out
    comment_form = None
    image_formset = None
    invite_form = None
    confirm_form = None
    archive_form = None
    public_form = None
    # this tells us which form was filled out since there are many on the page
    submit_flag = request.POST.get("submit_flag")

    # process the comment form only if they are allowed to leave comments
    if can_create_comment(request.user, report):
        ImageFormSet = get_image_formset(user=request.user)
        PartialCommentForm = curry(CommentForm, user=request.user, report=report)
        if request.POST and submit_flag == CommentForm.SUBMIT_FLAG:
            image_formset = ImageFormSet(request.POST, request.FILES, queryset=Image.objects.none())
            comment_form = PartialCommentForm(request.POST, request.FILES)
            if comment_form.is_valid() and image_formset.is_valid():
                comment = comment_form.save()
                image_formset.save(user=comment.created_by, fk=comment)
                messages.success(request, "Comment Added!")
                return redirect(request.get_full_path())
        else:
            comment_form = PartialCommentForm()
            image_formset = ImageFormSet(queryset=Image.objects.none())

    # handle all the management forms
    if can_manage_report(request.user, report):
        # Confirming the report form...
        if request.POST and submit_flag == ConfirmForm.SUBMIT_FLAG:
            confirm_form = ConfirmForm(request.POST, instance=report)
            if confirm_form.is_valid():
                confirm_form.save()
                messages.success(request, "Updated!")
                return redirect(request.get_full_path())
        else:
            confirm_form = ConfirmForm(instance=report)

        # Marking the report as public...
        if request.POST and submit_flag == PublicForm.SUBMIT_FLAG:
            public_form = PublicForm(request.POST, instance=report)
            if public_form.is_valid():
                public_form.save()
                messages.success(request, "Updated!")
                return redirect(request.get_full_path())
        else:
            public_form = PublicForm(instance=report)

        # Marking the report as archived...
        if request.POST and submit_flag == ArchiveForm.SUBMIT_FLAG:
            archive_form = ArchiveForm(request.POST, instance=report)
            if archive_form.is_valid():
                archive_form.save()
                messages.success(request, "Updated!")
                return redirect(request.get_full_path())
        else:
            archive_form = ArchiveForm(instance=report)

        # Inviting experts...
        if request.POST and submit_flag == InviteForm.SUBMIT_FLAG:
            invite_form = InviteForm(request.POST)
            if invite_form.is_valid():
                invite_report = invite_form.save(report=report, user=request.user)
                message = "%d invited" % (len(invite_report.invited))
                if invite_report.already_invited:
                    message += " (%d already invited)" % len(invite_report.already_invited)
                messages.success(request, message)
                return redirect(request.get_full_path())
        else:
            invite_form = InviteForm()

    # filter down the comments based on the user's permissions
    comments = Comment.objects.filter(report=report)
    images = Image.objects.filter(Q(report=report) | Q(comment__report=report))
    if request.user.is_anonymous():
        comments = comments.filter(visibility=Comment.PUBLIC)
        images = images.filter(visibility=Image.PUBLIC)
    elif request.user.is_elevated or Invite.objects.filter(user=request.user, report=report).exists():
        # no need to filter for these folks
        pass
    else:
        # the logged in user is the person who reported
        comments = comments.filter(Q(visibility=Comment.PUBLIC) | Q(visibility=Comment.PROTECTED))
        images = images.filter(Q(visibility=Image.PUBLIC) | Q(visibility=Image.PROTECTED))

    invites = list(i.user.email for i in Invite.objects.filter(report=report).select_related("user"))

    return render(request, "reports/detail.html", {
        "report": report,
        "comments": comments,
        "images": list(images),
        "category_id_to_species_id": category_id_to_species_id_json(),
        "invites": invites,
        # all the forms
        "image_formset": image_formset,
        "comment_form": comment_form,
        "public_form": public_form,
        "archive_form": archive_form,
        "invite_form": invite_form,
        "confirm_form": confirm_form,
    })


@permissions.can_claim_report
def claim(request, report_id):
    report = get_object_or_404(Report, pk=report_id)
    if request.method == "POST" and (report.claimed_by is None or "steal" in request.POST):
        report.claimed_by = request.user
        report.save()
        return redirect("reports-detail", report.pk)

    return render(request, "reports/claim.html", {
        "report": report,
    })
