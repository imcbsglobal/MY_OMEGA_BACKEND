# user_controll/urls.py
from django.urls import path
from .views import AdminUserMenuViewSet, MyMenuView

# Admin endpoints
admin_users = AdminUserMenuViewSet.as_view({"get": "users"})
admin_menu_tree = AdminUserMenuViewSet.as_view({"get": "menu_tree"})
admin_user_menus = AdminUserMenuViewSet.as_view({"get": "get_user_menus", "post": "set_user_menus"})

urlpatterns = [
    # Admin endpoints
    path("admin/users/", admin_users, name="admin-users"),
    path("admin/menu-tree/", admin_menu_tree, name="admin-menu-tree"),
    path("admin/user/<int:user_id>/menus/", admin_user_menus, name="admin-user-menus"),
    
    # User menu endpoint
    path("my-menu/", MyMenuView.as_view(), name="my-menu"),
]