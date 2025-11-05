from django.shortcuts import render

# Create your views here.
# HR/views.py - Complete Attendance Views
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Sum
from django.utils import timezone
from datetime import datetime
import calendar

from .models import Attendance, Holiday, LeaveRequest

# FIXED: Changed from .serializers to .Serializer (matching your filename)
from .Serializers import (
    AttendanceSerializer, PunchInSerializer, PunchOutSerializer,
    AttendanceVerifySerializer, AttendanceUpdateStatusSerializer,
    HolidaySerializer, LeaveRequestSerializer,
    LeaveRequestCreateSerializer, LeaveRequestReviewSerializer,
)
from User.models import AppUser


class AttendanceViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Attendance records"""
    queryset = Attendance.objects.all().select_related('user', 'verified_by')
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset based on permissions and query params"""
        user = self.request.user
        queryset = Attendance.objects.select_related('user', 'verified_by')
        
        # Admin can see all, users see only their own
        is_admin = user.user_level in ('Super Admin', 'Admin') or user.is_staff or user.is_superuser
        if not is_admin:
            queryset = queryset.filter(user=user)
        
        # Filter by user_id (for admin)
        user_id = self.request.query_params.get('user_id')
        if user_id and is_admin:
            queryset = queryset.filter(user_id=user_id)
        
        # Filter by date range
        from_date = self.request.query_params.get('from_date')
        to_date = self.request.query_params.get('to_date')
        if from_date:
            queryset = queryset.filter(date__gte=from_date)
        if to_date:
            queryset = queryset.filter(date__lte=to_date)
        
        # Filter by month and year
        month = self.request.query_params.get('month')
        year = self.request.query_params.get('year')
        if month and year:
            queryset = queryset.filter(date__month=month, date__year=year)
        
        # Filter by status
        att_status = self.request.query_params.get('status')
        if att_status:
            queryset = queryset.filter(status=att_status)
        
        # Filter by verification status
        verification_status = self.request.query_params.get('verification_status')
        if verification_status:
            queryset = queryset.filter(verification_status=verification_status)
        
        return queryset.order_by('-date', '-punch_in_time')
    
    @action(detail=False, methods=['post'])
    def punch_in(self, request):
        """Punch in action - URL: /api/hr/attendance/punch_in/"""
        serializer = PunchInSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        today = timezone.now().date()
        
        # Check if already punched in today
        existing = Attendance.objects.filter(user=user, date=today).first()
        if existing and existing.punch_in_time:
            return Response(
                {'error': 'Already punched in today'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create or update attendance
        attendance, created = Attendance.objects.get_or_create(
            user=user,
            date=today,
            defaults={
                'punch_in_time': timezone.now(),
                'punch_in_location': serializer.validated_data['location'],
                'punch_in_latitude': serializer.validated_data['latitude'],
                'punch_in_longitude': serializer.validated_data['longitude'],
                'note': serializer.validated_data.get('note', ''),
            }
        )
        
        if not created:
            attendance.punch_in_time = timezone.now()
            attendance.punch_in_location = serializer.validated_data['location']
            attendance.punch_in_latitude = serializer.validated_data['latitude']
            attendance.punch_in_longitude = serializer.validated_data['longitude']
            if serializer.validated_data.get('note'):
                attendance.note = serializer.validated_data['note']
            attendance.save()
        
        response_serializer = AttendanceSerializer(attendance)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'])
    def punch_out(self, request):
        """Punch out action - URL: /api/hr/attendance/punch_out/"""
        serializer = PunchOutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        today = timezone.now().date()
        
        # Get today's attendance
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
        
        # Update attendance
        attendance.punch_out_time = timezone.now()
        attendance.punch_out_location = serializer.validated_data['location']
        attendance.punch_out_latitude = serializer.validated_data['latitude']
        attendance.punch_out_longitude = serializer.validated_data['longitude']
        if serializer.validated_data.get('note'):
            if attendance.note:
                attendance.note += '\n' + serializer.validated_data['note']
            else:
                attendance.note = serializer.validated_data['note']
        
        # Calculate working hours
        attendance.calculate_working_hours()
        
        # Auto-determine status based on working hours
        if attendance.working_hours >= 8:
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
        """Get today's attendance status - URL: /api/hr/attendance/today_status/"""
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
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify attendance (Admin only) - URL: /api/hr/attendance/{id}/verify/"""
        if not (request.user.user_level in ('Super Admin', 'Admin') or 
                request.user.is_staff or request.user.is_superuser):
            return Response(
                {'error': 'Only admins can verify attendance'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        attendance = self.get_object()
        serializer = AttendanceVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        attendance.verification_status = 'verified'
        attendance.verified_by = request.user
        attendance.verified_at = timezone.now()
        if serializer.validated_data.get('admin_note'):
            attendance.admin_note = serializer.validated_data['admin_note']
        attendance.save()
        
        response_serializer = AttendanceSerializer(attendance)
        return Response(response_serializer.data)
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update attendance status (Admin only) - URL: /api/hr/attendance/{id}/update_status/"""
        if not (request.user.user_level in ('Super Admin', 'Admin') or 
                request.user.is_staff or request.user.is_superuser):
            return Response(
                {'error': 'Only admins can update attendance status'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        attendance = self.get_object()
        serializer = AttendanceUpdateStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        attendance.status = serializer.validated_data['status']
        if serializer.validated_data.get('admin_note'):
            attendance.admin_note = serializer.validated_data['admin_note']
        attendance.save()
        
        response_serializer = AttendanceSerializer(attendance)
        return Response(response_serializer.data)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get attendance summary - URL: /api/hr/attendance/summary/"""
        user_id = request.query_params.get('user_id', request.user.id)
        month = int(request.query_params.get('month', timezone.now().month))
        year = int(request.query_params.get('year', timezone.now().year))
        
        # Check permission
        is_admin = request.user.user_level in ('Super Admin', 'Admin') or \
                   request.user.is_staff or request.user.is_superuser
        
        if not is_admin and int(user_id) != request.user.id:
            return Response(
                {'error': 'You can only view your own summary'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            user = AppUser.objects.get(id=user_id)
        except AppUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get attendance records
        attendances = Attendance.objects.filter(
            user_id=user_id,
            date__month=month,
            date__year=year
        )
        
        # Get holidays
        holidays = Holiday.objects.filter(
            date__month=month,
            date__year=year,
            is_active=True
        ).count()
        
        # Calculate statistics
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
        not_marked = days_in_month - marked_days - holidays
        
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
        })
    
    @action(detail=False, methods=['get'])
    def monthly_grid(self, request):
        """Get monthly attendance grid (Admin only) - URL: /api/hr/attendance/monthly_grid/"""
        if not (request.user.user_level in ('Super Admin', 'Admin') or 
                request.user.is_staff or request.user.is_superuser):
            return Response(
                {'error': 'Only admins can view attendance grid'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        month = int(request.query_params.get('month', timezone.now().month))
        year = int(request.query_params.get('year', timezone.now().year))
        
        days_in_month = calendar.monthrange(year, month)[1]
        
        # Get all active users
        users = AppUser.objects.filter(is_active=True).order_by('name')
        
        # Get all holidays
        holidays = set(Holiday.objects.filter(
            date__month=month,
            date__year=year,
            is_active=True
        ).values_list('date', flat=True))
        
        result = []
        
        for user in users:
            # Get attendance for this user
            attendances = Attendance.objects.filter(
                user=user,
                date__month=month,
                date__year=year
            )
            
            # Create attendance dict by day
            attendance_dict = {att.date.day: att for att in attendances}
            
            # Build attendance array
            attendance_array = []
            for day in range(1, days_in_month + 1):
                current_date = datetime(year, month, day).date()
                
                if current_date in holidays:
                    attendance_array.append('holiday')
                elif day in attendance_dict:
                    att = attendance_dict[day]
                    if att.verification_status == 'verified':
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


class HolidayViewSet(viewsets.ModelViewSet):
    """ViewSet for managing Holidays"""
    queryset = Holiday.objects.all().order_by('-date')
    serializer_class = HolidaySerializer
    permission_classes = [IsAuthenticated]
    
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
    
    def get_queryset(self):
        user = self.request.user
        queryset = LeaveRequest.objects.select_related('user', 'reviewed_by')
        
        is_admin = user.user_level in ('Super Admin', 'Admin') or user.is_staff or user.is_superuser
        if not is_admin:
            queryset = queryset.filter(user=user)
        
        req_status = self.request.query_params.get('status')
        if req_status:
            queryset = queryset.filter(status=req_status)
        
        return queryset.order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return LeaveRequestCreateSerializer
        return LeaveRequestSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        """Review leave request (Admin only)"""
        if not (request.user.user_level in ('Super Admin', 'Admin') or 
                request.user.is_staff or request.user.is_superuser):
            return Response(
                {'error': 'Only admins can review leave requests'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        leave_request = self.get_object()
        serializer = LeaveRequestReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        leave_request.status = serializer.validated_data['status']
        leave_request.admin_comment = serializer.validated_data.get('admin_comment', '')
        leave_request.reviewed_by = request.user
        leave_request.reviewed_at = timezone.now()
        leave_request.save()
        
        response_serializer = LeaveRequestSerializer(leave_request)
        return Response(response_serializer.data)