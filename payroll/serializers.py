from rest_framework import serializers
from .models import Payroll, PayrollDeduction, PayrollAllowance


class PayrollDeductionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollDeduction
        fields = ['id', 'deduction_type', 'amount', 'description']


class PayrollAllowanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayrollAllowance
        fields = ['id', 'allowance_type', 'amount', 'description']


class PayrollSerializer(serializers.ModelSerializer):
    # Fix: Use get_full_name() method instead of direct 'name' field
    employee_name = serializers.SerializerMethodField()
    employee_id = serializers.IntegerField(source='employee.id')
    employee_position = serializers.CharField(source='employee.designation', read_only=True)
    deduction_items = PayrollDeductionSerializer(many=True, read_only=True)
    allowance_items = PayrollAllowanceSerializer(many=True, read_only=True)
    
    class Meta:
        model = Payroll
        fields = [
            'id', 'employee_id', 'employee_name', 'employee_position', 'month', 'year',
            'salary', 'attendance_days', 'working_days', 'earned_salary', 'allowances',
            'gross_pay', 'deductions', 'tax', 'net_pay', 'status', 'paid_date',
            'created_at', 'updated_at', 'deduction_items', 'allowance_items'
        ]
        read_only_fields = ['earned_salary', 'gross_pay', 'tax', 'net_pay', 'created_at', 'updated_at']
    
    def get_employee_name(self, obj):
        """Get employee full name safely"""
        return obj.employee.get_full_name() if obj.employee else 'Unknown'


class PayrollListSerializer(serializers.ModelSerializer):
    # Fix: Use get_full_name() method
    employee_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Payroll
        fields = [
            'id', 'employee_name', 'month', 'year', 'gross_pay', 'tax', 'net_pay',
            'attendance_days', 'working_days', 'status', 'paid_date'
        ]
    
    def get_employee_name(self, obj):
        """Get employee full name safely"""
        return obj.employee.get_full_name() if obj.employee else 'Unknown'