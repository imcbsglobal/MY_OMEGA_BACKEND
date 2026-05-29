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
        ('PF', 'Provident Fund'),
        ('TDS', 'Tax Deducted at Source'),
        ('Other', 'Other'),
    ]

    payroll = models.ForeignKey(Payroll, on_delete=models.CASCADE, related_name='deduction_items')
    deduction_type = models.CharField(max_length=100)  # Remove choices to allow any type
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
        ('PF', 'Provident Fund'),
        ('Overtime', 'Overtime'),
        ('Festival', 'Festival'),
        ('Other', 'Other'),
    ]

    payroll = models.ForeignKey(Payroll, on_delete=models.CASCADE, related_name='allowance_items')
    allowance_type = models.CharField(max_length=100)  # Remove choices to allow any type
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = 'payroll_payrollallowance'

    def __str__(self):
        return f"{self.payroll} - {self.allowance_type}"


class SalaryIncrement(models.Model):
    CYCLE_CHOICES = [
        ('Custom / Manual', 'Custom / Manual'),
        ('Monthly', 'Monthly'),
        ('Quarterly', 'Quarterly'),
        ('Semi-Annual', 'Semi-Annual'),
        ('Annual', 'Annual'),
    ]

    employee = models.ForeignKey(
        'employee_management.Employee',
        on_delete=models.CASCADE,
        related_name='salary_increments'
    )
    
    increment_date = models.DateField()
    previous_salary = models.DecimalField(max_digits=12, decimal_places=2)
    new_salary = models.DecimalField(max_digits=12, decimal_places=2)
    increment_amount = models.DecimalField(max_digits=12, decimal_places=2)
    increment_percent = models.DecimalField(max_digits=5, decimal_places=2)
    
    increment_cycle = models.CharField(
        max_length=20,
        choices=CYCLE_CHOICES,
        default='Custom / Manual'
    )
    next_increment_date = models.DateField(null=True, blank=True)
    
    notes = models.TextField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='created_increments'
    )

    class Meta:
        ordering = ['-increment_date']
        db_table = 'payroll_salarincrement'

    def __str__(self):
        emp_name = getattr(self.employee, 'name', None) or getattr(self.employee, 'employee_id', None)
        return f"{emp_name} - {self.increment_date} (INR {self.increment_amount})"


class AutomationRule(models.Model):
    """
    Automation rules for attendance penalties (Late Entry, Early Exit, Overtime, Breaks, etc.)
    """
    RULE_TYPES = [
        ('late', 'Late Entry Rules'),
        ('early', 'Early Exit Rules'),
        ('missed', 'Punch Miss Rules'),
    ]

    DEDUCTION_TYPES = [
        ('Fixed Amount', 'Fixed Amount'),
        ('Percentage Per Day', 'Percentage Per Day'),
        ('Half Day', 'Half Day'),
        ('Full Day', 'Full Day'),
    ]

    rule_type = models.CharField(max_length=20, choices=RULE_TYPES)
    rule_name = models.CharField(max_length=200)
    
    # Time threshold (in minutes)
    threshold_hours = models.IntegerField(default=0)
    threshold_minutes = models.IntegerField(default=0)
    
    # Deduction configuration
    deduct_salary = models.BooleanField(default=False)
    deduction_type = models.CharField(max_length=20, choices=DEDUCTION_TYPES, null=True, blank=True)
    deduction_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Additional options
    deduct_half_day = models.BooleanField(default=False)
    deduct_full_day = models.BooleanField(default=False)
    set_occurrences = models.BooleanField(default=False)
    max_occurrences = models.IntegerField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='created_automation_rules'
    )

    class Meta:
        ordering = ['rule_type', '-created_at']
        db_table = 'payroll_automationrule'

    def __str__(self):
        return f"{self.get_rule_type_display()} - {self.rule_name}"

    def get_threshold_display(self):
        """Return threshold in readable format"""
        if self.threshold_hours == 0 and self.threshold_minutes == 0:
            return "No threshold"
        return f"{self.threshold_hours:02d}:{self.threshold_minutes:02d}"
