# user_controll/permissions.py
from rest_framework import permissions
from user_controll.models import UserMenuAccess

class HasMenuAccess(permissions.BasePermission):
    """
    Permission that checks whether a user has access to a given menu key.
    View-level permission — set view.menu_key = "<menu_key>" on views where used.

    Django superusers bypass checks.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        user = request.user
        # Django superusers bypass
        if getattr(user, "is_superuser", False):
            return True

        menu_key = getattr(view, "menu_key", None)
        if not menu_key:
            return False

        return UserMenuAccess.objects.filter(
            user=user,
            menu_item__key=menu_key,
            menu_item__is_active=True
        ).exists()


class IsSuperAdmin(permissions.BasePermission):
    """
    Permit only Django superuser OR AppUser with user_level 'Super Admin' or 'Admin'.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        user = request.user
        if getattr(user, "is_superuser", False):
            return True

        user_level = getattr(user, "user_level", "")
        if user_level in ("Super Admin", "Admin"):
            return True

        return False


class IsAuthenticated(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)
