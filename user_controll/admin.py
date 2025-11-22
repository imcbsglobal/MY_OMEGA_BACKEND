# user_controll/admin.py
from django.contrib import admin
from .models import MenuItem, UserMenuAccess


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ["name", "key", "path", "parent", "order", "is_active"]
    list_filter = ["is_active", "parent"]
    search_fields = ["name", "key", "path"]
    list_editable = ["order", "is_active"]
    ordering = ["parent__id", "order", "name"]

    fieldsets = (
        ("Basic Information", {
            "fields": ("name", "key", "path", "icon")
        }),
        ("Hierarchy", {
            "fields": ("parent", "order")
        }),
        ("Status", {
            "fields": ("is_active",)
        }),
    )


@admin.register(UserMenuAccess)
class UserMenuAccessAdmin(admin.ModelAdmin):
    list_display = ["user", "menu_item", "can_view", "can_edit", "can_delete"]
    list_filter = ["menu_item", "user"]
    search_fields = ["user__username", "user__email", "menu_item__name"]
    raw_id_fields = ["user", "menu_item"]







from .models import ApprovalCategory, UserApprovalPermission


@admin.register(ApprovalCategory)
class ApprovalCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'key', 'is_active', 'order']
    list_filter = ['is_active']
    search_fields = ['name', 'key', 'description']
    list_editable = ['order', 'is_active']
    ordering = ['order', 'name']


@admin.register(UserApprovalPermission)
class UserApprovalPermissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'category', 'can_approve', 'can_reject', 'can_view_all', 'updated_at']
    list_filter = ['category', 'can_approve', 'can_reject', 'can_view_all']
    search_fields = ['user__username', 'user__email', 'category__name']
    raw_id_fields = ['user', 'category']
    readonly_fields = ['created_at', 'updated_at']