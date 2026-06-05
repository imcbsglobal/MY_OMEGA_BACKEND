#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myomega_backend.settings')
django.setup()

from HR.views import attendance_penalty_review
from rest_framework.test import APIRequestFactory
from django.contrib.auth.models import AnonymousUser
from employee_management.models import Employee
from HR.models import EarlyRequest

print("\n=== Checking API Penalty Amount Response ===\n")

# Get HP
hp = Employee.objects.filter(full_name__icontains='HP').first()
early = EarlyRequest.objects.filter(user=hp.user, date__year=2026, date__month=6).first()

print(f"HP Early Request Status BEFORE: {early.status}")

# Make API request
factory = APIRequestFactory()
request = factory.get('/api/hr/penalty-review/?month=6&year=2026&page=1&page_size=8&search=HP')
request.user = AnonymousUser()

response = attendance_penalty_review(request)

if response.status_code == 200:
    data = response.data.get('data', {})
    employees = data.get('employees', [])
    
    for emp in employees:
        if emp.get('name') and 'HP' in emp['name']:
            print(f"\n--- API Response for HP ---")
            print(f"Name: {emp['name']}")
            print(f"Status: {emp.get('status')}")
            print(f"Status Display: {emp.get('status_display')}")
            print(f"\nPenalty Counts:")
            print(f"  Late: {emp.get('late')}")
            print(f"  Early: {emp.get('early')}")
            print(f"  Missed: {emp.get('missed')}")
            print(f"  Total Penalty: {emp.get('total_penalty')}")
            print(f"\nDeduction Info:")
            print(f"  Base Salary: ₹{emp.get('base_salary')}")
            print(f"  Penalty Amount (SALARY DEDUCTION): ₹{emp.get('penalty_amount')}")
            print(f"  Amount After Penalties: ₹{emp.get('amount_after_penalties')}")
            
            print(f"\nDeduction Breakdown:")
            breakdown = emp.get('deduction_breakdown', [])
            if breakdown:
                for item in breakdown:
                    print(f"  {item.get('what')}: ₹{item.get('amount')}")
            else:
                print(f"  (no breakdown)")
            
            print(f"\nRequest Counts:")
            print(f"  Late: {emp.get('late_request_count')}")
            print(f"  Early: {emp.get('early_request_count')}")
            print(f"  Pending: {emp.get('pending_request_count')}")
            print(f"  Approved: {emp.get('approved_request_count')}")
            print(f"  Rejected: {emp.get('rejected_request_count')}")
else:
    print(f"API Error: {response.status_code}")

print("\n=== Check Complete ===\n")
