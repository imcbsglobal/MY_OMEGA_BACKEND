"""
Script to create test attendance records for May 2026 with penalties
"""
import os
import django
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myomega_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from attendance.models import Attendance, PunchRecord
from datetime import time
from dateutil.relativedelta import relativedelta

User = get_user_model()

# Get first available user
user = User.objects.first()
if not user:
    print("No users found in database")
    exit()

print(f"Creating test attendance for user: {user.email}")

# May 2026 date range
start_date = datetime(2026, 5, 1).date()
end_date = datetime(2026, 5, 31).date()

# Working days (Monday to Friday)
current_date = start_date
days_created = 0

while current_date <= end_date:
    # Skip weekends (Saturday=5, Sunday=6)
    if current_date.weekday() < 5:
        # Check if attendance already exists
        existing = Attendance.objects.filter(user=user, date=current_date).exists()
        if not existing:
            # Create attendance record
            att = Attendance.objects.create(
                user=user,
                date=current_date,
                status='present',
                first_punch_in_time=None,
                last_punch_out_time=None,
                total_working_hours=8.0,
                total_break_hours=1.0,
                is_leave=False,
                is_sunday=False,
                is_working_sunday=False,
                is_holiday=False,
                is_paid_day=True,
                verification_status='verified',
                verified_at=datetime.now(),
            )

            # Create punch records
            # Different punch times for different days to create penalties
            day_of_week = current_date.weekday()
            
            if day_of_week == 0:  # Monday - Late arrival (30 min late)
                punch_in = datetime.combine(current_date, time(9, 30))
                punch_out = datetime.combine(current_date, time(18, 0))
            elif day_of_week == 1:  # Tuesday - Late arrival (45 min late)
                punch_in = datetime.combine(current_date, time(9, 45))
                punch_out = datetime.combine(current_date, time(18, 30))
            elif day_of_week == 2:  # Wednesday - Early exit (30 min early)
                punch_in = datetime.combine(current_date, time(9, 0))
                punch_out = datetime.combine(current_date, time(17, 30))
            elif day_of_week == 3:  # Thursday - Normal
                punch_in = datetime.combine(current_date, time(9, 0))
                punch_out = datetime.combine(current_date, time(18, 0))
            else:  # Friday - Late arrival (60+ min late)
                punch_in = datetime.combine(current_date, time(10, 15))
                punch_out = datetime.combine(current_date, time(18, 30))
            
            # Create punch records
            PunchRecord.objects.create(
                attendance=att,
                punch_type='in',
                punch_time=punch_in,
                location='Office',
                latitude=13.0827,
                longitude=80.2707,
            )
            
            PunchRecord.objects.create(
                attendance=att,
                punch_type='out',
                punch_time=punch_out,
                location='Office',
                latitude=13.0827,
                longitude=80.2707,
            )
            
            # Update attendance with punch times
            att.first_punch_in_time = punch_in
            att.last_punch_out_time = punch_out
            att.save()
            
            days_created += 1
            penalty_info = ""
            if day_of_week == 0:
                penalty_info = " [LATE 30 min]"
            elif day_of_week == 1:
                penalty_info = " [LATE 45 min]"
            elif day_of_week == 2:
                penalty_info = " [EARLY EXIT 30 min]"
            elif day_of_week == 4:
                penalty_info = " [LATE 75 min]"
            
            print(f"Created: {current_date}{penalty_info}")
    
    current_date += timedelta(days=1)

print(f"\nTotal attendance records created: {days_created}")
print(f"Penalties included:")
print(f"  - Mondays: 30 min late")
print(f"  - Tuesdays: 45 min late")
print(f"  - Wednesdays: 30 min early exit")
print(f"  - Fridays: 75 min late")
