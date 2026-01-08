# HR/management/commands/setup_leave_system.py
"""
Management command to setup leave system:
1. Create mandatory holidays
2. Initialize employee leave balances
3. Credit monthly casual leaves

Usage: python manage.py setup_leave_system
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date
from HR.models import Holiday, EmployeeLeaveBalance
from User.models import AppUser


class Command(BaseCommand):
    help = 'Setup leave system: create mandatory holidays and initialize employee leave balances'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting leave system setup...'))
        
        # 1. Create mandatory holidays (fixed dates each year)
        current_year = timezone.now().year
        mandatory_holidays = [
            {
                'name': 'Labour Day',
                'month': 5,
                'day': 1,
                'description': 'International Workers Day'
            },
            {
                'name': 'Independence Day',
                'month': 8,
                'day': 15,
                'description': 'Indian Independence Day'
            },
            {
                'name': 'Gandhi Jayanti',
                'month': 10,
                'day': 2,
                'description': 'Mahatma Gandhi Birthday'
            },
        ]
        
        created_count = 0
        for holiday_data in mandatory_holidays:
            holiday_date = date(current_year, holiday_data['month'], holiday_data['day'])
            holiday, created = Holiday.objects.get_or_create(
                date=holiday_date,
                defaults={
                    'name': holiday_data['name'],
                    'holiday_type': 'mandatory',
                    'description': holiday_data['description'],
                    'is_active': True,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created mandatory holiday: {holiday.name} on {holiday.date}')
                )
            else:
                self.stdout.write(f'Holiday already exists: {holiday.name} on {holiday.date}')
        
        self.stdout.write(self.style.SUCCESS(f'Created {created_count} new mandatory holidays'))
        
        # 2. Initialize leave balances for all active employees
        active_users = AppUser.objects.filter(is_active=True)
        current_month = timezone.now().month
        
        balance_created_count = 0
        balance_updated_count = 0
        
        for user in active_users:
            balance, created = EmployeeLeaveBalance.objects.get_or_create(
                user=user,
                year=current_year,
                defaults={
                    'casual_leave_balance': current_month,  # 1 per month up to current
                    'sick_leave_balance': 3,
                    'special_leave_balance': 7,
                    'last_casual_credit_month': current_month,
                }
            )
            
            if created:
                balance_created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created leave balance for {user.name}: '
                        f'Casual={balance.casual_leave_balance}, '
                        f'Sick={balance.sick_leave_balance}, '
                        f'Special={balance.special_leave_balance}'
                    )
                )
            else:
                # Credit monthly casual leave if not already credited for current month
                if balance.credit_monthly_casual_leave(current_month):
                    balance_updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Credited casual leave for {user.name}. '
                            f'New balance: {balance.casual_leave_balance}'
                        )
                    )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSummary:\n'
                f'- Created {balance_created_count} new leave balances\n'
                f'- Updated {balance_updated_count} existing leave balances\n'
                f'- Total employees processed: {active_users.count()}'
            )
        )
        
        self.stdout.write(self.style.SUCCESS('\nLeave system setup completed successfully!'))