
# HR/management/commands/credit_monthly_leaves.py
"""
Management command to credit monthly casual leaves
Should be run via cron job on 1st of every month

Usage: python manage.py credit_monthly_leaves
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from HR.models import EmployeeLeaveBalance
from User.models import AppUser


class Command(BaseCommand):
    help = 'Credit monthly casual leave (1 day) to all active employees'

    def handle(self, *args, **options):
        current_month = timezone.now().month
        current_year = timezone.now().year
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Crediting monthly casual leave for {current_month}/{current_year}...'
            )
        )
        
        active_users = AppUser.objects.filter(is_active=True)
        credited_count = 0
        
        for user in active_users:
            balance, created = EmployeeLeaveBalance.objects.get_or_create(
                user=user,
                year=current_year,
                defaults={
                    'casual_leave_balance': 1,
                    'sick_leave_balance': 3,
                    'special_leave_balance': 7,
                    'last_casual_credit_month': current_month,
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created balance for new employee: {user.name}')
                )
                credited_count += 1
            elif balance.credit_monthly_casual_leave(current_month):
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Credited leave to {user.name}. '
                        f'New balance: {balance.casual_leave_balance}'
                    )
                )
                credited_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nCompleted: Credited casual leave to {credited_count} employees'
            )
        )