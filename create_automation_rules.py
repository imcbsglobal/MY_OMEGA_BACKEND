#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myomega_backend.settings')
django.setup()

from payroll.models import AutomationRule
from decimal import Decimal

print("Creating AutomationRules for penalty deductions...\n")

# Create Late Arrival Rule
late_rule, created = AutomationRule.objects.update_or_create(
    rule_type='late',
    rule_name='Standard Late Entry Penalty',
    defaults={
        'deduction_type': 'Fixed Amount',
        'deduction_amount': Decimal('30.00'),  # ₹30 per late arrival
        'set_occurrences': True,
        'max_occurrences': 3,  # Grace period: first 3 are allowed
        'is_active': True,
    }
)
print(f"{'Created' if created else 'Updated'} Late Arrival Rule: ₹30 per occurrence (grace: 3)")

# Create Early Exit Rule
early_rule, created = AutomationRule.objects.update_or_create(
    rule_type='early',
    rule_name='Standard Early Exit Penalty',
    defaults={
        'deduction_type': 'Fixed Amount',
        'deduction_amount': Decimal('25.00'),  # ₹25 per early exit
        'set_occurrences': True,
        'max_occurrences': 1,  # Grace period: first 1 is allowed
        'is_active': True,
    }
)
print(f"{'Created' if created else 'Updated'} Early Exit Rule: ₹25 per occurrence (grace: 1)")

# Create Missed Punch Rule (using 'breaks' rule_type as proxy)
missed_rule, created = AutomationRule.objects.update_or_create(
    rule_type='breaks',
    rule_name='Missed Punch Penalty',
    defaults={
        'deduction_type': 'Fixed Amount',
        'deduction_amount': Decimal('60.00'),  # ₹60 per missed punch
        'set_occurrences': True,
        'max_occurrences': 1,  # Grace period: first 1 is allowed
        'is_active': True,
    }
)
print(f"{'Created' if created else 'Updated'} Missed Punch Rule: ₹60 per occurrence (grace: 1)")

print("\n✓ AutomationRules configured successfully!")

