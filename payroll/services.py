# payroll/services.py - UPDATED: Tax removed from calculations

from decimal import Decimal
from datetime import datetime, timedelta
from django.db.models import Q
from HR.models import Attendance, Holiday, EmployeeLeaveBalance


class PayrollCalculationService:
    """
    Service to calculate payroll with proper leave handling
    """
    
    # Map month names to numbers
    MONTH_NAME_TO_NUMBER = {
        'January': 1, 'February': 2, 'March': 3, 'April': 4,
        'May': 5, 'June': 6, 'July': 7, 'August': 8,
        'September': 9, 'October': 10, 'November': 11, 'December': 12
    }
    
    @staticmethod
    def get_month_dates(year, month):
        """Get all dates in a month"""
        first_day = datetime(year, month, 1).date()
        if month == 12:
            last_day = datetime(year, 12, 31).date()
        else:
            last_day = (datetime(year, month + 1, 1) - timedelta(days=1)).date()
        
        dates = []
        current = first_day
        while current <= last_day:
            dates.append(current)
            current += timedelta(days=1)
        
        return dates
    
    @staticmethod
    def get_sundays_count(year, month):
        """Count Sundays in a month"""
        dates = PayrollCalculationService.get_month_dates(year, month)
        return sum(1 for d in dates if d.weekday() == 6)
    
    @staticmethod
    def get_holidays_in_month(year, month):
        """Get holidays in a month with their types"""
        dates = PayrollCalculationService.get_month_dates(year, month)
        first_day = dates[0]
        last_day = dates[-1]
        
        holidays = Holiday.objects.filter(
            date__gte=first_day,
            date__lte=last_day,
            is_active=True
        ).values('date', 'name', 'holiday_type')
        
        holiday_dict = {}
        for h in holidays:
            holiday_dict[h['date']] = {
                'name': h['name'],
                'type': h['holiday_type'],
                'is_paid': h['holiday_type'] in ['mandatory', 'special']
            }
        
        return holiday_dict
    
    @staticmethod
    def get_employee_salary(employee):
        """
        Get employee's basic salary from multiple possible locations
        """
        salary_fields = [
            'basic_salary',
            'salary',
            'base_salary',
        ]
        
        # Check employee directly
        for field in salary_fields:
            if hasattr(employee, field):
                value = getattr(employee, field)
                if value and float(value) > 0:
                    return Decimal(str(value))
        
        # Check job_info if it exists
        if hasattr(employee, 'job_info') and employee.job_info:
            for field in salary_fields:
                if hasattr(employee.job_info, field):
                    value = getattr(employee.job_info, field)
                    if value and float(value) > 0:
                        return Decimal(str(value))
        
        # Check employment_details if it exists
        if hasattr(employee, 'employment_details') and employee.employment_details:
            for field in salary_fields:
                if hasattr(employee.employment_details, field):
                    value = getattr(employee.employment_details, field)
                    if value and float(value) > 0:
                        return Decimal(str(value))
        
        return Decimal('0')
    
    @staticmethod
    def calculate_employee_payroll_data(employee, year, month):
        """
        Calculate comprehensive payroll data for an employee
        """
        dates = PayrollCalculationService.get_month_dates(year, month)
        total_days_in_month = len(dates)
        
        holidays = PayrollCalculationService.get_holidays_in_month(year, month)
        mandatory_holidays_count = sum(1 for h in holidays.values() if h['type'] == 'mandatory')
        special_holidays_count = sum(1 for h in holidays.values() if h['type'] == 'special')
        total_paid_holidays = mandatory_holidays_count + special_holidays_count
        
        sundays_count = PayrollCalculationService.get_sundays_count(year, month)
        
        user_for_attendance = employee.user if hasattr(employee, 'user') else employee
        
        attendances = Attendance.objects.filter(
            user=user_for_attendance,
            date__in=dates
        ).select_related('user')
        
        attendance_dict = {att.date: att for att in attendances}
        
        full_days_worked = 0
        half_days_worked = 0
        casual_leave_days = 0
        sick_leave_days = 0
        special_leave_days = 0
        unpaid_leave_days = 0
        wfh_days = 0
        not_marked_days = 0
        
        for date in dates:
            if date.weekday() == 6:
                continue
            
            if date in holidays:
                continue
            
            if date in attendance_dict:
                att = attendance_dict[date]
                status = att.status
                
                if status == 'full':
                    full_days_worked += 1
                elif status == 'half':
                    half_days_worked += 0.5
                elif status == 'casual_leave':
                    casual_leave_days += 1
                elif status == 'sick_leave':
                    sick_leave_days += 1
                elif status == 'special_leave':
                    special_leave_days += 1
                elif status == 'unpaid_leave':
                    unpaid_leave_days += 1
                elif status == 'wfh':
                    wfh_days += 1
                elif status in ['mandatory_holiday', 'special_holiday']:
                    pass
                else:
                    not_marked_days += 1
            else:
                not_marked_days += 1
        
        total_working_days = total_days_in_month - sundays_count - total_paid_holidays
        
        paid_working_days = (
            full_days_worked + 
            half_days_worked + 
            casual_leave_days + 
            sick_leave_days + 
            special_leave_days +
            wfh_days
        )
        
        total_paid_days = (
            paid_working_days + 
            total_paid_holidays + 
            sundays_count
        )
        
        days_to_deduct = unpaid_leave_days + not_marked_days
        effective_paid_days = total_working_days - days_to_deduct
        
        try:
            leave_balance = EmployeeLeaveBalance.objects.get(
                user=user_for_attendance,
                year=year
            )
        except EmployeeLeaveBalance.DoesNotExist:
            leave_balance = None
        
        return {
            'month': month,
            'year': year,
            'total_days_in_month': total_days_in_month,
            'sundays': sundays_count,
            'mandatory_holidays': mandatory_holidays_count,
            'special_holidays': special_holidays_count,
            'total_paid_holidays': total_paid_holidays,
            'total_working_days': total_working_days,
            'full_days_worked': full_days_worked,
            'half_days_worked': half_days_worked,
            'wfh_days': wfh_days,
            'casual_leave_days': casual_leave_days,
            'sick_leave_days': sick_leave_days,
            'special_leave_days': special_leave_days,
            'unpaid_leave_days': unpaid_leave_days,
            'not_marked_days': not_marked_days,
            'paid_working_days': paid_working_days,
            'total_paid_days': total_paid_days,
            'days_to_deduct': days_to_deduct,
            'effective_paid_days': effective_paid_days,
            'leave_balance': {
                'casual_balance': float(leave_balance.casual_leave_balance) if leave_balance else 0,
                'casual_used': float(leave_balance.casual_leave_used) if leave_balance else 0,
                'sick_balance': leave_balance.sick_leave_balance if leave_balance else 0,
                'sick_used': leave_balance.sick_leave_used if leave_balance else 0,
                'special_balance': leave_balance.special_leave_balance if leave_balance else 0,
                'special_used': leave_balance.special_leave_used if leave_balance else 0,
                'unpaid_taken': float(leave_balance.unpaid_leave_taken) if leave_balance else 0,
            } if leave_balance else None,
        }
    
    @staticmethod
    def calculate_salary(base_salary, working_days, paid_days, allowances=0, deductions=0):
        """
        Calculate salary based on paid days - NO TAX
        
        Args:
            base_salary: Monthly base salary
            working_days: Total working days in month
            paid_days: Days to be paid for
            allowances: Additional allowances
            deductions: Deductions (insurance, loans, etc.)
        
        Returns:
            dict: Salary breakdown without tax
        """
        base_salary = Decimal(str(base_salary))
        allowances = Decimal(str(allowances))
        deductions = Decimal(str(deductions))
        
        # Calculate daily rate
        daily_rate = base_salary / Decimal(str(working_days)) if working_days > 0 else Decimal('0')
        
        # Calculate earned salary
        earned_salary = daily_rate * Decimal(str(paid_days))
        
        # Calculate gross pay
        gross_pay = earned_salary + allowances
        
        # NO TAX - Set to 0
        tax = Decimal('0')
        
        # Calculate net pay (no tax deduction)
        net_pay = gross_pay - deductions
        
        return {
            'base_salary': float(base_salary),
            'monthly_basic': float(base_salary),
            'daily_rate': float(daily_rate),
            'earned_salary': float(earned_salary),
            'allowances': float(allowances),
            'gross_pay': float(gross_pay),
            'deductions': float(deductions),
            'tax': float(tax),  # Always 0
            'net_pay': float(net_pay),
        }
    
    @staticmethod
    def calculate_preview(employee, month, year, base_salary, allowances=0, deductions=0):
        """
        Calculate complete payroll preview - NO TAX
        """
        month_number = PayrollCalculationService.MONTH_NAME_TO_NUMBER.get(month)
        if not month_number:
            raise ValueError(f"Invalid month name: {month}")
        
        attendance_breakdown = PayrollCalculationService.calculate_employee_payroll_data(
            employee=employee,
            year=int(year),
            month=month_number
        )
        
        # Calculate salary without tax
        salary_calculation = PayrollCalculationService.calculate_salary(
            base_salary=base_salary,
            working_days=attendance_breakdown['total_working_days'],
            paid_days=attendance_breakdown['effective_paid_days'],
            allowances=allowances,
            deductions=deductions
        )
        
        return {
            'attendance_breakdown': attendance_breakdown,
            'salary_calculation': salary_calculation,
            'month': month,
            'year': year,
        }