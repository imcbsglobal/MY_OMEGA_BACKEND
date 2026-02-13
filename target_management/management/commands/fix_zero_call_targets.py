# target_management/management/commands/fix_zero_call_targets.py
from django.core.management.base import BaseCommand
from target_management.models import CallTargetPeriod, CallDailyTarget


class Command(BaseCommand):
    help = 'Fix call targets that have zero target calls by setting reasonable default values'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making actual changes',
        )
        parser.add_argument(
            '--weekday-calls',
            type=int,
            default=30,
            help='Default target calls for weekdays (default: 30)',
        )
        parser.add_argument(
            '--weekend-calls',
            type=int,
            default=20,
            help='Default target calls for weekends (default: 20)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        weekday_calls = options['weekday_calls']
        weekend_calls = options['weekend_calls']

        self.stdout.write(self.style.SUCCESS('🔍 Finding call targets with zero target calls...'))

        # Find all call target periods that have zero total target calls
        zero_targets = []
        all_targets = CallTargetPeriod.objects.all()
        
        for target in all_targets:
            if target.total_target_calls == 0:
                zero_targets.append(target)

        self.stdout.write(f'Found {len(zero_targets)} call targets with zero target calls:')
        
        if not zero_targets:
            self.stdout.write(self.style.SUCCESS('✅ No call targets need fixing!'))
            return

        updated_count = 0
        
        for target in zero_targets:
            self.stdout.write(f'\n📋 Target ID {target.id}: {target.employee} ({target.start_date} to {target.end_date})')
            
            # Get daily targets with zero calls
            zero_daily_targets = target.daily_targets.filter(target_calls=0)
            
            if zero_daily_targets.exists():
                self.stdout.write(f'   Found {zero_daily_targets.count()} daily targets with 0 calls')
                
                if not dry_run:
                    # Fix each daily target
                    for daily_target in zero_daily_targets:
                        # Determine default calls based on day of week
                        day_of_week = daily_target.target_date.weekday()  # Monday=0, Sunday=6
                        default_calls = weekend_calls if day_of_week in [5, 6] else weekday_calls
                        
                        old_calls = daily_target.target_calls
                        daily_target.target_calls = default_calls
                        daily_target.save()
                        
                        self.stdout.write(f'   📅 {daily_target.target_date}: {old_calls} → {default_calls} calls')
                    
                    updated_count += 1
                    
                    # Verify the fix
                    new_total = target.total_target_calls
                    self.stdout.write(f'   ✅ Fixed! New total: {new_total} calls')
                else:
                    # Dry run - show what would be changed
                    for daily_target in zero_daily_targets:
                        day_of_week = daily_target.target_date.weekday()
                        default_calls = weekend_calls if day_of_week in [5, 6] else weekday_calls
                        self.stdout.write(f'   📅 {daily_target.target_date}: 0 → {default_calls} calls (DRY RUN)')
            else:
                self.stdout.write(f'   ℹ️ No daily targets need fixing')

        if dry_run:
            self.stdout.write(f'\n🔍 DRY RUN: Would update {len(zero_targets)} call targets')
            self.stdout.write('Run without --dry-run to apply changes')
        else:
            self.stdout.write(f'\n✅ Successfully updated {updated_count} call targets!')
            
        self.stdout.write(self.style.SUCCESS('Done!'))