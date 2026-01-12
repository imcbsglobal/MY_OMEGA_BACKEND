from rest_framework import serializers
from .models import Payroll, PayrollDeduction, PayrollAllowance


# =========================
# PAYROLL DEDUCTION
# =========================
class PayrollDeductionSerializer(serializers.ModelSerializer):
    # 🔹 NEW FIELDS
    employee_id = serializers.IntegerField(
        source='payroll.employee.id',
        read_only=True
    )
    employee_name = serializers.SerializerMethodField()
    year = serializers.IntegerField(source='payroll.year', read_only=True)
    month = serializers.CharField(source='payroll.month', read_only=True)

    class Meta:
        model = PayrollDeduction
        fields = [
            'id',
            'deduction_type',
            'amount',
            'description',
            'employee_id',
            'employee_name',
            'year',
            'month',
        ]

    def get_employee_name(self, obj):
        """
        Safely return employee full name
        """
        employee = getattr(obj.payroll, 'employee', None)
        if not employee:
            return 'Unknown'

        # Try get_full_name() first
        if hasattr(employee, 'get_full_name') and callable(employee.get_full_name):
            try:
                name = employee.get_full_name()
                if name and name.strip():
                    return name
            except Exception:
                pass

        # Try full_name attribute
        if hasattr(employee, 'full_name') and employee.full_name:
            return employee.full_name

        # Try name attribute
        if hasattr(employee, 'name') and employee.name:
            return employee.name

        # Try first_name + last_name
        first = getattr(employee, 'first_name', '')
        last = getattr(employee, 'last_name', '')
        if first or last:
            return f"{first} {last}".strip()

        # Fallback to employee_id or id
        emp_id = getattr(employee, 'employee_id', None) or getattr(employee, 'id', None)
        return f'Employee_{emp_id}' if emp_id else 'Unknown'

    def create(self, validated_data):
        # Normalize deduction_type to uppercase before saving
        deduction_type = validated_data.get('deduction_type')
        if deduction_type:
            validated_data['deduction_type'] = deduction_type.strip().upper()
        return super().create(validated_data)

    def update(self, instance, validated_data):
        deduction_type = validated_data.get('deduction_type')
        if deduction_type:
            validated_data['deduction_type'] = deduction_type.strip().upper()
        return super().update(instance, validated_data)


# =========================
# PAYROLL ALLOWANCE
# =========================
class PayrollAllowanceSerializer(serializers.ModelSerializer):
    # 🔹 NEW FIELDS
    employee_id = serializers.IntegerField(
        source='payroll.employee.id',
        read_only=True
    )
    employee_name = serializers.SerializerMethodField()
    year = serializers.IntegerField(source='payroll.year', read_only=True)
    month = serializers.CharField(source='payroll.month', read_only=True)

    class Meta:
        model = PayrollAllowance
        fields = [
            'id',
            'allowance_type',
            'amount',
            'description',
            'employee_id',
            'employee_name',
            'year',
            'month',
        ]

    def get_employee_name(self, obj):
        """
        Safely return employee full name
        """
        employee = getattr(obj.payroll, 'employee', None)
        if not employee:
            return 'Unknown'

        # Try get_full_name() first
        if hasattr(employee, 'get_full_name') and callable(employee.get_full_name):
            try:
                name = employee.get_full_name()
                if name and name.strip():
                    return name
            except Exception:
                pass

        # Try full_name attribute
        if hasattr(employee, 'full_name') and employee.full_name:
            return employee.full_name

        # Try name attribute
        if hasattr(employee, 'name') and employee.name:
            return employee.name

        # Try first_name + last_name
        first = getattr(employee, 'first_name', '')
        last = getattr(employee, 'last_name', '')
        if first or last:
            return f"{first} {last}".strip()

        # Fallback to employee_id or id
        emp_id = getattr(employee, 'employee_id', None) or getattr(employee, 'id', None)
        return f'Employee_{emp_id}' if emp_id else 'Unknown'

    def create(self, validated_data):
        # Normalize allowance_type to uppercase before saving
        allowance_type = validated_data.get('allowance_type')
        if allowance_type:
            validated_data['allowance_type'] = allowance_type.strip().upper()
        return super().create(validated_data)

    def update(self, instance, validated_data):
        allowance_type = validated_data.get('allowance_type')
        if allowance_type:
            validated_data['allowance_type'] = allowance_type.strip().upper()
        return super().update(instance, validated_data)


# =========================
# PAYROLL DETAIL SERIALIZER
# =========================
class PayrollSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    employee_id = serializers.IntegerField(source='employee.id')
    employee_position = serializers.CharField(
        source='employee.designation',
        read_only=True
    )

    deduction_items = PayrollDeductionSerializer(many=True, read_only=True)
    allowance_items = PayrollAllowanceSerializer(many=True, read_only=True)

    class Meta:
        model = Payroll
        fields = [
            'id',
            'employee_id',
            'employee_name',
            'employee_position',
            'month',
            'year',
            'salary',
            'attendance_days',
            'working_days',
            'earned_salary',
            'allowances',
            'gross_pay',
            'deductions',
            'tax',
            'net_pay',
            'status',
            'paid_date',
            'created_at',
            'updated_at',
            'deduction_items',
            'allowance_items',
        ]

        read_only_fields = [
            'earned_salary',
            'gross_pay',
            'tax',
            'net_pay',
            'created_at',
            'updated_at',
        ]

    def get_employee_name(self, obj):
        """
        Get employee full name safely
        """
        return obj.employee.get_full_name() if obj.employee else 'Unknown'


# =========================
# PAYROLL LIST SERIALIZER
# =========================
class PayrollListSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()

    class Meta:
        model = Payroll
        fields = [
            'id',
            'employee_name',
            'month',
            'year',
            'gross_pay',
            'tax',
            'net_pay',
            'attendance_days',
            'working_days',
            'status',
            'paid_date',
        ]

    def get_employee_name(self, obj):
        """
        Get employee full name safely
        """
        return obj.employee.get_full_name() if obj.employee else 'Unknown'
