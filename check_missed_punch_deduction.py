#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'omega.settings')
django.setup()

from django.contrib.auth.models import User
from employee_management.models import Employee
from HR.models import Attendance
from payroll.services import PayrollCalculationService

# Find HP user
users = User.objects.filter(email__icontains='heura')
if users.exists():
    user = users.first()
    print(f"User: {user.email}")
    print("=" * 80)
    
    # Check May 2026 attendance
    may_records = Attendance.objects.filter(
        user=user,
        date__year=2026,
        date__month=5
    ).order_by('date').values('date', 'admin_note', 'status')
    
    print("\n📋 May 2026 Attendance Records:")
    print("-" * 80)
    for rec in may_records:
        note = rec['admin_note'][:70] if rec['admin_note'] else 'NO NOTE'
        print(f"  {rec['date']}: {rec['status']:<10} | {note}")
    
    # Check for deducted missed punches
    deducted = Attendance.objects.filter(
        user=user,
        date__year=2026,
        date__month=5,
        admin_note__icontains='deduct'
    ).values('date', 'admin_note')
    
    print(f"\n✅ Records with 'deduct' keyword: {deducted.count()}")
    print("-" * 80)
    for rec in deducted:
        print(f"  {rec['date']}: {rec['admin_note'][:80]}")
    
    # Now calculate deduction
    print(f"\n💰 Deduction Calculation for May 2026:")
    print("-" * 80)
    emp = Employee.objects.filter(user=user).first()
    if emp:
        try:
            result = PayrollCalculationService.calculate_attendance_penalty_deduction(
                emp, 2026, 5, 22, 50000
            )
            print(f"  Total Deduction Amount: ₹{result.get('amount', 0)}")
            print(f"  Items:")
            for item in result.get('items', []):
                print(f"    - {item.get('what')}: ₹{item.get('amount', 0)}")
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
    else:
        print("  ❌ Employee not found")
        
else:
    print("❌ User not found")
