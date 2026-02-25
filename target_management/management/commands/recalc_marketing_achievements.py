from django.core.management.base import BaseCommand, CommandError
from django.db.models import Sum
from datetime import datetime
import re

from target_management.models import (
    MarketingTargetPeriod, MarketingTargetParameter, TargetAchievementLog
)


class Command(BaseCommand):
    help = 'Recalculate marketing target parameter achievements from available logs'

    def add_arguments(self, parser):
        parser.add_argument('--employee', type=int, help='Employee PK to limit recalculation')
        parser.add_argument('--period', type=int, help='MarketingTargetPeriod PK to recalc')
        parser.add_argument('--dry-run', action='store_true', help='Do not save changes, just print')
        parser.add_argument('--start', type=str, help='Start date (YYYY-MM-DD) to filter logs')
        parser.add_argument('--end', type=str, help='End date (YYYY-MM-DD) to filter logs')

    def handle(self, *args, **options):
        employee_pk = options.get('employee')
        period_pk = options.get('period')
        dry_run = options.get('dry_run')
        start_str = options.get('start')
        end_str = options.get('end')

        date_filter = {}
        if start_str:
            try:
                date_filter['start'] = datetime.strptime(start_str, '%Y-%m-%d').date()
            except Exception:
                raise CommandError('Invalid --start date. Use YYYY-MM-DD')
        if end_str:
            try:
                date_filter['end'] = datetime.strptime(end_str, '%Y-%m-%d').date()
            except Exception:
                raise CommandError('Invalid --end date. Use YYYY-MM-DD')

        qs = MarketingTargetPeriod.objects.select_related('employee')
        if period_pk:
            qs = qs.filter(pk=period_pk)
        if employee_pk:
            qs = qs.filter(employee__pk=employee_pk)

        total_updated = 0
        for period in qs:
            self.stdout.write(f"Processing MarketingTargetPeriod id={period.pk} employee={period.employee.get_full_name()}")

            # compute log filters by date and employee
            logs = TargetAchievementLog.objects.filter(employee=period.employee)
            if 'start' in date_filter:
                logs = logs.filter(achievement_date__gte=date_filter['start'])
            else:
                logs = logs.filter(achievement_date__gte=period.start_date)
            if 'end' in date_filter:
                logs = logs.filter(achievement_date__lte=date_filter['end'])
            else:
                logs = logs.filter(achievement_date__lte=period.end_date)

            # Summaries
            # total_boxes <- sum of achievement_value where route_target is set
            route_sum = logs.filter(route_target__isnull=False).aggregate(total=Sum('achievement_value'))['total'] or 0

            # shops_visited and new_shops: try to parse from remarks using patterns
            shops_visited = 0
            new_shops = 0
            shops_pattern = re.compile(r'shops[_\s]?visited[:=\s]+(\d+)', re.I)
            new_shops_pattern = re.compile(r'new[_\s]?shops[:=\s]+(\d+)', re.I)
            for lg in logs:
                if lg.remarks:
                    m = shops_pattern.search(lg.remarks)
                    if m:
                        try:
                            shops_visited += int(m.group(1))
                        except Exception:
                            pass
                    m2 = new_shops_pattern.search(lg.remarks)
                    if m2:
                        try:
                            new_shops += int(m2.group(1))
                        except Exception:
                            pass

            # focus_category: not numeric — leave achieved_value as 0

            param_values = {
                'total_boxes': float(route_sum),
                'shops_visited': float(shops_visited),
                'new_shops': float(new_shops),
                'focus_category': 0.0,
            }

            for ptype, val in param_values.items():
                param, created = MarketingTargetParameter.objects.get_or_create(
                    marketing_target_period=period,
                    parameter_type=ptype,
                    defaults={
                        'parameter_label': dict(MarketingTargetParameter.PARAMETER_CHOICES).get(ptype, ptype),
                        'target_value': 0,
                        'incentive_value': 0,
                        'achieved_value': val,
                    }
                )
                if created:
                    self.stdout.write(f"  Created parameter {ptype} with achieved={val}")
                    if not dry_run:
                        param.save()
                        total_updated += 1
                else:
                    old = float(param.achieved_value or 0)
                    if abs(old - val) > 0.0001:
                        self.stdout.write(f"  Updating {ptype}: {old} -> {val}")
                        if not dry_run:
                            param.achieved_value = val
                            param.save()
                            total_updated += 1
                    else:
                        self.stdout.write(f"  No change for {ptype} (value={val})")

        self.stdout.write(self.style.SUCCESS(f"Recalculation complete. Total parameters updated: {total_updated}"))
