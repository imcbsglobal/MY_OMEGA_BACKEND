# user_controll/models.py
from django.db import models
from User.models import AppUser  # your custom user model

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
    """
    Join table mapping AppUser -> MenuItem with per-action permissions.
    """
    user = models.ForeignKey(
        AppUser,
        on_delete=models.CASCADE,
        related_name="user_controll_menu_access"
    )
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.CASCADE,
        related_name="user_access"
    )

    # Per-action permissions
    can_view = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "menu_item")
        db_table = "user_controll_usermenuaccess"

    def __str__(self):
        return f"{self.user.email} -> {self.menu_item.name} (V:{self.can_view} E:{self.can_edit} D:{self.can_delete})"
    






class ApprovalCategory(models.Model):
    """Categories for approval workflows (e.g., Attendance, Leave)"""
    name = models.CharField(max_length=100, unique=True)
    key = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = "Approval Categories"

    def __str__(self):
        return self.name


class UserApprovalPermission(models.Model):
    """Grant approval permissions to users for specific categories"""
    user = models.ForeignKey(
        AppUser,
        on_delete=models.CASCADE,
        related_name="approval_permissions"
    )
    category = models.ForeignKey(
        ApprovalCategory,
        on_delete=models.CASCADE,
        related_name="user_permissions"
    )
    can_approve = models.BooleanField(default=False)
    can_reject = models.BooleanField(default=False)
    can_view_all = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'category')
        db_table = 'user_controll_userapproval'

    def __str__(self):
        return f"{self.user.email} -> {self.category.name}"    
