# user_controll/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import MenuItem, UserMenuAccess

User = get_user_model()


class SimpleUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "is_staff", "is_superuser"]


class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ["id", "key", "name", "path", "icon", "parent", "order", "is_active"]


class MenuItemTreeSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = MenuItem
        fields = ["id", "key", "name", "path", "icon", "parent", "order", "is_active", "children"]

    def get_children(self, obj):
        qs = obj.children.filter(is_active=True).order_by("order", "name")
        return MenuItemTreeSerializer(qs, many=True).data


class UserMenuIdsSerializer(serializers.Serializer):
    menu_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=True
    )


# Per-action serializers
class UserMenuAccessSerializer(serializers.ModelSerializer):
    menu_id = serializers.IntegerField(source="menu_item.id", read_only=True)
    key = serializers.CharField(source="menu_item.key", read_only=True)
    name = serializers.CharField(source="menu_item.name", read_only=True)

    class Meta:
        model = UserMenuAccess
        fields = ['menu_id', 'key', 'name', 'can_view', 'can_edit', 'can_delete']


class AssignMenuPermissionItemSerializer(serializers.Serializer):
    menu_id = serializers.IntegerField()
    can_view = serializers.BooleanField(required=False, default=False)
    can_edit = serializers.BooleanField(required=False, default=False)
    can_delete = serializers.BooleanField(required=False, default=False)


class AssignMenusPayloadSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    items = serializers.ListField(child=AssignMenuPermissionItemSerializer(), required=False)
    all = serializers.BooleanField(required=False, default=False)







from .models import ApprovalCategory, UserApprovalPermission


class ApprovalCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalCategory
        fields = ['id', 'name', 'key', 'description', 'is_active', 'order']


class UserApprovalPermissionSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(source='category.id', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_key = serializers.CharField(source='category.key', read_only=True)

    class Meta:
        model = UserApprovalPermission
        fields = [
            'id', 'category_id', 'category_name', 'category_key',
            'can_approve', 'can_reject', 'can_view_all'
        ]


class AssignApprovalPermissionSerializer(serializers.Serializer):
    category_id = serializers.IntegerField()
    can_approve = serializers.BooleanField(default=False)
    can_reject = serializers.BooleanField(default=False)
    can_view_all = serializers.BooleanField(default=False)


class BulkAssignApprovalSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    permissions = serializers.ListField(
        child=AssignApprovalPermissionSerializer(),
        required=False
    )
    assign_all = serializers.BooleanField(required=False, default=False)