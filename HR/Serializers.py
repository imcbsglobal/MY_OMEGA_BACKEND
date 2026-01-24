# HR/serializers.py - UPDATED: Integrated with master.LeaveMaster

from rest_framework import serializers
from django.utils import timezone
from .models import (
    Attendance, Holiday, LeaveRequest, LateRequest, 
    EarlyRequest, PunchRecord, EmployeeLeaveBalance
)
from master.models import LeaveMaster
from master.serializers import LeaveMasterSerializer
from User.models import AppUser


# ========== LEAVE REQUEST SERIALIZERS ==========

class LeaveRequestSerializer(serializers.ModelSerializer):
    """
    Complete serializer for Leave Request with Leave Master info
    """
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.name', read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    total_days = serializers.IntegerField(read_only=True)
    
    # Leave Master information
    leave_master_details = LeaveMasterSerializer(source='leave_master', read_only=True)
    leave_name = serializers.CharField(source='leave_master.leave_name', read_only=True)
    leave_category = serializers.CharField(source='leave_master.category', read_only=True)
    
    class Meta:
        model = LeaveRequest
        fields = [
            'id',
            'user',
            'user_name',
            'user_email',
            'leave_master',  # ID of leave master (required)
            'leave_master_details',  # Full leave master object
            'leave_name',  # Quick access to leave name
            'leave_category',  # Quick access to category
            'from_date',
            'to_date',
            'total_days',
            'reason',
            'status',
            'status_display',
            'is_paid',
            'deducted_from_balance',
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
            'is_paid',
            'reviewed_by', 
            'reviewed_at', 
            'created_at', 
            'updated_at',
            'deducted_from_balance',
        ]


class LeaveRequestCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating leave requests - REQUIRES leave_master
    """
    class Meta:
        model = LeaveRequest
        fields = [
            'leave_master',  # REQUIRED
            'from_date',
            'to_date',
            'reason'
        ]
    
    def validate(self, data):
        """Validate leave dates and Leave Master"""
        from_date = data.get('from_date')
        to_date = data.get('to_date')
        
        if from_date and to_date:
            if from_date > to_date:
                raise serializers.ValidationError({
                    'to_date': 'To date must be after or equal to from date'
                })
            
            if from_date < timezone.now().date():
                raise serializers.ValidationError({
                    'from_date': 'Leave cannot be requested for past dates'
                })
        
        # Validate leave_master exists and is active
        leave_master = data.get('leave_master')
        if not leave_master:
            raise serializers.ValidationError({
                'leave_master': 'Leave type is required'
            })
        
        if not leave_master.is_active:
            raise serializers.ValidationError({
                'leave_master': 'Selected leave type is not active'
            })
        
        return data
    
    def create(self, validated_data):
        """Create leave request with Leave Master"""
        # Get the user from the context (set in the view)
        

        # Create the leave request
        return LeaveRequest.objects.create(**validated_data)


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


# ========== LATE REQUEST SERIALIZERS ==========

class LateRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for Late Requests - NO LEAVE MASTER REQUIRED
    """
    user_name = serializers.CharField(source='user.name', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.name', read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = LateRequest
        fields = [
            'id',
            'user',
            'user_name',
            'date',
            'late_by_minutes',
            'reason',
            'status',
            'status_display',
            'reviewed_by',
            'reviewed_by_name',
            'reviewed_at',
            'admin_comment',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'user', 'reviewed_by', 'reviewed_at', 'created_at', 'updated_at']


class LateRequestCreateSerializer(serializers.ModelSerializer):
    """Create serializer for Late Requests - Simple form"""
    class Meta:
        model = LateRequest
        fields = ['date', 'late_by_minutes', 'reason']
    
    def validate(self, data):
        date = data.get('date')
        if date and date < timezone.now().date():
            raise serializers.ValidationError({
                'date': 'Date cannot be in the past'
            })
        
        late_by_minutes = data.get('late_by_minutes')
        if late_by_minutes and late_by_minutes <= 0:
            raise serializers.ValidationError({
                'late_by_minutes': 'Must be greater than 0'
            })
        
        return data




# ========== EARLY REQUEST SERIALIZERS ==========

class EarlyRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for Early Requests - NO LEAVE MASTER REQUIRED
    """
    user_name = serializers.CharField(source='user.name', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.name', read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = EarlyRequest
        fields = [
            'id',
            'user',
            'user_name',
            'date',
            'early_by_minutes',
            'reason',
            'status',
            'status_display',
            'reviewed_by',
            'reviewed_by_name',
            'reviewed_at',
            'admin_comment',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'user', 'reviewed_by', 'reviewed_at', 'created_at', 'updated_at']


class EarlyRequestCreateSerializer(serializers.ModelSerializer):
    """Create serializer for Early Requests - Simple form"""
    class Meta:
        model = EarlyRequest
        fields = ['date', 'early_by_minutes', 'reason']
    
    def validate(self, data):
        from django.utils import timezone
        
        date = data.get('date')
        early_by_minutes = data.get('early_by_minutes')
        
        # ✅ Allow today and future dates only
        if date and date < timezone.now().date():
            raise serializers.ValidationError({
                'date': 'Date cannot be in the past. Please select today or a future date.'
            })
        
        # Validate early_by_minutes
        if early_by_minutes:
            if early_by_minutes <= 0:
                raise serializers.ValidationError({
                    'early_by_minutes': 'Must be greater than 0'
                })
            if early_by_minutes > 240:  # Max 4 hours
                raise serializers.ValidationError({
                    'early_by_minutes': 'Cannot exceed 240 minutes (4 hours)'
                })
        
        return data


# ========== PUNCH RECORD SERIALIZERS ==========

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


# ========== ATTENDANCE SERIALIZERS ==========

class AttendanceSerializer(serializers.ModelSerializer):
    """
    Complete serializer for Attendance records with Leave Master integration
    """
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.name', read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    verification_status_display = serializers.CharField(source='get_verification_status_display', read_only=True)
    
    # Leave Master information
    leave_master_details = LeaveMasterSerializer(source='leave_master', read_only=True)
    leave_name = serializers.CharField(source='leave_master.leave_name', read_only=True, allow_null=True)
    
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
            # Leave Master fields
            'is_leave',
            'leave_master',
            'leave_master_details',
            'leave_name',
            'is_paid_day',
            # Holiday fields
            'is_sunday',
            'is_holiday',
            # Notes
            'note',
            'admin_note',
            # Verification
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
    latitude = serializers.FloatField(
        required=True,
        help_text='GPS latitude'
    )
    longitude = serializers.FloatField(
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
    latitude = serializers.FloatField(
        required=True,
        help_text='GPS latitude'
    )
    longitude = serializers.FloatField(
        required=True,
        help_text='GPS longitude'
    )
    note = serializers.CharField(
        required=False, 
        allow_blank=True,
        help_text='Optional note for punch out'
    )


class AttendanceUpdateStatusSerializer(serializers.Serializer):
    """
    Serializer for updating attendance status
    """
    status = serializers.CharField(
        help_text='New status for the attendance record'
    )
    leave_master = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text='Leave Master ID (optional, for leave/special_leave/mandatory_holiday status)'
    )
    admin_note = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text='Admin note for the update'
    )


# ========== HOLIDAY SERIALIZERS ==========

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
            'holiday_type',
            'description',
            'is_active',
            'is_paid',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_date(self, value):
        """Ensure holiday date is not in the past"""
        if value < timezone.now().date():
            raise serializers.ValidationError("Holiday date cannot be in the past")
        return value


# ========== EMPLOYEE LEAVE BALANCE SERIALIZER ==========

class EmployeeLeaveBalanceSerializer(serializers.ModelSerializer):
    """Serializer for Employee Leave Balance"""
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = EmployeeLeaveBalance
        fields = [
            'id',
            'user',
            'user_name',
            'user_email',
            'casual_leave_balance',
            'casual_leave_used',
            'sick_leave_balance',
            'sick_leave_used',
            'special_leave_balance',
            'special_leave_used',
            'unpaid_leave_taken',
            'year',
            'last_casual_credit_month',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']