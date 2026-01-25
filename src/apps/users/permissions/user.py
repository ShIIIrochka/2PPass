from rest_framework.permissions import BasePermission

from apps.users.constants import UserRole


class IsAdminOrManager(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in (UserRole.ADMIN, UserRole.MANAGER)
