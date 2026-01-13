# HR/serializers.py - Updated with Complete Leave Master Integration

from rest_framework import serializers
from django.utils import timezone
from .models import (
    Attendance, Holiday, LeaveRequest, LateRequest, 
    EarlyRequest, PunchRecord, LeaveMaster, EmployeeLeaveBalance
)
from User.models import AppUser


# ========== LEAVE MASTER SERIALIZERS ==========

# HR/serializers.py - LeaveMaster Serializers Section

from rest_framework import serializers
from .models import LeaveMaster

class LeaveMasterSerializer(serializers.ModelSerializer):
    """Complete serializer for Leave Master"""
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.name', read_only=True, allow_null=True)
    
    class Meta:
        model = LeaveMaster
        fields = [
            'id',
            'leave_name',
            'leave_date',
            'category',
            'category_display',
            'payment_status',
            'payment_status_display',
            'description',
            'is_active',
            'created_by',
            'created_by_name',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class LeaveMasterSimpleSerializer(serializers.ModelSerializer):
    """Simple serializer for Leave Master in dropdowns"""
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    is_paid = serializers.SerializerMethodField()
    
    class Meta:
        model = LeaveMaster
        fields = [
            'id',
            'leave_name',
            'leave_date',
            'category',
            'category_display',
            'payment_status',
            'payment_status_display',
            'is_paid',
            'is_active',
            'description',
        ]
    
    def get_is_paid(self, obj):
        return obj.payment_status == 'paid'


class LeaveMasterCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating Leave Masters"""
    class Meta:
        model = LeaveMaster
        fields = [
            'leave_name',
            'leave_date',
            'category',
            'payment_status',
            'description',
            'is_active',
        ]
    
    def validate(self, data):
        """Validate leave master data"""
        # Date is required for festival, national, company leaves
        if data.get('category') in ['festival', 'national', 'company', 'mandatory_holiday'] and not data.get('leave_date'):
            raise serializers.ValidationError({
                'leave_date': 'Date is required for this category of leave'
            })
        return data


# ========== LEAVE REQUEST SERIALIZERS ==========

class LeaveRequestSerializer(serializers.ModelSerializer):
    """
    Complete serializer for Leave Request with Leave Master info
    """
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.name', read_only=True, allow_null=True)
    leave_type_display = serializers.CharField(source='get_leave_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    total_days = serializers.IntegerField(read_only=True)
    
    # Leave Master information
    leave_master_details = LeaveMasterSimpleSerializer(source='leave_master', read_only=True)
    leave_display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = LeaveRequest
        fields = [
            'id',
            'user',
            'user_name',
            'user_email',
            'leave_type',
            'leave_type_display',
            'leave_master',  # ID of leave master
            'leave_master_details',  # Full leave master object
            'leave_display_name',  # Smart display name
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
            'reviewed_by', 
            'reviewed_at', 
            'created_at', 
            'updated_at',
            'deducted_from_balance',
        ]
    
    def get_leave_display_name(self, obj):
        """Get smart display name - either from Leave Master or leave type"""
        if obj.leave_master:
            return obj.leave_master.leave_name
        return obj.get_leave_type_display()


class LeaveRequestCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating leave requests with Leave Master support
    """
    leave_master_id = serializers.IntegerField(required=False, allow_null=True, write_only=True)
    
    class Meta:
        model = LeaveRequest
        fields = [
            'leave_type',
            'leave_master_id',  # Optional - for Leave Master based requests
            'from_date',
            'to_date',
            'reason'
        ]
    
    def validate(self, data):
        """Validate leave dates and Leave Master selection"""
        # Date validations
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
        
        # If leave_master_id is provided, validate it
        leave_master_id = data.get('leave_master_id')
        if leave_master_id:
            try:
                leave_master = LeaveMaster.objects.get(id=leave_master_id, is_active=True)
                # Store the leave_master object for later use in create()
                data['_leave_master'] = leave_master
            except LeaveMaster.DoesNotExist:
                raise serializers.ValidationError({
                    'leave_master_id': 'Invalid or inactive leave master selected'
                })
        
        return data
    
    def create(self, validated_data):
        """Create leave request with Leave Master if provided"""
        # Extract leave_master_id and the stored object
        leave_master_id = validated_data.pop('leave_master_id', None)
        leave_master = validated_data.pop('_leave_master', None)
        
        # Get the user from the context (set in the view)
        user = self.context['request'].user
        
        # If leave master is selected, set it
        if leave_master:
            validated_data['leave_master'] = leave_master
            validated_data['leave_type'] = 'leave_master'
            validated_data['is_paid'] = (leave_master.payment_status == 'paid')
        
        # Create the leave request
        return LeaveRequest.objects.create(user=user, **validated_data)


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


# ========== LATE REQUEST SERIALIZERS ==========

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


# ========== EARLY REQUEST SERIALIZERS ==========

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