# HR/serializers.py - Updated Serializers for new Punch In/Out System
from rest_framework import serializers
from django.utils import timezone
from .models import Attendance, Holiday, LeaveRequest, LateRequest, EarlyRequest, PunchRecord
from User.models import AppUser


class PunchRecordSerializer(serializers.ModelSerializer):
    """Serializer for individual punch records"""
    punch_type_display = serializers.CharField(source='get_punch_type_display', read_only=True)
    
    class Meta:
        model = PunchRecord
        fields = [
            'id',
            'punch_type',
            'punch_type_display',
            'punch_time',
            'location',
            'latitude',
            'longitude',
            'note',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class AttendanceSerializer(serializers.ModelSerializer):
    """
    Complete serializer for Attendance records
    """
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.name', read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    verification_status_display = serializers.CharField(source='get_verification_status_display', read_only=True)
    
    # Backward compatibility fields
    punch_in_time = serializers.DateTimeField(source='first_punch_in_time', read_only=True)
    punch_out_time = serializers.DateTimeField(source='last_punch_out_time', read_only=True)
    punch_in_location = serializers.CharField(source='first_punch_in_location', read_only=True)
    punch_out_location = serializers.CharField(source='last_punch_out_location', read_only=True)
    working_hours = serializers.DecimalField(source='total_working_hours', max_digits=5, decimal_places=2, read_only=True)
    
    class Meta:
        model = Attendance
        fields = [
            'id',
            'user',
            'user_name',
            'user_email',
            'date',
            # New fields
            'first_punch_in_time',
            'first_punch_in_location',
            'first_punch_in_latitude',
            'first_punch_in_longitude',
            'last_punch_out_time',
            'last_punch_out_location',
            'last_punch_out_latitude',
            'last_punch_out_longitude',
            'total_working_hours',
            'total_break_hours',
            'is_currently_on_break',
            # Backward compatibility fields
            'punch_in_time',
            'punch_out_time',
            'punch_in_location',
            'punch_out_location',
            'working_hours',
            # Status fields
            'status',
            'status_display',
            'verification_status',
            'verification_status_display',
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
            'total_working_hours',
            'total_break_hours',
            'is_currently_on_break',
            'verified_by',
            'verified_at',
            'created_at',
            'updated_at'
        ]


class PunchInSerializer(serializers.Serializer):
    """
    Serializer for punch in action
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


class HolidaySerializer(serializers.ModelSerializer):
    """
    Serializer for Holiday model
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


class LateRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for Late Requests
    """
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
            return obj.user.name if hasattr(obj.user, 'name') else str(obj.user)
        except:
            return None

    def get_reviewed_by_name(self, obj):
        try:
            return obj.reviewed_by.name if obj.reviewed_by and hasattr(obj.reviewed_by, 'name') else None
        except:
            return None

    def get_status_display(self, obj):
        try:
            return obj.get_status_display() if hasattr(obj, 'get_status_display') else obj.status
        except:
            return obj.status

    def get_late_time_display(self, obj):
        try:
            return obj.late_time_display if hasattr(obj, 'late_time_display') else f"{obj.late_by_minutes} minutes"
        except:
            return None


class LateRequestCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating late requests
    """
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


class EarlyRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for Early Requests
    """
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
            return obj.user.name if hasattr(obj.user, 'name') else str(obj.user)
        except:
            return None

    def get_reviewed_by_name(self, obj):
        try:
            return obj.reviewed_by.name if obj.reviewed_by and hasattr(obj.reviewed_by, 'name') else None
        except:
            return None

    def get_status_display(self, obj):
        try:
            return obj.get_status_display() if hasattr(obj, 'get_status_display') else obj.status
        except:
            return obj.status

    def get_early_time_display(self, obj):
        try:
            return obj.early_time_display if hasattr(obj, 'early_time_display') else f"{obj.early_by_minutes} minutes"
        except:
            return None


class EarlyRequestCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating early requests
    """
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