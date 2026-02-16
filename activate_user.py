#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myomega_backend.settings')
django.setup()

from User.models import AppUser

# Get all users
users = AppUser.objects.all()
print(f"Total users: {users.count()}")

# Activate all inactive users
for user in users:
    if not user.is_active:
        print(f"Activating: {user.email}")
        user.is_active = True
        user.save()
    else:
        print(f"Already active: {user.email}")

print("✅ All users activated!")
