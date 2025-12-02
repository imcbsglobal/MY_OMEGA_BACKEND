# payroll/models.py
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal

# Use string references where possible to avoid import-time issues:
# - 'employee_management.Employee' will be resolved by Django's app registry.

class Payroll(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Cancelled', 'Cancelled'),
    ]

    # Refer to Employee by string to avoid import-time resolution problems
    employee = models.ForeignKey(
        'employee_management.Employee',
        on_delete=models.CASCADE,
        related_name='payrolls'
    )

    month = models.CharField(max_length=20)  # e.g., "November"
    year = models.IntegerField()
    salary = models.DecimalField(max_digits=12, decimal_places=2)

    # Attendance
    attendance_days = models.IntegerField(validators=[MinValueValidator(0)])
    working_days = models.IntegerField(default=22)

    # Earnings
    earned_salary = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    allowances = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    gross_pay = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    # Deductions
    deductions = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    # Final
    net_pay = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    paid_date = models.DateField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # IMPORTANT: use settings.AUTH_USER_MODEL instead of direct User model
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='created_payrolls'
    )

    class Meta:
        ordering = ['-created_at']
        unique_together = ['employee', 'month', 'year']
        db_table = 'payroll_payroll'

    def __str__(self):
        # defensive: Employee might not have attribute 'name'
        emp_repr = getattr(self.employee, 'employee_id', None) or getattr(self.employee, 'id', None)
        try:
            name = getattr(self.employee, 'get_full_name', None)
            if callable(name):
                emp_name = name()
            else:
                emp_name = getattr(self.employee, 'name', None) or getattr(self.employee, 'user', None)
        except Exception:
            emp_name = None

        if emp_name:
            return f"{emp_name} - {self.month} {self.year}"
        return f"Employee {emp_repr} - {self.month} {self.year}"


class PayrollDeduction(models.Model):
    DEDUCTION_TYPES = [
        ('Insurance', 'Insurance'),
        ('Loan', 'Loan'),
        ('Advance', 'Advance'),
        ('Other', 'Other'),
    ]

    payroll = models.ForeignKey(Payroll, on_delete=models.CASCADE, related_name='deduction_items')
    deduction_type = models.CharField(max_length=40, choices=DEDUCTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = 'payroll_payrolldeduction'

    def __str__(self):
        return f"{self.payroll} - {self.deduction_type}"


class PayrollAllowance(models.Model):
    ALLOWANCE_TYPES = [
        ('HRA', 'House Rent Allowance'),
        ('DA', 'Dearness Allowance'),
        ('Bonus', 'Bonus'),
        ('Incentive', 'Incentive'),
        ('Other', 'Other'),
    ]

    payroll = models.ForeignKey(Payroll, on_delete=models.CASCADE, related_name='allowance_items')
    allowance_type = models.CharField(max_length=40, choices=ALLOWANCE_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = 'payroll_payrollallowance'

    def __str__(self):
        return f"{self.payroll} - {self.allowance_type}"
