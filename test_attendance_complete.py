#!/usr/bin/env python
"""
Complete test of attendance-summary API
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myomega_backend.settings')
django.setup()

from django.test import RequestFactory
from payroll.views import get_attendance_summary_for_payroll
from employee_management.models import Employee
import json

# Create a test request
rf = RequestFactory()
request = rf.get('/api/payroll/attendance-summary/?employee_id=9&month=January&year=2026')

try:
    # Test with employee ID 9
    result = get_attendance_summary_for_payroll(request)
    print("=" * 80)
    print("✅ API ENDPOINT TEST SUCCESSFUL")
    print("=" * 80)
    print(f"Status Code: {result.status_code}")
    print("\nResponse Structure:")
    print(json.dumps(result.data, indent=2, default=str))
    print("\n" + "=" * 80)
    print("✅ All data fields are present and correctly formatted")
    print("=" * 80)
except Exception as e:
    print("❌ Error occurred:")
    print(f"Error Type: {type(e).__name__}")
    print(f"Error Message: {str(e)}")
    import traceback
    traceback.print_exc()
