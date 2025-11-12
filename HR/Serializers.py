# HR/serializers.py - Complete Attendance Serializers
from rest_framework import serializers
from django.utils import timezone
from .models import Attendance, Holiday, LeaveRequest
from User.models import AppUser


class AttendanceSerializer(serializers.ModelSerializer):
    """
    Complete serializer for Attendance records
    Used for GET requests and responses
    """
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.name', read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    verification_status_display = serializers.CharField(source='get_verification_status_display', read_only=True)
    
    class Meta:
        model = Attendance
        fields = [
            'id',
            'user',
            'user_name',
            'user_email',
            'date',
            'punch_in_time',
            'punch_out_time',
            'punch_in_location',
            'punch_out_location',
            'punch_in_latitude',
            'punch_in_longitude',
            'punch_out_latitude',
            'punch_out_longitude',
            'status',
            'status_display',
            'verification_status',
            'verification_status_display',
            'working_hours',
            'note',
            'admin_note',
            'verified_by',
            'verified_by_name',
            'verified_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 
            'working_hours', 
            'verified_by', 
            'verified_at', 
            'created_at', 
            'updated_at'
        ]


class PunchInSerializer(serializers.Serializer):
    """
    Serializer for punch in action
    Validates location and coordinates
    """
    location = serializers.CharField(
        required=True,
        help_text='Location name/address'
    )
    latitude = serializers.DecimalField(
        max_digits=10, 
        decimal_places=7, 
        required=True,
        help_text='GPS latitude'
    )
    longitude = serializers.DecimalField(
        max_digits=10, 
        decimal_places=7, 
        required=True,
        help_text='GPS longitude'
    )
    note = serializers.CharField(
        required=False, 
        allow_blank=True,
        help_text='Optional note for punch in'
    )


class PunchOutSerializer(serializers.Serializer):
    """
    Serializer for punch out action
    Validates location and coordinates
    """
    location = serializers.CharField(
        required=True,
        help_text='Location name/address'
    )
    latitude = serializers.DecimalField(
        max_digits=10, 
        decimal_places=7, 
        required=True,
        help_text='GPS latitude'
    )
    longitude = serializers.DecimalField(
        max_digits=10, 
        decimal_places=7, 
        required=True,
        help_text='GPS longitude'
    )
    note = serializers.CharField(
        required=False, 
        allow_blank=True,
        help_text='Optional note for punch out'
    )


class AttendanceVerifySerializer(serializers.Serializer):
    """
    Serializer for verifying attendance by admin
    """
    admin_note = serializers.CharField(
        required=False, 
        allow_blank=True,
        help_text='Admin note for verification'
    )


class AttendanceUpdateStatusSerializer(serializers.Serializer):
    """
    Serializer for updating attendance status by admin
    """
    status = serializers.ChoiceField(
        choices=Attendance.STATUS_CHOICES,
        help_text='New attendance status'
    )
    admin_note = serializers.CharField(
        required=False, 
        allow_blank=True,
        help_text='Admin note for status change'
    )


class AttendanceSummarySerializer(serializers.Serializer):
    """
    Serializer for monthly attendance summary
    Returns aggregated statistics
    """
    user_id = serializers.IntegerField()
    user_name = serializers.CharField()
    user_email = serializers.CharField()
    month = serializers.IntegerField()
    year = serializers.IntegerField()
    total_days = serializers.IntegerField()
    full_days_unverified = serializers.IntegerField()
    verified_full_days = serializers.IntegerField()
    half_days_unverified = serializers.IntegerField()
    verified_half_days = serializers.IntegerField()
    leaves = serializers.IntegerField()
    not_marked = serializers.IntegerField()
    total_working_hours = serializers.DecimalField(max_digits=10, decimal_places=2)
    holidays = serializers.IntegerField()


class MonthlyGridSerializer(serializers.Serializer):
    """
    Serializer for monthly attendance grid
    Returns attendance data for each day of the month
    """
    user_id = serializers.IntegerField()
    user_name = serializers.CharField()
    user_email = serializers.CharField()
    duty_start = serializers.CharField()
    duty_end = serializers.CharField()
    attendance = serializers.ListField(
        child=serializers.CharField(),
        help_text='Array of attendance status for each day'
    )


