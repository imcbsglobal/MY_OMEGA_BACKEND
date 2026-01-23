# payroll/services.py - COMPLETE LEAVE INTEGRATION WITH PAYROLL

from decimal import Decimal
from datetime import datetime, timedelta
from django.db.models import Q, Sum
from django.db import transaction
from HR.models import Attendance, Holiday, EmployeeLeaveBalance
from master.models import LeaveMaster


class PayrollCalculationService:
    """
    Service to calculate payroll with comprehensive leave handling
    """
    
    # Map month names to numbers
    MONTH_NAME_TO_NUMBER = {
        'January': 1, 'February': 2, 'March': 3, 'April': 4,
        'May': 5, 'June': 6, 'July': 7, 'August': 8,
        'September': 9, 'October': 10, 'November': 11, 'December': 12
    }
    
    # Leave rules
    CASUAL_LEAVE_YEARLY = 12  # 12 casual leaves per year (accumulate monthly: 1 per month)
    SICK_LEAVE_YEARLY = 3     # 3 sick leaves per year (no accumulation)
    
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
        ).values('date', 'name', 'holiday_type', 'is_paid')
        
        holiday_dict = {}
        for h in holidays:
            holiday_dict[h['date']] = {
                'name': h['name'],
                'type': h['holiday_type'],
                'is_paid': h['is_paid']
            }
        
        return holiday_dict
    
    @staticmethod
    def get_or_create_leave_balance(user, year):
        """Get or create employee leave balance for the year"""
        balance, created = EmployeeLeaveBalance.objects.get_or_create(
            user=user,
            year=year,
            defaults={
                'casual_leave_balance': Decimal('0.00'),
                'casual_leave_used': Decimal('0.00'),
                'sick_leave_balance': PayrollCalculationService.SICK_LEAVE_YEARLY,
                'sick_leave_used': 0,
                'special_leave_balance': 7,  # Special leaves
                'special_leave_used': 0,
                'unpaid_leave_taken': Decimal('0.00'),
                'last_casual_credit_month': 0
            }
        )
        return balance
    
    @staticmethod
    def update_casual_leave_balance(balance, current_month):
        """
        Update casual leave balance - 1 leave per month accumulates
        Maximum 12 leaves per year
        """
        # Credit casual leaves up to current month if not already credited
        if balance.last_casual_credit_month < current_month:
            months_to_credit = current_month - balance.last_casual_credit_month
            
            # Each month gives 1 casual leave
            new_leaves = Decimal(str(months_to_credit))
            
            # Maximum casual leave balance is 12
            balance.casual_leave_balance = min(
                balance.casual_leave_balance + new_leaves,
                Decimal('12.00')
            )
            balance.last_casual_credit_month = current_month
            balance.save()
        
        return balance
    
    @staticmethod
    def get_employee_salary(employee):
        """Get employee's basic salary from multiple possible locations"""
        salary_fields = ['basic_salary', 'salary', 'base_salary']
        
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
        
        return Decimal('0')
    
    @staticmethod
    def calculate_employee_payroll_data(employee, year, month):
        """
        Calculate comprehensive payroll data for an employee with FULL leave integration
        """
        dates = PayrollCalculationService.get_month_dates(year, month)
        total_days_in_month = len(dates)
        
        # Get holidays and Sundays
        holidays = PayrollCalculationService.get_holidays_in_month(year, month)
        sundays_count = PayrollCalculationService.get_sundays_count(year, month)
        
        # Count different types of holidays
        mandatory_holidays_count = sum(1 for h in holidays.values() if h['type'] == 'mandatory')
        special_holidays_count = sum(1 for h in holidays.values() if h['type'] == 'special')
        total_paid_holidays = sum(1 for h in holidays.values() if h['is_paid'])
        
        # Get user for attendance
        user_for_attendance = employee.user if hasattr(employee, 'user') else employee
        
        # Get or create leave balance
        leave_balance = PayrollCalculationService.get_or_create_leave_balance(user_for_attendance, year)
        
        # Update casual leave balance for current month
        leave_balance = PayrollCalculationService.update_casual_leave_balance(leave_balance, month)
        
        # Get all attendance records for the month
        attendances = Attendance.objects.filter(
            user=user_for_attendance,
            date__in=dates
        ).select_related('leave_master')
        
        attendance_dict = {att.date: att for att in attendances}
        
        # Initialize counters
        full_days_worked = Decimal('0.00')
        half_days_worked = Decimal('0.00')
        
        # Leave counters
        casual_leave_days = Decimal('0.00')
        sick_leave_days = Decimal('0.00')
        special_leave_days = Decimal('0.00')
        mandatory_holiday_leaves = Decimal('0.00')
        unpaid_leave_days = Decimal('0.00')
        
        # Other
        wfh_days = Decimal('0.00')
        not_marked_days = 0
        
        # Temporary counters for this month's leave usage
        casual_used_this_month = Decimal('0.00')
        sick_used_this_month = 0
        special_used_this_month = 0
        
        # Process each day
        for date in dates:
            # Skip Sundays - they are paid but not working days
            if date.weekday() == 6:
                continue
            
            # Skip holidays - they are handled separately
            if date in holidays:
                continue
            
            # Check if attendance is marked
            if date in attendance_dict:
                att = attendance_dict[date]
                status = att.status.lower() if att.status else ''
                
                # Full day work
                if status == 'full':
                    full_days_worked += Decimal('1.00')
                
                # Half day work
                elif status == 'half':
                    half_days_worked += Decimal('0.5')
                
                # Work from home
                elif status == 'wfh':
                    wfh_days += Decimal('1.00')
                
                # Leave - need to check leave master for type
                elif status == 'leave':
                    if att.leave_master:
                        leave_category = att.leave_master.category
                        is_paid = att.leave_master.payment_status == 'paid'
                        
                        # Casual Leave
                        if leave_category == 'casual':
                            casual_used_this_month += Decimal('1.00')
                            
                            # Check if within balance
                            if casual_used_this_month <= leave_balance.casual_leave_balance:
                                casual_leave_days += Decimal('1.00')  # Paid
                            else:
                                unpaid_leave_days += Decimal('1.00')  # Unpaid - exceeded limit
                        
                        # Sick Leave
                        elif leave_category == 'sick':
                            sick_used_this_month += 1
                            
                            # Check if within yearly limit (3 days)
                            total_sick_used = leave_balance.sick_leave_used + sick_used_this_month
                            if total_sick_used <= PayrollCalculationService.SICK_LEAVE_YEARLY:
                                sick_leave_days += Decimal('1.00')  # Paid
                            else:
                                unpaid_leave_days += Decimal('1.00')  # Unpaid - exceeded limit
                        
                        # Special Leave
                        elif leave_category == 'special':
                            special_used_this_month += 1
                            if is_paid:
                                special_leave_days += Decimal('1.00')  # Paid
                            else:
                                unpaid_leave_days += Decimal('1.00')  # Unpaid
                        
                        # Mandatory Holiday (marked as leave)
                        elif leave_category == 'mandatory_holiday':
                            if is_paid:
                                mandatory_holiday_leaves += Decimal('1.00')  # Paid
                            else:
                                unpaid_leave_days += Decimal('1.00')  # Unpaid
                        
                        else:
                            # Unknown leave type - treat as unpaid
                            unpaid_leave_days += Decimal('1.00')
                    else:
                        # No leave master - treat as unpaid
                        unpaid_leave_days += Decimal('1.00')
                
                # Holiday status
                elif status == 'holiday':
                    # Already counted in holidays, skip
                    pass
                
                # Sunday status
                elif status == 'sunday':
                    # Already counted in sundays, skip
                    pass
                
                else:
                    # Unknown status or not marked properly
                    not_marked_days += 1
            
            else:
                # Not marked at all
                not_marked_days += 1
        
        # Update leave balance for the year (cumulative)
        leave_balance.casual_leave_used += casual_used_this_month
        leave_balance.sick_leave_used += sick_used_this_month
        leave_balance.special_leave_used += special_used_this_month
        leave_balance.unpaid_leave_taken += unpaid_leave_days
        leave_balance.save()
        
        # Calculate totals
        total_working_days = total_days_in_month - sundays_count - total_paid_holidays
        
        # Paid working days = actual work + paid leaves + WFH
        paid_working_days = (
            full_days_worked + 
            half_days_worked + 
            casual_leave_days + 
            sick_leave_days + 
            special_leave_days +
            mandatory_holiday_leaves +
            wfh_days
        )
        
        # Total paid days = paid working days + Sundays + paid holidays
        total_paid_days = paid_working_days + sundays_count + total_paid_holidays
        
        # Days to deduct from salary = unpaid leaves + not marked days
        days_to_deduct = float(unpaid_leave_days) + not_marked_days
        
        # Effective paid days for salary calculation
        effective_paid_days = float(paid_working_days)
        
        return {
            'month': month,
            'year': year,
            'total_days_in_month': total_days_in_month,
            
            # Sundays and Holidays
            'sundays': sundays_count,
            'mandatory_holidays': mandatory_holidays_count,
            'special_holidays': special_holidays_count,
            'total_paid_holidays': total_paid_holidays,
            
            # Working days
            'total_working_days': total_working_days,
            'full_days_worked': float(full_days_worked),
            'half_days_worked': float(half_days_worked),
            'wfh_days': float(wfh_days),
            
            # Leaves breakdown
            'casual_leave_days': float(casual_leave_days),
            'sick_leave_days': float(sick_leave_days),
            'special_leave_days': float(special_leave_days),
            'mandatory_holiday_leaves': float(mandatory_holiday_leaves),
            'unpaid_leave_days': float(unpaid_leave_days),
            'not_marked_days': not_marked_days,
            
            # Totals for payment
            'paid_working_days': float(paid_working_days),
            'total_paid_days': float(total_paid_days),
            'days_to_deduct': days_to_deduct,
            'effective_paid_days': effective_paid_days,
            
            # Leave balance information
            'leave_balance': {
                'casual_balance': float(leave_balance.casual_leave_balance),
                'casual_used': float(leave_balance.casual_leave_used),
                'casual_remaining': float(leave_balance.casual_leave_balance - leave_balance.casual_leave_used),
                
                'sick_balance': leave_balance.sick_leave_balance,
                'sick_used': leave_balance.sick_leave_used,
                'sick_remaining': leave_balance.sick_leave_balance - leave_balance.sick_leave_used,
                
                'special_balance': leave_balance.special_leave_balance,
                'special_used': leave_balance.special_leave_used,
                'special_remaining': leave_balance.special_leave_balance - leave_balance.special_leave_used,
                
                'unpaid_taken': float(leave_balance.unpaid_leave_taken),
            },
            
            # This month's usage
            'this_month_usage': {
                'casual_used': float(casual_used_this_month),
                'sick_used': sick_used_this_month,
                'special_used': special_used_this_month,
                'unpaid_used': float(unpaid_leave_days),
            }
        }
    
    @staticmethod
    def calculate_salary(base_salary, working_days, paid_days, allowances=0, deductions=0):
        """
        Calculate salary based on paid days - NO TAX
        
        Args:
            base_salary: Monthly base salary
            working_days: Total working days in month
            paid_days: Days to be paid for (including paid leaves)
            allowances: Additional allowances
            deductions: Deductions (insurance, loans, etc.)
        
        Returns:
            dict: Salary breakdown without tax
        """
        base_salary = Decimal(str(base_salary))
        allowances = Decimal(str(allowances))
        deductions = Decimal(str(deductions))
        
        # Calculate daily rate based on total working days
        daily_rate = base_salary / Decimal(str(working_days)) if working_days > 0 else Decimal('0')
        
        # Calculate earned salary based on paid days
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
        Calculate complete payroll preview with full leave breakdown
        """
        month_number = PayrollCalculationService.MONTH_NAME_TO_NUMBER.get(month)
        if not month_number:
            raise ValueError(f"Invalid month name: {month}")
        
        # Get attendance breakdown with leave details
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
            
            # Summary for display
            'summary': {
                'total_days': attendance_breakdown['total_days_in_month'],
                'total_working_days': attendance_breakdown['total_working_days'],
                'sundays': attendance_breakdown['sundays'],
                'holidays': attendance_breakdown['total_paid_holidays'],
                
                'actual_worked': (
                    attendance_breakdown['full_days_worked'] + 
                    attendance_breakdown['half_days_worked'] + 
                    attendance_breakdown['wfh_days']
                ),
                
                'paid_leaves': (
                    attendance_breakdown['casual_leave_days'] +
                    attendance_breakdown['sick_leave_days'] +
                    attendance_breakdown['special_leave_days'] +
                    attendance_breakdown['mandatory_holiday_leaves']
                ),
                
                'unpaid_leaves': attendance_breakdown['unpaid_leave_days'],
                'not_marked': attendance_breakdown['not_marked_days'],
                
                'effective_paid_days': attendance_breakdown['effective_paid_days'],
                'days_deducted': attendance_breakdown['days_to_deduct'],
            }
        }
    
    @staticmethod
    def generate_payroll_summary_text(payroll_data):
        """
        Generate a human-readable summary of the payroll calculation
        """
        att = payroll_data['attendance_breakdown']
        sal = payroll_data['salary_calculation']
        summ = payroll_data['summary']
        
        summary = f"""
