from apps.roles.models import Permission
from apps.users.constants import UserRole


def has_permission(user, resource: str, action: str) -> bool:
    if user is None or not getattr(user, 'is_authenticated', False):
        return False

    if user.role == UserRole.ADMIN:
        return True

    custom_role_id = getattr(user, 'custom_role_id', None)
    if not custom_role_id:
        return False

    permissions = Permission.objects.filter(role_id=custom_role_id, resource=resource).values_list('actions', flat=True)
    for actions in permissions:
        actions_list = actions or []
        if 'admin' in actions_list:
            return True
        if action in actions_list:
            return True

    return False

