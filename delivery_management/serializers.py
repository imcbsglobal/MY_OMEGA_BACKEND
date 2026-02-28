# delivery_management/serializers.py
from rest_framework import serializers
from django.db import transaction
from .models import Delivery, DeliveryProduct, DeliveryStop
from decimal import Decimal


# ===================== NESTED/RELATED SERIALIZERS =====================

class EmployeeBriefSerializer(serializers.Serializer):
    """Brief employee info for delivery"""
    id = serializers.IntegerField()
    employee_id = serializers.CharField()
    full_name = serializers.CharField()
    designation = serializers.CharField(allow_blank=True, required=False)
    phone_number = serializers.CharField(allow_blank=True, required=False)


class VehicleBriefSerializer(serializers.Serializer):
    """Brief vehicle info for delivery"""
    id = serializers.IntegerField()
    registration_number = serializers.CharField()
    vehicle_type = serializers.CharField()
    # Make model optional and use SerializerMethodField to safely access it
    model = serializers.SerializerMethodField()
    capacity = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True, required=False)
    
    def get_model(self, obj):
        """Safely get model field if it exists"""
        return getattr(obj, 'model', None) or getattr(obj, 'vehicle_model', '')


class RouteBriefSerializer(serializers.Serializer):
    """Brief route info for delivery"""
    id = serializers.IntegerField()
    origin = serializers.CharField()
    destination = serializers.CharField()
    route_name = serializers.CharField()


class ProductBriefSerializer(serializers.Serializer):
    """Brief product info"""
    id = serializers.IntegerField()
    product_name = serializers.CharField()
    product_code = serializers.CharField(allow_blank=True, required=False)
    unit = serializers.CharField()


# ===================== DELIVERY PRODUCT SERIALIZERS =====================

