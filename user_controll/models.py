from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class MenuItem(models.Model):
    """
    Table name: user_controll_menuitem
    Represents a navigable item (or group) in your sidebar/menu.
    """
    name = models.CharField(max_length=100)
    path = models.CharField(max_length=200, unique=True)  # e.g. "/hr/attendance" or "#" for a group
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="children")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["parent__id", "order", "name"]

    def __str__(self):
        return self.name


class UserMenuAccess(models.Model):
    """
    Table name: user_controll_usermenuaccess
    A many-to-many via model linking a user to specific menu items they can access.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="menu_access")
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name="user_access")

    class Meta:
        unique_together = ("user", "menu_item")

    def __str__(self):
        return f"{self.user_id} -> {self.menu_item_id}"
