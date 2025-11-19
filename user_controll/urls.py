# user_controll/urls.py
from django.urls import path
from .views import (
    AdminUserMenuViewSet,
    MyMenuView,
    AdminMenuItemListCreate,
    AdminMenuItemDetail,
    AdminApprovalViewSet,
    MyApprovalsView,
)

# map viewset methods manually to endpoints used by the frontend
admin_users = AdminUserMenuViewSet.as_view({"get": "users"})
admin_menu_tree = AdminUserMenuViewSet.as_view({"get": "menu_tree"})
admin_user_menus = AdminUserMenuViewSet.as_view({"get": "get_user_menus", "post": "set_user_menus"})

admin_approval_categories = AdminApprovalViewSet.as_view({"get": "list_categories"})
admin_user_approvals = AdminApprovalViewSet.as_view({
    "get": "get_user_approvals",
    "post": "set_user_approvals"
})

urlpatterns = [
    # Admin endpoints (using the ViewSet methods)
    path("admin/users/", admin_users, name="admin-users"),
    path("admin/menu-tree/", admin_menu_tree, name="admin-menu-tree"),
    path("admin/user/<int:user_id>/menus/", admin_user_menus, name="admin-user-menus"),

    # Current-user menu endpoint
    path("my-menu/", MyMenuView.as_view(), name="my-menu"),
    
    # Current-user approval permissions endpoint (NEW)
    path("my-approvals/", MyApprovalsView.as_view(), name="my-approvals"),

    # Admin menu item CRUD endpoints
    path("admin/menu-items/", AdminMenuItemListCreate.as_view(), name="admin-menu-items-create"),
    path("admin/menu-items/<int:menu_id>/", AdminMenuItemDetail.as_view(), name="admin-menu-items-detail"),

    # Admin approval endpoints
    path("admin/approval-categories/", admin_approval_categories, name="admin-approval-categories"),
    path("admin/user/<int:user_id>/approvals/", admin_user_approvals, name="admin-user-approvals"),
]