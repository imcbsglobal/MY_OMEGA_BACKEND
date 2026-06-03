#!/usr/bin/env python
"""Check what automation rules exist"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'omega.settings')
django.setup()

from payroll.models import AutomationRule

print("=" * 60)
print("AUTOMATION RULES CHECK")
print("=" * 60)

rules = AutomationRule.objects.all()
print(f"\nTotal rules found: {rules.count()}\n")

if not rules.exists():
    print("❌ NO AUTOMATION RULES FOUND!")
    print("\nYou need to create automation rules for penalties to be deducted.")
    print("Go to Payroll Settings and create rules for:")
    print("  - Late Entry (late)")
    print("  - Early Exit (early)")
    print("  - Punch Miss (missed)")
    print("\nMake sure to check 'Deduct salary' when creating the rules!")
else:
    print("Found rules:")
    for rule in rules:
        print(f"\n  Type: {rule.rule_type}")
        print(f"  Name: {rule.rule_name}")
        print(f"  Active: {rule.is_active}")
        print(f"  Deduct Salary: {rule.deduct_salary}")
        print(f"  Deduction Type: {rule.deduction_type}")
        print(f"  Deduction Amount: {rule.deduction_amount}")
        print(f"  Threshold: {rule.threshold_hours}h {rule.threshold_minutes}m")

print("\n" + "=" * 60)
