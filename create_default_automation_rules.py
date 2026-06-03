#!/usr/bin/env python
"""
Create default automation rules for penalty deductions
Run this once to set up penalty rules
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'omega.settings')
django.setup()

from payroll.models import AutomationRule
from decimal import Decimal

print("=" * 60)
print("CREATING DEFAULT AUTOMATION RULES")
print("=" * 60)

# Define default rules
default_rules = [
    {
        'rule_type': 'late',
        'rule_name': 'Late Entry - 15 mins',
        'threshold_hours': 0,
        'threshold_minutes': 15,
        'deduct_salary': True,
        'deduction_type': 'Fixed Amount',
        'deduction_amount': Decimal('100.00'),
        'set_occurrences': True,
        'max_occurrences': 1,  # Grace period: first occurrence is free
    },
    {
        'rule_type': 'early',
        'rule_name': 'Early Exit - 15 mins',
        'threshold_hours': 0,
        'threshold_minutes': 15,
        'deduct_salary': True,
        'deduction_type': 'Fixed Amount',
        'deduction_amount': Decimal('100.00'),
        'set_occurrences': True,
        'max_occurrences': 1,  # Grace period: first occurrence is free
    },
    {
        'rule_type': 'missed',
        'rule_name': 'Missed Punch',
        'threshold_hours': 0,
        'threshold_minutes': 0,
        'deduct_salary': True,
        'deduction_type': 'Half Day',
        'deduction_amount': Decimal('0.00'),  # Not used for Half Day type
        'set_occurrences': False,
        'max_occurrences': None,
    },
]

created_count = 0
skipped_count = 0

for rule_config in default_rules:
    # Check if rule already exists
    existing = AutomationRule.objects.filter(
        rule_type=rule_config['rule_type'],
        rule_name=rule_config['rule_name']
    ).first()
    
    if existing:
        print(f"\n⊘ Skipping {rule_config['rule_type'].upper()}: '{rule_config['rule_name']}' (already exists)")
        skipped_count += 1
    else:
        rule = AutomationRule.objects.create(
            rule_type=rule_config['rule_type'],
            rule_name=rule_config['rule_name'],
            threshold_hours=rule_config['threshold_hours'],
            threshold_minutes=rule_config['threshold_minutes'],
            deduct_salary=rule_config['deduct_salary'],
            deduction_type=rule_config['deduction_type'],
            deduction_amount=rule_config['deduction_amount'],
            set_occurrences=rule_config.get('set_occurrences', False),
            max_occurrences=rule_config.get('max_occurrences'),
            is_active=True,
        )
        print(f"\n✓ Created {rule_config['rule_type'].upper()}: '{rule.rule_name}'")
        print(f"  - Deduction: {rule.deduction_type} - ₹{rule.deduction_amount}")
        print(f"  - Threshold: {rule.threshold_hours}h {rule.threshold_minutes}m")
        print(f"  - Grace period: {rule.max_occurrences} occurrences" if rule.set_occurrences else "  - No grace period")
        created_count += 1

print("\n" + "=" * 60)
print(f"Summary: {created_count} created, {skipped_count} skipped")
print("=" * 60)

if created_count > 0:
    print("\n✅ Default rules created successfully!")
    print("\nNow penalties will be deducted:")
    print("  - Late Entry: ₹100 per occurrence (1st occurrence free)")
    print("  - Early Exit: ₹100 per occurrence (1st occurrence free)")
    print("  - Missed Punch: Half day deduction")
else:
    print("\n⊘ No new rules created (all already exist)")

print("\nTo modify these rules, go to:")
print("  Payroll Settings → Automation Rules → Edit")
