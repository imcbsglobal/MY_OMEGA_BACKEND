from rest_framework import permissions
from user_controll.models import UserMenuAccess
from User.models import AppUser

class IsSuperAdmin(permissions.BasePermission):
    """
    Allow access if:
    1. User has user_level = "Super Admin" or "Admin"
    2. OR user has 'user_control' menu access
    """
    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        user = request.user
        
        # Get user level from the user model
        user_level = getattr(user, 'user_level', 'User')
        
        print(f"[IsSuperAdmin] User: {user.email}")
        print(f"[IsSuperAdmin] User Level: {user_level}")
        print(f"[IsSuperAdmin] is_staff: {user.is_staff}")
        print(f"[IsSuperAdmin] is_superuser: {user.is_superuser}")
        
        # Allow Super Admin and Admin
        if user_level in ('Super Admin', 'Admin'):
            print(f"[IsSuperAdmin] ✓ Access granted - {user_level}")
            return True
        
        # Allow staff and superuser
        if user.is_staff or user.is_superuser:
            print(f"[IsSuperAdmin] ✓ Access granted - Django staff/superuser")
            return True
        
        # Check if user has 'user_control' menu access
        has_user_control = UserMenuAccess.objects.filter(
            user=user,
            menu_item__key="user_control",
            menu_item__is_active=True
        ).exists()
        
        if has_user_control:
            print(f"[IsSuperAdmin] ✓ Access granted - has user_control menu")
            return True
        
        print(f"[IsSuperAdmin] ✗ Access denied - no permissions")
        return False