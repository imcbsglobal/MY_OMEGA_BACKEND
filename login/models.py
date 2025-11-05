from django.db import models
from User.models import AppUser


class Menu(models.Model):
    """
    Canonical set of menus/pages in your app.
    Example rows:
      ("dashboard","Dashboard","/dashboard"),
      ("user_control","User Control","/admin/user-control")
    """
    key = models.SlugField(max_length=64, unique=True)
    label = models.CharField(max_length=128)
    path = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ["label"]

    def __str__(self):
        return self.label


class UserMenuAccess(models.Model):
    """
    Menus a *non-admin* user is allowed to access.
    (Super Admin/Admin ignore this and get all Menu entries.)
    """
    user = models.ForeignKey(AppUser, on_delete=models.CASCADE, related_name="menu_access")
    menu = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name="user_access")

    class Meta:
        unique_together = (("user", "menu"),)

    def __str__(self):
        return f"{self.user_id} -> {self.menu.key}"
