#!/usr/bin/env python
"""
Smoke test for attendance-related APIs with authentication.
"""
import os
import sys
from pathlib import Path
import django

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myomega_backend.settings')
django.setup()

from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework.response import Response
from payroll.views import get_all_employees_attendance_summary
from User.models import AppUser


def get_active_user():
    user = AppUser.objects.filter(is_active=True).first()
    if not user:
        # Fallback: pick any user
        user = AppUser.objects.first()
    return user


def run():
    rf = APIRequestFactory()
    user = get_active_user()
    if not user:
        print("❌ No users found to authenticate; cannot run test.")
        return
    print(f"🔐 Using user: {getattr(user, 'email', user.id)} (active={user.is_active})")

    # Test default (active-only)
    req1 = rf.get('/api/payroll/attendance-summaries/all/?month=January&year=2026')
    force_authenticate(req1, user=user)
    res1 = get_all_employees_attendance_summary(req1)
    print("\n=== Default (active-only) ===")
    print("Status:", res1.status_code)
    data1 = getattr(res1, 'data', {})
    print("Total employees:", data1.get('total_employees'))

    # Test explicit inactive filter
    req2 = rf.get('/api/payroll/attendance-summaries/all/?month=January&year=2026&is_active=false')
    force_authenticate(req2, user=user)
    res2 = get_all_employees_attendance_summary(req2)
    print("\n=== Inactive filter (is_active=false) ===")
    print("Status:", res2.status_code)
    data2 = getattr(res2, 'data', {})
    print("Total employees:", data2.get('total_employees'))


if __name__ == '__main__':
    run()
