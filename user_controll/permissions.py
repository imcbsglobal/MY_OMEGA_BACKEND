# user_controll/permissions.py - COMPLETE REPLACEMENT
from rest_framework import permissions
from user_controll.models import UserMenuAccess

class HasMenuAccess(permissions.BasePermission):
    """
    Check if user has access to a specific menu key.
    
    Usage in views:
        permission_classes = [HasMenuAccess]
        menu_key = 'attendance'  # Set this in your view
    
    ONLY Django superusers (is_superuser=True) bypass menu checks.
    ALL other users (including Admin/Super Admin) need menu assignments.
    """
    def has_permission(self, request, view):
        # Check authentication
        if not request.user or not request.user.is_authenticated:
            return False
        
        user = request.user
        user_level = getattr(user, 'user_level', 'User')
        
        print(f"[HasMenuAccess] User: {user.email}, Level: {user_level}")
        print(f"[HasMenuAccess] is_superuser: {user.is_superuser}")
        
        # ONLY Django superusers bypass all checks
        if user.is_superuser:
            print(f"[HasMenuAccess] ✓ Django superuser - full access granted")
            return True
        
        # Get the menu_key from the view
        menu_key = getattr(view, 'menu_key', None)
        
        if not menu_key:
            print(f"[HasMenuAccess] ✗ No menu_key defined in view")
            return False
        
        print(f"[HasMenuAccess] Checking menu_key: {menu_key}")
        
        # ALL users (including Admin/Super Admin) must have menu assigned
        has_access = UserMenuAccess.objects.filter(
            user=user,
            menu_item__key=menu_key,
            menu_item__is_active=True
        ).exists()
        
        if has_access:
            print(f"[HasMenuAccess] ✓ User has '{menu_key}' menu access")
        else:
            print(f"[HasMenuAccess] ✗ User does NOT have '{menu_key}' menu access")
        
        return has_access


class IsSuperAdmin(permissions.BasePermission):
    """
    For user_control management endpoints ONLY.
    
    Allow access if:
    1. Django superuser (is_superuser=True) - full access
    2. AppUser with user_level = "Super Admin" or "Admin" - can manage users
    """
    def has_permission(self, request, view):
        # Check authentication
        if not request.user or not request.user.is_authenticated:
            return False
        
        user = request.user
        user_level = getattr(user, 'user_level', 'User')
        
        print(f"[IsSuperAdmin] User: {user.email}")
        print(f"[IsSuperAdmin] User Level: {user_level}")
        print(f"[IsSuperAdmin] is_superuser: {user.is_superuser}")
        
        # Django superusers always have access
        if user.is_superuser:
            print(f"[IsSuperAdmin] ✓ Django superuser - full access")
            return True
        
        # Allow AppUser Admin and Super Admin for user management
        if user_level in ('Super Admin', 'Admin'):
            print(f"[IsSuperAdmin] ✓ Access granted - {user_level}")
            return True
        
        print(f"[IsSuperAdmin] ✗ Access denied - not an admin")
        return False


class IsAuthenticated(permissions.BasePermission):
    """
    Allow any authenticated user - NO menu checks.
    Use this for endpoints that should be open to all logged-in users.
    
    Example: User profile, notifications, dashboard
    """
    def has_permission(self, request, view):
        is_auth = request.user and request.user.is_authenticated
        
        if is_auth:
            print(f"[IsAuthenticated] ✓ User {request.user.email} authenticated")
        else:
            print(f"[IsAuthenticated] ✗ User not authenticated")
        
        return is_auth