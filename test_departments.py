"""
Test script to check Department model and API
Run with: python manage.py shell < test_departments.py
Or: python test_departments.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myomega_backend.settings')
django.setup()

from cv_management.models import Department

print("=" * 60)
print("Testing Department Model")
print("=" * 60)

try:
    # Test 1: Check if we can query departments
    print("\n1. Fetching all departments...")
    departments = Department.objects.all()
    print(f"   ✓ Found {departments.count()} departments")
    
    for dept in departments:
        print(f"   - ID: {dept.id}, Name: {dept.name}")
    
    # Test 2: Check if we can create a department
    print("\n2. Testing department creation...")
    test_dept, created = Department.objects.get_or_create(
        name="TEST DEPARTMENT"
    )
    if created:
        print(f"   ✓ Created test department: {test_dept.name}")
    else:
        print(f"   ✓ Test department already exists: {test_dept.name}")
    
    # Test 3: Check serializer
    print("\n3. Testing DepartmentSerializer...")
    from cv_management.serializers import DepartmentSerializer
    serializer = DepartmentSerializer(departments, many=True)
    print(f"   ✓ Serializer works! Data: {serializer.data[:2]}")  # Show first 2
    
    # Clean up test department
    if created:
        test_dept.delete()
        print("\n4. Cleaned up test department")
    
    print("\n" + "=" * 60)
    print("✓ All tests passed! Department model is working correctly.")
    print("=" * 60)
    
except Exception as e:
    print(f"\n✗ Error occurred: {str(e)}")
    import traceback
    traceback.print_exc()
    print("\n" + "=" * 60)
    print("✗ Tests failed! Please check the error above.")
    print("=" * 60)
