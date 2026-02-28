# user_controll/views.py
from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from User.models import AppUser
from .models import MenuItem, UserMenuAccess
from .serializers import (
    SimpleUserSerializer,
    MenuItemTreeSerializer,
    UserMenuIdsSerializer,
    MenuItemSerializer,
    UserMenuAccessSerializer,
    AssignMenusPayloadSerializer,
)
from .permissions import IsSuperAdmin


# -------------------------------------------
# Admin viewset: list users, menu tree, get/set user menus
# -------------------------------------------
class AdminUserMenuViewSet(viewsets.ViewSet):
    permission_classes = [IsSuperAdmin]

    def users(self, request):
        """GET /admin/users/  -> list AppUser"""
        # Default: show only active users in admin lists
        qs = AppUser.objects.all().order_by("-date_joined")
        is_active = request.query_params.get("is_active", None)
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == "true")
        else:
            qs = qs.filter(is_active=True)
        return Response(SimpleUserSerializer(qs, many=True).data)

    def menu_tree(self, request):
        """GET /admin/menu-tree/  -> full active menu tree"""
        roots = MenuItem.objects.filter(
            parent__isnull=True,
            is_active=True
        ).order_by("order", "name")
        return Response(MenuItemTreeSerializer(roots, many=True).data)
    def get_user_menus(self, request, user_id=None):
        """
        GET /admin/user/<user_id>/menus/

        Returns existing menu assignments for user.

        Response format:
        {
            "menu_ids": [1,2,3],
            "menu_perms": [
                {
                    "menu_item": 1,
                    "can_view": true,
                    "can_edit": false,
                    "can_delete": false
                }
            ]
        }
        """

        try:
            user = AppUser.objects.get(id=user_id)
        except AppUser.DoesNotExist:
            return Response(
                {"detail": "User not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Get all permissions
        perms_qs = UserMenuAccess.objects.filter(
            user=user
        ).select_related("menu_item")

        # ✅ Extract menu IDs (needed for checkbox checked state)
        menu_ids = list(
            perms_qs.values_list("menu_item_id", flat=True)
        )

        # ✅ Serialize full permission data
        serializer = UserMenuAccessSerializer(perms_qs, many=True)

        return Response({
            "menu_ids": menu_ids,
            "menu_perms": serializer.data
        })


    def set_user_menus(self, request, user_id=None):
        """
         POST /admin/user/<user_id>/menus/

        Supports:
          { "menu_ids": [...] }
          { "items": [...] }
          { "all": true }
        """

        try:
            user = AppUser.objects.get(id=user_id)
        except AppUser.DoesNotExist:
            return Response(
                {"detail": "User not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # =====================================================
        # ✅ PER ACTION PERMISSION MODE
        # =====================================================
        if "items" in request.data or "all" in request.data:

            serializer = AssignMenusPayloadSerializer(
                data={**request.data, "user_id": user.id}
            )

            if not serializer.is_valid():
                return Response(
                    {"detail": "Invalid data", "errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            data = serializer.validated_data
            assigned = 0

            try:
                with transaction.atomic():

                    UserMenuAccess.objects.filter(user=user).delete()

                    # ✅ Assign ALL menus
                    if data.get("all"):
                        menus = MenuItem.objects.filter(is_active=True)

                        bulk = [
                            UserMenuAccess(
                                user=user,
                                menu_item=m,
                                can_view=True,
                                can_edit=True,
                                can_delete=True,
                            )
                            for m in menus
                        ]

                        UserMenuAccess.objects.bulk_create(bulk)
                        assigned = len(bulk)

                    else:
                        items = data.get("items", [])
                        bulk = []
                        valid_menu_ids = set()

                        # ✅ keep only existing menus
                        existing_menus = MenuItem.objects.filter(
                            id__in=[i["menu_id"] for i in items]
                        )

                        menu_map = {m.id: m for m in existing_menus}

                        for it in items:
                            mid = it["menu_id"]

                            if mid not in menu_map:
                                continue

                            valid_menu_ids.add(mid)

                            bulk.append(
                                UserMenuAccess(
                                    user=user,
                                    menu_item_id=mid,
                                    can_view=it.get("can_view", False),
                                    can_edit=it.get("can_edit", False),
                                    can_delete=it.get("can_delete", False),
                                )
                            )

                        # ✅ AUTO ADD PARENTS
                        parent_ids = set()

                        for menu in existing_menus:
                            parent = menu.parent
                            while parent:
                                parent_ids.add(parent.id)
                                parent = parent.parent

                        for pid in parent_ids:
                            bulk.append(
                                UserMenuAccess(
                                    user=user,
                                    menu_item_id=pid,
                                    can_view=True,
                                    can_edit=False,
                                    can_delete=False,
                                )
                            )

                        if bulk:
                            UserMenuAccess.objects.bulk_create(bulk)
                            assigned = len(bulk)

                return Response(
                    {"detail": "Assigned", "assigned_count": assigned},
                    status=status.HTTP_200_OK,
                )

            except Exception as e:
                return Response(
                    {"detail": f"Error assigning menus: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        # =====================================================
        # ✅ SIMPLE CHECKBOX MODE (menu_ids)
        # =====================================================

        serializer = UserMenuIdsSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {"detail": "Invalid data", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        menu_ids = set(serializer.validated_data.get("menu_ids", []))

        # ✅ only valid menus
        valid_menus = MenuItem.objects.filter(id__in=menu_ids)
        final_menu_ids = set(valid_menus.values_list("id", flat=True))

        # ✅ AUTO INCLUDE PARENTS SAFELY
        for menu in valid_menus:
            parent = menu.parent
            while parent:
                final_menu_ids.add(parent.id)
                parent = parent.parent

        try:
            with transaction.atomic():

                UserMenuAccess.objects.filter(user=user).delete()

                bulk = [
                    UserMenuAccess(
                        user=user,
                        menu_item_id=mid,
                        can_view=True,
                        can_edit=False,
                        can_delete=False,
                    )
                    for mid in final_menu_ids
                ]

                if bulk:
                    UserMenuAccess.objects.bulk_create(bulk)

            return Response(
                {
                    "ok": True,
                    "menu_ids": list(final_menu_ids),
                    "message": f"Menus saved successfully for {user.email}",
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"detail": f"Error saving menus: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# -------------------------------------------
# MyMenuView - returns menu tree filtered for current user
# -------------------------------------------
def _serialize_node_with_perms(node, allowed_map=None):
    """
    allowed_map: dict menu_id -> { can_view, can_edit, can_delete }
    If allowed_map is None, include all nodes and set all permissions True (superuser).
    """
    base = {
        "id": node.id,
        "key": node.key,
        "name": node.name,
        "path": node.path,
        "icon": node.icon,
        "order": node.order,
        "children": [],
    }

    # superuser-style: allowed_map is None => full access and all children
    if allowed_map is None:
        base["allowed_actions"] = {
            "can_view": True,
            "can_edit": True,
            "can_delete": True,
        }
        children = node.children.filter(is_active=True).order_by("order", "name")
        base["children"] = [
            _serialize_node_with_perms(c, None) for c in children
        ]
        return base

    perms = allowed_map.get(node.id, {})
    base["allowed_actions"] = {
        "can_view": bool(perms.get("can_view", False)),
        "can_edit": bool(perms.get("can_edit", False)),
        "can_delete": bool(perms.get("can_delete", False)),
    }

    children = node.children.filter(is_active=True).order_by("order", "name")
    serialized_children = [
        _serialize_node_with_perms(c, allowed_map) for c in children
    ]

    # Keep child if it can_view OR if it has any children (so parents of allowed nodes stay)
    kept_children = []
    for c in serialized_children:
        if c["allowed_actions"]["can_view"] or c["children"]:
            kept_children.append(c)

    base["children"] = kept_children
    return base


class MyMenuView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        user_level = getattr(user, "user_level", "User")
        is_django_superuser = user.is_superuser
        is_app_admin = user_level in ("Super Admin", "Admin")

        # Django superuser gets full menu tree w/ full permissions on every node
        if is_django_superuser:
            roots = MenuItem.objects.filter(
                is_active=True, parent__isnull=True
            ).order_by("order", "name")
            data = [_serialize_node_with_perms(r, None) for r in roots]
            return Response(
                {
                    "menu": data,
                    "is_django_superuser": True,
                    "is_app_admin": is_app_admin,
                    "user_level": user_level,
                }
            )

        # everyone else -> use explicit UserMenuAccess rows
        allowed_qs = UserMenuAccess.objects.filter(
            user=user, menu_item__is_active=True
        )
        allowed_map = {
            a.menu_item_id: {
                "can_view": a.can_view,
                "can_edit": a.can_edit,
                "can_delete": a.can_delete,
            }
            for a in allowed_qs
        }

        if not allowed_map:
            return Response(
                {
                    "menu": [],
                    "is_django_superuser": False,
                    "is_app_admin": is_app_admin,
                    "user_level": user_level,
                    "message": "No menus assigned. Contact administrator.",
                }
            )

        roots = MenuItem.objects.filter(
            is_active=True, parent__isnull=True
        ).order_by("order", "name")

        data = []
        for r in roots:
            node = _serialize_node_with_perms(r, allowed_map)
            # keep node if it itself is allowed or if it has any visible children
            if r.id in allowed_map or node["children"]:
                data.append(node)

        return Response(
            {
                "menu": data,
                "is_django_superuser": False,
                "is_app_admin": is_app_admin,
                "user_level": user_level,
            }
        )


# -------------------------------------------
# Menu item CRUD (admin)
# -------------------------------------------
class AdminMenuItemListCreate(APIView):
    permission_classes = [IsSuperAdmin]

    def post(self, request):
        serializer = MenuItemSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"detail": "Invalid data", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        item = serializer.save()
        return Response(
            MenuItemTreeSerializer(item).data,
            status=status.HTTP_201_CREATED,
        )


class AdminMenuItemDetail(APIView):
    permission_classes = [IsSuperAdmin]

    def put(self, request, menu_id):
        menu = get_object_or_404(MenuItem, id=menu_id)
        serializer = MenuItemSerializer(menu, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                {"detail": "Invalid data", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        menu = serializer.save()
        return Response(MenuItemTreeSerializer(menu).data)

    def delete(self, request, menu_id):
        menu = get_object_or_404(MenuItem, id=menu_id)
        menu.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)





from .models import ApprovalCategory, UserApprovalPermission
from .serializers import (
    # ... your existing imports ...
    ApprovalCategorySerializer,
    UserApprovalPermissionSerializer,
    BulkAssignApprovalSerializer,
)


class AdminApprovalViewSet(viewsets.ViewSet):
    """Admin endpoints for managing approval permissions"""
    permission_classes = [IsSuperAdmin]

    def list_categories(self, request):
        """GET /admin/approval-categories/"""
        categories = ApprovalCategory.objects.filter(is_active=True).order_by('order', 'name')
        serializer = ApprovalCategorySerializer(categories, many=True)
        return Response(serializer.data)

    def get_user_approvals(self, request, user_id=None):
        """GET /admin/user/<user_id>/approvals/"""
        try:
            user = AppUser.objects.get(id=user_id)
        except AppUser.DoesNotExist:
            return Response(
                {"detail": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        permissions = UserApprovalPermission.objects.filter(
            user=user,
            category__is_active=True
        ).select_related('category')

        serializer = UserApprovalPermissionSerializer(permissions, many=True)
        return Response({
            "user_id": user.id,
            "username": user.username or user.email,
            "permissions": serializer.data
        })

    def set_user_approvals(self, request, user_id=None):
        """POST /admin/user/<user_id>/approvals/"""
        try:
            user = AppUser.objects.get(id=user_id)
        except AppUser.DoesNotExist:
            return Response(
                {"detail": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = BulkAssignApprovalSerializer(
            data={**request.data, "user_id": user.id}
        )
        
        if not serializer.is_valid():
            return Response(
                {"detail": "Invalid data", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data

        try:
            with transaction.atomic():
                # Clear existing permissions
                UserApprovalPermission.objects.filter(user=user).delete()

                assigned_count = 0

                if data.get('assign_all'):
                    # Assign all categories with full permissions
                    categories = ApprovalCategory.objects.filter(is_active=True)
                    bulk = [
                        UserApprovalPermission(
                            user=user,
                            category=cat,
                            can_approve=True,
                            can_reject=True,
                            can_view_all=True
                        )
                        for cat in categories
                    ]
                    if bulk:
                        UserApprovalPermission.objects.bulk_create(bulk)
                        assigned_count = len(bulk)
                else:
                    # Assign specific permissions
                    permissions = data.get('permissions', [])
                    bulk = []
                    
                    for perm in permissions:
                        category_id = perm['category_id']
                        
                        try:
                            category = ApprovalCategory.objects.get(
                                id=category_id,
                                is_active=True
                            )
                        except ApprovalCategory.DoesNotExist:
                            continue

                        # Only create if at least one permission is granted
                        if perm.get('can_approve') or perm.get('can_reject') or perm.get('can_view_all'):
                            bulk.append(
                                UserApprovalPermission(
                                    user=user,
                                    category=category,
                                    can_approve=perm.get('can_approve', False),
                                    can_reject=perm.get('can_reject', False),
                                    can_view_all=perm.get('can_view_all', False)
                                )
                            )
                    
                    if bulk:
                        UserApprovalPermission.objects.bulk_create(bulk)
                        assigned_count = len(bulk)

                return Response({
                    "detail": "Approval permissions updated",
                    "assigned_count": assigned_count
                }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"detail": f"Error assigning approvals: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

# Add this to the END of your user_controll/views.py file

from .approval_helpers import get_user_approval_permissions


class MyApprovalsView(APIView):
    """
    GET /api/user-controll/my-approvals/
    
    Returns current user's approval permissions.
    Used by LeaveManagement.jsx to show/hide approval controls.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        is_superuser = getattr(user, 'is_superuser', False)

        # Get all approval permissions using helper
        permissions_dict = get_user_approval_permissions(user)

        # Format for frontend
        permissions_list = [
            {
                'category_key': key,
                'can_approve': perms['can_approve'],
                'can_reject': perms['can_reject'],
                'can_view_all': perms['can_view_all']
            }
            for key, perms in permissions_dict.items()
        ]

        return Response({
            'is_superuser': is_superuser,
            'is_admin': False,  # App admins don't get automatic access
            'all_permissions': is_superuser,  # Only superusers have all perms
            'permissions': permissions_list
        })