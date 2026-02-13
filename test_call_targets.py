#!/usr/bin/env python3
"""
Test script to debug call target issues
"""
import os
import sys
import django
from datetime import date, timedelta

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myomega_backend.settings')
django.setup()

from target_management.models import CallTargetPeriod, CallDailyTarget
from employee_management.models import Employee

def test_call_targets():
    print("=== Call Target Debug Test ===\n")
    
    # Check existing targets
    targets = CallTargetPeriod.objects.all()
    print(f"Found {targets.count()} call target periods")
    
    for target in targets[:3]:  # Check first 3
        print(f"\nTarget ID: {target.id}")
        print(f"Employee: {target.employee}")
        print(f"Period: {target.start_date} to {target.end_date}")
        print(f"Total Target Calls (property): {target.total_target_calls}")
        print(f"Total Achieved Calls (property): {target.total_achieved_calls}")
        print(f"Achievement %: {target.achievement_percentage:.1f}%")
        
        # Check daily targets
        daily_targets = target.daily_targets.all()
        print(f"Daily targets count: {daily_targets.count()}")
        
        if daily_targets.exists():
            print("First 5 daily targets:")
            for dt in daily_targets[:5]:
                print(f"  {dt.target_date}: Target={dt.target_calls}, Achieved={dt.achieved_calls}")
            
            # Check for zero targets
            zero_targets = daily_targets.filter(target_calls=0).count()
            if zero_targets > 0:
                print(f"⚠️  WARNING: {zero_targets} daily targets have target_calls=0")
        
        print("-" * 50)
    
    # Test creating a new target with daily targets
    print("\n=== Test Creating New Target ===")
    
    # Get first employee
    employee = Employee.objects.first()
    if not employee:
        print("No employees found. Create an employee first.")
        return
    
    print(f"Testing with employee: {employee}")
    
    # Test data
    start_date = date.today() + timedelta(days=7)  # Next week
    end_date = start_date + timedelta(days=6)      # 7-day period
    
    test_daily_targets = []
    current_date = start_date
    while current_date <= end_date:
        day_of_week = current_date.weekday()
        target_calls = 20 if day_of_week in [5, 6] else 30
        
        test_daily_targets.append({
            'target_date': current_date,
            'target_calls': target_calls,
            'achieved_calls': 0,
            'productive_calls': 0,
            'order_received': 0,
            'order_amount': 0.0,
            'remarks': 'Test target'
        })
        current_date += timedelta(days=1)
    
    print(f"Creating test target with {len(test_daily_targets)} daily targets")
    
    # Create the target period
    test_target = CallTargetPeriod.objects.create(
        employee=employee,
        start_date=start_date,
        end_date=end_date,
        notes="Test target for debugging",
        is_active=True
    )
    
    # Create daily targets
    for dt_data in test_daily_targets:
        CallDailyTarget.objects.create(
            call_target_period=test_target,
            **dt_data
        )
    
    print(f"✅ Created test target ID: {test_target.id}")
    print(f"Total target calls: {test_target.total_target_calls}")
    print(f"Expected total: {sum(dt['target_calls'] for dt in test_daily_targets)}")
    
    if test_target.total_target_calls > 0:
        print("✅ SUCCESS: Target calls are calculating correctly!")
    else:
        print("❌ FAILED: Target calls still showing as 0")
    
    print("\nTest completed.")

if __name__ == '__main__':
    test_call_targets()