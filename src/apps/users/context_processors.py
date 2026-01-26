from apps.roles.utils.permissions import has_permission
from apps.users.constants import UserRole


def permission_flags(request):
    user = getattr(request, 'user', None)
    is_authenticated = bool(user and getattr(user, 'is_authenticated', False))

    is_admin = is_authenticated and getattr(user, 'role', None) == UserRole.ADMIN
    is_manager = is_authenticated and getattr(user, 'role', None) == UserRole.MANAGER

    can_view_users = is_authenticated and (
        is_admin
        or is_manager
        or has_permission(user, 'users', 'view')
    )
    can_create_users = is_authenticated and (
        is_admin
        or is_manager
        or has_permission(user, 'users', 'create')
    )
    can_edit_users = is_authenticated and (
        is_admin
        or is_manager
        or has_permission(user, 'users', 'edit')
    )
    can_delete_users = is_authenticated and (
        is_admin
        or is_manager
        or has_permission(user, 'users', 'delete')
    )

    can_manage_users = can_create_users or can_edit_users or can_delete_users

    can_view_audit = is_authenticated and (
        is_admin
        or has_permission(user, 'audit', 'view')
    )
    can_export_audit = is_authenticated and (
        is_admin
        or has_permission(user, 'audit', 'export')
    )

    can_create_vaults = is_authenticated and (
        is_admin
        or is_manager
        or has_permission(user, 'vaults', 'create')
    )

    return {
        'is_admin': is_admin,
        'is_manager': is_manager,
        'can_view_users': can_view_users,
        'can_create_users': can_create_users,
        'can_edit_users': can_edit_users,
        'can_delete_users': can_delete_users,
        'can_manage_users': can_manage_users,
        'can_view_audit': can_view_audit,
        'can_export_audit': can_export_audit,
        'can_create_vaults': can_create_vaults,
    }

