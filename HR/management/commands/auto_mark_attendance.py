# HR/management/commands/auto_mark_attendance.py
"""
Management command to automatically mark attendance for:
1. Holidays (paid/unpaid)
2. Approved leaves
3. Missing punch-ins (as auto leave)

Run this command daily via cron:
0 23 * * * python manage.py auto_mark_attendance
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from HR.models import Attendance, Holiday, LeaveRequest
from User.models import AppUser


class Command(BaseCommand):
    help = 'Automatically mark attendance for holidays, approved leaves, and missing punch-ins'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Specific date to process (YYYY-MM-DD). Defaults to yesterday.',
        )
        parser.add_argument(
            '--days-back',
            type=int,
            default=1,
            help='Number of days to process backwards from today (default: 1)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simulate without making changes',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if options['date']:
            # Process specific date
            try:
                target_date = datetime.strptime(options['date'], '%Y-%m-%d').date()
                dates_to_process = [target_date]
            except ValueError:
                self.stdout.write(self.style.ERROR('Invalid date format. Use YYYY-MM-DD'))
                return
        else:
            # Process last N days
            days_back = options['days_back']
            today = timezone.now().date()
            dates_to_process = [today - timedelta(days=i) for i in range(1, days_back + 1)]
        
        self.stdout.write(self.style.SUCCESS(f'Processing {len(dates_to_process)} date(s)...'))
        
        for process_date in dates_to_process:
            self.stdout.write(f'\n--- Processing {process_date} ---')
            
            # Skip Sundays
            if process_date.weekday() == 6:
                self.stdout.write(self.style.WARNING(f'  Skipping {process_date} (Sunday)'))
                continue
            
            # 1. Mark holidays for all active users
            self.mark_holidays(process_date, dry_run)
            
            # 2. Apply approved leaves to attendance
            self.apply_approved_leaves(process_date, dry_run)
            
            # 3. Auto-mark missing punch-ins as leave
            self.auto_mark_missing_attendance(process_date, dry_run)
        
        self.stdout.write(self.style.SUCCESS('\n✓ Auto-marking completed!'))
    
    def mark_holidays(self, date, dry_run=False):
        """Mark holidays for all active users"""
        holidays = Holiday.objects.filter(date=date, is_active=True)
        
        if not holidays.exists():
            self.stdout.write(f'  No holidays found for {date}')
            return
        
        holiday = holidays.first()
        self.stdout.write(self.style.WARNING(f'  Found holiday: {holiday.name} ({holiday.get_holiday_type_display()})'))
        
        active_users = AppUser.objects.filter(is_active=True)
        marked_count = 0
        skipped_count = 0
        
        for user in active_users:
            # Skip if attendance already exists
            if Attendance.objects.filter(user=user, date=date).exists():
                skipped_count += 1
                continue
            
            if not dry_run:
                Attendance.objects.create(
                    user=user,
                    date=date,
                    status='holiday',
                    verification_status='auto_verified',
                    is_auto_marked=True,
                    auto_mark_reason=f'Holiday: {holiday.name}',
                    admin_note=f'Auto-marked for {holiday.get_holiday_type_display()} - {holiday.name}',
                    verified_at=timezone.now(),
                )
            marked_count += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'  ✓ Holiday marked for {marked_count} users (skipped {skipped_count} existing records)'
        ))
    
    def apply_approved_leaves(self, date, dry_run=False):
        """Apply approved leaves to attendance"""
        # Find approved leaves that cover this date
        approved_leaves = LeaveRequest.objects.filter(
            status='approved',
            from_date__lte=date,
            to_date__gte=date,
            is_applied_to_attendance=False,
        )
        
        if not approved_leaves.exists():
            self.stdout.write(f'  No approved leaves for {date}')
            return
        
        marked_count = 0
        
        for leave in approved_leaves:
            # Skip if it's a holiday
            if Holiday.objects.filter(date=date, is_active=True).exists():
                continue
            
            # Skip if attendance already exists and is not auto-marked
            existing = Attendance.objects.filter(user=leave.user, date=date).first()
            if existing and not existing.is_auto_marked:
                self.stdout.write(
                    f'  ⚠ Skipping {leave.user.name} - manual attendance exists'
                )
                continue
            
            if not dry_run:
                Attendance.objects.update_or_create(
                    user=leave.user,
                    date=date,
                    defaults={
                        'status': 'leave',
                        'verification_status': 'auto_verified',
                        'is_auto_marked': True,
                        'auto_mark_reason': f'Approved {leave.get_leave_type_display()}',
                        'admin_note': f'Auto-marked from leave request #{leave.id}',
                        'verified_by': leave.reviewed_by,
                        'verified_at': leave.reviewed_at or timezone.now(),
                    }
                )
            marked_count += 1
            
            self.stdout.write(
                f'  ✓ Applied leave for {leave.user.name} ({leave.get_leave_type_display()})'
            )
        
        if marked_count > 0:
            self.stdout.write(self.style.SUCCESS(
                f'  ✓ Applied {marked_count} approved leave(s)'
            ))
    
    def auto_mark_missing_attendance(self, date, dry_run=False):
        """
        Auto-mark missing attendance as leave for users who:
        - Have no attendance record for the date
        - Date is not a holiday
        - Date is not a Sunday
        - User is active
        """
        # Skip if it's a holiday
        if Holiday.objects.filter(date=date, is_active=True).exists():
            self.stdout.write(f'  Skipping auto-mark (holiday)')
            return
        
        active_users = AppUser.objects.filter(is_active=True)
        marked_count = 0
        
        for user in active_users:
            # Skip if attendance exists
            if Attendance.objects.filter(user=user, date=date).exists():
                continue
            
            # Skip if there's a pending leave request for this date
            has_pending_leave = LeaveRequest.objects.filter(
                user=user,
                status='pending',
                from_date__lte=date,
                to_date__gte=date,
            ).exists()
            
            if has_pending_leave:
                self.stdout.write(
                    f'  ⏳ Skipping {user.name} - pending leave request exists'
                )
                continue
            
            if not dry_run:
                Attendance.objects.create(
                    user=user,
                    date=date,
                    status='auto_leave',
                    verification_status='unverified',
                    is_auto_marked=True,
                    auto_mark_reason='No punch-in detected - Auto-marked as leave',
                    admin_note='Automatically marked as leave due to missing attendance. Please verify.',
                )
            marked_count += 1
            
            self.stdout.write(
                f'  🔴 Auto-marked leave for {user.name} (no punch-in)'
            )
        
        if marked_count > 0:
            self.stdout.write(self.style.WARNING(
                f'  ⚠ Auto-marked {marked_count} missing attendance(s) as leave (needs verification)'
            ))