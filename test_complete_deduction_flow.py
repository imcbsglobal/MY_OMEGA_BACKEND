#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myomega_backend.settings')
django.setup()

from employee_management.models import Employee
from HR.models import EarlyRequest, LateRequest
from HR.daily_penalty_action import apply_daily_penalty_action
from HR.views import attendance_penalty_review
from rest_framework.test import APIRequestFactory
from django.contrib.auth.models import AnonymousUser

print("\n=== Complete Deduction Flow Test ===\n")

hp = Employee.objects.filter(full_name__icontains='HP').first()
user = hp.user

# Reset all to pending
print("Step 1: Reset all penalties to PENDING")
for req in EarlyRequest.objects.filter(user=user, date__year=2026, date__month=6):
    req.status = 'pending'
    req.save()
    print(f"  Early {req.date}: pending")

for req in LateRequest.objects.filter(user=user, date__year=2026, date__month=6):
    req.status = 'pending'
    req.save()
    print(f"  Late {req.date}: pending")

# Check API response BEFORE
print(f"\nStep 2: Check API BEFORE any deducts")
factory = APIRequestFactory()
req = factory.get('/api/hr/penalty-review/?month=6&year=2026&search=HP')
req.user = AnonymousUser()
resp = attendance_penalty_review(req)

if resp.status_code == 200:
    for emp in resp.data['data']['employees']:
        if 'HP' in emp.get('name', ''):
            print(f"  Status: {emp.get('status')}")
            print(f"  Salary Deduction: ₹{emp.get('penalty_amount')}")

# Deduct an early penalty
print(f"\nStep 3: Click DEDUCT on Early Exit (2026-06-02)")
early = EarlyRequest.objects.filter(user=user, date__year=2026, date__month=6).first()
req_deduct = factory.post('/api/hr/penalty-review/daily-action/', {
    'employee_id': hp.id,
    'date': str(early.date),
    'penalty_type': 'early',
    'action': 'deduct'
}, format='json')
req_deduct.user = AnonymousUser()

resp_deduct = apply_daily_penalty_action(req_deduct)
print(f"  Response: {resp_deduct.status_code}")
print(f"  Message: {resp_deduct.data.get('message')}")

early.refresh_from_db()
print(f"  Early Status Now: {early.status}")

# Check API response AFTER
print(f"\nStep 4: Check API AFTER deduct")
req2 = factory.get('/api/hr/penalty-review/?month=6&year=2026&search=HP')
req2.user = AnonymousUser()
resp2 = attendance_penalty_review(req2)

if resp2.status_code == 200:
    for emp in resp2.data['data']['employees']:
        if 'HP' in emp.get('name', ''):
            print(f"  Status: {emp.get('status')}")
            print(f"  Salary Deduction: ₹{emp.get('penalty_amount')}")
            print(f"  Breakdown: {emp.get('deduction_breakdown', [])}")

print("\nStep 5: Expected vs Actual")
print("  Expected:")
print("    - Before: Status=Pending, Deduction=₹0")
print("    - After: Status=Approved, Deduction=₹89")
print(f"\n  Check if salary deduction INCREASED from ₹0 to ₹89")

print("\n=== Test Complete ===\n")
