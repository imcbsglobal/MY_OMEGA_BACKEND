#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myomega_backend.settings')
django.setup()

from User.models import AppUser
from user_controll.models import MenuItem, UserMenuAccess

# Get all active menu items
menu_items = MenuItem.objects.filter(is_active=True)
print(f"✅ Found {menu_items.count()} active menu items")

if menu_items.count() == 0:
    print("❌ No active menu items found in database!")
    print("Please ensure menus are created first.")
    exit(1)

# Get all active users
users = AppUser.objects.filter(is_active=True)
print(f"✅ Found {users.count()} active users")

# Assign all menus to all users
for user in users:
    # Delete existing assignments
    UserMenuAccess.objects.filter(user=user).delete()
    
    # Create new assignments for all menu items
    assignments = [
        UserMenuAccess(
            user=user,
            menu_item=menu_item,
            can_view=True,
            can_edit=False,
            can_delete=False
        )
        for menu_item in menu_items
    ]
    
    UserMenuAccess.objects.bulk_create(assignments)
    print(f"✅ Assigned {len(assignments)} menus to {user.email}")

print("\n✅ All menus assigned to all users!")
