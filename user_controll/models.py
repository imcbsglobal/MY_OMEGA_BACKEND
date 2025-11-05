# user_controll/models.py
from django.db import models
from django.conf import settings
from User.models import AppUser  # Import your actual user model

class MenuItem(models.Model):
    name = models.CharField(max_length=100)
    key = models.CharField(max_length=100, unique=True)
    path = models.CharField(max_length=200, blank=True)
    icon = models.CharField(max_length=50, blank=True)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="children")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["parent__id", "order", "name"]

    def __str__(self):
        return self.name


class UserMenuAccess(models.Model):
    # CHANGE THIS: Use AppUser directly instead of settings.AUTH_USER_MODEL
    user = models.ForeignKey(
        AppUser,  # Change from settings.AUTH_USER_MODEL to AppUser
        on_delete=models.CASCADE, 
        related_name="user_controll_menu_access"
    )
    menu_item = models.ForeignKey(
        MenuItem, 
        on_delete=models.CASCADE, 
        related_name="user_access"
    )

    class Meta:
        unique_together = ("user", "menu_item")
        db_table = "user_controll_usermenuaccess"  # Keep the same table name

    def __str__(self):
        return f"{self.user.email} -> {self.menu_item.name}"