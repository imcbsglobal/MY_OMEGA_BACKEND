from rest_framework import permissions

class IsSuperAdmin(permissions.BasePermission):
    """
    Only allow requests from a logged-in superuser (is_superuser=True).
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)
