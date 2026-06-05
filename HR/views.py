from rest_framework.exceptions import ValidationError
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Sum
from django.db import transaction
from django.utils import timezone
from datetime import datetime, time
from django.conf import settings
from master.models import LeaveMaster  # ✅ CORRECT - Import from master app
from .models import LeaveRequest  # ✅ LeaveRequest is in HR.models
from master.serializers import LeaveMasterCreateSerializer
from payroll.models import AutomationRule  # For grace period configuration

import calendar
import requests

from HR.utils.geofence import validate_office_geofence
from HR.utils.attendance_penalties import calculate_monthly_penalties
from .models import (
    Attendance, Holiday, LeaveRequest, LateRequest,
    EarlyRequest, PunchRecord
)
from .Serializers import (
    AttendanceSerializer, PunchInSerializer, PunchOutSerializer,
    HolidaySerializer, LeaveRequestSerializer,
    LeaveRequestCreateSerializer, LeaveRequestReviewSerializer,
    LateRequestSerializer, LateRequestCreateSerializer,
    EarlyRequestSerializer, EarlyRequestCreateSerializer, 
    PunchRecordSerializer, AttendanceUpdateStatusSerializer
)
from master.models import LeaveMaster
from master.serializers import LeaveMasterSerializer
from User.models import AppUser
from employee_management.models import Employee


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def attendance_penalty_apply_deduction(request):
    """Create or update payroll deduction items for an employee/month based on penalty summary."""

    employee_id = request.data.get('employee_id')
    month = request.data.get('month')
    year = request.data.get('year')

    if not employee_id or not month or not year:
        return Response({'error': 'employee_id, month and year are required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        employee = Employee.objects.select_related('user').get(id=employee_id)
    except Employee.DoesNotExist:
        return Response({'error': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)

    user = getattr(employee, 'user', None)
    if not user:
        return Response({'error': 'Employee has no linked user account'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        month = int(month)
        year = int(year)
    except Exception:
        return Response({'error': 'month and year must be valid numbers'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        from payroll.models import Payroll, PayrollDeduction
        from payroll.services import PayrollCalculationService
    except Exception:
        return Response({'error': 'Payroll module unavailable'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    created = 0
    payroll_ids = []

    with transaction.atomic():
        # find existing payrolls for this employee/month
        payrolls = Payroll.objects.filter(employee=employee, year=year, month=month)

        # if none, create a minimal payroll so deduction can be attached
        if not payrolls.exists():
            try:
                base_salary = PayrollCalculationService.get_employee_salary(employee)
            except Exception:
                base_salary = 0
            # create minimal payroll record
            p = Payroll.objects.create(
                employee=employee,
                month=PayrollCalculationService.MONTH_NAME_TO_NUMBER and list(PayrollCalculationService.MONTH_NAME_TO_NUMBER.keys())[month-1] if 1 <= month <= 12 else str(month),
                year=year,
                salary=base_salary or 0,
                attendance_days=0,
                working_days=22,
                earned_salary=0,
                allowances=0,
                gross_pay=0,
                deductions=0,
                tax=0,
                net_pay=0,
            )
            payrolls = Payroll.objects.filter(id=p.id)

        for p in payrolls:
            try:
                calc = PayrollCalculationService.calculate_attendance_penalty_deduction(employee, year, month, p.working_days or 0, getattr(p, 'salary', 0) or PayrollCalculationService.get_employee_salary(employee))
                items = calc.get('items', []) if isinstance(calc, dict) else []
            except Exception:
                items = []

            # remove existing attendance penalty deductions and create new ones
            PayrollDeduction.objects.filter(payroll=p, deduction_type='ATTENDANCE PENALTY').delete()
            for item in items:
                PayrollDeduction.objects.create(
                    payroll=p,
                    deduction_type=item.get('deduction_type', 'ATTENDANCE PENALTY'),
                    amount=item.get('amount', 0),
                    description=item.get('description', '')
                )
                created += 1
            payroll_ids.append(p.id)

    return Response({'success': True, 'message': 'Applied attendance penalty deductions', 'created': created, 'payroll_ids': payroll_ids})


def _get_employee_display_name(employee):
    if not employee:
        return 'Unknown'

    if hasattr(employee, 'get_full_name') and callable(employee.get_full_name):
        try:
            name = employee.get_full_name()
            if name and name.strip():
                return name
        except Exception:
            pass

    for field in ('full_name', 'name'):
        value = getattr(employee, field, None)
        if value:
            return value

    first_name = getattr(employee, 'first_name', '') or ''
    last_name = getattr(employee, 'last_name', '') or ''
    if first_name or last_name:
        return f'{first_name} {last_name}'.strip()

    employee_code = getattr(employee, 'employee_id', None) or getattr(employee, 'id', None)
    return f'Employee_{employee_code}' if employee_code else 'Unknown'


def _get_employee_department_name(employee):
    if not employee:
        return 'N/A'

    try:
        departments = list(employee.department.all()) if hasattr(employee, 'department') else []
        if departments:
            return ', '.join(dept.name for dept in departments if getattr(dept, 'name', None))
    except Exception:
        pass

    return getattr(employee, 'organization', None) or getattr(getattr(employee, 'user', None), 'organization', None) or 'N/A'


def _get_employee_avatar(name):
    parts = [part for part in str(name or '').split() if part]
    initials = ''.join(part[0] for part in parts[:2]).upper()
    return initials or 'E'


def _suggest_penalty_action(total_deduction_days, penalty_events):
    if penalty_events <= 0:
        return 'No Deduction (Grace)'
    if total_deduction_days <= 0:
        return 'Warn Only'
    if total_deduction_days <= 0.5:
        return 'Half Day Deduction'
    return 'Full Day Deduction'


def _review_status(pending_count, approved_count, rejected_count, penalty_events):
    if pending_count > 0:
        return 'Pending'
    if approved_count > 0:
        return 'Approved (Deduct)'
    if rejected_count > 0:
        return 'Waived'
    if penalty_events > 0:
        return 'Pending'
    return 'Waived'


def _serialize_employee_meta(employee):
    user = getattr(employee, 'user', None)
    departments = []
    try:
        departments = [dept.name for dept in employee.department.all() if getattr(dept, 'name', None)]
    except Exception:
        departments = []

    avatar_url = None
    try:
        if getattr(employee, 'avatar', None):
            avatar_url = employee.avatar.url
    except Exception:
        avatar_url = None

    return {
        'id': employee.id,
        'employee_id': employee.employee_id,
        'full_name': employee.full_name,
        'name': _get_employee_display_name(employee),
        'email': getattr(user, 'email', None),
        'phone_number': employee.phone_number,
        'personal_phone': employee.personal_phone,
        'designation': employee.designation,
        'employment_status': employee.employment_status,
        'employment_type': employee.employment_type,
        'work_type': employee.work_type,
        'date_of_joining': employee.date_of_joining,
        'date_of_leaving': employee.date_of_leaving,
        'duty_time': employee.duty_time,
        'location': employee.location,
        'work_location': employee.work_location,
        'organization': employee.organization,
        'departments': departments,
        'department': departments[0] if departments else None,
        'avatar_url': avatar_url,
        'avatar': _get_employee_avatar(_get_employee_display_name(employee)),
    }


def _serialize_attendance_detail(attendance, penalty_detail=None):
    punches = []
    for punch in attendance.punch_records.all().order_by('punch_time'):
        punches.append({
            'id': punch.id,
            'punch_type': punch.punch_type,
            'punch_time': punch.punch_time,
            'location': punch.location,
            'latitude': punch.latitude,
            'longitude': punch.longitude,
            'note': punch.note,
        })

    leave_name = None
    if attendance.leave_master:
        leave_name = attendance.leave_master.leave_name
    elif attendance.leave_request and attendance.leave_request.leave_master:
        leave_name = attendance.leave_request.leave_master.leave_name

    # Get late/early request status for this date
    # PRIMARY: check admin_note (written by daily_penalty_action endpoint)
    # FALLBACK: check LateRequest/EarlyRequest.status
    late_request_status = None
    early_request_status = None
    missed_punch_status = None

    admin_note_text = ''
    try:
        admin_note_text = str(getattr(attendance, 'admin_note', '') or '').lower()
    except Exception:
        admin_note_text = ''

    # Late status — check admin_note first (daily_penalty_action writes here)
    if 'late penalty waived' in admin_note_text:
        late_request_status = 'rejected'
    elif 'late penalty deducted' in admin_note_text:
        late_request_status = 'approved'
    else:
        # Fallback to LateRequest.status
        try:
            late_req = LateRequest.objects.filter(user=attendance.user, date=attendance.date).first()
            if late_req:
                late_request_status = late_req.status
        except Exception:
            pass

    # Early status — check admin_note first
    if 'early exit penalty waived' in admin_note_text:
        early_request_status = 'rejected'
    elif 'early exit penalty deducted' in admin_note_text:
        early_request_status = 'approved'
    else:
        # Fallback to EarlyRequest.status
        try:
            early_req = EarlyRequest.objects.filter(user=attendance.user, date=attendance.date).first()
            if early_req:
                early_request_status = early_req.status
        except Exception:
            pass

    # Missed punch status — read from admin_note (this was already correct)
    if 'missed punch penalty waived' in admin_note_text or ('waived' in admin_note_text and 'missed' in admin_note_text):
        missed_punch_status = 'rejected'
    elif 'missed punch penalty deducted' in admin_note_text or ('deducted' in admin_note_text and 'missed' in admin_note_text) or ('applied' in admin_note_text and 'missed' in admin_note_text):
        missed_punch_status = 'approved'

    return {
        'id': attendance.id,
        'date': attendance.date,
        'status': attendance.status,
        'status_display': attendance.get_status_display(),
        'verification_status': attendance.verification_status,
        'verification_status_display': attendance.get_verification_status_display(),
        'first_punch_in_time': attendance.first_punch_in_time,
        'first_punch_in_location': attendance.first_punch_in_location,
        'last_punch_out_time': attendance.last_punch_out_time,
        'last_punch_out_location': attendance.last_punch_out_location,
        'total_working_hours': attendance.total_working_hours,
        'total_break_hours': attendance.total_break_hours,
        'is_leave': attendance.is_leave,
        'is_sunday': attendance.is_sunday,
        'is_working_sunday': attendance.is_working_sunday,
        'is_holiday': attendance.is_holiday,
        'is_paid_day': attendance.is_paid_day,
        'leave_name': leave_name,
        'note': attendance.note,
        'admin_note': attendance.admin_note,
        'verified_at': attendance.verified_at,
        'verified_by_name': getattr(getattr(attendance, 'verified_by', None), 'name', None),
        'punches': punches,
        'late_request_status': late_request_status,
        'early_request_status': early_request_status,
        'missed_punch_status': missed_punch_status,
        'penalty': penalty_detail or {
            'late_minutes': 0,
            'late_bucket': None,
            'late_over_60_absent': False,
            'late_grace_applied': False,
            'late_deduction_days': 0.0,
            'missed_punch': False,
            'missed_punch_grace_applied': False,
            'missed_punch_deduction_days': 0.0,
            'early_exit_minutes': 0,
            'early_exit_grace_applied': False,
            'early_exit_deduction_days': 0.0,
            'total_deduction_days': 0.0,
        },
    }


class AttendanceViewSet(viewsets.ModelViewSet):
    pagination_class = None
    """Clean AttendanceViewSet with punch in/out endpoints."""
    queryset = Attendance.objects.all().select_related('user', 'verified_by')
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]
    menu_key = 'attendance'

    def _is_admin(self, user):
        return (
            getattr(user, 'user_level', None) in ('Super Admin', 'Admin') or
            user.is_staff or user.is_superuser
        )

    def get_queryset(self):
        user = self.request.user
        qs = Attendance.objects.select_related('user', 'verified_by')
        if not self._is_admin(user):
            qs = qs.filter(user=user)

        user_id = self.request.query_params.get('user_id')
        if user_id and self._is_admin(user):
            qs = qs.filter(user_id=user_id)

        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')
        if from_date:
            qs = qs.filter(date__gte=from_date)
        if to_date:
            qs = qs.filter(date__lte=to_date)

        month = self.request.query_params.get('month')
        year = self.request.query_params.get('year')
        if month and year:
            qs = qs.filter(date__month=month, date__year=year)

        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param)

        verification_status = self.request.query_params.get('verification_status')
        if verification_status:
            qs = qs.filter(verification_status=verification_status)

        return qs.order_by('-date', '-first_punch_in_time')

    @action(detail=False, methods=['post'], url_path='punch_in')
    @transaction.atomic
    def punch_in(self, request):
        serializer = PunchInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        today = timezone.now().date()

        lat = serializer.validated_data.get('latitude')
        lon = serializer.validated_data.get('longitude')

        # Get office info from database
        from HR.models import OfficeLocation
        from HR.utils.geofence import get_office_info
        
        office_info = get_office_info()
        if not office_info:
            return Response({
                'error': 'Office location not configured',
                'detail': 'No office location has been set up. Please contact your administrator.',
                'message': 'Office configuration is missing'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        print("=" * 80)
        print(f"🔵 PUNCH IN ATTEMPT")
        print(f"User: {user.email}")
        print(f"Received Latitude: {lat}")
        print(f"Received Longitude: {lon}")
        print(f"Office: {office_info['name']}")
        print(f"Office Latitude: {office_info['latitude']}")
        print(f"Office Longitude: {office_info['longitude']}")
        print(f"Allowed Radius: {office_info['radius']}m")
        print(f"Source: {office_info['source']}")
        print("=" * 80)

        # Determine if geofence should be enforced for this user
        enforce_geofence = False
        try:
            emp = getattr(user, 'employee_profile', None)
            # ✅ IN-HOUSE (office) employees MUST punch in at office location only
            # OUT-HOUSE (field/remote) employees can punch in from anywhere
            if emp and getattr(emp, 'work_type', None) == 'in_house':
                enforce_geofence = True
        except Exception:
            emp = None

        # ✅ VALIDATE GEOFENCE (only for in_house/office employees)
        if enforce_geofence:
            allowed, distance = validate_office_geofence(lat, lon, user=user)
            print(f"🎯 Geofence Result: allowed={allowed}, distance={distance}m")
        else:
            # Out-house employees don't need geofence validation
            allowed, distance = True, 0
            print(f"🎯 Geofence Skipped for out-house/field employee (work_type != in_house).")
        print("=" * 80)

        if not allowed:
            excess_distance = distance - office_info['radius']
            
            print(f"❌ PUNCH IN REJECTED!")
            print(f"Distance: {distance}m")
            print(f"Excess: {excess_distance}m")
            print("=" * 80)
            
            return Response({
                'error': 'Punch in denied: You are outside the office premises',
                'detail': f'You are {distance:.0f}m away from office. You need to be within {office_info["radius"]:.0f}m.',
                'distance_meters': distance,
                'allowed_radius': office_info['radius'],
                'excess_distance': round(excess_distance, 2),
                'office_location': {
                    'latitude': office_info['latitude'],
                    'longitude': office_info['longitude'],
                    'address': office_info['address']
                },
                'user_location': {
                    'latitude': lat,
                    'longitude': lon
                }
            }, status=status.HTTP_403_FORBIDDEN)

        # ✅ Geofence passed - proceed with punch in
        print(f"✅ PUNCH IN ALLOWED - Distance: {distance}m")
        print("=" * 80)

        # ✅ FIX: Explicitly set is_paid_day when creating attendance
        attendance, created = Attendance.objects.get_or_create(
            user=user,
            date=today,
            defaults={
                'status': 'half',
                'is_currently_on_break': False,
                'is_paid_day': True,  # ✅ CRITICAL: Explicitly set this!
            }
        )

        last_punch = attendance.punch_records.order_by('-punch_time').first()
        if last_punch and last_punch.punch_type == 'in':
            return Response({
                'error': 'You are already punched in'
            }, status=status.HTTP_400_BAD_REQUEST)

        punch = PunchRecord.objects.create(
            attendance=attendance,
            punch_type='in',
            punch_time=timezone.now(),
            location=serializer.validated_data.get('location', ''),
            latitude=lat,
            longitude=lon,
            note=serializer.validated_data.get('note', '')
        )

        if not attendance.first_punch_in_time:
            attendance.first_punch_in_time = punch.punch_time
            attendance.first_punch_in_location = punch.location
            attendance.first_punch_in_latitude = punch.latitude
            attendance.first_punch_in_longitude = punch.longitude

        attendance.is_currently_on_break = False
        attendance.save()

        punches = attendance.punch_records.order_by('punch_time')
        data = AttendanceSerializer(attendance, context={'request': request}).data
        data['punch_records'] = PunchRecordSerializer(punches, many=True).data
        data['message'] = f'Punched in successfully (Distance from office: {distance:.0f}m)'
        data['can_punch_out'] = True
        data['distance_from_office'] = distance
        
        return Response(data, status=status.HTTP_200_OK)


    @action(detail=False, methods=['post'], url_path='punch_out')
    @transaction.atomic
    def punch_out(self, request):
        serializer = PunchOutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        today = timezone.now().date()

        try:
            attendance = Attendance.objects.get(user=user, date=today)
        except Attendance.DoesNotExist:
            return Response({
                'error': 'No punch in record for today'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not attendance.first_punch_in_time:
            return Response({
                'error': 'You must punch in first'
            }, status=status.HTTP_400_BAD_REQUEST)

        last_punch = attendance.punch_records.order_by('-punch_time').first()
        if last_punch and last_punch.punch_type == 'out':
            return Response({
                'error': 'You are already punched out'
            }, status=status.HTTP_400_BAD_REQUEST)

        lat = serializer.validated_data.get('latitude')
        lon = serializer.validated_data.get('longitude')
        
        # Get office info from database
        from HR.models import OfficeLocation
        from HR.utils.geofence import get_office_info
        
        office_info = get_office_info()
        if not office_info:
            return Response({
                'error': 'Office location not configured',
                'detail': 'No office location has been set up. Please contact your administrator.',
                'message': 'Office configuration is missing'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # 🔴 CRITICAL: Print received coordinates for debugging
        print("=" * 80)
        print(f"🔍 PUNCH OUT ATTEMPT")
        print(f"User: {user.email}")
        print(f"Received Latitude: {lat}")
        print(f"Received Longitude: {lon}")
        print(f"Office: {office_info['name']}")
        print(f"Office Latitude: {office_info['latitude']}")
        print(f"Office Longitude: {office_info['longitude']}")
        print(f"Allowed Radius: {office_info['radius']}m")
        print(f"Source: {office_info['source']}")
        print("=" * 80)
        
        # Determine if geofence should be enforced for this user
        enforce_geofence = False
        try:
            emp = getattr(user, 'employee_profile', None)
            # ✅ IN-HOUSE (office) employees MUST punch out at office location only
            # OUT-HOUSE (field/remote) employees can punch out from anywhere
            if emp and getattr(emp, 'work_type', None) == 'in_house':
                enforce_geofence = True
        except Exception:
            emp = None

        # If lat/lon are provided, validate geofence only when enforcement applies
        if lat is not None and lon is not None:
            if enforce_geofence:
                allowed, distance = validate_office_geofence(lat, lon, user=user)
                print(f"Geofence Result: allowed={allowed}, distance={distance}m")
                print("=" * 80)

                if not allowed:
                    excess_distance = distance - office_info['radius']
                    
                    print(f"❌ PUNCH OUT REJECTED!")
                    print(f"Distance: {distance}m")
                    print(f"Excess: {excess_distance}m")
                    print("=" * 80)
                    
                    return Response({
                        'error': 'Punch out denied: You are outside the office premises',
                        'detail': f'You are {distance:.0f}m away from office. You need to be within {office_info["radius"]:.0f}m.',
                        'distance_meters': distance,
                        'allowed_radius': office_info['radius'],
                        'excess_distance': round(excess_distance, 2),
                        'office_location': {
                            'latitude': office_info['latitude'],
                            'longitude': office_info['longitude'],
                            'address': office_info['address']
                        },
                        'user_location': {
                            'latitude': lat,
                            'longitude': lon
                        }
                    }, status=status.HTTP_403_FORBIDDEN)
                
                print(f"✅ PUNCH OUT ALLOWED - Distance: {distance}m")
                print("=" * 80)
            else:
                # Geofence not enforced for this user
                distance = 0
                print(f"⚠️ PUNCH OUT - Geofence check skipped for user (work_type != out_house)")
                print("=" * 80)
        else:
            # Geofence validation skipped (no coords provided)
            distance = None
            print(f"⚠️ PUNCH OUT - Geofence validation skipped (no coordinates provided)")
            print("=" * 80)

        punch_record = PunchRecord.objects.create(
            attendance=attendance,
            punch_type='out',
            punch_time=timezone.now(),
            location=serializer.validated_data.get('location', ''),
            latitude=lat,
            longitude=lon,
            note=serializer.validated_data.get('note', '')
        )

        attendance.last_punch_out_time = punch_record.punch_time
        attendance.last_punch_out_location = punch_record.location
        attendance.last_punch_out_latitude = punch_record.latitude
        attendance.last_punch_out_longitude = punch_record.longitude
        attendance.is_currently_on_break = True

        attendance.calculate_times()
        attendance.update_status()
        attendance.save()

        punches = attendance.punch_records.all().order_by('punch_time')
        data = AttendanceSerializer(attendance, context={'request': request}).data
        data['punch_records'] = PunchRecordSerializer(punches, many=True).data
        data['message'] = f'Punched out successfully (Distance from office: {distance:.0f}m)'
        data['can_punch_out'] = False
        data['distance_from_office'] = distance
        
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='today_status')
    def today_status(self, request):
        user = request.user
        today = timezone.now().date()
        try:
            attendance = Attendance.objects.get(user=user, date=today)
            punches = attendance.punch_records.all().order_by('punch_time')
            data = AttendanceSerializer(attendance, context={'request': request}).data
            data['punch_records'] = PunchRecordSerializer(punches, many=True).data
            data['can_punch_in'] = not punches.exists() or punches.last().punch_type == 'out'
            data['can_punch_out'] = punches.exists() and punches.last().punch_type == 'in'
            return Response(data)
        except Attendance.DoesNotExist:
            return Response({'message': 'No attendance record for today', 'date': today, 'can_punch_in': True, 'can_punch_out': False})

    @action(detail=False, methods=['get'], url_path='my_records')
    def my_records(self, request):
        try:
            user = request.user
            month = request.query_params.get('month')
            year = request.query_params.get('year')
            qs = Attendance.objects.filter(user=user)
            if month and year:
                qs = qs.filter(date__month=month, date__year=year)
            result = []
            for att in qs.order_by('date', 'first_punch_in_time'):
                d = AttendanceSerializer(att, context={'request': request}).data
                punches = att.punch_records.all().order_by('punch_time')
                d['punch_records'] = PunchRecordSerializer(punches, many=True).data
                result.append(d)
            return Response(result)
        except Exception as e:
            print(f"❌ ERROR in my_records: {e}")
            import traceback
            traceback.print_exc()
            return Response({'error': str(e), 'detail': 'Failed to fetch attendance records'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _count_sundays(self, year, month):
        """Count the number of Sundays in a given month"""
        import calendar
        from datetime import datetime
        
        days_in_month = calendar.monthrange(year, month)[1]
        sundays = 0
        
        for day in range(1, days_in_month + 1):
            date = datetime(year, month, day)
            if date.weekday() == 6:  # 6 = Sunday
                sundays += 1
        
        return sundays

    # ... rest of your existing methods ...
    
    @action(detail=False, methods=['get'], url_path='my_summary')
    def my_summary(self, request):
        user = request.user
        month = int(request.query_params.get('month', timezone.now().month))
        year = int(request.query_params.get('year', timezone.now().year))
        
        attendances = Attendance.objects.filter(user=user, date__month=month, date__year=year)
        holidays = Holiday.objects.filter(date__month=month, date__year=year, is_active=True).count()
        
        sundays = self._count_sundays(year, month)
        days_in_month = calendar.monthrange(year, month)[1]

        full_days = attendances.filter(status='full').count()
        half_days = attendances.filter(status='half').count()
        leaves = attendances.filter(status='leave').count()
        total_working_hours = attendances.aggregate(total=Sum('total_working_hours'))['total'] or 0
        total_break_hours = attendances.aggregate(total=Sum('total_break_hours'))['total'] or 0
        marked_days = attendances.count()
        not_marked = days_in_month - marked_days - holidays - sundays

        return Response({
            'user_id': user.id,
            'user_name': user.name,
            'user_email': user.email,
            'month': month,
            'year': year,
            'total_days': days_in_month,
            'full_days': full_days,
            'half_days': half_days,
            'leaves': leaves,
            'not_marked': not_marked,
            'total_working_hours': round(total_working_hours, 2),
            'total_break_hours': round(total_break_hours, 2),
            'holidays': holidays,
            'sundays': sundays,
        })

    @action(detail=False, methods=['post'], url_path='mark_leave')
    def mark_leave(self, request):
        if not self._is_admin(request.user):
            return Response({'error': 'Only admins can mark leave'}, status=status.HTTP_403_FORBIDDEN)

        user_id = request.data.get('user_id')
        date_str = request.data.get('date')
        admin_note = request.data.get('admin_note', '')

        if not user_id or not date_str:
            return Response({'error': 'user_id and date are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = AppUser.objects.get(id=user_id)
        except AppUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)

        attendance, created = Attendance.objects.update_or_create(
            user=user,
            date=attendance_date,
            defaults={
                'status': 'leave',
                'first_punch_in_time': None,
                'last_punch_out_time': None,
                'first_punch_in_location': None,
                'last_punch_out_location': None,
                'first_punch_in_latitude': None,
                'first_punch_in_longitude': None,
                'last_punch_out_latitude': None,
                'last_punch_out_longitude': None,
                'total_working_hours': 0,
                'total_break_hours': 0,
                'is_currently_on_break': False,
                'verification_status': 'verified',
                'verified_by': request.user,
                'verified_at': timezone.now(),
            }
        )

        # Delete all punch records for this attendance
        attendance.punch_records.all().delete()

        # Add admin note
        if admin_note:
            stamped = f"[{timezone.now().strftime('%Y-%m-%d %H:%M')}] {admin_note}"
            if attendance.admin_note:
                attendance.admin_note += f"\n{stamped}"
            else:
                attendance.admin_note = stamped
            attendance.save(update_fields=['admin_note'])

        response_serializer = AttendanceSerializer(attendance, context={'request': request})
        return Response({'message': 'Leave marked successfully', 'attendance': response_serializer.data},
                        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    # =========================================================================
    # ✅ BUG FIX: mark_sunday_working
    #    Previously used 'status': 'half' as a placeholder which caused the
    #    frontend determineStatus() to show HD (Half Day) instead of WS
    #    (Working Sunday) for a Sunday with no actual punch data.
    #    Fix: Use 'status': 'working_sunday' as the placeholder so the
    #    frontend can reliably detect the WS state without relying on hours
    #    or punch data.
    # =========================================================================
    @action(detail=False, methods=['post'], url_path='mark_sunday_working')
    def mark_sunday_working(self, request):
        """
        Mark a Sunday as a working day (Admin only).
        Creates or updates an Attendance record so the day behaves like a
        regular work-day instead of auto-resolving to 'sunday'.
        Body: { user_id, date, admin_note (optional) }
        """
        if not self._is_admin(request.user):
            return Response({'error': 'Only admins can mark a Sunday as a working day'},
                            status=status.HTTP_403_FORBIDDEN)

        user_id = request.data.get('user_id')
        date_str = request.data.get('date')
        admin_note = request.data.get('admin_note', '')

        if not user_id or not date_str:
            return Response({'error': 'user_id and date are required'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            target_user = AppUser.objects.get(id=user_id)
        except AppUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD'},
                            status=status.HTTP_400_BAD_REQUEST)

        if attendance_date.weekday() != 6:
            return Response({'error': 'The provided date is not a Sunday'},
                            status=status.HTTP_400_BAD_REQUEST)

        attendance, created = Attendance.objects.get_or_create(
            user=target_user,
            date=attendance_date,
            defaults={
                'is_working_sunday': True,
                'is_sunday': True,
                # ✅ FIX: Use 'working_sunday' instead of 'half' so the frontend
                #    can correctly show the WS badge rather than the HD badge.
                #    The status will be updated to 'full' or 'half' after the
                #    employee actually punches in/out on that day.
                'status': 'working_sunday',
                'is_paid_day': True,
                'verification_status': 'unverified',
            }
        )

        if not created:
            attendance.is_working_sunday = True
            attendance.is_sunday = True
            # ✅ FIX: Reset status if it was previously 'sunday' OR 'half'
            #    (the old broken placeholder). This ensures existing records
            #    that were saved with 'half' are also corrected on next update.
            if attendance.status in ('sunday', 'half', 'working_sunday'):
                # Only reset if there is no real punch data yet
                has_punch = bool(attendance.first_punch_in_time)
                if not has_punch:
                    attendance.status = 'working_sunday'
                    attendance.verification_status = 'unverified'

        if admin_note:
            stamped = f"[{timezone.now().strftime('%Y-%m-%d %H:%M')}] Working Sunday: {admin_note}"
            attendance.admin_note = f"{attendance.admin_note}\n{stamped}" if attendance.admin_note else stamped

        attendance.save()

        serializer = AttendanceSerializer(attendance, context={'request': request})
        return Response(
            {'message': 'Sunday marked as working day', 'attendance': serializer.data},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )

    @action(detail=False, methods=['post'], url_path='unmark_sunday_working')
    def unmark_sunday_working(self, request):
        """
        Revert a working Sunday back to a normal (off) Sunday (Admin only).
        Body: { user_id, date }
        """
        if not self._is_admin(request.user):
            return Response({'error': 'Only admins can revert a working Sunday'},
                            status=status.HTTP_403_FORBIDDEN)

        user_id = request.data.get('user_id')
        date_str = request.data.get('date')

        if not user_id or not date_str:
            return Response({'error': 'user_id and date are required'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            attendance = Attendance.objects.get(user_id=user_id, date=attendance_date)
        except Attendance.DoesNotExist:
            return Response({'error': 'No attendance record found for this date'},
                            status=status.HTTP_404_NOT_FOUND)

        attendance.is_working_sunday = False
        # Clear any punch data and reset to sunday status
        attendance.status = 'sunday'
        attendance.is_paid_day = True
        attendance.verification_status = 'verified'
        attendance.first_punch_in_time = None
        attendance.first_punch_in_location = None
        attendance.first_punch_in_latitude = None
        attendance.first_punch_in_longitude = None
        attendance.last_punch_out_time = None
        attendance.last_punch_out_location = None
        attendance.last_punch_out_latitude = None
        attendance.last_punch_out_longitude = None
        attendance.total_working_hours = 0
        attendance.total_break_hours = 0
        attendance.is_currently_on_break = False
        attendance.punch_records.all().delete()
        attendance.save()

        serializer = AttendanceSerializer(attendance, context={'request': request})
        return Response({'message': 'Working Sunday reverted to regular Sunday', 'attendance': serializer.data})

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get attendance summary for a user"""
        user_id = request.query_params.get('user_id', request.user.id)
        month = int(request.query_params.get('month', timezone.now().month))
        year = int(request.query_params.get('year', timezone.now().year))

        is_admin = self._is_admin(request.user)

        if not is_admin and int(user_id) != request.user.id:
            return Response(
                {'error': 'You can only view your own summary'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            user = AppUser.objects.get(id=user_id)
        except AppUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        attendances = Attendance.objects.filter(
            user_id=user_id,
            date__month=month,
            date__year=year
        )

        holidays = Holiday.objects.filter(
            date__month=month,
            date__year=year,
            is_active=True
        ).count()

        sundays = self._count_sundays(year, month)
        days_in_month = calendar.monthrange(year, month)[1]

        full_days_unverified = attendances.filter(
            status='full',
            verification_status='unverified'
        ).count()

        verified_full_days = attendances.filter(
            status='full',
            verification_status='verified'
        ).count()

        half_days_unverified = attendances.filter(
            status='half',
            verification_status='unverified'
        ).count()

        verified_half_days = attendances.filter(
            status='half',
            verification_status='verified'
        ).count()

        leaves = attendances.filter(status='leave').count()

        total_working_hours = attendances.aggregate(
            total=Sum('total_working_hours')
        )['total'] or 0

        total_break_hours = attendances.aggregate(
            total=Sum('total_break_hours')
        )['total'] or 0

        marked_days = attendances.count()
        not_marked = days_in_month - marked_days - holidays - sundays

        return Response({
            'user_id': user.id,
            'user_name': user.name,
            'user_email': user.email,
            'month': month,
            'year': year,
            'total_days': days_in_month,
            'full_days_unverified': full_days_unverified,
            'verified_full_days': verified_full_days,
            'half_days_unverified': half_days_unverified,
            'verified_half_days': verified_half_days,
            'leaves': leaves,
            'not_marked': not_marked,
            'total_working_hours': round(total_working_hours, 2),
            'total_break_hours': round(total_break_hours, 2),
            'holidays': holidays,
            'sundays': sundays,
        })

    @action(detail=False, methods=['get'], url_path='summary-all')
    def summary_all(self, request):
        """
        Get attendance summary (user-wise) for ALL users for a given month/year (Admin only)
        """
        if not self._is_admin(request.user):
            return Response(
                {'error': 'Only admins can view all users summary'},
                status=status.HTTP_403_FORBIDDEN
            )

        month = int(request.query_params.get('month', timezone.now().month))
        year = int(request.query_params.get('year', timezone.now().year))

        days_in_month = calendar.monthrange(year, month)[1]

        holidays_count = Holiday.objects.filter(
            date__month=month,
            date__year=year,
            is_active=True
        ).count()

        sundays_count = self._count_sundays(year, month)

        result = []

        # Only active users by default; override with ?is_active=true|false
        users = AppUser.objects.all().order_by('name')
        is_active = request.query_params.get('is_active', None)
        if is_active is not None:
            users = users.filter(is_active=is_active.lower() == 'true')
        else:
            users = users.filter(is_active=True)

        for user in users:
            attendances = Attendance.objects.filter(
                user=user,
                date__month=month,
                date__year=year
            )

            full_days_unverified = attendances.filter(
                status='full',
                verification_status='unverified'
            ).count()

            verified_full_days = attendances.filter(
                status='full',
                verification_status='verified'
            ).count()

            half_days_unverified = attendances.filter(
                status='half',
                verification_status='unverified'
            ).count()

            verified_half_days = attendances.filter(
                status='half',
                verification_status='verified'
            ).count()

            leaves = attendances.filter(status='leave').count()

            total_working_hours = attendances.aggregate(
                total=Sum('total_working_hours')
            )['total'] or 0

            total_break_hours = attendances.aggregate(
                total=Sum('total_break_hours')
            )['total'] or 0

            marked_days = attendances.count()
            not_marked = days_in_month - marked_days - holidays_count - sundays_count

            result.append({
                'user_id': user.id,
                'user_name': user.name,
                'user_email': user.email,
                'month': month,
                'year': year,
                'total_days': days_in_month,
                'full_days_unverified': full_days_unverified,
                'verified_full_days': verified_full_days,
                'half_days_unverified': half_days_unverified,
                'verified_half_days': verified_half_days,
                'leaves': leaves,
                'not_marked': not_marked,
                'total_working_hours': round(float(total_working_hours), 2),
                'total_break_hours': round(float(total_break_hours), 2),
                'holidays': holidays_count,
                'sundays': sundays_count,
            })

        return Response(result)

    @action(detail=False, methods=['get'])
    def monthly_grid(self, request):
        """Get monthly attendance grid"""
        month = int(request.query_params.get('month', timezone.now().month))
        year = int(request.query_params.get('year', timezone.now().year))

        days_in_month = calendar.monthrange(year, month)[1]
        # Only active users by default; override with ?is_active=true|false
        users = AppUser.objects.all().order_by('name')
        is_active = request.query_params.get('is_active', None)
        if is_active is not None:
            users = users.filter(is_active=is_active.lower() == 'true')
        else:
            users = users.filter(is_active=True)

        holidays = set(Holiday.objects.filter(
            date__month=month,
            date__year=year,
            is_active=True
        ).values_list('date', flat=True))

        result = []

        for user in users:
            attendances = Attendance.objects.filter(
                user=user,
                date__month=month,
                date__year=year
            )

            attendance_dict = {att.date.day: att for att in attendances}
            attendance_array = []

            for day in range(1, days_in_month + 1):
                current_date = datetime(year, month, day).date()

                if current_date.weekday() == 6:
                    attendance_array.append('sunday')
                elif current_date in holidays:
                    attendance_array.append('holiday')
                elif day in attendance_dict:
                    att = attendance_dict[day]

                    # Recalculate if needed
                    att.calculate_times()
                    att.update_status()
                    att.save()

                    if not att.first_punch_in_time:
                        attendance_array.append('not-marked')
                    elif att.verification_status == 'verified':
                        if att.status == 'full':
                            attendance_array.append('verified')
                        elif att.status == 'half':
                            attendance_array.append('half-verified')
                        elif att.status == 'leave':
                            attendance_array.append('verified-leave')
                        else:
                            attendance_array.append('verified')
                    else:
                        if att.status == 'full':
                            attendance_array.append('full')
                        elif att.status == 'half':
                            attendance_array.append('half')
                        elif att.status == 'leave':
                            attendance_array.append('leave')
                        else:
                            attendance_array.append('full')
                else:
                    attendance_array.append('not-marked')

            result.append({
                'user_id': user.id,
                'user_name': user.name,
                'user_email': user.email,
                'duty_start': user.duty_time_start.strftime('%H:%M') if user.duty_time_start else '09:00',
                'duty_end': user.duty_time_end.strftime('%H:%M') if user.duty_time_end else '18:00',
                'attendance': attendance_array
            })

        return Response(result)
    

        # ✅ CORRECT - verify starts at the SAME LEVEL as monthly_grid
    @action(detail=True, methods=['post'], url_path='verify')
    def verify(self, request, pk=None):
        """
        Verify attendance record (Admin only)
        Marks an attendance record as verified
        """
        print(f"=" * 80)
        print(f"🔵 VERIFY ENDPOINT CALLED")
        print(f"User: {request.user}")
        print(f"Attendance ID: {pk}")
        print(f"Request Data: {request.data}")
        print(f"=" * 80)
        
        if not self._is_admin(request.user):
            return Response(
                {'error': 'Only admins can verify attendance'}, 
                status=status.HTTP_403_FORBIDDEN
            )

        attendance = self.get_object()
        
        print(f"✅ Attendance found: {attendance}")
        print(f"Current verification status: {attendance.verification_status}")

        # Check if already verified
        if attendance.verification_status == 'verified':
            print(f"⚠️ Already verified")
            return Response(
                {
                    'success': True,
                    'message': 'Attendance already verified', 
                    'attendance': AttendanceSerializer(attendance, context={'request': request}).data
                },
                status=status.HTTP_200_OK
            )

        # Verify the attendance
        attendance.verification_status = 'verified'
        attendance.verified_by = request.user
        attendance.verified_at = timezone.now()

        # Add verification note
        admin_note_from_request = request.data.get('admin_note', '')
        verification_note = f"[{timezone.now().strftime('%Y-%m-%d %H:%M')}] Verified by {request.user.name if hasattr(request.user, 'name') else request.user.username}"
        
        if admin_note_from_request:
            verification_note = f"{admin_note_from_request}\n{verification_note}"
        
        if attendance.admin_note:
            attendance.admin_note += f"\n{verification_note}"
        else:
            attendance.admin_note = verification_note

        attendance.save()
        
        print(f"✅ Attendance verified successfully")
        print(f"=" * 80)

        response_serializer = AttendanceSerializer(attendance, context={'request': request})
        return Response(
            {
                'success': True,
                'message': 'Attendance verified successfully',
                'attendance': response_serializer.data
            },
            status=status.HTTP_200_OK
        )


    @action(detail=True, methods=['patch'], url_path='update_status')
    def update_status(self, request, pk=None):
        """Update attendance status (Admin only)"""
        if not self._is_admin(request.user):
            return Response(
                {'error': 'Only admins can update attendance status'}, 
                status=status.HTTP_403_FORBIDDEN
            )

        attendance = self.get_object()
        serializer = AttendanceUpdateStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        old_status = attendance.status
        new_status = serializer.validated_data['status']
        admin_note = serializer.validated_data.get('admin_note', '')
        leave_master_id = serializer.validated_data.get('leave_master')

        # Handle leave status
        if new_status in ['leave', 'special_leave', 'mandatory_holiday', 'absent']:
            attendance.first_punch_in_time = None
            attendance.last_punch_out_time = None
            attendance.first_punch_in_location = None
            attendance.last_punch_out_location = None
            attendance.first_punch_in_latitude = None
            attendance.first_punch_in_longitude = None
            attendance.last_punch_out_latitude = None
            attendance.last_punch_out_longitude = None
            attendance.total_working_hours = 0
            attendance.total_break_hours = 0
            attendance.is_currently_on_break = False

            # Delete all punch records
            attendance.punch_records.all().delete()

            # Set leave_master if provided (only for leave types, not absent)
            if leave_master_id and new_status != 'absent':
                try:
                    leave_master = LeaveMaster.objects.get(id=leave_master_id)
                    attendance.leave_master = leave_master
                    attendance.is_leave = True
                    attendance.is_paid_day = (leave_master.payment_status == 'paid')
                except LeaveMaster.DoesNotExist:
                    return Response(
                        {'error': f'Leave Master with id {leave_master_id} not found'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

            auto_note = f"Status changed to {new_status} from {old_status}"
            if attendance.admin_note:
                attendance.admin_note += f"\n[{timezone.now().strftime('%Y-%m-%d %H:%M')}] {auto_note}"
            else:
                attendance.admin_note = auto_note

        attendance.status = new_status

        if admin_note:
            stamped = f"[{timezone.now().strftime('%Y-%m-%d %H:%M')}] {admin_note}"
            if attendance.admin_note:
                attendance.admin_note += f"\n{stamped}"
            else:
                attendance.admin_note = stamped

        attendance.save()

        response_serializer = AttendanceSerializer(attendance, context={'request': request})
        return Response(
            {'message': 'Status updated', 'attendance': response_serializer.data}, 
            status=status.HTTP_200_OK
        )


class HolidayViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Holidays"""
    queryset = Holiday.objects.all().order_by('-date')
    serializer_class = HolidaySerializer
    permission_classes = [IsAuthenticated]
    menu_key = 'attendance'

    def get_queryset(self):
        queryset = Holiday.objects.all()
        year = self.request.query_params.get('year')
        if year:
            queryset = queryset.filter(date__year=year)
        month = self.request.query_params.get('month')
        if month:
            queryset = queryset.filter(date__month=month)
        return queryset.order_by('date')


class LeaveRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Leave Requests"""
    queryset = LeaveRequest.objects.all().select_related('user', 'reviewed_by')
    serializer_class = LeaveRequestSerializer
    permission_classes = [IsAuthenticated]
    menu_key = 'attendance'

    def _is_admin(self, user):
        """Helper to check if user is admin"""
        return (
            user.user_level in ('Super Admin', 'Admin') or
            user.is_staff or
            user.is_superuser
        )

    def get_queryset(self):
        """Filter queryset based on permissions and query params"""
        user = self.request.user
        queryset = LeaveRequest.objects.select_related('user', 'reviewed_by')

        is_admin = self._is_admin(user)

        if not is_admin:
            queryset = queryset.filter(user=user)

        user_id = self.request.query_params.get('user_id')
        if user_id and is_admin:
            queryset = queryset.filter(user_id=user_id)

        req_status = self.request.query_params.get('status')
        if req_status:
            queryset = queryset.filter(status=req_status)

        leave_type = self.request.query_params.get('leave_type')
        if leave_type:
            queryset = queryset.filter(leave_type=leave_type)

        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')
        if from_date:
            queryset = queryset.filter(from_date__gte=from_date)
        if to_date:
            queryset = queryset.filter(to_date__lte=to_date)

        month = self.request.query_params.get('month')
        year = self.request.query_params.get('year')
        if month and year:
            queryset = queryset.filter(from_date__month=month, from_date__year=year)

        return queryset.order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'create':
            return LeaveRequestCreateSerializer
        return LeaveRequestSerializer

    def perform_create(self, serializer):
        """Create leave request with the authenticated user"""
        serializer.save(user=self.request.user)



    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        instance = LeaveRequest.objects.get(id=serializer.instance.id)
        response_serializer = LeaveRequestSerializer(instance)

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'], url_path='review')
    def review(self, request, pk=None):
        """Review leave request (Admin only)"""
        if not self._is_admin(request.user):
            return Response(
                {'error': 'Only admins can review leave requests'},
                status=status.HTTP_403_FORBIDDEN
            )

        leave_request = self.get_object()

        if leave_request.status != 'pending':
            return Response(
                {'error': f'This request has already been {leave_request.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = LeaveRequestReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        leave_request.status = serializer.validated_data['status']
        leave_request.admin_comment = serializer.validated_data.get('admin_comment', '')
        leave_request.reviewed_by = request.user
        leave_request.reviewed_at = timezone.now()
        leave_request.save()

        response_serializer = LeaveRequestSerializer(leave_request)
        return Response(response_serializer.data)

    @action(detail=True, methods=['post'], url_path='override-review')
    def override_review(self, request, pk=None):
        """Admin override for leave request status"""
        if not self._is_admin(request.user):
            return Response(
                {'error': 'Only admins can override leave requests.'},
                status=status.HTTP_403_FORBIDDEN
            )

        leave_request = self.get_object()

        serializer = LeaveRequestReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data['status']
        admin_comment = serializer.validated_data.get('admin_comment', '')

        prev_status = leave_request.status

        leave_request.status = new_status
        leave_request.reviewed_by = request.user
        leave_request.reviewed_at = timezone.now()

        user_label = request.user.name if hasattr(request.user, 'name') else request.user.username
        override_note = f"[OVERRIDE by {user_label} at {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}] changed from {prev_status}"

        combined_note_parts = []
        if admin_comment:
            combined_note_parts.append(admin_comment)
        combined_note_parts.append(override_note)
        combined = "\n".join([p for p in combined_note_parts if p])

        if leave_request.admin_comment:
            leave_request.admin_comment = f"{leave_request.admin_comment}\n{combined}"
        else:
            leave_request.admin_comment = combined

        leave_request.save()

        response_serializer = LeaveRequestSerializer(leave_request)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='my-requests')
    def my_requests(self, request):
        """Get only current user's leave requests"""
        queryset = self.filter_queryset(
            LeaveRequest.objects.filter(user=request.user)
        ).select_related('user', 'reviewed_by')

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='pending')
    def pending(self, request):
        """Get all pending leave requests (Admin only)"""
        if not self._is_admin(request.user):
            return Response(
                {'error': 'Only admins can view all pending requests'},
                status=status.HTTP_403_FORBIDDEN
            )

        queryset = self.filter_queryset(
            LeaveRequest.objects.filter(status='pending')
        ).select_related('user', 'reviewed_by')

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        """Get leave request summary statistics"""
        user = request.user
        is_admin = self._is_admin(user)

        user_id = request.query_params.get('user_id', user.id)

        if not is_admin and int(user_id) != user.id:
            return Response(
                {'error': 'You can only view your own summary'},
                status=status.HTTP_403_FORBIDDEN
            )

        month = int(request.query_params.get('month', timezone.now().month))
        year = int(request.query_params.get('year', timezone.now().year))

        requests_qs = LeaveRequest.objects.filter(
            user_id=user_id,
            from_date__month=month,
            from_date__year=year
        )

        total = requests_qs.count()
        pending = requests_qs.filter(status='pending').count()
        approved = requests_qs.filter(status='approved').count()
        rejected = requests_qs.filter(status='rejected').count()

        total_days = sum([req.total_days for req in requests_qs])
        approved_days = sum([req.total_days for req in requests_qs.filter(status='approved')])

        return Response({
            'user_id': user_id,
            'month': month,
            'year': year,
            'total_requests': total,
            'pending': pending,
            'approved': approved,
            'rejected': rejected,
            'total_days_requested': total_days,
            'approved_days': approved_days,
        })


import logging
logger = logging.getLogger(__name__)


class LateRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Late Requests
    """
    queryset = LateRequest.objects.all().select_related('user', 'reviewed_by')
    serializer_class = LateRequestSerializer
    permission_classes = [IsAuthenticated]
    menu_key = 'attendance'

    def _is_admin(self, user):
        return (
            user.user_level in ('Super Admin', 'Admin') or
            user.is_staff or user.is_superuser
        )

    def get_queryset(self):
        user = self.request.user
        queryset = LateRequest.objects.select_related('user', 'reviewed_by')
        is_admin = self._is_admin(user)
        if not is_admin:
            queryset = queryset.filter(user=user)

        date = self.request.query_params.get('date')
        if date:
            queryset = queryset.filter(date=date)
        req_status = self.request.query_params.get('status')
        if req_status:
            queryset = queryset.filter(status=req_status)

        month = self.request.query_params.get('month')
        year = self.request.query_params.get('year')
        if month and year:
            queryset = queryset.filter(date__month=month, date__year=year)

        return queryset.order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'create':
            return LateRequestCreateSerializer
        return LateRequestSerializer

    def perform_create(self, serializer):
        logger.info(f"Creating late request for user: {self.request.user.id}")
        serializer.save(user=self.request.user)
        logger.info(f"Late request created successfully: {serializer.instance.id}")

    def create(self, request, *args, **kwargs):
        try:
            logger.info(f"=== LATE REQUEST CREATE START ===")
            logger.info(f"User: {request.user.id}")
            logger.info(f"Request data: {request.data}")

            serializer = self.get_serializer(data=request.data)
            logger.info(f"Serializer validation...")

            serializer.is_valid(raise_exception=True)
            logger.info(f"Serializer validation passed")

            logger.info(f"Performing create...")
            self.perform_create(serializer)
            logger.info(f"Perform create completed")

            logger.info(f"Fetching created instance...")
            instance = LateRequest.objects.select_related(
                'user', 'reviewed_by'
            ).get(id=serializer.instance.id)
            
            response_serializer = LateRequestSerializer(instance)
            logger.info(f"Instance serialized successfully")

            logger.info(f"=== LATE REQUEST CREATE SUCCESS ===")
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            logger.error(f"=== LATE REQUEST CREATE FAILED ===")
            logger.error(f"Error: {e}")
            import traceback
            logger.error(traceback.format_exc())

            return Response(
                {
                    'error': str(e),
                    'detail': 'Late request creation failed. Check server logs for details.'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='my-requests')
    def my_requests(self, request):
        qs = LateRequest.objects.filter(user=request.user).select_related(
            'user', 'reviewed_by'
        ).order_by('-created_at')
        serializer = LateRequestSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='review')
    def review(self, request, pk=None):
        if not self._is_admin(request.user):
            return Response({'error': 'Only admins can review'}, status=status.HTTP_403_FORBIDDEN)
        instance = self.get_object()
        if instance.status != 'pending':
            return Response({'error': f'Already {instance.status}'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = LeaveRequestReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance.status = serializer.validated_data['status']
        instance.admin_comment = serializer.validated_data.get('admin_comment', '')
        instance.reviewed_by = request.user
        instance.reviewed_at = timezone.now()
        instance.save()
        return Response(LateRequestSerializer(instance).data)

    @action(detail=True, methods=['post'], url_path='override-review')
    def override_review(self, request, pk=None):
        if not self._is_admin(request.user):
            return Response({'error': 'Only admins can override'}, status=status.HTTP_403_FORBIDDEN)
        instance = self.get_object()
        serializer = LeaveRequestReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        prev = instance.status
        instance.status = serializer.validated_data['status']
        instance.reviewed_by = request.user
        instance.reviewed_at = timezone.now()
        note_parts = []
        if serializer.validated_data.get('admin_comment'):
            note_parts.append(serializer.validated_data.get('admin_comment'))
        note_parts.append(f"[OVERRIDE by {request.user.name if hasattr(request.user, 'name') else request.user.username} at {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}] changed from {prev}")
        combined = "\n".join(note_parts)
        instance.admin_comment = f"{instance.admin_comment}\n{combined}" if instance.admin_comment else combined
        instance.save()
        return Response(LateRequestSerializer(instance).data)
    
   


class EarlyRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Early Requests
    """
    queryset = EarlyRequest.objects.all().select_related('user', 'reviewed_by')
    serializer_class = EarlyRequestSerializer
    permission_classes = [IsAuthenticated]
    menu_key = 'attendance'

    def _is_admin(self, user):
        return (
            user.user_level in ('Super Admin', 'Admin') or
            user.is_staff or user.is_superuser
        )

    def get_queryset(self):
        user = self.request.user
        queryset = EarlyRequest.objects.select_related('user', 'reviewed_by')
        is_admin = self._is_admin(user)
        if not is_admin:
            queryset = queryset.filter(user=user)

        date = self.request.query_params.get('date')
        if date:
            queryset = queryset.filter(date=date)
        req_status = self.request.query_params.get('status')
        if req_status:
            queryset = queryset.filter(status=req_status)

        month = self.request.query_params.get('month')
        year = self.request.query_params.get('year')
        if month and year:
            queryset = queryset.filter(date__month=month, date__year=year)

        return queryset.order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'create':
            return EarlyRequestCreateSerializer
        return EarlyRequestSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        instance = EarlyRequest.objects.select_related(
            'user', 'reviewed_by'
        ).get(id=serializer.instance.id)
        
        response_serializer = EarlyRequestSerializer(instance)
        
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=['get'], url_path='my-requests')
    def my_requests(self, request):
        qs = EarlyRequest.objects.filter(user=request.user).select_related(
            'user', 'reviewed_by'
        ).order_by('-created_at')
        serializer = EarlyRequestSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='review')
    def review(self, request, pk=None):
        if not self._is_admin(request.user):
            return Response({'error': 'Only admins can review'}, status=status.HTTP_403_FORBIDDEN)
        instance = self.get_object()
        if instance.status != 'pending':
            return Response({'error': f'Already {instance.status}'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = LeaveRequestReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance.status = serializer.validated_data['status']
        instance.admin_comment = serializer.validated_data.get('admin_comment', '')
        instance.reviewed_by = request.user
        instance.reviewed_at = timezone.now()
        instance.save()
        return Response(EarlyRequestSerializer(instance).data)

    @action(detail=True, methods=['post'], url_path='override-review')
    def override_review(self, request, pk=None):
        if not self._is_admin(request.user):
            return Response({'error': 'Only admins can override'}, status=status.HTTP_403_FORBIDDEN)
        instance = self.get_object()
        serializer = LeaveRequestReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        prev = instance.status
        instance.status = serializer.validated_data['status']
        instance.reviewed_by = request.user
        instance.reviewed_at = timezone.now()
        note_parts = []
        if serializer.validated_data.get('admin_comment'):
            note_parts.append(serializer.validated_data.get('admin_comment'))
        note_parts.append(f"[OVERRIDE by {request.user.name if hasattr(request.user, 'name') else request.user.username} at {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}] changed from {prev}")
        combined = "\n".join(note_parts)
        instance.admin_comment = f"{instance.admin_comment}\n{combined}" if instance.admin_comment else combined
        instance.save()
        return Response(EarlyRequestSerializer(instance).data)
    
    


# Reverse Geocoding Functions (unchanged)
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def reverse_geocode(request):
    """
    Reverse geocode coordinates to address.
    Supports both GET (with query params) and POST (with body) methods.
    """
    # Support both GET and POST methods
    if request.method == 'GET':
        latitude = request.query_params.get('latitude')
        longitude = request.query_params.get('longitude')
    else:
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')

    if not latitude or not longitude:
        return Response(
            {'error': 'Latitude and longitude are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        response = requests.get(
            f'https://nominatim.openstreetmap.org/reverse',
            params={
                'format': 'json',
                'lat': latitude,
                'lon': longitude,
                'zoom': 18,
                'addressdetails': 1
            },
            headers={
                'User-Agent': 'AttendanceApp/1.0 (your-email@example.com)'
            },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            address = data.get('display_name', f'{latitude}, {longitude}')

            return Response({
                'address': address,
                'latitude': latitude,
                'longitude': longitude,
                'details': data.get('address', {})
            })

        return Response({
            'address': f'Lat: {latitude}, Lon: {longitude}',
            'latitude': latitude,
            'longitude': longitude,
            'details': {}
        })

    except requests.exceptions.RequestException as e:
        return Response({
            'address': f'Lat: {latitude}, Lon: {longitude}',
            'latitude': latitude,
            'longitude': longitude,
            'details': {},
            'error': str(e)
        })


# The reverse_geocode_bigdata function is already correct with @api_view(['POST'])
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reverse_geocode_bigdata(request):
    """Reverse geocode using BigDataCloud API"""
    latitude = request.data.get('latitude')
    longitude = request.data.get('longitude')

    if not latitude or not longitude:
        return Response(
            {'error': 'Latitude and longitude are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        response = requests.get(
            'https://api.bigdatacloud.net/data/reverse-geocode-client',
            params={
                'latitude': latitude,
                'longitude': longitude,
                'localityLanguage': 'en'
            },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            
            # Build address from components
            components = []
            if data.get('locality'):
                components.append(data['locality'])
            if data.get('city'):
                components.append(data['city'])
            if data.get('principalSubdivision'):
                components.append(data['principalSubdivision'])
            if data.get('countryName'):
                components.append(data['countryName'])
            
            address = ', '.join(components) if components else f'{latitude}, {longitude}'

            return Response({
                'address': address,
                'latitude': latitude,
                'longitude': longitude,
                'details': data
            })

        return Response({
            'address': f'Lat: {latitude}, Lon: {longitude}',
            'latitude': latitude,
            'longitude': longitude,
            'details': {}
        })

    except requests.exceptions.RequestException as e:
        return Response({
            'address': f'Lat: {latitude}, Lon: {longitude}',
            'latitude': latitude,
            'longitude': longitude,
            'details': {},
            'error': str(e)
        })


@action(detail=False, methods=['get'], url_path='all-details')
def all_details(self, request):
    """
    Get full attendance details for ALL users for a given month/year,
    including days where attendance is not marked.
    Admin only.
    """
    # Only admins can view everyone
    if not self._is_admin(request.user):
        return Response(
            {'error': 'Only admins can view all users attendance'},
            status=status.HTTP_403_FORBIDDEN
        )

    month = int(request.query_params.get('month', timezone.now().month))
    year = int(request.query_params.get('year', timezone.now().year))

    days_in_month = calendar.monthrange(year, month)[1]

    # Preload holidays for marking
    holidays = set(Holiday.objects.filter(
        date__month=month,
        date__year=year,
        is_active=True
    ).values_list('date', flat=True))

    result = []

    # Only active users by default; override with ?is_active=true|false
    users = AppUser.objects.all().order_by('name')
    is_active = request.query_params.get('is_active', None)
    if is_active is not None:
        users = users.filter(is_active=is_active.lower() == 'true')
    else:
        users = users.filter(is_active=True)

    for user in users:
        # All real attendance rows for this user in this month
        user_att_qs = Attendance.objects.filter(
            user=user,
            date__month=month,
            date__year=year
        )

        # Index by day for quick lookup
        att_by_day = {att.date.day: att for att in user_att_qs}

        day_records = []

        for day in range(1, days_in_month + 1):
            current_date = datetime(year, month, day).date()
            rec = {
                'date': current_date.isoformat(),
            }

            # Sunday
            if current_date.weekday() == 6:
                rec['status'] = 'sunday'
                rec['marked'] = False
                rec['attendance'] = None

            # Holiday
            elif current_date in holidays:
                rec['status'] = 'holiday'
                rec['marked'] = False
                rec['attendance'] = None

            # Has attendance row
            elif day in att_by_day:
                att = att_by_day[day]

                # Make sure times and status are up-to-date
                att.calculate_times()
                att.update_status()
                att.save()

                rec['status'] = att.status
                rec['marked'] = True
                rec['attendance'] = AttendanceSerializer(att).data

            # No row at all = not marked
            else:
                rec['status'] = 'not-marked'
                rec['marked'] = False
                rec['attendance'] = None

            day_records.append(rec)

        result.append({
            'user_id': user.id,
            'user_name': user.name,
            'user_email': user.email,
            'month': month,
            'year': year,
            'days': day_records,
        })

    return Response(result)


# HR/views.py - Add Leave Master ViewSet and enhance Leave Request endpoints

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone

from master.models import LeaveMaster  # ✅ Import from master app
from .models import LeaveRequest 
from .Serializers import (
    LeaveMasterSerializer,
    LeaveRequestSerializer,
    LeaveRequestCreateSerializer,
    LeaveRequestReviewSerializer,
)




class LeaveMasterViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Leave Master
    """
    queryset = LeaveMaster.objects.all().order_by('-created_at')
    serializer_class = LeaveMasterSerializer
    permission_classes = [IsAuthenticated]
    menu_key = 'attendance'
    
    def _is_admin(self, user):
        """Helper to check if user is admin"""
        return (
            user.user_level in ('Super Admin', 'Admin') or
            user.is_staff or
            user.is_superuser
        )
    
    def get_queryset(self):
        """Filter queryset based on query params"""
        queryset = LeaveMaster.objects.all()
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Filter by payment status
        payment_status = self.request.query_params.get('payment_status')
        if payment_status:
            queryset = queryset.filter(payment_status=payment_status)
        
        # Filter by month/year ONLY if both parameters are provided
        month = self.request.query_params.get('month')
        year = self.request.query_params.get('year')
        if month and year:
            queryset = queryset.filter(
                Q(leave_date__month=month, leave_date__year=year) |
                Q(leave_date__isnull=True)
            )
        
        return queryset.order_by('leave_date', 'leave_name')
    
    def list(self, request, *args, **kwargs):
        """Override list to return consistent response structure"""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'count': queryset.count()
        })
    
    def create(self, request, *args, **kwargs):
        """Only admins can create leave masters"""
        if not self._is_admin(request.user):
            return Response(
                {'error': 'Only admins can create leave masters'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = LeaveMasterCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        
        # Return full serialized data
        instance = LeaveMaster.objects.get(id=serializer.instance.id)
        response_serializer = LeaveMasterSerializer(instance)
        
        return Response({
            'success': True,
            'data': response_serializer.data,
            'message': 'Leave master created successfully'
        }, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """Only admins can update leave masters"""
        if not self._is_admin(request.user):
            return Response(
                {'error': 'Only admins can update leave masters'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = LeaveMasterCreateSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Return full serialized data
        response_serializer = LeaveMasterSerializer(instance)
        
        return Response({
            'success': True,
            'data': response_serializer.data,
            'message': 'Leave master updated successfully'
        })
    
    def destroy(self, request, *args, **kwargs):
        """Only admins can delete leave masters"""
        if not self._is_admin(request.user):
            return Response(
                {'error': 'Only admins can delete leave masters'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        instance = self.get_object()
        instance.delete()
        
        return Response({
            'success': True,
            'message': 'Leave master deleted successfully'
        }, status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'], url_path='active-leaves')
    def active_leaves(self, request):
        """
        CRITICAL ENDPOINT: Get ALL active leaves for leave request dropdown
        This endpoint returns ALL active leaves without any date filtering
        """
        print("=" * 80)
        print("🔵 ACTIVE LEAVES ENDPOINT CALLED")
        print("=" * 80)
        print(f"Request User: {request.user}")
        print(f"Request Method: {request.method}")
        print(f"Request Path: {request.path}")
        print(f"Query Params: {dict(request.query_params)}")
        
        # Get ALL active leaves - NO FILTERING by month/year
        leaves = LeaveMaster.objects.filter(is_active=True).order_by('leave_date', 'leave_name')
        
        print(f"\n📊 Database Query Results:")
        print(f"Total active leaves in database: {leaves.count()}")
        print(f"SQL Query: {leaves.query}")
        
        # Debug each leave
        if leaves.exists():
            print(f"\n📋 Leave Details:")
            for idx, leave in enumerate(leaves, 1):
                print(f"\n  {idx}. {leave.leave_name}")
                print(f"     • ID: {leave.id}")
                print(f"     • Category: {leave.category} ({leave.get_category_display()})")
                print(f"     • Payment: {leave.payment_status} ({leave.get_payment_status_display()})")
                print(f"     • Date: {leave.leave_date or 'No specific date'}")
                print(f"     • Active: {leave.is_active}")
                print(f"     • Description: {leave.description or 'None'}")
        else:
            print("\n⚠️  NO ACTIVE LEAVES FOUND IN DATABASE!")
            print("   Please create leave types in the Leave Master section first.")
        
        # Serialize the data
        serializer = LeaveMasterSerializer(leaves, many=True)
        
        print(f"\n🔄 Serialization Results:")
        print(f"Serialized records: {len(serializer.data)}")
        
        # Prepare response
        response_data = {
            'success': True,
            'data': serializer.data,
            'count': leaves.count(),
            'message': f'{leaves.count()} active leave type(s) available'
        }
        
        print(f"\n✅ Response Data:")
        print(f"Success: {response_data['success']}")
        print(f"Count: {response_data['count']}")
        print(f"Message: {response_data['message']}")
        print(f"Data length: {len(response_data['data'])}")
        
        print("=" * 80)
        print("🔵 ACTIVE LEAVES ENDPOINT COMPLETE")
        print("=" * 80)
        
        return Response(response_data)
    
    @action(detail=False, methods=['get'], url_path='categories')
    def categories(self, request):
        """Get all leave categories grouped"""
        categories = {}
        leave_masters = LeaveMaster.objects.filter(is_active=True)
        
        for leave in leave_masters:
            category = leave.get_category_display()
            if category not in categories:
                categories[category] = []
            
            categories[category].append({
                'id': leave.id,
                'name': leave.leave_name,
                'date': leave.leave_date,
                'payment_status': leave.get_payment_status_display(),
                'is_paid': leave.payment_status == 'paid',
                'description': leave.description,
            })
        
        return Response({
            'success': True,
            'data': {
                'categories': categories,
                'category_choices': [
                    {'value': choice[0], 'label': choice[1]}
                    for choice in LeaveMaster.CATEGORY_CHOICES
                ]
            }
        })


class LeaveRequestViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Leave Requests - NOW REQUIRES leave_master from master app
    """
    queryset = LeaveRequest.objects.all().select_related('user', 'reviewed_by', 'leave_master')
    serializer_class = LeaveRequestSerializer
    permission_classes = [IsAuthenticated]
    menu_key = 'attendance'
    
    def _is_admin(self, user):
        """Helper to check if user is admin"""
        return (
            user.user_level in ('Super Admin', 'Admin') or
            user.is_staff or
            user.is_superuser
        )
    
    def get_queryset(self):
        """Filter queryset based on permissions and query params"""
        user = self.request.user
        queryset = LeaveRequest.objects.select_related('user', 'reviewed_by', 'leave_master')

        is_admin = self._is_admin(user)

        if not is_admin:
            queryset = queryset.filter(user=user)

        user_id = self.request.query_params.get('user_id')
        if user_id and is_admin:
            queryset = queryset.filter(user_id=user_id)

        req_status = self.request.query_params.get('status')
        if req_status:
            queryset = queryset.filter(status=req_status)

        # Filter by leave_master category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(leave_master__category=category)

        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')
        if from_date:
            queryset = queryset.filter(from_date__gte=from_date)
        if to_date:
            queryset = queryset.filter(to_date__lte=to_date)

        month = self.request.query_params.get('month')
        year = self.request.query_params.get('year')
        if month and year:
            queryset = queryset.filter(from_date__month=month, from_date__year=year)

        return queryset.order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'create':
            return LeaveRequestCreateSerializer
        return LeaveRequestSerializer

    def perform_create(self, serializer):
        """Create leave request with the authenticated user"""
        serializer.save(user=self.request.user)


    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        instance = LeaveRequest.objects.select_related(
            'user', 'reviewed_by', 'leave_master'
        ).get(id=serializer.instance.id)
        response_serializer = LeaveRequestSerializer(instance)

        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'], url_path='review')
    def review(self, request, pk=None):
        """Review leave request (Admin only)"""
        if not self._is_admin(request.user):
            return Response(
                {'error': 'Only admins can review leave requests'},
                status=status.HTTP_403_FORBIDDEN
            )

        leave_request = self.get_object()

        if leave_request.status != 'pending':
            return Response(
                {'error': f'This request has already been {leave_request.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = LeaveRequestReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        leave_request.status = serializer.validated_data['status']
        leave_request.admin_comment = serializer.validated_data.get('admin_comment', '')
        leave_request.reviewed_by = request.user
        leave_request.reviewed_at = timezone.now()
        leave_request.save()

        response_serializer = LeaveRequestSerializer(leave_request)
        return Response(response_serializer.data)

    @action(detail=True, methods=['post'], url_path='override-review')
    def override_review(self, request, pk=None):
        """Admin override for leave request status"""
        if not self._is_admin(request.user):
            return Response(
                {'error': 'Only admins can override leave requests.'},
                status=status.HTTP_403_FORBIDDEN
            )

        leave_request = self.get_object()

        serializer = LeaveRequestReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data['status']
        admin_comment = serializer.validated_data.get('admin_comment', '')

        prev_status = leave_request.status

        leave_request.status = new_status
        leave_request.reviewed_by = request.user
        leave_request.reviewed_at = timezone.now()

        user_label = request.user.name if hasattr(request.user, 'name') else request.user.username
        override_note = f"[OVERRIDE by {user_label} at {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}] changed from {prev_status}"

        combined_note_parts = []
        if admin_comment:
            combined_note_parts.append(admin_comment)
        combined_note_parts.append(override_note)
        combined = "\n".join([p for p in combined_note_parts if p])

        if leave_request.admin_comment:
            leave_request.admin_comment = f"{leave_request.admin_comment}\n{combined}"
        else:
            leave_request.admin_comment = combined

        leave_request.save()

        response_serializer = LeaveRequestSerializer(leave_request)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='my-requests')
    def my_requests(self, request):
        """Get only current user's leave requests"""
        queryset = self.filter_queryset(
            LeaveRequest.objects.filter(user=request.user)
        ).select_related('user', 'reviewed_by', 'leave_master')

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='pending')
    def pending(self, request):
        """Get all pending leave requests (Admin only)"""
        if not self._is_admin(request.user):
            return Response(
                {'error': 'Only admins can view all pending requests'},
                status=status.HTTP_403_FORBIDDEN
            )

        queryset = self.filter_queryset(
            LeaveRequest.objects.filter(status='pending')
        ).select_related('user', 'reviewed_by', 'leave_master')

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        """Get leave request summary statistics"""
        user = request.user
        is_admin = self._is_admin(user)

        user_id = request.query_params.get('user_id', user.id)

        if not is_admin and int(user_id) != user.id:
            return Response(
                {'error': 'You can only view your own summary'},
                status=status.HTTP_403_FORBIDDEN
            )

        month = int(request.query_params.get('month', timezone.now().month))
        year = int(request.query_params.get('year', timezone.now().year))

        requests_qs = LeaveRequest.objects.filter(
            user_id=user_id,
            from_date__month=month,
            from_date__year=year
        )

        total = requests_qs.count()
        pending = requests_qs.filter(status='pending').count()
        approved = requests_qs.filter(status='approved').count()
        rejected = requests_qs.filter(status='rejected').count()

        total_days = sum([req.total_days for req in requests_qs])
        approved_days = sum([req.total_days for req in requests_qs.filter(status='approved')])

        return Response({
            'user_id': user_id,
            'month': month,
            'year': year,
            'total_requests': total,
            'pending': pending,
            'approved': approved,
            'rejected': rejected,
            'total_days_requested': total_days,
            'approved_days': approved_days,
        })
    
    @action(detail=False, methods=['get'], url_path='available-leave-types')
    def available_leave_types(self, request):
        """Get available leave types from master.LeaveMaster"""
        leave_types = LeaveMaster.objects.filter(is_active=True).order_by('category', 'leave_name')
        serializer = LeaveMasterSerializer(leave_types, many=True)
        
        return Response({
            'success': True,
            'data': serializer.data,
            'count': leave_types.count()
        })


# HR/views.py - Add this new endpoint

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_office_geofence_info(request):
    """
    Get office geofence configuration for display purposes only
    Frontend should NOT use this for validation - validation happens server-side
    
    NOTE: This function is DEPRECATED - use /api/hr/geofence-info/ instead
    (handled by views_office_config.get_office_geofence_info)
    """
    from HR.utils.geofence import get_office_info
    
    office_info = get_office_info()
    
    if not office_info:
        return Response({
            'error': 'Office location not configured',
            'detail': 'No office location has been set up. Please contact your administrator.',
            'message': 'Office configuration is missing'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    return Response({
        'office_latitude': office_info['latitude'],
        'office_longitude': office_info['longitude'],
        'radius_meters': office_info['radius'],
        'office_address': office_info['address'],
        'office_name': office_info['name'],
        'source': office_info['source'],
        'message': 'You must be within the office radius to punch in/out'
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def attendance_penalty_review(request):
    """Get monthly attendance penalty review rows for admin/HR review."""
    month = int(request.query_params.get('month', timezone.now().month))
    year = int(request.query_params.get('year', timezone.now().year))
    status_filter = (request.query_params.get('status') or '').strip().lower()
    department_filter = (request.query_params.get('department') or '').strip().lower()
    employee_filter = (request.query_params.get('employee_id') or request.query_params.get('employee')).strip() if (request.query_params.get('employee_id') or request.query_params.get('employee')) else ''
    search = (request.query_params.get('search') or '').strip().lower()

    employees = Employee.objects.select_related('user').prefetch_related('department').all().order_by('full_name', 'employee_id')

    if employee_filter:
        employees = employees.filter(Q(id=employee_filter) | Q(employee_id=employee_filter) | Q(user__id=employee_filter) | Q(user__email__iexact=employee_filter))

    if department_filter:
        employees = employees.filter(department__name__icontains=department_filter)

    rows = []
    totals = {
        'total_employees': 0,
        'late_arrivals': 0,
        'early_leaves': 0,
        'missed_punches': 0,
        'pending_actions': 0,
        'approved_actions': 0,
        'waived_actions': 0,
        'leave_penalties': 0,
        'leave_penalty_days': 0,
        'total_deduction_amount': 0,
    }

    last_day = calendar.monthrange(year, month)[1]
    month_start = datetime(year, month, 1).date()
    month_end = datetime(year, month, last_day).date()

    # Get pagination parameters early and limit employee processing
    page = int(request.query_params.get('page', 1) or 1)
    page_size = int(request.query_params.get('page_size', 8) or 8)
    page = max(1, page)
    page_size = max(1, min(page_size, 100))

    all_employees_list = list(employees.distinct())
    if search:
        filtered_employees = []
        for employee in all_employees_list:
            user = getattr(employee, 'user', None)
            employee_name = _get_employee_display_name(employee)
            employee_id_text = str(getattr(employee, 'employee_id', '') or '').lower()
            employee_email_text = str(getattr(user, 'email', '') or '').lower() if user else ''
            if (
                search in employee_name.lower()
                or search in employee_id_text
                or search in employee_email_text
            ):
                filtered_employees.append(employee)
        all_employees_list = filtered_employees

    # Apply pagination after search filtering so search works across the full result set
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    employees_for_processing = all_employees_list[start_index:end_index]
    
    for employee in employees_for_processing:
        user = getattr(employee, 'user', None)
        if not user:
            continue

        employee_name = _get_employee_display_name(employee)
        if search and search not in employee_name.lower() and search not in str(getattr(employee, 'employee_id', '') or '').lower() and search not in str(getattr(user, 'email', '') or '').lower():
            continue

        penalty_data = calculate_monthly_penalties(user, year, month)
        per_date = penalty_data.get('per_date', {}) or {}
        summary = penalty_data.get('summary', {}) or {}
        try:
            from payroll.services import PayrollCalculationService
        except Exception:
            PayrollCalculationService = None

        base_salary = float(getattr(employee, 'basic_salary', 0) or 0)
        if PayrollCalculationService:
            try:
                base_salary = float(PayrollCalculationService.get_employee_salary(employee))
            except Exception:
                base_salary = float(getattr(employee, 'basic_salary', 0) or 0)

        penalty_amount = 0.0
        deduction_breakdown = []
        if PayrollCalculationService:
            try:
                # Calculate working days (default to 22 if not in summary)
                working_days = int(summary.get('working_days', 0) or 22)
                if working_days <= 0:
                    working_days = 22
                    
                deduction_result = PayrollCalculationService.calculate_attendance_penalty_deduction(
                    employee=employee,
                    year=year,
                    month_number=month,
                    working_days=working_days,
                    base_salary=base_salary,
                )
                penalty_amount = float(deduction_result.get('amount', 0) or 0)
                deduction_breakdown = deduction_result.get('items', [])
            except Exception:
                penalty_amount = 0.0
                deduction_breakdown = []
        amount_after_penalties = max(base_salary - penalty_amount, 0.0)

        # Load attendance details
        attendance_rows = []
        attendance_qs = Attendance.objects.filter(
            user=user,
            date__year=year,
            date__month=month,
        ).select_related('leave_master', 'leave_request', 'verified_by', 'holiday').prefetch_related('punch_records').order_by('date')

        attendance_dates = set()

        for attendance in attendance_qs:
            attendance_dates.add(attendance.date)
            attendance_rows.append(_serialize_attendance_detail(attendance, per_date.get(attendance.date)))

        # Add synthetic missed-punch rows for dates where no Attendance row exists.
        # This keeps the sidebar actionable for employees who never punched in.
        for penalty_date, penalty_detail in sorted(per_date.items(), key=lambda item: item[0]):
            if not (penalty_detail or {}).get('missed_punch'):
                continue
            if penalty_date in attendance_dates:
                continue

            attendance_rows.append({
                'id': f'synthetic-{employee.id}-{penalty_date.isoformat()}',
                'date': penalty_date,
                'status': 'absent',
                'status_display': 'Absent',
                'verification_status': 'unverified',
                'verification_status_display': 'Unverified',
                'first_punch_in_time': None,
                'first_punch_in_location': None,
                'last_punch_out_time': None,
                'last_punch_out_location': None,
                'total_working_hours': 0,
                'total_break_hours': 0,
                'is_leave': False,
                'is_sunday': penalty_date.weekday() == 6,
                'is_working_sunday': False,
                'is_holiday': False,
                'is_paid_day': False,
                'leave_name': None,
                'note': '',
                'admin_note': '',
                'verified_at': None,
                'verified_by_name': None,
                'punches': [],
                'late_request_status': None,
                'early_request_status': None,
                'missed_punch_status': 'pending',
                'penalty': penalty_detail,
                'synthetic': True,
            })

        # Batch query late and early requests to avoid N+1 queries
        late_requests = LateRequest.objects.filter(user=user, date__year=year, date__month=month)
        early_requests = EarlyRequest.objects.filter(user=user, date__year=year, date__month=month)
        unpaid_leave_requests = LeaveRequest.objects.filter(
            user=user,
            status='approved',
            is_paid=False,
            from_date__lte=month_end,
            to_date__gte=month_start,
        )

        attendance_rows.sort(key=lambda item: item.get('date') or month_start)

        # Only count penalties that have been APPROVED for deduction (not pending or waived)
        late_count_approved = late_requests.filter(status='approved').count()
        early_count_approved = early_requests.filter(status='approved').count()
        
        # For missed punches, count only DEDUCTED ones, but only AFTER grace period exhausted
        attendance_records = Attendance.objects.filter(
            user=user,
            date__year=month_start.year,
            date__month=month_start.month
        ).values('date', 'admin_note')
        
        # Get grace period for missed punch
        missed_grace = 1  # Default
        try:
            rule = AutomationRule.objects.filter(rule_type='missed', is_active=True, deduction_type='Fixed Amount').first()
            if rule:
                missed_grace = int(rule.max_occurrences or 1)
        except Exception:
            pass
        
        # Count ALL missed and DEDUCTED separately
        all_missed_dates = set()
        deducted_missed_dates = set()
        for att in attendance_records:
            if att['admin_note']:
                admin_lower = str(att['admin_note']).lower()
                # Check if reviewed (deducted or waived)
                if ('deduct' in admin_lower or 'applied' in admin_lower or 'waive' in admin_lower) and 'missed punch' in admin_lower:
                    all_missed_dates.add(att['date'])
                # Check if deducted
                if ('deduct' in admin_lower or 'applied' in admin_lower) and 'missed punch' in admin_lower:
                    deducted_missed_dates.add(att['date'])
        
        # Only count deductions AFTER grace reached
        total_missed = len(all_missed_dates)
        if total_missed > missed_grace:
            missed_count_approved = len(deducted_missed_dates)
        else:
            missed_count_approved = 0
        
        # For ALL penalties (for status display)
        late_total = late_requests.count()
        early_total = early_requests.count()
        missed_total = sum(1 for item in per_date.values() if (item or {}).get('missed_punch'))
        penalty_events = late_total + early_total + missed_total

        # Count penalties by status for determining overall review status
        # Late and Early: tracked in LateRequest/EarlyRequest
        pending_count = late_requests.filter(status='pending').count() + early_requests.filter(status='pending').count()
        approved_count = late_requests.filter(status='approved').count() + early_requests.filter(status='approved').count()
        rejected_count = late_requests.filter(status='rejected').count() + early_requests.filter(status='rejected').count()

        leave_penalty_days = 0
        for leave_request in unpaid_leave_requests:
            overlap_start = max(leave_request.from_date, month_start)
            overlap_end = min(leave_request.to_date, month_end)
            if overlap_end >= overlap_start:
                leave_penalty_days += (overlap_end - overlap_start).days + 1

        review_status = _review_status(pending_count, approved_count, rejected_count, penalty_events)
        action = _suggest_penalty_action(float(summary.get('total_deduction_days', 0) or 0), penalty_events)
        
        # Store approved counts for deduction calculation later
        # We'll use late_count_approved and early_count_approved below

        review_status = _review_status(pending_count, approved_count, rejected_count, penalty_events)
        action = _suggest_penalty_action(float(summary.get('total_deduction_days', 0) or 0), penalty_events)

        if status_filter and status_filter != 'all':
            normalized = review_status.lower()
            if status_filter not in normalized:
                continue

        department_name = _get_employee_department_name(employee)
        avatar = _get_employee_avatar(employee_name)

        latest_late = late_requests.order_by('-created_at').first()
        latest_early = early_requests.order_by('-created_at').first()
        latest_request = None
        if latest_late and latest_early:
            latest_request = latest_late if latest_late.created_at >= latest_early.created_at else latest_early
        else:
            latest_request = latest_late or latest_early

        latest_comment = ''
        if latest_request:
            latest_comment = latest_request.admin_comment or latest_request.reason or ''

        row = {
            'id': employee.id,
            'employee': _serialize_employee_meta(employee),
            'name': employee_name,
            'empId': employee.employee_id or getattr(user, 'email', None) or f'EMP{employee.id}',
            'dept': department_name,
            'departments': [dept.name for dept in employee.department.all() if getattr(dept, 'name', None)],
            'avatar': avatar,
            'avatar_url': getattr(getattr(employee, 'avatar', None), 'url', None) if getattr(employee, 'avatar', None) else None,
            'designation': getattr(employee, 'designation', None),
            'phone_number': getattr(employee, 'phone_number', None),
            'personal_phone': getattr(employee, 'personal_phone', None),
            'email': getattr(user, 'email', None),
            'date_of_joining': getattr(employee, 'date_of_joining', None),
            'work_type': getattr(employee, 'work_type', None),
            'late': late_total,
            'early': early_total,
            'missed': missed_total,
            'leave_penalty_days': leave_penalty_days,
            'leave_penalty_requests': unpaid_leave_requests.count(),
            'total_penalty': late_total + early_total + missed_total + leave_penalty_days,
            'action': action,
            'status': review_status,
            'status_display': 'Approved' if review_status == 'Approved (Deduct)' else 'Cleared' if review_status == 'Waived' else 'Pending',
            'remarks': latest_comment,
            'total_deduction_days': float(summary.get('total_deduction_days', 0) or 0),
            'base_salary': base_salary,
            'penalty_amount': penalty_amount,
            'deduction_breakdown': deduction_breakdown,
            'amount_after_penalties': amount_after_penalties,
            'penalty_summary': summary,
            'attendance_details': attendance_rows,
            'late_request_count': late_requests.count(),
            'early_request_count': early_requests.count(),
            'pending_request_count': pending_count,
            'approved_request_count': approved_count,
            'rejected_request_count': rejected_count,
        }
        rows.append(row)

    totals['total_employees'] = len(all_employees_list)
    totals['late_arrivals'] = sum(row.get('late_request_count', 0) for row in rows)
    totals['early_leaves'] = sum(row.get('early_request_count', 0) for row in rows)
    totals['missed_punches'] = sum(row['missed'] for row in rows)
    totals['leave_penalties'] = sum(1 for row in rows if row['leave_penalty_days'] > 0)
    totals['leave_penalty_days'] = sum(row['leave_penalty_days'] for row in rows)
    totals['total_deduction_amount'] = sum(float(row.get('penalty_amount', 0) or 0) for row in rows)
    totals['pending_actions'] = sum(1 for row in rows if row['status'] == 'Pending')
    totals['approved_actions'] = sum(1 for row in rows if row['status'] == 'Approved (Deduct)')
    totals['waived_actions'] = sum(1 for row in rows if row['status'] == 'Waived')

    department_options = sorted({
        dept
        for row in rows
        for dept in (row.get('departments') or [row.get('dept')])
        if dept
    })
    employee_options = [
        {'id': row['id'], 'name': row['name'], 'empId': row.get('empId')}
        for row in rows
    ]

    total_count = len(all_employees_list)
    total_pages = (total_count + page_size - 1) // page_size
    page_rows = rows  # Already paginated above

    # Fetch PayrollSettings/AutomationRules for display (guard import if payroll app missing)
    try:
        from payroll.models import AutomationRule
    except Exception:
        AutomationRule = None

    payroll_settings = {}
    if AutomationRule:
        try:
            late_rule = AutomationRule.objects.filter(rule_type='late', is_active=True).first()
            if late_rule:
                payroll_settings['late'] = {
                    'amount': float(late_rule.deduction_amount or 0),
                    'grace_period': late_rule.max_occurrences if late_rule.set_occurrences else 0,
                    'type': late_rule.deduction_type,
                }
            
            early_rule = AutomationRule.objects.filter(rule_type='early', is_active=True).first()
            if early_rule:
                payroll_settings['early'] = {
                    'amount': float(early_rule.deduction_amount or 0),
                    'grace_period': early_rule.max_occurrences if early_rule.set_occurrences else 0,
                    'type': early_rule.deduction_type,
                }
            
            missed_rule = AutomationRule.objects.filter(rule_type='missed', is_active=True).first()
            if missed_rule:
                payroll_settings['missed'] = {
                    'amount': float(missed_rule.deduction_amount or 0),
                    'grace_period': missed_rule.max_occurrences if missed_rule.set_occurrences else 0,
                    'type': missed_rule.deduction_type,
                }
        except Exception:
            pass

    return Response({
        'success': True,
        'message': 'Attendance penalty review loaded successfully',
        'data': {
            'summary': totals,
            'employees': page_rows,
            'payroll_settings': payroll_settings,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_pages': total_pages,
            },
            'options': {
                'departments': department_options,
                'employees': employee_options,
            },
            'filters': {
                'month': month,
                'year': year,
                'status': request.query_params.get('status', 'All'),
                'department': request.query_params.get('department', 'All Departments'),
                'employee_id': request.query_params.get('employee_id') or request.query_params.get('employee') or 'All Employees',
                'search': request.query_params.get('search', ''),
            },
        },
    })


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def attendance_penalty_review_action(request):
    """Apply approve/waive action to pending late and early requests for one employee/month."""

    employee_id = request.data.get('employee_id')
    month = request.data.get('month')
    year = request.data.get('year')
    action = str(request.data.get('action') or '').strip().lower()
    comment = str(request.data.get('comment') or '').strip()

    if not employee_id or not month or not year or action not in ('approve', 'waive'):
        return Response(
            {'error': 'employee_id, month, year and action (approve|waive) are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        employee = Employee.objects.select_related('user').get(id=employee_id)
    except Employee.DoesNotExist:
        return Response({'error': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)

    user = getattr(employee, 'user', None)
    if not user:
        return Response({'error': 'Employee has no linked user account'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        month = int(month)
        year = int(year)
    except Exception:
        return Response({'error': 'month and year must be valid numbers'}, status=status.HTTP_400_BAD_REQUEST)

    new_status = 'approved' if action == 'approve' else 'rejected'
    review_label = 'Approved (Deduct)' if action == 'approve' else 'Waived'

    updated_late = 0
    updated_early = 0

    with transaction.atomic():
        late_qs = LateRequest.objects.select_for_update().filter(
            user=user,
            date__year=year,
            date__month=month,
            status='pending'
        )
        early_qs = EarlyRequest.objects.select_for_update().filter(
            user=user,
            date__year=year,
            date__month=month,
            status='pending'
        )

        for late_request in late_qs:
            late_request.status = new_status
            late_request.reviewed_by = request.user
            late_request.reviewed_at = timezone.now()
            late_request.admin_comment = comment or late_request.admin_comment or f'Penalty review {review_label.lower()}'
            late_request.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'admin_comment', 'updated_at'])
            updated_late += 1

        for early_request in early_qs:
            early_request.status = new_status
            early_request.reviewed_by = request.user
            early_request.reviewed_at = timezone.now()
            early_request.admin_comment = comment or early_request.admin_comment or f'Penalty review {review_label.lower()}'
            early_request.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'admin_comment', 'updated_at'])
            updated_early += 1

        # Optional: sync payroll deductions whenever review status changes.
        sync_payroll = str(request.data.get('sync_payroll', 'false')).lower() in ['1', 'true', 'yes']
        if sync_payroll:
            try:
                from payroll.services import PayrollCalculationService
                from payroll.models import Payroll, PayrollDeduction

                payrolls = Payroll.objects.filter(employee=employee.user, year=year, month=month)
                for p in payrolls:
                    pen = calculate_monthly_penalties(employee.user, year, month)
                    deduction_days = float(pen.get('summary', {}).get('total_deduction_days', 0) or 0)
                    if deduction_days <= 0:
                        PayrollDeduction.objects.filter(payroll=p, deduction_type='ATTENDANCE PENALTY').delete()
                        continue

                    base_salary = getattr(p, 'basic_salary', None) or PayrollCalculationService.get_employee_salary(employee)
                    try:
                        calc = PayrollCalculationService.calculate_attendance_penalty_deduction(employee.user, year, month, p.working_days or 0, base_salary)
                        items = calc.get('items', []) if isinstance(calc, dict) else []
                    except Exception:
                        items = []

                    # delete existing ATTENDANCE PENALTY rows and create new ones from items
                    PayrollDeduction.objects.filter(payroll=p, deduction_type='ATTENDANCE PENALTY').delete()
                    for item in items:
                        try:
                            PayrollDeduction.objects.create(
                                payroll=p,
                                deduction_type=item.get('deduction_type', 'ATTENDANCE PENALTY'),
                                amount=item.get('amount', 0),
                                description=item.get('description', '')
                            )
                        except Exception:
                            logger.exception('Failed to create PayrollDeduction item: %s', item)
            except Exception:
                logger.exception('Failed to sync payroll deductions for penalty review')

    return Response({
        'success': True,
        'message': f'Penalty review updated: {review_label}',
        'data': {
            'employee_id': employee.id,
            'month': month,
            'year': year,
            'action': action,
            'updated_late_requests': updated_late,
            'updated_early_requests': updated_early,
            'updated_total': updated_late + updated_early,
        }
    })

# Keep all your other existing ViewSets (AttendanceViewSet, HolidayViewSet, etc.)
# ... unchanged ...