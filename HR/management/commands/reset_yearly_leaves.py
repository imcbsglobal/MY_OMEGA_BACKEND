 #HR/management/commands/reset_yearly_leaves.py
"""
Management command to reset yearly leave balances
Should be run via cron job on January 1st

Usage: python manage.py reset_yearly_leaves
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from HR.models import EmployeeLeaveBalance


class Command(BaseCommand):
    help = 'Reset yearly leave balances (sick and special) for all employees'

    def handle(self, *args, **options):
        current_year = timezone.now().year
        
        self.stdout.write(
            self.style.SUCCESS(f'Resetting yearly leave balances for {current_year}...')
        )
        
        # Get all balances from previous year
        previous_year = current_year - 1
        previous_balances = EmployeeLeaveBalance.objects.filter(year=previous_year)
        
        reset_count = 0
        for old_balance in previous_balances:
            # Create new balance for current year with carried forward casual leave
            new_balance, created = EmployeeLeaveBalance.objects.get_or_create(
                user=old_balance.user,
                year=current_year,
                defaults={
                    'casual_leave_balance': old_balance.casual_leave_balance,  # Carry forward
                    'sick_leave_balance': 3,  # Reset to 3
                    'special_leave_balance': 7,  # Reset to 7
                    'last_casual_credit_month': 0,
                }
            )
            
            if created:
                reset_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Reset balance for {old_balance.user.name}: '
                        f'Casual carried forward: {new_balance.casual_leave_balance}, '
                        f'Sick: {new_balance.sick_leave_balance}, '
                        f'Special: {new_balance.special_leave_balance}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted: Reset balances for {reset_count} employees'
            )
        )