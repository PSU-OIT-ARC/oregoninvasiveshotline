from ..perms import permissions
from .models import Invite, Report


@permissions.register(model=Report)
def can_view_private_report(user, report):
    if getattr(user, 'is_elevated', False):
        return True

    if Invite.objects.filter(report=report, user_id=user.pk).exists():
        return True

    if report.created_by == user:
        return True


@permissions.register(model=Report)
def can_edit_report(user, report):
    return report.claimed_by == user
