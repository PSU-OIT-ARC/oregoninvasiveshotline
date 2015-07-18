from ..perms import permissions
from .models import Invite, Report


@permissions.register(model=Report)
def can_view_private_report(user, report):
    if user.is_anonymous():
        return False

    if Invite.objects.filter(report=report, user_id=user.pk).exists():
        return True

    if report.created_by == user:
        return True

    if user.is_elevated:
        return True


@permissions.register(model=Report)
def can_adjust_visibility(user, report):
    return user.is_elevated or Invite.objects.filter(user=user, report=report).exists()


@permissions.register(model=Report)
def can_claim_report(user, report):
    return user.is_elevated


@permissions.register(model=Report)
def can_manage_report(user, report):
    return user.is_authenticated() and (user.is_staff or report.claimed_by_id == user.pk)
