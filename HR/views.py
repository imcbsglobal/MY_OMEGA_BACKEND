# HR/views.py - Updated with new Punch In/Out Break System
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Sum
from django.db import transaction
from django.utils import timezone
from datetime import datetime, time
import calendar
import requests

from .models import (
    Attendance, Holiday, LeaveRequest, LateRequest,
    EarlyRequest, PunchRecord
)
from .Serializers import (
    AttendanceSerializer, PunchInSerializer, PunchOutSerializer,
    AttendanceVerifySerializer, AttendanceUpdateStatusSerializer,
    HolidaySerializer, LeaveRequestSerializer,
    LeaveRequestCreateSerializer, LeaveRequestReviewSerializer,
    LateRequestSerializer, LateRequestCreateSerializer,
    EarlyRequestSerializer, EarlyRequestCreateSerializer,
    PunchRecordSerializer
)
from User.models import AppUser


class AttendanceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Attendance records with new punch in/out system
    """
    queryset = Attendance.objects.all().select_related('user', 'verified_by')
    serializer_class = AttendanceSerializer
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
        queryset = Attendance.objects.select_related('user', 'verified_by')

        is_admin = self._is_admin(user)
        if not is_admin:
            queryset = queryset.filter(user=user)

        user_id = self.request.query_params.get('user_id')
        if user_id and is_admin:
            queryset = queryset.filter(user_id=user_id)

        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')
        if from_date:
            queryset = queryset.filter(date__gte=from_date)
        if to_date:
            queryset = queryset.filter(date__lte=to_date)

        month = self.request.query_params.get('month')
        year = self.request.query_params.get('year')
        if month and year:
            queryset = queryset.filter(date__month=month, date__year=year)

        att_status = self.request.query_params.get('status')
        if att_status:
            queryset = queryset.filter(status=att_status)

        verification_status = self.request.query_params.get('verification_status')
        if verification_status:
            queryset = queryset.filter(verification_status=verification_status)

        return queryset.order_by('-date', '-first_punch_in_time')

    @action(detail=False, methods=['post'])
    @transaction.atomic
    def punch_in(self, request):
        """
        Punch in action - can be used multiple times in a day
        First punch in = Start of work day
        Subsequent punch ins = Return from break
        """
        serializer = PunchInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        today = timezone.now().date()

        # Get or create attendance record for today
        attendance, created = Attendance.objects.get_or_create(
            user=user,
            date=today,
            defaults={
                'status': 'half',
                'is_currently_on_break': False
            }
        )

        # Check if user is currently on break (last punch was OUT)
        last_punch = attendance.punch_records.order_by('-punch_time').first()

        if last_punch and last_punch.punch_type == 'in':
            return Response(
                {'error': 'You are already punched in. Please punch out before punching in again.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create new punch in record
        punch_record = PunchRecord.objects.create(
            attendance=attendance,
            punch_type='in',
            punch_time=timezone.now(),
            location=serializer.validated_data['location'],
            latitude=serializer.validated_data['latitude'],
            longitude=serializer.validated_data['longitude'],
            note=serializer.validated_data.get('note', '')
        )

        # Update attendance record
        attendance.is_currently_on_break = False

        # If this is the first punch in, update first_punch_in fields
        if not attendance.first_punch_in_time:
            attendance.first_punch_in_time = punch_record.punch_time
            attendance.first_punch_in_location = punch_record.location
            attendance.first_punch_in_latitude = punch_record.latitude
            attendance.first_punch_in_longitude = punch_record.longitude

        attendance.save()

        # Get punch records for response
        punch_records = attendance.punch_records.all().order_by('punch_time')

        response_data = AttendanceSerializer(attendance).data
        response_data['punch_records'] = PunchRecordSerializer(punch_records, many=True).data
        response_data['message'] = 'Punched in successfully' if created or not last_punch else 'Returned from break successfully'

        return Response(response_data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    @transaction.atomic
    def punch_out(self, request):
        """
        Punch out action - can be used multiple times in a day
        Intermediate punch outs = Going on break
        Final punch out = End of work day
        """
        serializer = PunchOutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        today = timezone.now().date()

        try:
            attendance = Attendance.objects.get(user=user, date=today)
        except Attendance.DoesNotExist:
            return Response(
                {'error': 'No punch in record found for today. Please punch in first.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user has punched in
        if not attendance.first_punch_in_time:
            return Response(
                {'error': 'You must punch in first before punching out'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if last punch was OUT
        last_punch = attendance.punch_records.order_by('-punch_time').first()
        if last_punch and last_punch.punch_type == 'out':
            return Response(
                {'error': 'You are already punched out. Please punch in before punching out again.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create new punch out record
        punch_record = PunchRecord.objects.create(
            attendance=attendance,
            punch_type='out',
            punch_time=timezone.now(),
            location=serializer.validated_data['location'],
            latitude=serializer.validated_data['latitude'],
            longitude=serializer.validated_data['longitude'],
            note=serializer.validated_data.get('note', '')
        )

        # Update last punch out
        attendance.last_punch_out_time = punch_record.punch_time
        attendance.last_punch_out_location = punch_record.location
        attendance.last_punch_out_latitude = punch_record.latitude
        attendance.last_punch_out_longitude = punch_record.longitude
        attendance.is_currently_on_break = True

        # Calculate working hours and break hours
        attendance.calculate_times()
        attendance.update_status()
        attendance.save()

        # Get punch records for response
        punch_records = attendance.punch_records.all().order_by('punch_time')

        response_data = AttendanceSerializer(attendance).data
        response_data['punch_records'] = PunchRecordSerializer(punch_records, many=True).data
        response_data['message'] = 'Punched out successfully'
        response_data['total_working_hours'] = float(attendance.total_working_hours)
        response_data['total_break_hours'] = float(attendance.total_break_hours)

        return Response(response_data)

    @action(detail=False, methods=['get'])
    def today_status(self, request):
        """Get today's attendance status with punch records"""
        user = request.user
        today = timezone.now().date()

        try:
            attendance = Attendance.objects.get(user=user, date=today)
            punch_records = attendance.punch_records.all().order_by('punch_time')

            response_data = AttendanceSerializer(attendance).data
            response_data['punch_records'] = PunchRecordSerializer(punch_records, many=True).data
            response_data['can_punch_in'] = not punch_records.exists() or punch_records.last().punch_type == 'out'
            response_data['can_punch_out'] = punch_records.exists() and punch_records.last().punch_type == 'in'

            return Response(response_data)
        except Attendance.DoesNotExist:
            return Response({
                'message': 'No attendance record for today',
                'date': today,
                'can_punch_in': True,
                'can_punch_out': False
            }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'])
    def my_records(self, request):
        """Get only MY attendance records with punch records"""
        user = request.user
        month = request.query_params.get('month')
        year = request.query_params.get('year')

        queryset = Attendance.objects.filter(user=user).select_related('user', 'verified_by')

        if month and year:
            queryset = queryset.filter(date__month=month, date__year=year)

        queryset = queryset.order_by('-date', '-first_punch_in_time')

        # Include punch records for each attendance
        result = []
        for attendance in queryset:
            att_data = AttendanceSerializer(attendance).data
            punch_records = attendance.punch_records.all().order_by('punch_time')
            att_data['punch_records'] = PunchRecordSerializer(punch_records, many=True).data
            result.append(att_data)

        return Response(result)

    @action(detail=False, methods=['get'])
    def my_summary(self, request):
        """Get only MY attendance summary"""
        user = request.user
        month = int(request.query_params.get('month', timezone.now().month))
        year = int(request.query_params.get('year', timezone.now().year))

        attendances = Attendance.objects.filter(
            user=user,
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

    def _count_sundays(self, year, month):
        """Count the number of Sundays in a given month"""
        days_in_month = calendar.monthrange(year, month)[1]
        sundays = 0
        for day in range(1, days_in_month + 1):
            if datetime(year, month, day).weekday() == 6:
                sundays += 1
        return sundays

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify attendance (Admin only) - recalculates times from punch records"""
        if not self._is_admin(request.user):
            return Response(
                {'error': 'Only admins can verify attendance'},
                status=status.HTTP_403_FORBIDDEN
            )

        attendance = self.get_object()
        serializer = AttendanceVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Recalculate times from punch records
        attendance.calculate_times()
        # attendance.update_status()

        # Verify
        attendance.verification_status = 'verified'
        attendance.verified_by = request.user
        attendance.verified_at = timezone.now()

        admin_note = serializer.validated_data.get('admin_note', '')
        if admin_note:
            if attendance.admin_note:
                attendance.admin_note += f"\n[{timezone.now().strftime('%Y-%m-%d %H:%M')}] {admin_note}"
            else:
                attendance.admin_note = admin_note

        attendance.save()

        response_serializer = AttendanceSerializer(attendance)
        return Response({'message': 'Attendance verified', 'attendance': response_serializer.data}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def mark_leave(self, request):
        """Mark a day as leave (Admin only)"""
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

        users = AppUser.objects.all().order_by('name')
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
        users = AppUser.objects.all().order_by('name')

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

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update attendance status (Admin only)"""
        if not self._is_admin(request.user):
            return Response({'error': 'Only admins can update attendance status'}, status=status.HTTP_403_FORBIDDEN)

        attendance = self.get_object()
        serializer = AttendanceUpdateStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        old_status = attendance.status
        new_status = serializer.validated_data['status']
        admin_note = serializer.validated_data.get('admin_note', '')

        # Handle leave status
        if new_status == 'leave':
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

            auto_note = f"Status changed to leave from {old_status}"
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
        return Response({'message': 'Status updated', 'attendance': response_serializer.data}, status=status.HTTP_200_OK)


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
    """ViewSet for managing Late Requests"""
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

            try:
                serializer.is_valid(raise_exception=True)
                logger.info(f"Serializer validation passed")
            except Exception as e:
                logger.error(f"Serializer validation failed: {e}")
                logger.error(f"Validation errors: {serializer.errors}")
                raise

            logger.info(f"Performing create...")
            try:
                self.perform_create(serializer)
                logger.info(f"Perform create completed")
            except Exception as e:
                logger.error(f"Perform create failed: {e}")
                import traceback
                logger.error(traceback.format_exc())
                raise

            logger.info(f"Fetching created instance...")
            try:
                instance = LateRequest.objects.get(id=serializer.instance.id)
                response_serializer = LateRequestSerializer(instance)
                logger.info(f"Instance serialized successfully")
            except Exception as e:
                logger.error(f"Failed to serialize response: {e}")
                import traceback
                logger.error(traceback.format_exc())
                raise

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
        qs = LateRequest.objects.filter(user=request.user).order_by('-created_at')
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
    """ViewSet for managing Early Requests"""
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

    @action(detail=False, methods=['get'], url_path='my-requests')
    def my_requests(self, request):
        qs = EarlyRequest.objects.filter(user=request.user).order_by('-created_at')
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
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reverse_geocode(request):
    """Reverse geocode coordinates to address"""
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

            address_parts = []
            if data.get('locality'):
                address_parts.append(data['locality'])
            if data.get('city'):
                address_parts.append(data['city'])
            if data.get('principalSubdivision'):
                address_parts.append(data['principalSubdivision'])
            if data.get('countryName'):
                address_parts.append(data['countryName'])

            address = ', '.join(address_parts) if address_parts else f'Lat: {latitude}, Lon: {longitude}'

            return Response({
                'address': address,
                'latitude': latitude,
                'longitude': longitude,
                'details': data
            })

        return Response({
            'address': f'Lat: {latitude}, Lon: {longitude}',
            'latitude': latitude,
            'longitude': longitude
        })

    except requests.exceptions.RequestException as e:
        return Response({
            'address': f'Lat: {latitude}, Lon: {longitude}',
            'latitude': latitude,
            'longitude': longitude,
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

    users = AppUser.objects.all().order_by('name')

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
