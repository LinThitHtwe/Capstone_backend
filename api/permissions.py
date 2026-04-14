"""Custom DRF permissions."""

from rest_framework.permissions import BasePermission

from .constants import ROLE_ADMIN


class IsAuthenticatedNonAdmin(BasePermission):
    """Logged-in users except admin (admin uses separate tools)."""

    message = "This action is not available for admin accounts."

    def has_permission(self, request, view):
        u = getattr(request, "user", None)
        return bool(
            u and u.is_authenticated and getattr(u, "role", None) != ROLE_ADMIN
        )


class IsAdminRole(BasePermission):
    """Requires an authenticated JWT user whose role is admin."""

    message = "Admin access only."

    def has_permission(self, request, view):
        u = getattr(request, "user", None)
        return bool(
            u and u.is_authenticated and getattr(u, "role", None) == ROLE_ADMIN
        )
