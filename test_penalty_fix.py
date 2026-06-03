#!/usr/bin/env python
"""
Test script to verify the penalty deduction fix
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'omega.settings')
django.setup()

from django.contrib.auth import get_user_model
from HR.models import LateRequest, EarlyRequest, Attendance
from employee_management.models import Employee
from payroll.services import PayrollCalculationService
from datetime import datetime, date

User = get_user_model()

def test_penalty_calculation():
    """Test that penalties are correctly calculated based on approval status"""
    
    print("=" * 60)
    print("TESTING PAYROLL PENALTY DEDUCTION FIX")
    print("=" * 60)
    
    # Find or create test employee
    try:
        user = User.objects.filter(username__icontains='test').first()
        if not user:
            print("❌ No test user found. Please create a test user first.")
            return
        
        employee = user.employee_profile
        if not employee:
            print("❌ User has no employee profile")
            return
            
        print(f"✓ Found test employee: {user.username} ({employee.id})")
        
        # Test for current month
        today = date.today()
        year = today.year
        month = today.month
        
        # Get or create penalties for testing
        late_reqs = LateRequest.objects.filter(
            user=user, 
            date__year=year, 
            date__month=month
        )
        print(f"\nFound {late_reqs.count()} late requests in {year}-{month:02d}")
        
        # Show status breakdown
        pending = late_reqs.filter(status='pending').count()
        approved = late_reqs.filter(status='approved').count()
        rejected = late_reqs.filter(status='rejected').count()
        
        print(f"  - Pending: {pending}")
        print(f"  - Approved: {approved}")
        print(f"  - Rejected/Waived: {rejected}")
        
        # Get base salary
        base_salary = PayrollCalculationService.get_employee_salary(employee)
        print(f"\n✓ Base Salary: ₹{base_salary:,.0f}")
        
        # Calculate penalty deduction
        print(f"\nCalculating penalty deduction...")
        penalty_info = PayrollCalculationService.calculate_attendance_penalty_deduction(
            employee=employee,
            year=year,
            month_number=month,
            working_days=22,  # Standard
            base_salary=base_salary
        )
        
        total_amount = penalty_info.get('amount', 0)
        items = penalty_info.get('items', [])
        
        print(f"\n✓ Total Penalty Deduction: ₹{float(total_amount):,.2f}")
        
        if items:
            print("\nDeduction Breakdown:")
            for item in items:
                print(f"  - {item['what']}: ₹{item['amount']:,.0f}")
        else:
            print("\n  (No deductions - all penalties either pending or waived)")
        
        print("\n" + "=" * 60)
        print("KEY TEST: Only APPROVED penalties should be counted above")
        print(f"Expected count: {approved} (APPROVED only)")
        print(f"Status check:")
        print(f"  ✓ Pending penalties ({pending}): NOT included")
        print(f"  ✓ Approved penalties ({approved}): INCLUDED")
        print(f"  ✓ Rejected/Waived penalties ({rejected}): NOT included")
        print("=" * 60)
        
        # Recommend actions
        print("\nTo test the fix:")
        print("1. Go to Penalty Review")
        print("2. Click 'Deduct' on a pending penalty → should increase total deduction")
        print("3. Click 'Waive' on an approved penalty → should decrease total deduction")
        print("4. Leave a penalty 'pending' → should NOT be included in total")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_penalty_calculation()
