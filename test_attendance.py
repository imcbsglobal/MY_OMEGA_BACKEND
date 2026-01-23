#!/usr/bin/env python
"""
Test script to debug attendance-summary API
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myomega_backend.settings')
django.setup()

from django.test import RequestFactory
from payroll.views import get_attendance_summary_for_payroll
from employee_management.models import Employee

# Create a test request
rf = RequestFactory()
request = rf.get('/api/payroll/attendance-summary/?employee_id=9&month=January&year=2026')

try:
    # Test with employee ID 9
    result = get_attendance_summary_for_payroll(request)
    print("Response Status:", result.status_code)
    print("Response Data:", result.data)
except Exception as e:
    print("Error Type:", type(e).__name__)
    print("Error Message:", str(e))
    import traceback
    traceback.print_exc()
