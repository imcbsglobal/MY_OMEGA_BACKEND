#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myomega_backend.settings')
django.setup()

from HR.utils.attendance_penalties import calculate_monthly_penalties
from payroll.services import PayrollCalculationService
from User.models import AppUser

# Get the test user
user = AppUser.objects.get(email='test+penalty@example.com')
print(f'Testing penalty calculation for {user.email}...\n')

# Calculate penalties for May 2026
penalties = calculate_monthly_penalties(user, 2026, 5)

print('Per-date breakdown:')
for date, data in penalties['per_date'].items():
    print(f'  {date}: late_minutes={data["late_minutes"]}, late_deduction={data["late_deduction_days"]}')

print(f'\nPenalty Summary:')
summary = penalties['summary']
for key, value in summary.items():
    print(f'  {key}: {value}')

# Now test the deduction calculation
base_salary = 50000
deduction_result = PayrollCalculationService.calculate_attendance_penalty_deduction(
    employee=user.employee_profile,
    year=2026,
    month_number=5,
    working_days=22,
    base_salary=base_salary,
)

print(f'\n\nDeduction Calculation Result:')
print(f'  Total amount: {deduction_result.get("amount", 0)}')
print(f'  Items: {deduction_result.get("items", [])}')
