from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import MenuItem

User = get_user_model()

class SimpleUserSerializer(serializers.ModelSerializer):
    """
    For listing/choosing users in the admin panel.
    """
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "is_staff", "is_superuser"]


class MenuItemTreeSerializer(serializers.ModelSerializer):
    """
    Tree structure for the left sidebar.
    """
    children = serializers.SerializerMethodField()

    class Meta:
        model = MenuItem
        fields = ["id", "name", "path", "parent", "order", "children"]

    def get_children(self, obj):
        qs = obj.children.filter(is_active=True).order_by("order", "name")
        return MenuItemTreeSerializer(qs, many=True).data


class UserMenuIdsSerializer(serializers.Serializer):
    """
    POST body for saving selections.
    """
    menu_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=True)
