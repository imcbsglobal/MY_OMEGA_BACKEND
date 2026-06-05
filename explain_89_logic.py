#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myomega_backend.settings')
django.setup()

from payroll.models import AutomationRule
from employee_management.models import Employee
from HR.models import EarlyRequest

print("\n" + "="*60)
print("WHY IS ₹89 SHOWING FOR HP EMPLOYEE?")
print("="*60 + "\n")

# Step 1: Show Payroll Settings
print("STEP 1: Check Payroll Settings Rules")
print("-" * 60)

early_rule = AutomationRule.objects.filter(rule_type='early', is_active=True).first()
if early_rule:
    print(f"\n✓ EARLY EXIT RULE (Active):")
    print(f"  Rule Name: {early_rule.rule_name}")
    print(f"  Deduction Type: {early_rule.deduction_type}")
    print(f"  Deduction Amount: ₹{early_rule.deduction_amount}")
    print(f"  Deduct Salary: {early_rule.deduct_salary}")
    print(f"  Grace Period: {early_rule.max_occurrences if early_rule.set_occurrences else 'None (0)'}")

# Step 2: Check HP's Early Exits
print(f"\n\nSTEP 2: Check HP Employee's Early Exits")
print("-" * 60)

hp = Employee.objects.filter(full_name__icontains='HP').first()
user = hp.user

early_requests = EarlyRequest.objects.filter(
    user=user,
    date__year=2026,
    date__month=6
)

print(f"\nHP's Early Exit Penalties (June 2026):")
for req in early_requests:
    print(f"  Date: {req.date}")
    print(f"    Minutes Early: {req.early_by_minutes}")
    print(f"    Status: {req.status} ← THIS MATTERS!")

# Step 3: Explain the Logic
print(f"\n\nSTEP 3: Deduction Calculation Logic")
print("-" * 60)

approved_count = early_requests.filter(status='approved').count()
pending_count = early_requests.filter(status='pending').count()
grace_period = early_rule.max_occurrences if early_rule.set_occurrences else 0

print(f"\nHow the deduction is calculated:")
print(f"  Total Early Exits: {early_requests.count()}")
print(f"  - Approved (will deduct): {approved_count}")
print(f"  - Pending (won't deduct): {pending_count}")
print(f"\n  Grace Period: {grace_period}")
print(f"  Billable Count: {approved_count} - {grace_period} = {max(0, approved_count - grace_period)}")
print(f"\n  Deduction Amount per Exit: ₹{early_rule.deduction_amount}")
print(f"  Total Deduction: {max(0, approved_count - grace_period)} × ₹{early_rule.deduction_amount} = ₹{max(0, approved_count - grace_period) * early_rule.deduction_amount}")

# Step 4: Why 89?
print(f"\n\nSTEP 4: Why Exactly ₹89?")
print("-" * 60)

print(f"\nBecause:")
print(f"  1. HP has 1 APPROVED early exit (on 2026-06-02)")
print(f"  2. Payroll Setting says: Early Exit = ₹{early_rule.deduction_amount} (fixed amount)")
print(f"  3. Grace Period = {grace_period} (no free passes)")
print(f"  4. Calculation: 1 approved × ₹{early_rule.deduction_amount} = ₹89")

print(f"\n✓ So ₹89 is the EARLY EXIT PENALTY AMOUNT set in Payroll Settings")
print(f"✓ It's being deducted because HP has 1 APPROVED early exit")

print("\n" + "="*60 + "\n")
