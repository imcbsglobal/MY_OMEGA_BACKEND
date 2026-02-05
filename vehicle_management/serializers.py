# vehicle_management/serializers.py
from rest_framework import serializers
from django.apps import apps
from .models import Vehicle, Trip, VehicleChallan
from datetime import datetime


# Try to get AppUser model
UserModel = None
try:
    from User.models import AppUser as UserModel
except Exception:
    try:
        UserModel = apps.get_model('User', 'AppUser')
    except Exception:
        UserModel = None


class VehicleListSerializer(serializers.ModelSerializer):
    """Serializer for vehicle list view"""
    photo_url = serializers.SerializerMethodField()
    total_trips = serializers.IntegerField(read_only=True)
    total_distance = serializers.SerializerMethodField()
    
    class Meta:
        model = Vehicle
        fields = [
            'id',
            'vehicle_name',
            'company',
            'registration_number',
            'vehicle_type',
            'fuel_type',
            'color',
            'photo',
            'photo_url',
            'current_odometer',
            'is_active',
            'total_trips',
            'total_distance',
            'insurance_expiry_date',
            'next_service_date',
            'created_at',
        ]
    
    def get_photo_url(self, obj):
        request = self.context.get('request')
        if obj.photo:
            return request.build_absolute_uri(obj.photo.url) if request else obj.photo.url
        return None
    
    def get_total_distance(self, obj):
        return float(obj.total_distance_traveled) if hasattr(obj, 'total_distance_traveled') else 0.00


class VehicleDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed vehicle view"""
    photo_url = serializers.SerializerMethodField()
    total_trips = serializers.IntegerField(read_only=True)
    total_distance = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Vehicle
        fields = [
            # Basic
            'id',
            'vehicle_name',
            'company',
            'registration_number',
            'vehicle_type',
            'fuel_type',
            'color',
            'manufacturing_year',
            'seating_capacity',
            'photo',
            'photo_url',
            
            # Ownership
            'owner_name',
            'insurance_number',
            'insurance_expiry_date',
            
            # Maintenance
            'last_service_date',
            'next_service_date',
            'current_odometer',
            
            # Technical
            'chassis_number',
            'engine_number',
            
            # Additional
            'notes',
            'is_active',
            
            # Stats
            'total_trips',
            'total_distance',
            
            # Audit
            'created_by',
            'created_by_name',
            'created_at',
            'updated_at',
        ]
    
    def get_photo_url(self, obj):
        request = self.context.get('request')
        if obj.photo:
            return request.build_absolute_uri(obj.photo.url) if request else obj.photo.url
        return None
    
    def get_total_distance(self, obj):
        return float(obj.total_distance_traveled) if hasattr(obj, 'total_distance_traveled') else 0.00
    
    def get_created_by_name(self, obj):
        if obj.created_by:
            if hasattr(obj.created_by, 'get_full_name'):
                return obj.created_by.get_full_name()
            return str(obj.created_by)
        return None


class VehicleCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating vehicles"""
    
    class Meta:
        model = Vehicle
        fields = [
            'vehicle_name',
            'company',
            'registration_number',
            'vehicle_type',
            'fuel_type',
            'color',
            'manufacturing_year',
            'seating_capacity',
            'photo',
            'owner_name',
            'insurance_number',
            'insurance_expiry_date',
            'last_service_date',
            'next_service_date',
            'current_odometer',
            'chassis_number',
            'engine_number',
            'notes',
            'is_active',
        ]
    
    def validate_registration_number(self, value):
        """Ensure registration number is unique"""
        qs = Vehicle.objects.filter(registration_number=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                "A vehicle with this registration number already exists."
            )
        return value


# ==================== TRIP SERIALIZERS ====================

