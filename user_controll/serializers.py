from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import MenuItem

User = get_user_model()

class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "is_staff", "is_superuser"]


class MenuItemTreeSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = MenuItem
        fields = ["id", "key", "name", "path", "icon", "parent", "order", "children"]

    def get_children(self, obj):
        qs = obj.children.filter(is_active=True).order_by("order", "name")
        return MenuItemTreeSerializer(qs, many=True).data


class UserMenuIdsSerializer(serializers.Serializer):
    menu_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=True
    )
