#!/usr/bin/env python3
"""
Quick API test to check call target data
"""
import os
import sys
import django
import json
from datetime import date, timedelta

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myomega_backend.settings')
django.setup()

from django.test import RequestFactory
from target_management.views import CallTargetPeriodListCreateView
from target_management.models import CallTargetPeriod, CallDailyTarget
from employee_management.models import Employee

def test_api_response():
    print("=== Testing Call Target API Response ===\n")
    
    # Check database directly first
    targets = CallTargetPeriod.objects.all()
    print(f"Total call targets in database: {targets.count()}")
    
    if targets.exists():
        print("\nFirst few targets from database:")
        for target in targets[:3]:
            print(f"Target ID: {target.id}")
            print(f"- Employee: {target.employee}")
            print(f"- Period: {target.start_date} to {target.end_date}")
            print(f"- Total target calls (property): {target.total_target_calls}")
            print(f"- Total achieved calls (property): {target.total_achieved_calls}")
            print(f"- Daily targets count: {target.daily_targets.count()}")
            
            # Check individual daily targets
            for dt in target.daily_targets.all()[:3]:
                print(f"  - {dt.target_date}: target={dt.target_calls}, achieved={dt.achieved_calls}")
            print("-" * 50)
    
    # Test API view response
    print("\n=== Testing API View Response ===")
    
    factory = RequestFactory()
    request = factory.get('/target-management/call-targets/')
    
    view = CallTargetPeriodListCreateView()
    view.request = request
    
    # Get serialized data like the API would return
    queryset = view.get_queryset()
    serializer = view.get_serializer(queryset, many=True)
    data = serializer.data
    
    print(f"API would return {len(data)} targets")
    
    if data:
        print("\nFirst target from API serializer:")
        first_target = data[0]
        print(json.dumps(first_target, indent=2, default=str))
        
        print(f"\nKey fields check:")
        print(f"- total_target_calls: {first_target.get('total_target_calls', 'MISSING')}")
        print(f"- total_achieved_calls: {first_target.get('total_achieved_calls', 'MISSING')}")
        print(f"- daily_targets count: {len(first_target.get('daily_targets', []))}")

if __name__ == '__main__':
    test_api_response()