class TripEmployeeSerializer(serializers.ModelSerializer):
    """Brief employee info for trips"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = UserModel if UserModel else 'auth.User'
        fields = ['id', 'email', 'full_name']
    
    def get_full_name(self, obj):
        if hasattr(obj, 'get_full_name'):
            return obj.get_full_name()
        return str(obj)


class TripVehicleSerializer(serializers.ModelSerializer):
    """Brief vehicle info for trips"""
    photo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Vehicle
        fields = [
            'id',
            'vehicle_name',
            'company',
            'registration_number',
            'vehicle_type',
            'photo_url'
        ]
    
    def get_photo_url(self, obj):
        request = self.context.get('request')
        if obj.photo:
            return request.build_absolute_uri(obj.photo.url) if request else obj.photo.url
        return None


class TripListSerializer(serializers.ModelSerializer):
    """Serializer for trip list view"""
    vehicle_info = TripVehicleSerializer(source='vehicle', read_only=True)
    employee_info = TripEmployeeSerializer(source='employee', read_only=True)
    odometer_start_url = serializers.SerializerMethodField()
    odometer_end_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Trip
        fields = [
            'id',
            'vehicle',
            'vehicle_info',
            'employee',
            'employee_info',
            'date',
            'start_time',
            'end_time',
            'time_period',
            'client_name',
            'purpose',
            'fuel_cost',
            'odometer_start',
            'odometer_end',
            'odometer_start_url',
            'odometer_end_url',
            'distance_km',
            'duration_hours',
            'status',
            'created_at',
            'completed_at',
        ]
    
    def get_odometer_start_url(self, obj):
        request = self.context.get('request')
        if obj.odometer_start_image:
            return request.build_absolute_uri(obj.odometer_start_image.url) if request else obj.odometer_start_image.url
        return None
    
    def get_odometer_end_url(self, obj):
        request = self.context.get('request')
        if obj.odometer_end_image:
            return request.build_absolute_uri(obj.odometer_end_image.url) if request else obj.odometer_end_image.url
        return None


class TripDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed trip view"""
    vehicle_info = TripVehicleSerializer(source='vehicle', read_only=True)
    employee_info = TripEmployeeSerializer(source='employee', read_only=True)
    approved_by_info = TripEmployeeSerializer(source='approved_by', read_only=True)
    odometer_start_url = serializers.SerializerMethodField()
    odometer_end_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Trip
        fields = [
            # Basic Info
            'id',
            'vehicle',
            'vehicle_info',
            'employee',
            'employee_info',
            
            # Trip Details
            'date',
            'start_time',
            'end_time',
            'time_period',
            'client_name',
            'purpose',
            
            # Fuel & Odometer
            'fuel_cost',
            'odometer_start',
            'odometer_start_image',
            'odometer_start_url',
            'odometer_end',
            'odometer_end_image',
            'odometer_end_url',
            
            # Calculated
            'distance_km',
            'duration_hours',
            
            # Status & Approval
            'status',
            'approved_by',
            'approved_by_info',
            'approved_at',
            'admin_notes',
            
            # Audit
            'created_at',
            'updated_at',
            'completed_at',
        ]
    
    def get_odometer_start_url(self, obj):
        request = self.context.get('request')
        if obj.odometer_start_image:
            return request.build_absolute_uri(obj.odometer_start_image.url) if request else obj.odometer_start_image.url
        return None
    
    def get_odometer_end_url(self, obj):
        request = self.context.get('request')
        if obj.odometer_end_image:
            return request.build_absolute_uri(obj.odometer_end_image.url) if request else obj.odometer_end_image.url
        return None


class TripStartSerializer(serializers.ModelSerializer):
    """Serializer for starting a new trip"""
    
    class Meta:
        model = Trip
        fields = [
             'id', 
            'vehicle',
            'employee',
            'date',
            'start_time',
            'time_period',
            'client_name',
            'purpose',
            'fuel_cost',
            'odometer_start',
            'odometer_start_image',
        ]
    
    def validate(self, data):
        """Validate trip start data"""
        vehicle = data.get('vehicle')
        
        # Check if vehicle is active
        if not vehicle.is_active:
            raise serializers.ValidationError({
                'vehicle': 'This vehicle is not active.'
            })
        
        # Check if there's an ongoing trip for this vehicle
        ongoing_trip = Trip.objects.filter(
            vehicle=vehicle,
            status='started'
        ).exists()
        
        if ongoing_trip:
            raise serializers.ValidationError({
                'vehicle': 'This vehicle already has an ongoing trip. Please complete it first.'
            })
        
        return data
    
    def create(self, validated_data):
        """Create trip with started status"""
        validated_data['status'] = 'started'
        return super().create(validated_data)


