# user_controll/approval_helpers.py
"""
Helper functions to check approval permissions in your views.

CRITICAL BEHAVIOR:
- ONLY Django superuser (is_superuser=True) automatically bypasses permission checks
- App-level Admin/Super Admin (user_level field) MUST have explicit permissions assigned
"""
from .models import UserApprovalPermission, ApprovalCategory


def user_can_approve(user, category_key):
    """Check if user can approve requests for a given category."""
    # ONLY Django superuser bypasses checks
    if getattr(user, 'is_superuser', False):
        return True
    
    # Check explicit permission
    try:
        perm = UserApprovalPermission.objects.get(
            user=user,
            category__key=category_key,
            category__is_active=True
        )
        return perm.can_approve
    except UserApprovalPermission.DoesNotExist:
        return False


def user_can_reject(user, category_key):
    """Check if user can reject requests for a given category."""
    if getattr(user, 'is_superuser', False):
        return True
    
    try:
        perm = UserApprovalPermission.objects.get(
            user=user,
            category__key=category_key,
            category__is_active=True
        )
        return perm.can_reject
    except UserApprovalPermission.DoesNotExist:
        return False


def user_can_view_all(user, category_key):
    """Check if user can view all requests for a given category."""
    if getattr(user, 'is_superuser', False):
        return True
    
    try:
        perm = UserApprovalPermission.objects.get(
            user=user,
            category__key=category_key,
            category__is_active=True
        )
        return perm.can_view_all
    except UserApprovalPermission.DoesNotExist:
        return False


def get_user_approval_permissions(user):
    """Get all approval permissions for a user as a dictionary."""
    if getattr(user, 'is_superuser', False):
        # ONLY Django superusers get automatic all permissions
        categories = ApprovalCategory.objects.filter(is_active=True)
        return {
            cat.key: {
                'can_approve': True,
                'can_reject': True,
                'can_view_all': True
            }
            for cat in categories
        }
    
    # Everyone else gets only explicit permissions
    perms = UserApprovalPermission.objects.filter(
        user=user,
        category__is_active=True
    ).select_related('category')
    
    return {
        perm.category.key: {
            'can_approve': perm.can_approve,
            'can_reject': perm.can_reject,
            'can_view_all': perm.can_view_all
        }
        for perm in perms
    }