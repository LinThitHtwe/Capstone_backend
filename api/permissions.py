from rest_framework.permissions import BasePermission

from .constants import ROLE_ADMIN


class IsAdminRole(BasePermission):
    """Allow access only to authenticated users with role ``admin``."""

    message = "Admin role required."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.is_staff
            and getattr(user, "role", None) == ROLE_ADMIN
        )