class DeliveryProductSerializer(serializers.ModelSerializer):
    """Serializer for delivery products"""
    product_details = ProductBriefSerializer(source='product', read_only=True)
    product_name = serializers.CharField(source='product.product_name', read_only=True)
    delivery_percentage = serializers.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        read_only=True
    )

    class Meta:
        model = DeliveryProduct
        fields = [
            'id', 
            'product', 
            'product_details',
            'product_name',
            'loaded_quantity',
            'delivered_quantity',
            'balance_quantity',
            'unit_price',
            'total_amount',
            'delivery_percentage',
            'notes',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['balance_quantity', 'total_amount']


class DeliveryProductCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating delivery products"""
    class Meta:
        model = DeliveryProduct
        fields = [
            'product',
            'loaded_quantity',
            'unit_price',
            'notes'
        ]

    def validate_loaded_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Loaded quantity must be greater than 0")
        return value


class DeliveryProductUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating delivery products (mainly delivered quantities)"""
    class Meta:
        model = DeliveryProduct
        fields = [
            'delivered_quantity',
            'balance_quantity',
            'notes'
        ]

    def validate(self, data):
        delivered = data.get('delivered_quantity', self.instance.delivered_quantity)
        if delivered > self.instance.loaded_quantity:
            raise serializers.ValidationError({
                'delivered_quantity': 'Delivered quantity cannot exceed loaded quantity'
            })
        return data


# ===================== DELIVERY STOP SERIALIZERS =====================

class DeliveryStopSerializer(serializers.ModelSerializer):
    """Serializer for delivery stops"""
    stop_duration = serializers.IntegerField(read_only=True)
    is_completed = serializers.BooleanField(read_only=True)

    class Meta:
        model = DeliveryStop
        fields = [
            'id',
            'shop_name',
            'stop_sequence',
            'customer_name',
            'customer_address',
            'customer_phone',
            'planned_boxes',
            'delivered_boxes',
            'balance_boxes',
            'planned_amount',
            'collected_amount',
            'pending_amount',
            'estimated_arrival',
            'actual_arrival',
            'departure_time',
            'status',
            'notes',
            'failure_reason',
            'signature_image',
            'proof_image',
            'latitude',
            'longitude',
            'stop_duration',
            'is_completed',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['balance_boxes', 'pending_amount']


class DeliveryStopCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating delivery stops"""
    class Meta:
        model = DeliveryStop
        fields = [
            'shop_name',
            'stop_sequence',
            'customer_name',
            'customer_address',
            'customer_phone',
            'planned_boxes',
            'planned_amount',
            'estimated_arrival',
            'notes'
        ]


class DeliveryStopUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating delivery stop by employee"""
    class Meta:
        model = DeliveryStop
        fields = [
            'shop_name',
            'delivered_boxes',
            'collected_amount',
            'status',
            'notes',
            'failure_reason',
            'signature_image',
            'proof_image',
            'latitude',
            'longitude'
        ]
    
    def validate(self, data):
        """Validate delivered boxes don't exceed planned boxes"""
        delivered_boxes = data.get('delivered_boxes', self.instance.delivered_boxes if self.instance else 0)
        planned_boxes = self.instance.planned_boxes if self.instance else 0
        
        if delivered_boxes and planned_boxes and delivered_boxes > planned_boxes:
            # Allow it but set status to partial if more delivered than planned
            if data.get('status') != 'delivered':
                data['status'] = 'partial'
        
        return data


# ===================== MAIN DELIVERY SERIALIZERS =====================

class DeliveryListSerializer(serializers.ModelSerializer):
    """Serializer for delivery list view"""
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    vehicle_number = serializers.CharField(source='vehicle.registration_number', read_only=True)
    route_name = serializers.CharField(source='route.route_name', read_only=True)
    duration_minutes = serializers.IntegerField(read_only=True)
    distance_traveled = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    delivery_efficiency = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)

    class Meta:
        model = Delivery
        fields = [
            'id',
            'delivery_number',
            'employee',
            'employee_name',
            'vehicle',
            'vehicle_number',
            'route',
            'route_name',
            'scheduled_date',
            'scheduled_time',
            'start_datetime',
            'end_datetime',
            'status',
            'total_loaded_boxes',
            'total_delivered_boxes',
            'total_balance_boxes',
            'total_amount',
            'collected_amount',
            'total_pending_amount',
            'duration_minutes',
            'distance_traveled',
            'delivery_efficiency',
            'created_at',
            'updated_at'
        ]


class DeliveryDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for delivery with all related data"""
    employee_details = EmployeeBriefSerializer(source='employee', read_only=True)
    vehicle_details = VehicleBriefSerializer(source='vehicle', read_only=True)
    route_details = RouteBriefSerializer(source='route', read_only=True)
    products = DeliveryProductSerializer(many=True, read_only=True)
    stops = DeliveryStopSerializer(many=True, read_only=True)
    
    # Add convenience fields for compatibility
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    vehicle_number = serializers.CharField(source='vehicle.registration_number', read_only=True)
    route_name = serializers.CharField(source='route.route_name', read_only=True)
    
    # Calculated fields
    duration_minutes = serializers.IntegerField(read_only=True)
    distance_traveled = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    fuel_consumed = serializers.DecimalField(max_digits=8, decimal_places=2, read_only=True)
    delivery_efficiency = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    
    created_by_name = serializers.CharField(source='created_by.email', read_only=True, allow_null=True)
    completed_by_name = serializers.CharField(source='completed_by.email', read_only=True, allow_null=True)

    class Meta:
        model = Delivery
        fields = [
            'id',
            'delivery_number',
            'employee',
            'employee_details',
            'employee_name',
            'vehicle',
            'vehicle_details',
            'vehicle_number',
            'route',
            'route_details',
            'route_name',
            'scheduled_date',
            'scheduled_time',
            'start_datetime',
            'end_datetime',
            'odometer_start',
            'odometer_end',
            'fuel_start',
            'fuel_end',
            'total_loaded_boxes',
            'total_delivered_boxes',
            'total_balance_boxes',
            'total_amount',
            'collected_amount',
            'total_pending_amount',
            'status',
            'start_notes',
            'end_notes',
            'remarks',
            'duration_minutes',
            'distance_traveled',
            'fuel_consumed',
            'delivery_efficiency',
            'created_by',
            'created_by_name',
            'completed_by',
            'completed_by_name',
            'assigned_to',
            'products',
            'stops',
            'created_at',
            'updated_at',
            'start_location',
            'start_latitude',
            'start_longitude',
            'completion_location',
            'completion_latitude',
            'completion_longitude'
        ]


class DeliveryCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new delivery"""
    products = DeliveryProductCreateSerializer(many=True, required=False)
    stops = DeliveryStopCreateSerializer(many=True, required=False)

    class Meta:
        model = Delivery
        fields = [
            'employee',
            'vehicle',
            'route',
            'assigned_to',
            'scheduled_date',
            'scheduled_time',
            'remarks',
            'products',
            'stops'
        ]

    def validate(self, data):
        # Validate scheduled date is not in the past
        from django.utils import timezone
        scheduled_date = data.get('scheduled_date')
        if scheduled_date and scheduled_date < timezone.now().date():
            raise serializers.ValidationError({
                'scheduled_date': 'Scheduled date cannot be in the past'
            })
        return data

    @transaction.atomic
    def create(self, validated_data):
        products_data = validated_data.pop('products', [])
        stops_data = validated_data.pop('stops', [])
        
        # Create delivery
        delivery = Delivery.objects.create(**validated_data)
        
        # Create products if provided
        total_loaded = Decimal('0.00')
        total_amount = Decimal('0.00')
        
        for product_data in products_data:
            product = DeliveryProduct.objects.create(
                delivery=delivery,
                **product_data
            )
            total_loaded += product.loaded_quantity
            if product.unit_price:
                total_amount += product.loaded_quantity * product.unit_price
        
        # Update delivery totals only if products were provided
        if products_data:
            delivery.total_loaded_boxes = total_loaded
            delivery.total_amount = total_amount
            delivery.save()
        
        # Create stops if provided
        for stop_data in stops_data:
            DeliveryStop.objects.create(
                delivery=delivery,
                **stop_data
            )
        
        return delivery


class DeliveryUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating delivery - only editable fields"""
    
    class Meta:
        model = Delivery
        fields = [
            'scheduled_date',
            'scheduled_time',
            'total_loaded_boxes',
            'total_delivered_boxes',
            'collected_amount',
            'remarks',
        ]
    # Allow manual overrides of totals via PATCH from the summary UI.
    # No special validation here; totals will be recalculated server-side after save.


class DeliveryStartSerializer(serializers.Serializer):
    """Serializer for starting a delivery"""
    odometer_reading = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=False,
        allow_null=True
    )
    fuel_level = serializers.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        required=False,
        allow_null=True
    )
    notes = serializers.CharField(
        required=False, 
        allow_blank=True,
        max_length=2000
    )
    # Location fields for delivery start
    start_location = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500,
        help_text="Human-readable start location description"
    )
    start_latitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        allow_null=True,
        help_text="GPS latitude for delivery start location"
    )
    start_longitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        allow_null=True,
        help_text="GPS longitude for delivery start location"
    )

    def validate_odometer_reading(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Odometer reading cannot be negative")
        return value

    def validate_fuel_level(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Fuel level cannot be negative")
        return value

    def validate_start_latitude(self, value):
        if value is not None and (value < -90 or value > 90):
            raise serializers.ValidationError("Latitude should be between -90 and 90")
        return value

    def validate_start_longitude(self, value):
        if value is not None and (value < -180 or value > 180):
            raise serializers.ValidationError("Longitude should be between -180 and 180")
        return value


class DeliveryCompleteSerializer(serializers.Serializer):
    """Serializer for completing a delivery"""
    odometer_reading = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=False,
        allow_null=True
    )
    fuel_level = serializers.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        required=False,
        allow_null=True
    )
    notes = serializers.CharField(
        required=False, 
        allow_blank=True,
        max_length=2000
    )
    products = serializers.ListField(
        child=serializers.DictField(),
        required=False,  # Make it optional and auto-generate if not provided
        help_text="List of products with delivered quantities"
    )
    # Completion location fields
    completion_location = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500,
        help_text="Human-readable completion location description"
    )
    completion_latitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        allow_null=True,
        help_text="GPS latitude for delivery completion location"
    )
    completion_longitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        allow_null=True,
        help_text="GPS longitude for delivery completion location"
    )

    def validate_odometer_reading(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Odometer reading cannot be negative")
        return value

    def validate_fuel_level(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Fuel level cannot be negative")
        return value

    def validate_completion_latitude(self, value):
        if value is not None and (value < -90 or value > 90):
            raise serializers.ValidationError("Latitude should be between -90 and 90")
        return value

    def validate_completion_longitude(self, value):
        if value is not None and (value < -180 or value > 180):
            raise serializers.ValidationError("Longitude should be between -180 and 180")
        return value

    def validate_products(self, value):
        # Allow empty products list - we'll use existing data
        if not value:
            return value
        
        for item in value:
            if 'product_id' not in item:
                raise serializers.ValidationError("Each product must have product_id")
            if 'delivered_quantity' not in item:
                raise serializers.ValidationError("Each product must have delivered_quantity")
            
            try:
                delivered = Decimal(str(item['delivered_quantity']))
                if delivered < 0:
                    raise serializers.ValidationError("Delivered quantity cannot be negative")
            except:
                raise serializers.ValidationError("Invalid delivered quantity format")
        
        return value

    def validate(self, data):
        # Validate odometer end is greater than start if both provided
        delivery = self.context.get('delivery')
        if delivery:
            odometer_end = data.get('odometer_reading')
            if odometer_end and delivery.odometer_start:
                if odometer_end < delivery.odometer_start:
                    raise serializers.ValidationError({
                        'odometer_reading': 'End odometer reading must be greater than or equal to start reading'
                    })
        
        return data


class DeliveryUpdateProductsSerializer(serializers.Serializer):
    """Serializer for bulk updating product quantities during delivery"""
    products = serializers.ListField(
        child=serializers.DictField(),
        required=True
    )

    def validate_products(self, value):
        for item in value:
            if 'id' not in item:
                raise serializers.ValidationError("Each product must have an id")
            if 'delivered_quantity' not in item:
                raise serializers.ValidationError("Each product must have delivered_quantity")
        return value


# ===================== STATISTICS SERIALIZERS =====================

class DeliveryStatsSerializer(serializers.Serializer):
    """Serializer for delivery statistics"""
    total_deliveries = serializers.IntegerField()
    scheduled_deliveries = serializers.IntegerField()
    in_progress_deliveries = serializers.IntegerField()
    completed_deliveries = serializers.IntegerField()
    cancelled_deliveries = serializers.IntegerField()
    total_boxes_loaded = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_boxes_delivered = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_boxes_returned = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_collected = serializers.DecimalField(max_digits=15, decimal_places=2)
    average_efficiency = serializers.DecimalField(max_digits=5, decimal_places=2)