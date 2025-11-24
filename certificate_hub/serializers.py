from rest_framework import serializers
from .models import SalaryCertificate, ExperienceCertificate
from employee_management.models import Employee


class SalaryCertificateSerializer(serializers.ModelSerializer):
    emp_name = serializers.CharField(source='employee.full_name', read_only=True)
    emp_email = serializers.EmailField(source='employee.user.email', read_only=True)
    emp_designation = serializers.CharField(source='employee.designation', read_only=True)
    emp_department = serializers.CharField(source='employee.department', read_only=True)
    emp_joining_date = serializers.DateField(source='employee.date_of_joining', read_only=True)
    emp_location = serializers.CharField(source='employee.location', read_only=True)
    generated_by_name = serializers.CharField(source='generated_by.name', read_only=True)
    
    class Meta:
        model = SalaryCertificate
        fields = [
            'id',
            'employee',
            'emp_name',
            'emp_email',
            'emp_designation',
            'emp_department',
            'emp_joining_date',
            'emp_location',
            'salary',
            'issued_date',
            'generated_by',
            'generated_by_name'
        ]
        read_only_fields = ['issued_date', 'generated_by', 'generated_by_name']
    
    # def validate_employee(self, value):
    #     """Ensure employee is active"""
    #     if not value.is_active:
    #         raise serializers.ValidationError("Cannot create salary certificate for inactive employee.")
    #     return value
    
    def validate_salary(self, value):
        """Ensure salary is positive"""
        if value <= 0:
            raise serializers.ValidationError("Salary must be greater than zero.")
        return value
    

class ExperienceCertificateSerializer(serializers.ModelSerializer):
    emp_name = serializers.CharField(source='employee.full_name', read_only=True)
    emp_email = serializers.EmailField(source='employee.user.email', read_only=True)
    emp_designation = serializers.CharField(source='employee.designation', read_only=True)
    emp_department = serializers.CharField(source='employee.department', read_only=True)
    emp_location = serializers.CharField(source='employee.location', read_only=True)
    offer_letter_joining = serializers.DateField(source='offer_letter.joining_data', read_only=True)
    generated_by_name = serializers.CharField(source='generated_by.name', read_only=True)

    class Meta:
        model = ExperienceCertificate
        fields = [
            'id',
            'employee',
            'emp_name',
            'emp_email',
            'emp_designation',
            'emp_department',
            'emp_location',
            'offer_letter',
            'offer_letter_joining',
            'joining_date',
            'issue_date',
            'generated_by',
            'generated_by_name'
        ]
        read_only_fields = ['issue_date', 'generated_by', 'generated_by_name', 'offer_letter_joining']
    
    def validate_joining_date(self, value):
        """Ensure joining date is not in the future"""
        from datetime import date
        if value and value > date.today():
            raise serializers.ValidationError("Joining date cannot be in the future.")
        return value