class TripEndSerializer(serializers.ModelSerializer):
    """Serializer for ending/completing a trip"""
    
    class Meta:
        model = Trip
        fields = [
            'end_time',
            'odometer_end',
            'odometer_end_image',
        ]
    
    def validate(self, data):
        """Validate trip end data"""
        if not self.instance:
            raise serializers.ValidationError("Trip instance is required.")
        
        # Ensure trip is in started status
        if self.instance.status != 'started':
            raise serializers.ValidationError({
                'status': f'Cannot complete trip. Current status is: {self.instance.status}'
            })
        
        # Validate odometer end is greater than start
        odometer_end = data.get('odometer_end')
        if odometer_end and self.instance.odometer_start:
            if odometer_end < self.instance.odometer_start:
                raise serializers.ValidationError({
                    'odometer_end': 'End odometer reading must be greater than or equal to start reading.'
                })
        
        return data
    
    def update(self, instance, validated_data):
        """Update trip and mark as completed"""
        validated_data['status'] = 'completed'
        return super().update(instance, validated_data)


class TripApprovalSerializer(serializers.ModelSerializer):
    """Serializer for admin approval/rejection of trips"""
    
    class Meta:
        model = Trip
        fields = [
            'status',
            'admin_notes',
        ]
    
    def validate_status(self, value):
        """Validate status is approved or rejected"""
        if value not in ['approved', 'rejected']:
            raise serializers.ValidationError(
                "Status must be either 'approved' or 'rejected'."
            )
        return value
    
    def update(self, instance, validated_data):
        """Update trip approval status"""
        if instance.status != 'completed':
            raise serializers.ValidationError(
                "Only completed trips can be approved or rejected."
            )
        
        validated_data['approved_by'] = self.context['request'].user
        validated_data['approved_at'] = datetime.now()
        
        return super().update(instance, validated_data)


# ==================== VEHICLE CHALLAN SERIALIZERS ====================

class ChallanVehicleSerializer(serializers.ModelSerializer):
    """Brief vehicle info for challans"""
    class Meta:
        model = Vehicle
        fields = [
            'id',
            'vehicle_name',
            'registration_number',
            'vehicle_type',
            'owner_name',
        ]


class ChallanOwnerSerializer(serializers.ModelSerializer):
    """Brief owner info for challans"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = UserModel if UserModel else 'auth.User'
        fields = ['id', 'email', 'full_name']
    
    def get_full_name(self, obj):
        if hasattr(obj, 'get_full_name'):
            return obj.get_full_name()
        return str(obj)


class VehicleChallanListSerializer(serializers.ModelSerializer):
    """Serializer for challan list view"""
    vehicle_info = ChallanVehicleSerializer(source='vehicle', read_only=True)
    owner_info = ChallanOwnerSerializer(source='owner', read_only=True)
    challan_document_url = serializers.SerializerMethodField()
    payment_receipt_url = serializers.SerializerMethodField()
    days_since_challan = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = VehicleChallan
        fields = [
            'id',
            'vehicle',
            'vehicle_info',
            'owner',
            'owner_info',
            'detail_date',
            'challan_number',
            'challan_date',
            'offence_type',
            'location',
            'fine_amount',
            'payment_status',
            'payment_date',
            'remarks',
            'challan_document_url',
            'payment_receipt_url',
            'days_since_challan',
            'created_at',
        ]
    
    def get_challan_document_url(self, obj):
        request = self.context.get('request')
        if obj.challan_document:
            return request.build_absolute_uri(obj.challan_document.url) if request else obj.challan_document.url
        return None
    
    def get_payment_receipt_url(self, obj):
        request = self.context.get('request')
        if obj.payment_receipt:
            return request.build_absolute_uri(obj.payment_receipt.url) if request else obj.payment_receipt.url
        return None


class VehicleChallanDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed challan view"""
    vehicle_info = ChallanVehicleSerializer(source='vehicle', read_only=True)
    owner_info = ChallanOwnerSerializer(source='owner', read_only=True)
    created_by_info = ChallanOwnerSerializer(source='created_by', read_only=True)
    challan_document_url = serializers.SerializerMethodField()
    payment_receipt_url = serializers.SerializerMethodField()
    days_since_challan = serializers.IntegerField(read_only=True)
    is_paid = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = VehicleChallan
        fields = [
            # Basic Info
            'id',
            'vehicle',
            'vehicle_info',
            'owner',
            'owner_info',
            
            # Challan Details
            'detail_date',
            'challan_number',
            'challan_date',
            
            # Violation Details
            'offence_type',
            'location',
            
            # Fine Details
            'fine_amount',
            'payment_status',
            'payment_date',
            
            # Additional Info
            'remarks',
            
            # Attachments
            'challan_document',
            'challan_document_url',
            'payment_receipt',
            'payment_receipt_url',
            
            # Computed Fields
            'days_since_challan',
            'is_paid',
            
            # Audit
            'created_by',
            'created_by_info',
            'created_at',
            'updated_at',
        ]
    
    def get_challan_document_url(self, obj):
        request = self.context.get('request')
        if obj.challan_document:
            return request.build_absolute_uri(obj.challan_document.url) if request else obj.challan_document.url
        return None
    
    def get_payment_receipt_url(self, obj):
        request = self.context.get('request')
        if obj.payment_receipt:
            return request.build_absolute_uri(obj.payment_receipt.url) if request else obj.payment_receipt.url
        return None


class VehicleChallanCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new challan"""
    
    class Meta:
        model = VehicleChallan
        fields = [
            'vehicle',
            'owner',
            'detail_date',
            'challan_number',
            'challan_date',
            'offence_type',
            'location',
            'fine_amount',
            'payment_status',
            'payment_date',
            'remarks',
            'challan_document',
            'payment_receipt',
        ]
    
    def validate_challan_number(self, value):
        """Ensure challan number is unique"""
        qs = VehicleChallan.objects.filter(challan_number=value)
        if qs.exists():
            raise serializers.ValidationError(
                "A challan with this number already exists."
            )
        return value
    
    def validate(self, data):
        """Validate challan data"""
        # If payment status is paid, ensure payment date is provided
        if data.get('payment_status') == 'paid' and not data.get('payment_date'):
            raise serializers.ValidationError({
                'payment_date': 'Payment date is required when payment status is paid.'
            })
        
        # Validate that challan_date is not before detail_date
        if data.get('challan_date') and data.get('detail_date'):
            if data['challan_date'] < data['detail_date']:
                raise serializers.ValidationError({
                    'challan_date': 'Challan date cannot be before the violation date.'
                })
        
        return data


class VehicleChallanUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating challan"""
    
    class Meta:
        model = VehicleChallan
        fields = [
            'vehicle',
            'owner',
            'detail_date',
            'challan_number',
            'challan_date',
            'offence_type',
            'location',
            'fine_amount',
            'payment_status',
            'payment_date',
            'remarks',
            'challan_document',
            'payment_receipt',
        ]
    
    def validate_challan_number(self, value):
        """Ensure challan number is unique"""
        qs = VehicleChallan.objects.filter(challan_number=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                "A challan with this number already exists."
            )
        return value
    
    def validate(self, data):
        """Validate challan data"""
        # If payment status is paid, ensure payment date is provided
        payment_status = data.get('payment_status', self.instance.payment_status if self.instance else None)
        payment_date = data.get('payment_date', self.instance.payment_date if self.instance else None)
        
        if payment_status == 'paid' and not payment_date:
            raise serializers.ValidationError({
                'payment_date': 'Payment date is required when payment status is paid.'
            })
        
        # Validate that challan_date is not before detail_date
        challan_date = data.get('challan_date', self.instance.challan_date if self.instance else None)
        detail_date = data.get('detail_date', self.instance.detail_date if self.instance else None)
        
        if challan_date and detail_date:
            if challan_date < detail_date:
                raise serializers.ValidationError({
                    'challan_date': 'Challan date cannot be before the violation date.'
                })
        
        return data


class ChallanPaymentSerializer(serializers.ModelSerializer):
    """Serializer for marking challan as paid"""
    
    class Meta:
        model = VehicleChallan
        fields = [
            'payment_status',
            'payment_date',
            'payment_receipt',
        ]
    
    def validate_payment_status(self, value):
        """Ensure only paid status is allowed"""
        if value != 'paid':
            raise serializers.ValidationError(
                "Payment status must be 'paid'."
            )
        return value
    
    def update(self, instance, validated_data):
        """Update payment status"""
        if not validated_data.get('payment_date'):
            validated_data['payment_date'] = datetime.now().date()
        return super().update(instance, validated_data)