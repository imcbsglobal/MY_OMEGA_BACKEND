from rest_framework import permissions


class IsActiveUser(permissions.BasePermission):
    """
    Global permission to ensure inactive accounts cannot access APIs.
    Blocks requests when `request.user.is_active` is False, even if token is valid.
    """
    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            return False
        return bool(getattr(user, "is_active", False))
