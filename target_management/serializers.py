# target_management/serializers.py - FIXED VERSION
from rest_framework import serializers
from .models import (
    Route, Product, RouteTargetPeriod, RouteTargetProductDetail,
    CallTargetPeriod, CallDailyTarget, TargetAchievementLog
)
from datetime import timedelta


# ==================== ROUTE SERIALIZERS ====================

class RouteSerializer(serializers.ModelSerializer):
    route_name = serializers.ReadOnlyField()
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Route
        fields = [
            'id', 'origin', 'destination', 'route_code', 'description',
            'is_active', 'route_name', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_created_by_name(self, obj):
        if obj.created_by:
            return getattr(obj.created_by, 'name', obj.created_by.email)
        return None
    
    def validate(self, data):
        """
        Custom validation to provide better error messages for unique constraints
        
        🔥 FIX: Handle missing origin/destination in PATCH requests
        """
        # Get origin and destination, use instance values if not provided (PATCH)
        if self.instance:
            origin = data.get('origin', self.instance.origin).strip() if data.get('origin') is not None else self.instance.origin
            destination = data.get('destination', self.instance.destination).strip() if data.get('destination') is not None else self.instance.destination
        else:
            origin = data.get('origin', '').strip()
            destination = data.get('destination', '').strip()
        
        # Normalize case for comparison
        origin_lower = origin.lower() if origin else ''
        destination_lower = destination.lower() if destination else ''
        
        # Validate that origin and destination exist
        if not origin or not destination:
            errors = {}
            if not origin:
                errors['origin'] = 'Origin is required.'
            if not destination:
                errors['destination'] = 'Destination is required.'
            if errors:
                raise serializers.ValidationError(errors)
        
        # Validate that origin and destination are different
        if origin_lower == destination_lower:
            raise serializers.ValidationError({
                'destination': 'Destination must be different from origin.'
            })
        
        # Check if updating or creating
        instance = self.instance
        
        # Build query to check for duplicate origin-destination combinations
        duplicate_query = Route.objects.filter(
            origin__iexact=origin,
            destination__iexact=destination
        )
        
        # Exclude current instance if updating
        if instance:
            duplicate_query = duplicate_query.exclude(pk=instance.pk)
        
        if duplicate_query.exists():
            raise serializers.ValidationError({
                'non_field_errors': [
                    f'A route from "{origin}" to "{destination}" already exists. '
                    'Please use a different origin-destination combination.'
                ]
            })
        
        # Check route_code uniqueness if provided
        route_code = data.get('route_code')
        if route_code:
            route_code = route_code.strip()
            
            # 🔥 FIX: Only validate if route_code is not empty
            if route_code:
                route_code_query = Route.objects.filter(route_code__iexact=route_code)
                
                if instance:
                    route_code_query = route_code_query.exclude(pk=instance.pk)
                
                if route_code_query.exists():
                    raise serializers.ValidationError({
                        'route_code': [f'Route code "{route_code}" already exists. Please use a unique code.']
                    })
        
        return data


class RouteDetailSerializer(serializers.ModelSerializer):
    route_name = serializers.ReadOnlyField()
    created_by_name = serializers.SerializerMethodField()
    active_targets_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Route
        fields = [
            'id', 'origin', 'destination', 'route_code', 'description',
            'is_active', 'route_name', 'created_by', 'created_by_name',
            'created_at', 'updated_at', 'active_targets_count'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_created_by_name(self, obj):
        if obj.created_by:
            return getattr(obj.created_by, 'name', obj.created_by.email)
        return None
    
    def get_active_targets_count(self, obj):
        return obj.target_periods.filter(is_active=True).count()
    
    def validate(self, data):
        """
        Custom validation - same as RouteSerializer
        
        🔥 FIX: Handle missing origin/destination in PATCH requests
        """
        # Get origin and destination, use instance values if not provided (PATCH)
        if self.instance:
            origin = data.get('origin', self.instance.origin).strip() if data.get('origin') is not None else self.instance.origin
            destination = data.get('destination', self.instance.destination).strip() if data.get('destination') is not None else self.instance.destination
        else:
            origin = data.get('origin', '').strip()
            destination = data.get('destination', '').strip()
        
        origin_lower = origin.lower() if origin else ''
        destination_lower = destination.lower() if destination else ''
        
        # Validate that origin and destination exist
        if not origin or not destination:
            errors = {}
            if not origin:
                errors['origin'] = 'Origin is required.'
            if not destination:
                errors['destination'] = 'Destination is required.'
            if errors:
                raise serializers.ValidationError(errors)
        
        if origin_lower == destination_lower:
            raise serializers.ValidationError({
                'destination': 'Destination must be different from origin.'
            })
        
        instance = self.instance
        
        duplicate_query = Route.objects.filter(
            origin__iexact=origin,
            destination__iexact=destination
        )
        
        if instance:
            duplicate_query = duplicate_query.exclude(pk=instance.pk)
        
        if duplicate_query.exists():
            raise serializers.ValidationError({
                'non_field_errors': [
                    f'A route from "{origin}" to "{destination}" already exists. '
                    'Please use a different origin-destination combination.'
                ]
            })
        
        route_code = data.get('route_code')
        if route_code:
            route_code = route_code.strip()
            
            # 🔥 FIX: Only validate if route_code is not empty
            if route_code:
                route_code_query = Route.objects.filter(route_code__iexact=route_code)
                
                if instance:
                    route_code_query = route_code_query.exclude(pk=instance.pk)
                
                if route_code_query.exists():
                    raise serializers.ValidationError({
                        'route_code': [f'Route code "{route_code}" already exists. Please use a unique code.']
                    })
        
        return data


# ==================== PRODUCT SERIALIZERS ====================

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'id', 'product_name', 'product_code', 'description',
            'unit', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ProductDetailSerializer(serializers.ModelSerializer):
    total_targets_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'product_name', 'product_code', 'description',
            'unit', 'is_active', 'created_at', 'updated_at',
            'total_targets_count'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_total_targets_count(self, obj):
        return obj.route_target_details.count()


# ==================== ROUTE TARGET PRODUCT DETAIL SERIALIZERS ====================

class RouteTargetProductDetailSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.product_name', read_only=True)
    product_code = serializers.CharField(source='product.product_code', read_only=True)
    product_unit = serializers.CharField(source='product.unit', read_only=True)
    achievement_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = RouteTargetProductDetail
        fields = [
            'id', 'product', 'product_name', 'product_code', 'product_unit',
            'target_quantity', 'achieved_quantity', 'unit_price',
            'achievement_percentage', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


# ==================== ROUTE TARGET PERIOD SERIALIZERS ====================

class RouteTargetPeriodSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    employee_id_display = serializers.SerializerMethodField()
    route_name = serializers.CharField(source='route.route_name', read_only=True)
    route_origin = serializers.CharField(source='route.origin', read_only=True)
    route_destination = serializers.CharField(source='route.destination', read_only=True)
    route_code = serializers.CharField(source='route.route_code', read_only=True)
    assigned_by_name = serializers.SerializerMethodField()
    period_display = serializers.ReadOnlyField()
    duration_days = serializers.ReadOnlyField()
    achievement_percentage_boxes = serializers.ReadOnlyField()
    achievement_percentage_amount = serializers.ReadOnlyField()
    product_details = RouteTargetProductDetailSerializer(many=True, required=False)
    
    class Meta:
        model = RouteTargetPeriod
        fields = [
            'id', 'employee', 'employee_name', 'employee_id_display',
            'start_date', 'end_date', 'period_display', 'duration_days',
            'route', 'route_name', 'route_origin', 'route_destination', 'route_code',
            'target_boxes', 'target_amount',
            'achieved_boxes', 'achieved_amount',
            'achievement_percentage_boxes', 'achievement_percentage_amount',
            'notes', 'is_active',
            'assigned_by', 'assigned_by_name', 'assigned_at',
            'created_at', 'updated_at',
            'product_details'
        ]
        read_only_fields = ['assigned_at', 'created_at', 'updated_at']
    
    def get_employee_name(self, obj):
        return obj.employee.get_full_name() if obj.employee else None
    
    def get_employee_id_display(self, obj):
        return obj.employee.employee_id if obj.employee else None
    
    def get_assigned_by_name(self, obj):
        if obj.assigned_by:
            return getattr(obj.assigned_by, 'name', obj.assigned_by.email)
        return None
    
    def create(self, validated_data):
        product_details_data = validated_data.pop('product_details', [])
        route_target = RouteTargetPeriod.objects.create(**validated_data)
        
        # Create product details
        for product_detail_data in product_details_data:
            RouteTargetProductDetail.objects.create(
                route_target_period=route_target,
                **product_detail_data
            )
        
        return route_target
    
    def update(self, instance, validated_data):
        product_details_data = validated_data.pop('product_details', None)
        
        # Update main fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update product details if provided
        if product_details_data is not None:
            # Delete existing product details
            instance.product_details.all().delete()
            
            # Create new product details
            for product_detail_data in product_details_data:
                RouteTargetProductDetail.objects.create(
                    route_target_period=instance,
                    **product_detail_data
                )
        
        return instance


class RouteTargetPeriodDetailSerializer(RouteTargetPeriodSerializer):
    """Extended serializer with full product details"""
    pass


# ==================== CALL DAILY TARGET SERIALIZERS ====================

class CallDailyTargetSerializer(serializers.ModelSerializer):
    day_name = serializers.ReadOnlyField()
    achievement_percentage = serializers.ReadOnlyField()
    productivity_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = CallDailyTarget
        fields = [
            'id', 'call_target_period', 'target_date', 'day_name',
            'target_calls', 'achieved_calls', 'productive_calls',
            'order_received', 'order_amount',
            'achievement_percentage', 'productivity_percentage',
            'remarks', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


# ==================== CALL TARGET PERIOD SERIALIZERS ====================

class CallTargetPeriodSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    employee_id_display = serializers.SerializerMethodField()
    assigned_by_name = serializers.SerializerMethodField()
    period_display = serializers.ReadOnlyField()
    duration_days = serializers.ReadOnlyField()
    total_target_calls = serializers.ReadOnlyField()
    total_achieved_calls = serializers.ReadOnlyField()
    achievement_percentage = serializers.ReadOnlyField()
    daily_targets = CallDailyTargetSerializer(many=True, required=False)
    
    class Meta:
        model = CallTargetPeriod
        fields = [
            'id', 'employee', 'employee_name', 'employee_id_display',
            'start_date', 'end_date', 'period_display', 'duration_days',
            'total_target_calls', 'total_achieved_calls', 'achievement_percentage',
            'notes', 'is_active',
            'assigned_by', 'assigned_by_name', 'assigned_at',
            'created_at', 'updated_at',
            'daily_targets'
        ]
        read_only_fields = ['assigned_at', 'created_at', 'updated_at']
    
    def get_employee_name(self, obj):
        return obj.employee.get_full_name() if obj.employee else None
    
    def get_employee_id_display(self, obj):
        return obj.employee.employee_id if obj.employee else None
    
    def get_assigned_by_name(self, obj):
        if obj.assigned_by:
            return getattr(obj.assigned_by, 'name', obj.assigned_by.email)
        return None
    
    def create(self, validated_data):
        daily_targets_data = validated_data.pop('daily_targets', [])
        call_target = CallTargetPeriod.objects.create(**validated_data)
        
        # If daily targets not provided, auto-generate them
        if not daily_targets_data:
            current_date = call_target.start_date
            while current_date <= call_target.end_date:
                CallDailyTarget.objects.create(
                    call_target_period=call_target,
                    target_date=current_date,
                    target_calls=0  # Default, can be updated later
                )
                current_date += timedelta(days=1)
        else:
            # Create provided daily targets
            for daily_target_data in daily_targets_data:
                CallDailyTarget.objects.create(
                    call_target_period=call_target,
                    **daily_target_data
                )
        
        return call_target
    
    def update(self, instance, validated_data):
        daily_targets_data = validated_data.pop('daily_targets', None)
        
        # Update main fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update daily targets if provided
        if daily_targets_data is not None:
            # Delete existing daily targets
            instance.daily_targets.all().delete()
            
            # Create new daily targets
            for daily_target_data in daily_targets_data:
                CallDailyTarget.objects.create(
                    call_target_period=instance,
                    **daily_target_data
                )
        
        return instance


class CallTargetPeriodDetailSerializer(CallTargetPeriodSerializer):
    """Extended serializer with full daily target details"""
    pass


# ==================== ACHIEVEMENT LOG SERIALIZERS ====================

class TargetAchievementLogSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    employee_id_display = serializers.SerializerMethodField()
    recorded_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = TargetAchievementLog
        fields = [
            'id', 'log_type', 'employee', 'employee_name', 'employee_id_display',
            'route_target', 'call_daily_target',
            'achievement_date', 'achievement_value', 'remarks',
            'recorded_by', 'recorded_by_name', 'created_at'
        ]
        read_only_fields = ['created_at']
    
    def get_employee_name(self, obj):
        return obj.employee.get_full_name() if obj.employee else None
    
    def get_employee_id_display(self, obj):
        return obj.employee.employee_id if obj.employee else None
    
    def get_recorded_by_name(self, obj):
        if obj.recorded_by:
            return getattr(obj.recorded_by, 'name', obj.recorded_by.email)
        return None

# ==================== EMPLOYEE SPECIFIC SERIALIZERS ====================

class EmployeeRouteTargetSerializer(serializers.ModelSerializer):
    """Simplified serializer for employee's own route targets"""
    route_name = serializers.SerializerMethodField()
    route_origin = serializers.CharField(source='route.origin', read_only=True)
    route_destination = serializers.CharField(source='route.destination', read_only=True)
    route_code = serializers.CharField(source='route.route_code', read_only=True)
    period_display = serializers.ReadOnlyField()
    duration_days = serializers.ReadOnlyField()
    achievement_percentage_boxes = serializers.ReadOnlyField()
    achievement_percentage_amount = serializers.ReadOnlyField()
    product_details = RouteTargetProductDetailSerializer(many=True, read_only=True)
    
    class Meta:
        model = RouteTargetPeriod
        fields = [
            'id', 'start_date', 'end_date', 'period_display', 'duration_days',
            'route', 'route_name', 'route_origin', 'route_destination', 'route_code',
            'target_boxes', 'target_amount',
            'achieved_boxes', 'achieved_amount',
            'achievement_percentage_boxes', 'achievement_percentage_amount',
            'notes', 'is_active', 'product_details'
        ]
    
    def get_route_name(self, obj):
        return obj.route.route_name if obj.route else None


class EmployeeCallTargetSerializer(serializers.ModelSerializer):
    """Simplified serializer for employee's own call targets"""
    period_display = serializers.ReadOnlyField()
    duration_days = serializers.ReadOnlyField()
    total_target_calls = serializers.ReadOnlyField()
    total_achieved_calls = serializers.ReadOnlyField()
    achievement_percentage = serializers.ReadOnlyField()
    daily_targets = CallDailyTargetSerializer(many=True, read_only=True)
    
    class Meta:
        model = CallTargetPeriod
        fields = [
            'id', 'start_date', 'end_date', 'period_display', 'duration_days',
            'total_target_calls', 'total_achieved_calls', 'achievement_percentage',
            'notes', 'is_active', 'daily_targets'
        ]


class UpdateRouteAchievementSerializer(serializers.Serializer):
    """Serializer for updating route target achievements"""
    achieved_boxes = serializers.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=False,
        min_value=0
    )
    achieved_amount = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        required=False,
        min_value=0
    )
    product_achievements = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        help_text="List of {product_id, achieved_quantity}"
    )
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_product_achievements(self, value):
        """Validate product achievements structure"""
        for item in value:
            if 'product_id' not in item:
                raise serializers.ValidationError("Each product achievement must have 'product_id'")
            if 'achieved_quantity' not in item:
                raise serializers.ValidationError("Each product achievement must have 'achieved_quantity'")
            try:
                float(item['achieved_quantity'])
            except (ValueError, TypeError):
                raise serializers.ValidationError("achieved_quantity must be a valid number")
        return value


class UpdateCallDailyAchievementSerializer(serializers.Serializer):
    """Serializer for updating daily call achievements"""
    achieved_calls = serializers.IntegerField(required=False, min_value=0)
    productive_calls = serializers.IntegerField(required=False, min_value=0)
    order_received = serializers.IntegerField(required=False, min_value=0)
    order_amount = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        required=False,
        min_value=0
    )
    remarks = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        """Validate that productive calls <= achieved calls"""
        achieved = data.get('achieved_calls')
        productive = data.get('productive_calls')
        
        if achieved is not None and productive is not None:
            if productive > achieved:
                raise serializers.ValidationError({
                    'productive_calls': 'Productive calls cannot exceed total achieved calls'
                })
        
        return data