class HolidaySerializer(serializers.ModelSerializer):
    """
    Serializer for Holiday model
    Used for creating and managing holidays
    """
    class Meta:
        model = Holiday
        fields = [
            'id',
            'name',
            'date',
            'description',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_date(self, value):
        """Ensure holiday date is not in the past"""
        if value < timezone.now().date():
            raise serializers.ValidationError("Holiday date cannot be in the past")
        return value


class LeaveRequestSerializer(serializers.ModelSerializer):
    """
    Complete serializer for Leave Request
    Includes computed fields and related data
    """
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.name', read_only=True, allow_null=True)
    leave_type_display = serializers.CharField(source='get_leave_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    total_days = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = LeaveRequest
        fields = [
            'id',
            'user',
            'user_name',
            'user_email',
            'leave_type',
            'leave_type_display',
            'from_date',
            'to_date',
            'total_days',
            'reason',
            'status',
            'status_display',
            'reviewed_by',
            'reviewed_by_name',
            'reviewed_at',
            'admin_comment',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 
            'user', 
            'reviewed_by', 
            'reviewed_at', 
            'created_at', 
            'updated_at'
        ]
    
    def validate(self, data):
        """
        Validate leave request dates
        Ensure from_date is before to_date
        """
        if 'from_date' in data and 'to_date' in data:
            if data['from_date'] > data['to_date']:
                raise serializers.ValidationError({
                    'to_date': 'To date must be after or equal to from date'
                })
        return data


class LeaveRequestCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating leave requests
    Used when employees submit leave requests
    """
    class Meta:
        model = LeaveRequest
        fields = [
            'leave_type',
            'from_date',
            'to_date',
            'reason'
        ]
    
    def validate(self, data):
        """Validate leave dates"""
        if data['from_date'] > data['to_date']:
            raise serializers.ValidationError({
                'to_date': 'To date must be after or equal to from date'
            })
        
        # Check if from_date is not in the past
        if data['from_date'] < timezone.now().date():
            raise serializers.ValidationError({
                'from_date': 'Leave cannot be requested for past dates'
            })
        
        return data


# Serializers.py (add this if missing)
from rest_framework import serializers

class LeaveRequestReviewSerializer(serializers.Serializer):
    """
    Validate admin review / override payload:
      - status: required, must be 'approved' or 'rejected'
      - admin_comment: optional string
    """
    status = serializers.ChoiceField(choices=['approved', 'rejected'])
    admin_comment = serializers.CharField(required=False, allow_blank=True, allow_null=True)



class AttendanceCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for manually creating attendance records (Admin only)
    Useful for correcting missing records
    """
    class Meta:
        model = Attendance
        fields = [
            'user',
            'date',
            'punch_in_time',
            'punch_out_time',
            'punch_in_location',
            'punch_out_location',
            'punch_in_latitude',
            'punch_in_longitude',
            'punch_out_latitude',
            'punch_out_longitude',
            'status',
            'note',
            'admin_note',
        ]
    
    def validate(self, data):
        """Validate attendance data"""
        # Check for duplicate attendance
        if Attendance.objects.filter(
            user=data['user'], 
            date=data['date']
        ).exists():
            raise serializers.ValidationError(
                'Attendance record already exists for this user on this date'
            )
        
        # Validate punch out is after punch in
        if data.get('punch_in_time') and data.get('punch_out_time'):
            if data['punch_out_time'] <= data['punch_in_time']:
                raise serializers.ValidationError({
                    'punch_out_time': 'Punch out time must be after punch in time'
                })
        
        return data


class AttendanceUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating attendance records
    Used by admins to modify existing records
    """
    class Meta:
        model = Attendance
        fields = [
            'punch_in_time',
            'punch_out_time',
            'punch_in_location',
            'punch_out_location',
            'punch_in_latitude',
            'punch_in_longitude',
            'punch_out_latitude',
            'punch_out_longitude',
            'status',
            'verification_status',
            'note',
            'admin_note',
        ]
    
    def validate(self, data):
        """Validate updated attendance data"""
        instance = self.instance
        
        # Get punch times (from data or instance)
        punch_in = data.get('punch_in_time', instance.punch_in_time)
        punch_out = data.get('punch_out_time', instance.punch_out_time)
        
        # Validate punch out is after punch in
        if punch_in and punch_out:
            if punch_out <= punch_in:
                raise serializers.ValidationError({
                    'punch_out_time': 'Punch out time must be after punch in time'
                })
        
        return data


class UserAttendanceStatsSerializer(serializers.Serializer):
    """
    Serializer for user attendance statistics
    Returns overall attendance stats for a user
    """
    user_id = serializers.IntegerField()
    user_name = serializers.CharField()
    total_attendance_days = serializers.IntegerField()
    total_full_days = serializers.IntegerField()
    total_half_days = serializers.IntegerField()
    total_leaves = serializers.IntegerField()
    total_working_hours = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_daily_hours = serializers.DecimalField(max_digits=5, decimal_places=2)
    verified_days = serializers.IntegerField()
    unverified_days = serializers.IntegerField()












# ============================================================
# SERIALIZERS.PY - Add/Update LeaveRequest Serializers
# ============================================================

from rest_framework import serializers
from django.utils import timezone
from .models import LeaveRequest
from User.models import AppUser


class LeaveRequestSerializer(serializers.ModelSerializer):
    """
    Complete serializer for Leave Request
    Includes computed fields and related data
    """
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.name', read_only=True, allow_null=True)
    leave_type_display = serializers.CharField(source='get_leave_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    total_days = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = LeaveRequest
        fields = [
            'id',
            'user',
            'user_name',
            'user_email',
            'leave_type',
            'leave_type_display',
            'from_date',
            'to_date',
            'total_days',
            'reason',
            'status',
            'status_display',
            'reviewed_by',
            'reviewed_by_name',
            'reviewed_at',
            'admin_comment',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 
            'user', 
            'reviewed_by', 
            'reviewed_at', 
            'created_at', 
            'updated_at'
        ]
    
    def validate(self, data):
        """
        Validate leave request dates
        Ensure from_date is before to_date
        """
        if 'from_date' in data and 'to_date' in data:
            if data['from_date'] > data['to_date']:
                raise serializers.ValidationError({
                    'to_date': 'To date must be after or equal to from date'
                })
        return data


class LeaveRequestCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating leave requests
    Used when employees submit leave requests
    """
    class Meta:
        model = LeaveRequest
        fields = [
            'leave_type',
            'from_date',
            'to_date',
            'reason'
        ]
    
    def validate(self, data):
        """Validate leave dates"""
        if data['from_date'] > data['to_date']:
            raise serializers.ValidationError({
                'to_date': 'To date must be after or equal to from date'
            })
        
        # Check if from_date is not in the past
        if data['from_date'] < timezone.now().date():
            raise serializers.ValidationError({
                'from_date': 'Leave cannot be requested for past dates'
            })
        
        return data


class LeaveRequestReviewSerializer(serializers.Serializer):
    """
    Serializer for reviewing leave requests by admin
    """
    status = serializers.ChoiceField(
        choices=['approved', 'rejected'],
        help_text='Approval status'
    )
    admin_comment = serializers.CharField(
        required=False, 
        allow_blank=True,
        help_text='Admin comment for the decision'
    )


# HR/Serializers.py
from rest_framework import serializers
from django.utils import timezone

from .models import LeaveRequest, LateRequest, EarlyRequest
# adjust AppUser import path only if your user model lives elsewhere
try:
    from User.models import AppUser
except Exception:
    AppUser = None


# Serializer used for admin review actions (status + optional comment)
class LeaveRequestReviewSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[('approved', 'approved'), ('rejected', 'rejected')])
    admin_comment = serializers.CharField(allow_blank=True, required=False)


# -------------------------
# LateRequest Serializers
# -------------------------
class LateRequestSerializer(serializers.ModelSerializer):
    # Computed / helper fields
    user_name = serializers.SerializerMethodField()
    reviewed_by_name = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    late_time_display = serializers.SerializerMethodField()

    class Meta:
        model = LateRequest
        fields = [
            'id', 'user', 'user_name', 'date', 'late_by_minutes', 'late_time_display',
            'reason', 'status', 'status_display',
            'reviewed_by', 'reviewed_by_name', 'reviewed_at', 'admin_comment',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'reviewed_by', 'reviewed_at', 'created_at', 'updated_at']

    def get_user_name(self, obj):
        try:
            u = getattr(obj, 'user', None)
            if not u:
                return None
            return getattr(u, 'name', None) or getattr(u, 'username', None) or str(u)
        except Exception:
            return None

    def get_reviewed_by_name(self, obj):
        try:
            rb = getattr(obj, 'reviewed_by', None)
            if not rb:
                return None
            return getattr(rb, 'name', None) or getattr(rb, 'username', None) or str(rb)
        except Exception:
            return None

    def get_status_display(self, obj):
        try:
            if hasattr(obj, 'get_status_display'):
                return obj.get_status_display()
            return getattr(obj, 'status', None)
        except Exception:
            return getattr(obj, 'status', None)

    def get_late_time_display(self, obj):
        try:
            # Prefer model-provided property/method if present
            val = getattr(obj, 'late_time_display', None)
            if callable(val):
                return val()
            if val is not None:
                return val
            minutes = getattr(obj, 'late_by_minutes', None)
            if minutes is None:
                return None
            return f"{minutes} minutes"
        except Exception:
            return None


class LateRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LateRequest
        fields = ['date', 'late_by_minutes', 'reason']

    def validate_date(self, value):
        if value < timezone.now().date():
            raise serializers.ValidationError("Date cannot be in the past.")
        return value

    def validate_late_by_minutes(self, value):
        if value <= 0:
            raise serializers.ValidationError("late_by_minutes must be greater than 0.")
        return value


# -------------------------
# EarlyRequest Serializers
# -------------------------
class EarlyRequestSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    reviewed_by_name = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    early_time_display = serializers.SerializerMethodField()

    class Meta:
        model = EarlyRequest
        fields = [
            'id', 'user', 'user_name', 'date', 'early_by_minutes', 'early_time_display',
            'reason', 'status', 'status_display',
            'reviewed_by', 'reviewed_by_name', 'reviewed_at', 'admin_comment',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'reviewed_by', 'reviewed_at', 'created_at', 'updated_at']

    def get_user_name(self, obj):
        try:
            u = getattr(obj, 'user', None)
            if not u:
                return None
            return getattr(u, 'name', None) or getattr(u, 'username', None) or str(u)
        except Exception:
            return None

    def get_reviewed_by_name(self, obj):
        try:
            rb = getattr(obj, 'reviewed_by', None)
            if not rb:
                return None
            return getattr(rb, 'name', None) or getattr(rb, 'username', None) or str(rb)
        except Exception:
            return None

    def get_status_display(self, obj):
        try:
            if hasattr(obj, 'get_status_display'):
                return obj.get_status_display()
            return getattr(obj, 'status', None)
        except Exception:
            return getattr(obj, 'status', None)

    def get_early_time_display(self, obj):
        try:
            val = getattr(obj, 'early_time_display', None)
            if callable(val):
                return val()
            if val is not None:
                return val
            minutes = getattr(obj, 'early_by_minutes', None)
            if minutes is None:
                return None
            return f"{minutes} minutes"
        except Exception:
            return None


class EarlyRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EarlyRequest
        fields = ['date', 'early_by_minutes', 'reason']

    def validate_date(self, value):
        if value < timezone.now().date():
            raise serializers.ValidationError("Date cannot be in the past.")
        return value

    def validate_early_by_minutes(self, value):
        if value <= 0:
            raise serializers.ValidationError("early_by_minutes must be greater than 0.")
        return value
