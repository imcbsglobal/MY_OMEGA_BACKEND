# user_controll/views.py
from django.shortcuts import render
from django.db import transaction
from django.conf import settings
from rest_framework import permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .models import MenuItem, UserMenuAccess
from .permissions import IsSuperAdmin
from .serializers import (
    SimpleUserSerializer,
    MenuItemTreeSerializer,
    UserMenuIdsSerializer,
)

# Get the user model
User = settings.AUTH_USER_MODEL
from User.models import AppUser


class AdminUserMenuViewSet(viewsets.ViewSet):
    """
    Admin endpoints for managing user menu permissions.
    Only accessible by superusers/staff or users with 'user_control' menu access.
    """
    permission_classes = [IsSuperAdmin]

    def users(self, request):
        """Get list of all users"""
        qs = AppUser.objects.all().order_by("-date_joined")
        return Response(SimpleUserSerializer(qs, many=True).data)

    def menu_tree(self, request):
        """Get complete menu tree structure"""
        roots = MenuItem.objects.filter(
            parent__isnull=True, 
            is_active=True
        ).order_by("order", "name")
        return Response(MenuItemTreeSerializer(roots, many=True).data)

    def get_user_menus(self, request, user_id=None):
        """Get menu IDs assigned to a specific user"""
        try:
            user = AppUser.objects.get(id=user_id)
        except AppUser.DoesNotExist:
            return Response(
                {"detail": "User not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # FIXED: Use user=user instead of user_id=user_id
        menu_ids = list(
            UserMenuAccess.objects.filter(user=user)
            .values_list("menu_item_id", flat=True)
        )
        
        return Response({"menu_ids": menu_ids})

    def set_user_menus(self, request, user_id=None):
        """Set menu permissions for a specific user"""
        print(f"\n[set_user_menus] Starting for user_id: {user_id}")
        print(f"[set_user_menus] Request data: {request.data}")
        
        try:
            user = AppUser.objects.get(id=user_id)
            print(f"[set_user_menus] Found user: {user.email}")
        except AppUser.DoesNotExist:
            print(f"[set_user_menus] ERROR: User not found")
            return Response(
                {"detail": "User not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Validate input
        serializer = UserMenuIdsSerializer(data=request.data)
        if not serializer.is_valid():
            print(f"[set_user_menus] Validation error: {serializer.errors}")
            return Response(
                {"detail": "Invalid data", "errors": serializer.errors}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        menu_ids = set(serializer.validated_data["menu_ids"])
        print(f"[set_user_menus] Validated menu_ids: {menu_ids}")
        
        # Validate that all menu IDs exist
        if menu_ids:
            valid_ids = set(
                MenuItem.objects.filter(id__in=menu_ids)
                .values_list("id", flat=True)
            )
            invalid_ids = menu_ids - valid_ids
            if invalid_ids:
                print(f"[set_user_menus] ERROR: Invalid menu IDs: {invalid_ids}")
                return Response(
                    {"detail": f"Invalid menu IDs: {invalid_ids}"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Automatically include parent menus when child is selected
        final_menu_ids = set(menu_ids)
        for menu_id in menu_ids:
            try:
                menu = MenuItem.objects.get(id=menu_id)
                # Add all parent menus
                current = menu.parent
                while current:
                    final_menu_ids.add(current.id)
                    current = current.parent
            except MenuItem.DoesNotExist:
                pass
        
        print(f"[set_user_menus] Final menu_ids (with parents): {final_menu_ids}")
        
        # Update user menu access atomically
        try:
            with transaction.atomic():
                # FIXED: Use user=user instead of user_id=user_id
                deleted_count = UserMenuAccess.objects.filter(user=user).delete()[0]
                print(f"[set_user_menus] Deleted {deleted_count} existing access records")
                
                # Create new access records
                if final_menu_ids:
                    bulk_create = [
                        UserMenuAccess(user=user, menu_item_id=menu_id)
                        for menu_id in final_menu_ids
                    ]
                    created = UserMenuAccess.objects.bulk_create(bulk_create)
                    print(f"[set_user_menus] Created {len(created)} new access records")
            
            print(f"[set_user_menus] SUCCESS: Updated menu permissions for {user.email}")
            return Response({
                "ok": True, 
                "menu_ids": list(final_menu_ids),
                "message": f"Successfully updated menu permissions for {user.email}"
            })
            
        except Exception as e:
            print(f"[set_user_menus] ERROR during save: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {"detail": f"Error saving menus: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


def serialize_node(node, allowed_ids=None):
    """
    Convert a MenuItem to dict, including only children that are allowed_ids (if provided).
    If allowed_ids is None -> include all active children (admin path).
    """
    base = {
        "id": node.id,
        "key": node.key,
        "name": node.name,
        "path": node.path,
        "icon": node.icon,
        "order": node.order,
        "children": []
    }

    children = list(node.children.filter(is_active=True).order_by("order", "name"))
    if allowed_ids is None:
        # admin: keep all children
        base["children"] = [serialize_node(c, None) for c in children]
        return base

    # regular user: keep only children that are allowed (or have allowed descendants)
    kept = []
    for c in children:
        child_serialized = serialize_node(c, allowed_ids)
        # keep the node if itself is allowed OR it has any kept children
        if c.id in allowed_ids or child_serialized["children"]:
            kept.append(child_serialized)
    # keep current node even if it wasn't directly assigned, as long as it has visible children
    base["children"] = kept
    return base


class MyMenuView(APIView):
    """
    Returns the menu tree for the currently authenticated user.
    - Super Admin/Admin get the full tree
    - Regular users get only their assigned menus
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Get user level from AppUser model
        user_level = getattr(user, 'user_level', 'User')
        
        print(f"[MyMenuView] User: {user.email}")
        print(f"[MyMenuView] User Level: {user_level}")
        print(f"[MyMenuView] is_superuser: {user.is_superuser}")
        print(f"[MyMenuView] is_staff: {user.is_staff}")
        
        # Check if user is Admin or Super Admin
        is_admin = user_level in ('Super Admin', 'Admin')
        
        # Super Admin and Admin: return full active tree
        if is_admin:
            print(f"[MyMenuView] ✓ User is {user_level}, returning FULL menu tree")
            roots = (MenuItem.objects
                     .filter(is_active=True, parent__isnull=True)
                     .prefetch_related('children')
                     .order_by("order", "name"))
            data = [serialize_node(r, None) for r in roots]
            return Response({
                "menu": data,
                "is_admin": True,
                "user_level": user_level
            })

        # Regular users: filter by assigned menu ids
        print(f"[MyMenuView] User is regular user, checking assigned menus...")
        # FIXED: Use user=user instead of user_id=user.id
        allowed_ids = set(
            UserMenuAccess.objects
            .filter(user=user, menu_item__is_active=True)
            .values_list("menu_item_id", flat=True)
        )
        
        print(f"[MyMenuView] Allowed menu IDs: {allowed_ids}")

        # If nothing assigned, return empty
        if not allowed_ids:
            print(f"[MyMenuView] ✗ No menus assigned to this user")
            return Response({
                "menu": [],
                "is_admin": False,
                "user_level": user_level,
                "message": "No menus assigned. Contact administrator."
            })

        # Start at active root nodes; serialize with allowed_ids filter
        roots = (MenuItem.objects
                 .filter(is_active=True, parent__isnull=True)
                 .prefetch_related('children')
                 .order_by("order", "name"))
        data = []
        for r in roots:
            node = serialize_node(r, allowed_ids)
            # show a root if it is allowed OR it has any allowed descendants
            if r.id in allowed_ids or node["children"]:
                data.append(node)

        print(f"[MyMenuView] ✓ Returning {len(data)} root menus for regular user")
        return Response({
            "menu": data,
            "is_admin": False,
            "user_level": user_level
        })