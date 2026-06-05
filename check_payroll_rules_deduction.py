#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myomega_backend.settings')
django.setup()

from payroll.models import AutomationRule
from employee_management.models import Employee
from HR.models import EarlyRequest
from payroll.services import PayrollCalculationService

print("\n=== Checking Payroll Rules & Deduction ===\n")

# Show all rules
print("--- Active Automation Rules ---\n")
for rule in AutomationRule.objects.filter(is_active=True):
    print(f"Rule Type: {rule.rule_type}")
    print(f"  Name: {rule.rule_name}")
    print(f"  Deduction Type: {rule.deduction_type}")
    print(f"  Deduction Amount: {rule.deduction_amount}")
    print(f"  Deduct Salary: {rule.deduct_salary}")
    print(f"  Set Occurrences: {rule.set_occurrences}")
    print(f"  Max Occurrences: {rule.max_occurrences}")
    print()

# Test with HP
hp = Employee.objects.filter(full_name__icontains='HP').first()
if not hp:
    print("HP not found")
    sys.exit(1)

user = hp.user
base_salary = float(getattr(hp, 'basic_salary', 0) or 0)

print(f"\n--- Testing HP Deduction ---")
print(f"Base Salary: ₹{base_salary}")

# Get approved early requests
early_approved = EarlyRequest.objects.filter(
    user=user,
    date__year=2026,
    date__month=6,
    status='approved'
)

print(f"\nApproved Early Requests: {early_approved.count()}")
for req in early_approved:
    print(f"  - {req.date}: {req.early_by_minutes} min early")

# Calculate deduction
result = PayrollCalculationService.calculate_attendance_penalty_deduction(
    employee=hp,
    year=2026,
    month_number=6,
    working_days=22,
    base_salary=base_salary,
)

print(f"\n--- Deduction Calculation ---")
print(f"Total Amount: ₹{result['amount']}")
print(f"\nBreakdown:")
for item in result['items']:
    print(f"  {item['deduction_type']}: {item['what']}")
    print(f"    Amount: ₹{item['amount']}")
    print(f"    Rule: {item.get('description', 'N/A')}")

print("\n=== Check Complete ===\n")
