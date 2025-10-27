from django.urls import path
from .views import AdminUserMenuViewSet, MyMenuView

admin_users = AdminUserMenuViewSet.as_view({"get": "users"})
admin_menu_tree = AdminUserMenuViewSet.as_view({"get": "menu_tree"})
admin_get_user_menus = AdminUserMenuViewSet.as_view({"get": "get_user_menus"})
admin_set_user_menus = AdminUserMenuViewSet.as_view({"post": "set_user_menus"})

urlpatterns = [
    path("admin/users/", admin_users),                            # GET list users
    path("admin/menu-tree/", admin_menu_tree),                    # GET menu tree
    path("admin/user/<int:user_id>/menus/", admin_get_user_menus),# GET selected ids
    path("admin/user/<int:user_id>/menus/", admin_set_user_menus),# POST {menu_ids:[]}
    path("my-menu/", MyMenuView.as_view()),                       # GET my allowed menu
]
