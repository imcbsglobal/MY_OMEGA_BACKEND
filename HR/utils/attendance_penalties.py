from datetime import datetime, timedelta
from django.utils import timezone

from HR.models import Attendance


def _get_month_bounds(year, month):
    start_date = datetime(year, month, 1).date()
    if month == 12:
        end_date = datetime(year, 12, 31).date()
    else:
        end_date = (datetime(year, month + 1, 1) - timedelta(days=1)).date()
    return start_date, end_date


def _make_aware_dt(date_value, time_value):
    if not time_value:
        return None
    dt = datetime.combine(date_value, time_value)
    tz = timezone.get_current_timezone()
    try:
        return timezone.make_aware(dt, tz)
    except Exception:
        return dt


def _minutes_diff(later, earlier):
    if not later or not earlier:
        return None
    delta = later - earlier
    return max(0, int(delta.total_seconds() // 60))


def calculate_monthly_penalties(user, year, month):
    """
    Calculate monthly attendance penalties for a user.

    Rules (per calendar month):
    - Late <= 15 mins: allowed 3 times. After that, 0.5 day deduction each.
    - Late 16-30 mins: 0.5 day deduction each.
    - Late 31-60 mins: 1 day deduction each.
    - Late > 60 mins: 1 day deduction each.
    - Missed punch (missing in or out): allowed once. After that, 0.5 day each.
    - Early exit >= 30 mins: allowed once. After that, 0.5 day each.
    """
    start_date, end_date = _get_month_bounds(year, month)

    attendances = Attendance.objects.filter(
        user=user,
        date__gte=start_date,
        date__lte=end_date
    ).order_by('date')

    per_date = {}

    late_grace_used = 0
    missed_punch_grace_used = 0
    early_exit_grace_used = 0

    summary_counts = {
        'late_under_15_grace_used': 0,
        'late_under_15_deducted': 0,
        'late_16_30_count': 0,
        'late_31_60_count': 0,
        'late_over_60_count': 0,
        'missed_punch_grace_used': 0,
        'missed_punch_deducted_count': 0,
        'early_exit_grace_used': 0,
        'early_exit_deducted_count': 0,
    }

    total_deduction_days = 0.0

    for att in attendances:
        if att.status in ('leave', 'holiday', 'sunday', 'absent', 'special_leave', 'mandatory_holiday'):
            continue

        duty_start = getattr(att.user, 'duty_time_start', None)
        duty_end = getattr(att.user, 'duty_time_end', None)

        first_in = att.first_punch_in_time
        last_out = att.last_punch_out_time

        if first_in:
            first_in = timezone.localtime(first_in)
        if last_out:
            last_out = timezone.localtime(last_out)

        scheduled_start = _make_aware_dt(att.date, duty_start) if duty_start else None
        scheduled_end = _make_aware_dt(att.date, duty_end) if duty_end else None

        late_minutes = _minutes_diff(first_in, scheduled_start) if scheduled_start else None
        early_minutes = _minutes_diff(scheduled_end, last_out) if scheduled_end else None

        late_deduction = 0.0
        early_deduction = 0.0
        missed_punch_deduction = 0.0

        late_bucket = None
        late_over_60_absent = False
        late_grace_applied = False
        early_grace_applied = False
        missed_punch_grace_applied = False

        if late_minutes and late_minutes > 0:
            if late_minutes <= 15:
                late_bucket = 'late_under_15'
                if late_grace_used < 3:
                    late_grace_used += 1
                    late_grace_applied = True
                    summary_counts['late_under_15_grace_used'] += 1
                else:
                    late_deduction = 0.5
                    summary_counts['late_under_15_deducted'] += 1
            elif late_minutes <= 30:
                late_bucket = 'late_16_30'
                late_deduction = 0.5
                summary_counts['late_16_30_count'] += 1
            elif late_minutes <= 60:
                late_bucket = 'late_31_60'
                late_deduction = 1.0
                summary_counts['late_31_60_count'] += 1
            else:
                late_bucket = 'late_over_60'
                late_deduction = 1.0
                summary_counts['late_over_60_count'] += 1
                late_over_60_absent = True

        missed_punch = not (first_in and last_out)
        if missed_punch:
            if missed_punch_grace_used < 1:
                missed_punch_grace_used += 1
                missed_punch_grace_applied = True
                summary_counts['missed_punch_grace_used'] += 1
            else:
                missed_punch_deduction = 0.5
                summary_counts['missed_punch_deducted_count'] += 1

        if early_minutes is not None and early_minutes >= 30:
            if early_exit_grace_used < 1:
                early_exit_grace_used += 1
                early_grace_applied = True
                summary_counts['early_exit_grace_used'] += 1
            else:
                early_deduction = 0.5
                summary_counts['early_exit_deducted_count'] += 1

        total_for_day = late_deduction + missed_punch_deduction + early_deduction
        total_deduction_days += total_for_day

        per_date[att.date] = {
            'late_minutes': late_minutes or 0,
            'late_bucket': late_bucket,
            'late_over_60_absent': late_over_60_absent,
            'late_grace_applied': late_grace_applied,
            'late_deduction_days': late_deduction,
            'missed_punch': missed_punch,
            'missed_punch_grace_applied': missed_punch_grace_applied,
            'missed_punch_deduction_days': missed_punch_deduction,
            'early_exit_minutes': early_minutes or 0,
            'early_exit_grace_applied': early_grace_applied,
            'early_exit_deduction_days': early_deduction,
            'total_deduction_days': total_for_day,
        }

    return {
        'per_date': per_date,
        'summary': {
            **summary_counts,
            'late_grace_used_total': late_grace_used,
            'missed_punch_grace_used_total': missed_punch_grace_used,
            'early_exit_grace_used_total': early_exit_grace_used,
            'total_deduction_days': total_deduction_days,
        }
    }
