from django.shortcuts import render

# Create your views here.
from django.db import transaction
from django.contrib.auth import get_user_model
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import MenuItem, UserMenuAccess
from .permissions import IsSuperAdmin
from .serializers import (
    SimpleUserSerializer,
    MenuItemTreeSerializer,
    UserMenuIdsSerializer,
)

User = get_user_model()


class AdminUserMenuViewSet(viewsets.ViewSet):
    """
    Super-admin only endpoints to control who sees which menus.

    Functions (actions):
    - users (GET): list all users (for selection)
    - menu_tree (GET): get the full menu tree
    - get_user_menus (GET): get selected menu IDs for a user
    - set_user_menus (POST): replace selected menu IDs for a user
    """
    permission_classes = [IsSuperAdmin]

    @action(detail=False, methods=["get"])
    def users(self, request):
        qs = User.objects.order_by("username")
        return Response(SimpleUserSerializer(qs, many=True).data)

    @action(detail=False, methods=["get"])
    def menu_tree(self, request):
        roots = MenuItem.objects.filter(parent__isnull=True, is_active=True).order_by("order", "name")
        return Response(MenuItemTreeSerializer(roots, many=True).data)

    @action(detail=False, methods=["get"], url_path=r"user/(?P<user_id>\d+)/menus")
    def get_user_menus(self, request, user_id=None):
        ids = list(UserMenuAccess.objects.filter(user_id=user_id).values_list("menu_item_id", flat=True))
        return Response({"menu_ids": ids})

    @action(detail=False, methods=["post"], url_path=r"user/(?P<user_id>\d+)/menus")
    def set_user_menus(self, request, user_id=None):
        serializer = UserMenuIdsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = set(serializer.validated_data["menu_ids"])
        with transaction.atomic():
            UserMenuAccess.objects.filter(user_id=user_id).delete()
            bulk = [UserMenuAccess(user_id=user_id, menu_item_id=i) for i in ids]
            if bulk:
                UserMenuAccess.objects.bulk_create(bulk)
        return Response({"ok": True, "menu_ids": list(ids)})


class MyMenuView(APIView):
    """
    Returns the allowed menu tree for the CURRENT logged-in user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        ids = UserMenuAccess.objects.filter(user=request.user).values_list("menu_item_id", flat=True)
        # Top-level nodes among those ids
        top = MenuItem.objects.filter(id__in=ids, parent__isnull=True, is_active=True).order_by("order", "name")
        return Response({"menu": MenuItemTreeSerializer(top, many=True).data})