PAYROLL SUMMARY - {payroll_data['month']} {payroll_data['year']}

DAYS BREAKDOWN:
- Total Days in Month: {att['total_days_in_month']}
- Sundays: {att['sundays']}
- Paid Holidays: {att['total_paid_holidays']} (Mandatory: {att['mandatory_holidays']}, Special: {att['special_holidays']})
- Total Working Days: {att['total_working_days']}

ATTENDANCE:
- Full Days Worked: {att['full_days_worked']}
- Half Days Worked: {att['half_days_worked']}
- Work From Home: {att['wfh_days']}

LEAVES TAKEN:
- Casual Leave (Paid): {att['casual_leave_days']}
- Sick Leave (Paid): {att['sick_leave_days']}
- Special Leave (Paid): {att['special_leave_days']}
- Mandatory Holiday Leave: {att['mandatory_holiday_leaves']}
- Unpaid Leave: {att['unpaid_leave_days']}
- Not Marked: {att['not_marked_days']}

LEAVE BALANCE:
- Casual Leave: {att['leave_balance']['casual_remaining']}/{att['leave_balance']['casual_balance']} remaining
- Sick Leave: {att['leave_balance']['sick_remaining']}/{att['leave_balance']['sick_balance']} remaining
- Special Leave: {att['leave_balance']['special_remaining']}/{att['leave_balance']['special_balance']} remaining

SALARY CALCULATION:
- Base Salary: ₹{sal['base_salary']:,.2f}
- Daily Rate: ₹{sal['daily_rate']:,.2f}
- Effective Paid Days: {summ['effective_paid_days']}
- Earned Salary: ₹{sal['earned_salary']:,.2f}
- Allowances: ₹{sal['allowances']:,.2f}
- Gross Pay: ₹{sal['gross_pay']:,.2f}
- Deductions: ₹{sal['deductions']:,.2f}
- Tax: ₹{sal['tax']:,.2f}
- NET PAY: ₹{sal['net_pay']:,.2f}
"""
        return summary