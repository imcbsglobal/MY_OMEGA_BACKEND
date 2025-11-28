# HR/views.py - COMPLETE CLEANED VERSION
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
    EarlyRequest, AttendanceBreak
)
from .Serializers import (
    AttendanceSerializer, PunchInSerializer, PunchOutSerializer,
    AttendanceVerifySerializer, AttendanceUpdateStatusSerializer,
    HolidaySerializer, LeaveRequestSerializer,
    LeaveRequestCreateSerializer, LeaveRequestReviewSerializer,
    LateRequestSerializer, LateRequestCreateSerializer,
    EarlyRequestSerializer, EarlyRequestCreateSerializer,
    BreakSerializer
)
from User.models import AppUser


class AttendanceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Attendance records
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
        
        return queryset.order_by('-date', '-punch_in_time')
    
    @action(detail=False, methods=['post'])
    def punch_in(self, request):
        """Punch in action"""
        serializer = PunchInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        today = timezone.now().date()
        
        existing = Attendance.objects.filter(user=user, date=today).first()
        if existing and existing.punch_in_time:
            return Response(
                {'error': 'Already punched in today'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        attendance, created = Attendance.objects.get_or_create(
            user=user,
            date=today,
            defaults={
                'punch_in_time': timezone.now(),
                'punch_in_location': serializer.validated_data['location'],
                'punch_in_latitude': serializer.validated_data['latitude'],
                'punch_in_longitude': serializer.validated_data['longitude'],
                'note': serializer.validated_data.get('note', ''),
                'status': 'half',
            }
        )
        
        if not created:
            attendance.punch_in_time = timezone.now()
            attendance.punch_in_location = serializer.validated_data['location']
            attendance.punch_in_latitude = serializer.validated_data['latitude']
            attendance.punch_in_longitude = serializer.validated_data['longitude']
            attendance.status = 'half'
            if serializer.validated_data.get('note'):
                attendance.note = serializer.validated_data['note']
            attendance.save()
        
        response_serializer = AttendanceSerializer(attendance)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def punch_out(self, request):
        """Punch out action"""
        serializer = PunchOutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        today = timezone.now().date()
        
        try:
            attendance = Attendance.objects.get(user=user, date=today)
        except Attendance.DoesNotExist:
            return Response(
                {'error': 'No punch in record found for today'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not attendance.punch_in_time:
            return Response(
                {'error': 'You must punch in first'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if attendance.punch_out_time:
            return Response(
                {'error': 'Already punched out today'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        attendance.punch_out_time = timezone.now()
        attendance.punch_out_location = serializer.validated_data['location']
        attendance.punch_out_latitude = serializer.validated_data['latitude']
        attendance.punch_out_longitude = serializer.validated_data['longitude']
        if serializer.validated_data.get('note'):
            if attendance.note:
                attendance.note += '\n' + serializer.validated_data['note']
            else:
                attendance.note = serializer.validated_data['note']
        
        attendance.calculate_working_hours()
        
        if attendance.working_hours >= 7.5:
            attendance.status = 'full'
        elif attendance.working_hours >= 4:
            attendance.status = 'half'
        else:
            attendance.status = 'half'
        
        attendance.save()
        
        response_serializer = AttendanceSerializer(attendance)
        return Response(response_serializer.data)
    
    @action(detail=False, methods=['get'])
    def today_status(self, request):
        """Get today's attendance status"""
        user = request.user
        today = timezone.now().date()
        
        try:
            attendance = Attendance.objects.get(user=user, date=today)
            serializer = AttendanceSerializer(attendance)
            return Response(serializer.data)
        except Attendance.DoesNotExist:
            return Response({
                'message': 'No attendance record for today',
                'date': today
            }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def my_records(self, request):
        """Get only MY attendance records"""
        user = request.user
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        
        queryset = Attendance.objects.filter(user=user).select_related('user', 'verified_by')
        
        if month and year:
            queryset = queryset.filter(date__month=month, date__year=year)
        
        queryset = queryset.order_by('-date', '-punch_in_time')
        serializer = AttendanceSerializer(queryset, many=True)
        return Response(serializer.data)
    
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
            total=Sum('working_hours')
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
        """Verify attendance (Admin only)"""
        if not self._is_admin(request.user):
            return Response(
                {'error': 'Only admins can verify attendance'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        attendance = self.get_object()
        serializer = AttendanceVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        if attendance.punch_in_time and not attendance.punch_out_time:
            punch_in_date = attendance.punch_in_time.date()
            duty_end = attendance.user.duty_time_end if attendance.user.duty_time_end else time(18, 0)
            punch_out_datetime = timezone.make_aware(
                datetime.combine(punch_in_date, duty_end)
            )
            attendance.punch_out_time = punch_out_datetime
            attendance.punch_out_location = "Auto-generated (missing punch out)"
            auto_note = f"Punch out auto-generated by admin due to missing punch out"
            if attendance.admin_note:
                attendance.admin_note += f"\n[{timezone.now().strftime('%Y-%m-%d %H:%M')}] {auto_note}"
            else:
                attendance.admin_note = auto_note
        
        if attendance.punch_in_time and attendance.punch_out_time:
            attendance.calculate_working_hours()
            if attendance.working_hours >= 7.5 and attendance.status not in ['leave', 'wfh']:
                attendance.status = 'full'
            elif attendance.working_hours < 7.5 and attendance.working_hours >= 4 and attendance.status not in ['leave', 'wfh']:
                attendance.status = 'half'
        
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
        return Response(response_serializer.data)
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify attendance (Admin only) - returns {'attendance': <serialized>}"""
        if not self._is_admin(request.user):
            return Response({'error': 'Only admins can verify attendance'}, status=status.HTTP_403_FORBIDDEN)

        attendance = self.get_object()
        serializer = AttendanceVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # If lack of punch_out, auto-generate it (keeps prior logic)
        if attendance.punch_in_time and not attendance.punch_out_time:
            punch_in_date = attendance.punch_in_time.date()
            duty_end = getattr(attendance.user, 'duty_time_end', None) or time(18, 0)
            punch_out_datetime = timezone.make_aware(datetime.combine(punch_in_date, duty_end))
            attendance.punch_out_time = punch_out_datetime
            attendance.punch_out_location = "Auto-generated (missing punch out)"
            auto_note = f"Punch out auto-generated by admin due to missing punch out"
            if attendance.admin_note:
                attendance.admin_note += f"\n[{timezone.now().strftime('%Y-%m-%d %H:%M')}] {auto_note}"
            else:
                attendance.admin_note = auto_note

        if attendance.punch_in_time and attendance.punch_out_time:
            attendance.calculate_working_hours()
            if attendance.working_hours >= 7.5 and attendance.status not in ['leave', 'wfh']:
                attendance.status = 'full'
            elif 4 <= attendance.working_hours < 7.5 and attendance.status not in ['leave', 'wfh']:
                attendance.status = 'half'

        attendance.verification_status = 'verified'
        attendance.verified_by = request.user
        attendance.verified_at = timezone.now()

        admin_note = serializer.validated_data.get('admin_note', '')
        if admin_note:
            stamped = f"[{timezone.now().strftime('%Y-%m-%d %H:%M')}] {admin_note}"
            if attendance.admin_note:
                attendance.admin_note += f"\n{stamped}"
            else:
                attendance.admin_note = stamped

        # Save all changed fields explicitly to ensure DB write
        save_fields = []
        for f in ('punch_out_time', 'punch_out_location', 'working_hours', 'status', 'verification_status', 'verified_by', 'verified_at', 'admin_note'):
            if hasattr(attendance, f):
                save_fields.append(f)
        attendance.save(update_fields=save_fields if save_fields else None)

        response_serializer = AttendanceSerializer(attendance, context={'request': request})
        # Return wrapped attendance so front-end can consistently read res.data.attendance
        return Response({'message': 'Attendance verified', 'attendance': response_serializer.data}, status=status.HTTP_200_OK)

        
    @action(detail=False, methods=['post'])
    def mark_leave(self, request):
        """Mark a day as leave (Admin only) - returns {'attendance': <serialized>}"""
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
                'punch_in_time': None,
                'punch_out_time': None,
                'punch_in_location': None,
                'punch_out_location': None,
                'punch_in_latitude': None,
                'punch_in_longitude': None,
                'punch_out_latitude': None,
                'punch_out_longitude': None,
                'working_hours': 0,
                'verification_status': 'verified',
                'verified_by': request.user,
                'verified_at': timezone.now(),
            }
        )

        # Attach admin note (append if exists)
        if admin_note:
            stamped = f"[{timezone.now().strftime('%Y-%m-%d %H:%M')}] {admin_note}"
            if attendance.admin_note:
                attendance.admin_note += f"\n{stamped}"
            else:
                attendance.admin_note = stamped
            # ensure admin_note persisted
            attendance.save(update_fields=['admin_note'])

        response_serializer = AttendanceSerializer(attendance, context={'request': request})
        return Response({'message': 'Leave marked successfully', 'attendance': response_serializer.data},
                        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

        
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get attendance summary"""
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
            total=Sum('working_hours')
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
            'holidays': holidays,
            'sundays': sundays,
        })
    
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
                    
                    needs_save = False
                    if att.punch_in_time and att.punch_out_time:
                        old_hours = att.working_hours
                        old_status = att.status
                        
                        att.calculate_working_hours()
                        
                        if att.working_hours >= 7.5 and att.status not in ['leave', 'wfh']:
                            if att.status != 'full':
                                att.status = 'full'
                                needs_save = True
                        elif att.working_hours >= 4 and att.working_hours < 7.5 and att.status not in ['leave', 'wfh', 'full']:
                            if att.status != 'half':
                                att.status = 'half'
                                needs_save = True
                        
                        if needs_save or old_hours != att.working_hours:
                            att.save()
                    
                    if not att.punch_in_time:
                        attendance_array.append('not-marked')
                    elif att.punch_in_time and not att.punch_out_time:
                        if att.verification_status == 'verified':
                            attendance_array.append('half-verified')
                        else:
                            attendance_array.append('half')
                    else:
                        if att.verification_status == 'verified':
                            if att.status == 'full':
                                attendance_array.append('verified')
                            elif att.status == 'half':
                                attendance_array.append('half-verified')
                            elif att.status == 'leave':
                                attendance_array.append('verified-leave')
                            elif att.status == 'wfh':
                                attendance_array.append('verified')
                            else:
                                attendance_array.append('verified')
                        else:
                            if att.status == 'full':
                                attendance_array.append('full')
                            elif att.status == 'half':
                                attendance_array.append('half')
                            elif att.status == 'leave':
                                attendance_array.append('leave')
                            elif att.status == 'wfh':
                                attendance_array.append('full')
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
    
    # -------------------------
    # BREAK MANAGEMENT ACTIONS
    # -------------------------
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def active_break(self, request):
        """Get active break for current user"""
        user = request.user
        active = AttendanceBreak.objects.filter(
            user=user, 
            break_end__isnull=True
        ).order_by('-break_start').first()
        
        if not active:
            return Response({"has_active_break": False}, status=status.HTTP_200_OK)
        
        return Response({
            "has_active_break": True, 
            "break": BreakSerializer(active).data
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    @transaction.atomic
    def start_break(self, request):
        """Start a break"""
        user = request.user
        attendance = Attendance.objects.filter(
            user=user, 
            date=timezone.localdate()
        ).first()
        
        if not attendance or not attendance.punch_in_time:
            return Response(
                {"error": "Must punch in first"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if attendance.punch_out_time:
            return Response(
                {"error": "Already punched out"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if AttendanceBreak.objects.filter(user=user, break_end__isnull=True).exists():
            return Response(
                {"error": "Active break exists"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        br = AttendanceBreak.objects.create(
            user=user,
            attendance=attendance,
            break_start=timezone.now(),
            location=request.data.get('location', None),
            note=request.data.get('note', '')
        )
        
        return Response({
            "success": True, 
            "break": BreakSerializer(br).data
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    @transaction.atomic
    def end_break(self, request):
        """End active break"""
        user = request.user
        br = AttendanceBreak.objects.filter(
            user=user, 
            break_end__isnull=True
        ).order_by('-break_start').first()
        
        if not br:
            return Response(
                {"error": "No active break"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        br.break_end = timezone.now()
        if 'note' in request.data:
            br.note = (br.note or '') + '\n' + str(request.data.get('note'))
        if 'location' in request.data:
            br.location = request.data.get('location')
        
        br.calculate_duration()
        br.save(update_fields=['break_end', 'duration_minutes', 'duration_display', 'note', 'location'])
        
        return Response({
            "success": True, 
            "break": BreakSerializer(br).data
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def today_breaks(self, request):
        """Get today's breaks for current user"""
        user = request.user
        today = timezone.localdate()
        attendance = Attendance.objects.filter(user=user, date=today).first()
        
        if not attendance:
            return Response({
                "breaks": [], 
                "total_breaks": 0, 
                "total_break_minutes": 0, 
                "total_break_display": "0m"
            }, status=status.HTTP_200_OK)
        
        qs = AttendanceBreak.objects.filter(attendance=attendance).order_by('break_start')
        serializer = BreakSerializer(qs, many=True)
        total_minutes = sum([b.duration_minutes or 0 for b in qs])
        hours = total_minutes // 60
        mins = total_minutes % 60
        total_display = f"{hours}h {mins}m" if hours else f"{mins}m"
        
        return Response({
            "breaks": serializer.data,
            "total_breaks": qs.count(),
            "total_break_minutes": total_minutes,
            "total_break_display": total_display
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def break_summary(self, request):
        """Get break summary for a month"""
        month = int(request.query_params.get('month', timezone.localdate().month))
        year = int(request.query_params.get('year', timezone.localdate().year))
        
        if month < 1 or month > 12:
            return Response(
                {"error": "Invalid month"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        days_in_month = calendar.monthrange(year, month)[1]
        total_minutes = 0
        total_breaks = 0
        breaks_by_date = []
        
        for day in range(1, days_in_month + 1):
            d = timezone.datetime(year, month, day).date()
            atts = Attendance.objects.filter(date=d)
            day_qs = AttendanceBreak.objects.filter(
                attendance__in=atts
            ).order_by('break_start')
            count = day_qs.count()
            mins = sum([b.duration_minutes or 0 for b in day_qs])
            total_minutes += mins
            total_breaks += count
            
            breaks_by_date.append({
                "date": d,
                "count": count,
                "total_minutes": mins,
                "breaks": BreakSerializer(day_qs, many=True).data
            })
        
        avg = (total_minutes // total_breaks) if total_breaks else 0
        hours = total_minutes // 60
        mins_r = total_minutes % 60
        total_display = f"{hours}h {mins_r}m" if hours else f"{mins_r}m"
        avg_display = f"{avg//60}h {avg%60}m" if avg >= 60 else f"{avg}m"
        
        return Response({
            "total_breaks": total_breaks,
            "completed_breaks": total_breaks,
            "active_breaks": AttendanceBreak.objects.filter(break_end__isnull=True).count(),
            "total_break_minutes": total_minutes,
            "total_break_display": total_display,
            "average_break_minutes": avg,
            "average_break_display": avg_display,
            "breaks_by_date": breaks_by_date
        }, status=status.HTTP_200_OK)


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
        serializer.save(user=self.request.user)

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


# -------------------------
# Reverse Geocoding Functions
# -------------------------
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




@action(detail=True, methods=['patch'])
def update_status(self, request, pk=None):
    """Update attendance status (Admin only) - returns {'attendance': <serialized>}"""
    if not self._is_admin(request.user):
        return Response({'error': 'Only admins can update attendance status'}, status=status.HTTP_403_FORBIDDEN)

    attendance = self.get_object()
    serializer = AttendanceUpdateStatusSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    old_status = attendance.status
    new_status = serializer.validated_data['status']
    admin_note = serializer.validated_data.get('admin_note', '')

    # Handle change-to-leave: clear punch times and hours
    if new_status == 'leave':
        attendance.punch_in_time = None
        attendance.punch_out_time = None
        attendance.punch_in_location = None
        attendance.punch_out_location = None
        attendance.punch_in_latitude = None
        attendance.punch_in_longitude = None
        attendance.punch_out_latitude = None
        attendance.punch_out_longitude = None
        attendance.working_hours = 0
        auto_note = f"Status changed to leave from {old_status}"
        if attendance.admin_note:
            attendance.admin_note += f"\n[{timezone.now().strftime('%Y-%m-%d %H:%M')}] {auto_note}"
        else:
            attendance.admin_note = auto_note

    # If setting to full and there's no punch_out, auto-generate a punch_out using duty_end
    elif new_status == 'full' and attendance.punch_in_time and not attendance.punch_out_time:
        punch_in_date = attendance.punch_in_time.date()
        duty_end = getattr(attendance.user, 'duty_time_end', None) or time(18, 0)
        punch_out_datetime = timezone.make_aware(datetime.combine(punch_in_date, duty_end))
        attendance.punch_out_time = punch_out_datetime
        attendance.punch_out_location = "Auto-generated by admin (status change to full day)"
        attendance.calculate_working_hours()
        auto_note = f"Punch out auto-generated when changing status to full day (was {old_status})"
        if attendance.admin_note:
            attendance.admin_note += f"\n[{timezone.now().strftime('%Y-%m-%d %H:%M')}] {auto_note}"
        else:
            attendance.admin_note = auto_note

    # If setting to half and there's no punch_out, auto-generate 4hrs from punch_in
    elif new_status == 'half' and attendance.punch_in_time and not attendance.punch_out_time:
        punch_in_date = attendance.punch_in_time.date()
        punch_in_dt = attendance.punch_in_time
        # Use timezone-aware addition
        punch_out_dt = punch_in_dt + timezone.timedelta(hours=4)
        attendance.punch_out_time = punch_out_dt
        attendance.punch_out_location = "Auto-generated by admin (status change to half day)"
        attendance.calculate_working_hours()
        auto_note = f"Punch out auto-generated when changing status to half day (was {old_status})"
        if attendance.admin_note:
            attendance.admin_note += f"\n[{timezone.now().strftime('%Y-%m-%d %H:%M')}] {auto_note}"
        else:
            attendance.admin_note = auto_note

    # Update the status
    attendance.status = new_status

    # Append admin note if provided
    if admin_note:
        stamped = f"[{timezone.now().strftime('%Y-%m-%d %H:%M')}] {admin_note}"
        if attendance.admin_note:
            attendance.admin_note += f"\n{stamped}"
        else:
            attendance.admin_note = stamped

    # Save changed fields explicitly
    save_fields = []
    for f in ('status', 'punch_out_time', 'punch_out_location', 'working_hours', 'admin_note'):
        if hasattr(attendance, f):
            save_fields.append(f)
    attendance.save(update_fields=save_fields if save_fields else None)

    response_serializer = AttendanceSerializer(attendance, context={'request': request})
    return Response({'message': 'Status updated', 'attendance': response_serializer.data}, status=status.HTTP_200_OK)

