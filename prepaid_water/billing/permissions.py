"""Reusable role-based permissions for Django REST Framework."""
from rest_framework.permissions import BasePermission


class IsAdminOrStaff(BasePermission):
    """Allow access only to Django admin users or users in WASAC_STAFF group."""

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (user.is_superuser or user.groups.filter(name="WASAC_STAFF").exists())
        )


class IsCustomer(BasePermission):
    """Allow access only to users in CUSTOMER group."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.groups.filter(name="CUSTOMER").exists())
