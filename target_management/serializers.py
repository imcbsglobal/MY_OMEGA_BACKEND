# target_management/serializers.py - FIXED VERSION
from rest_framework import serializers
from .models import (
    Route, Product, RouteTargetPeriod, RouteTargetProductDetail,
    CallTargetPeriod, CallDailyTarget, TargetAchievementLog, TargetParameters,
    MarketingTargetPeriod, MarketingTargetParameter
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
        # ...existing code...
        return data

# --- Marketing Target Serializers ---
class MarketingTargetParameterSerializer(serializers.ModelSerializer):
    parameter_type_display = serializers.CharField(source='get_parameter_type_display', read_only=True)
    achievement_percentage = serializers.ReadOnlyField()

    class Meta:
        model = MarketingTargetParameter
        fields = [
            'id', 'parameter_type', 'parameter_type_display',
            'parameter_label', 'target_value', 'incentive_value', 'achieved_value', 'achievement_percentage',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

class MarketingTargetPeriodSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    employee_email = serializers.SerializerMethodField()
    employee_id_display = serializers.SerializerMethodField()
    # Allow nested create/update of marketing parameters (writeable)
    target_parameters = MarketingTargetParameterSerializer(many=True, required=False)

    class Meta:
        model = MarketingTargetPeriod
        fields = [
            'id', 'employee', 'employee_name', 'employee_email', 'employee_id_display',
            'start_date', 'end_date', 'is_active',
            'assigned_by', 'assigned_at', 'created_at', 'updated_at',
            'target_parameters'
        ]
        read_only_fields = ['assigned_at', 'created_at', 'updated_at']

    def get_employee_name(self, obj):
        return obj.employee.get_full_name() if obj.employee else None

    def get_employee_email(self, obj):
        if obj.employee and obj.employee.user:
            return obj.employee.user.email
        return None

    def get_employee_id_display(self, obj):
        return obj.employee.employee_id if obj.employee else None

    def create(self, validated_data):
        target_parameters_data = validated_data.pop('target_parameters', [])
        if self.context and self.context.get('request') and self.context['request'].user.is_authenticated:
            assigned_by = self.context['request'].user
        else:
            assigned_by = None

        period = MarketingTargetPeriod.objects.create(assigned_by=assigned_by, **validated_data)

        for param_data in target_parameters_data:
            MarketingTargetParameter.objects.create(marketing_target_period=period, **param_data)

        return period

    def update(self, instance, validated_data):
        target_parameters_data = validated_data.pop('target_parameters', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # If parameters provided, update existing ones where possible, else create.
        if target_parameters_data is not None:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"MarketingTargetPeriod.update: updating {len(target_parameters_data)} parameters for period {instance.pk}")

            # Map existing parameters by id and by parameter_type for flexible matching
            existing_by_id = {p.id: p for p in instance.target_parameters.all()}
            existing_by_type = {p.parameter_type: p for p in instance.target_parameters.all()}

            seen_ids = set()

            for param_data in target_parameters_data:
                # Normalize keys (allow strings for decimals)
                param_id = param_data.get('id')
                param_type = param_data.get('parameter_type')

                # Try update by id first
                if param_id and param_id in existing_by_id:
                    obj = existing_by_id[param_id]
                    # Update allowed fields
                    for fld in ('parameter_type', 'parameter_label', 'target_value', 'incentive_value', 'achieved_value'):
                        if fld in param_data:
                            setattr(obj, fld, param_data[fld])
                    obj.save()
                    seen_ids.add(obj.id)
                    logger.info(f"Updated MarketingTargetParameter id={obj.id}")
                    continue

                # Next try to match by parameter_type
                if param_type and param_type in existing_by_type:
                    obj = existing_by_type[param_type]
                    for fld in ('parameter_label', 'target_value', 'incentive_value', 'achieved_value'):
                        if fld in param_data:
                            setattr(obj, fld, param_data[fld])
                    obj.save()
                    seen_ids.add(obj.id)
                    logger.info(f"Updated MarketingTargetParameter by type={param_type} id={obj.id}")
                    continue

                # Otherwise create new parameter (do not pass id)
                create_data = {k: v for k, v in param_data.items() if k != 'id'}
                new_obj = MarketingTargetParameter.objects.create(marketing_target_period=instance, **create_data)
                seen_ids.add(new_obj.id)
                logger.info(f"Created MarketingTargetParameter id={new_obj.id} type={new_obj.parameter_type}")

            # Optionally remove parameters not present in incoming data (keep behavior conservative)
            # Remove if you want strict replace semantics; currently we keep existing ones not referenced.

        return instance

    def to_representation(self, instance):
        """
        Ensure we always return the four canonical marketing parameters in the response,
        filling missing ones with zero/default values so frontend can render editable rows.
        """
        data = super().to_representation(instance)
        param_types = [
            ('shops_visited', 'No. of Shops Visited'),
            ('total_boxes', 'Total Boxes'),
            ('new_shops', 'New Shops'),
            ('focus_category', 'Focus Category')
        ]

        # existing params from serialized data (list of dicts)
        existing = {p.get('parameter_type'): p for p in data.get('target_parameters') or []}
        out = []
        for key, label in param_types:
            p = existing.get(key)
            if p:
                out.append(p)
            else:
                out.append({
                    'id': None,
                    'parameter_type': key,
                    'parameter_type_display': label,
                    'parameter_label': label,
                    'target_value': 0,
                    'incentive_value': 0,
                    'achieved_value': 0,
                    'achievement_percentage': 0,
                    'created_at': None,
                    'updated_at': None,
                })

        data['target_parameters'] = out
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


# ==================== TARGET PARAMETERS SERIALIZERS ====================

class TargetParametersSerializer(serializers.ModelSerializer):
    parameter_type_display = serializers.CharField(source='get_parameter_type_display', read_only=True)
    achievement_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = TargetParameters
        fields = [
            'id', 'parameter_type', 'parameter_type_display',
            'target_value', 'incentive_value', 'achieved_value',
            'achievement_percentage', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


# ==================== ROUTE TARGET PERIOD SERIALIZERS ====================

class RouteTargetPeriodSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()
    employee_email = serializers.SerializerMethodField()
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
    target_parameters = TargetParametersSerializer(many=True, required=False)
    
    class Meta:
        model = RouteTargetPeriod
        fields = [
            'id', 'employee', 'employee_name', 'employee_email', 'employee_id_display',
            'start_date', 'end_date', 'period_display', 'duration_days',
            'route', 'route_name', 'route_origin', 'route_destination', 'route_code',
            'target_boxes', 'target_amount',
            'achieved_boxes', 'achieved_amount',
            'achievement_percentage_boxes', 'achievement_percentage_amount',
            'notes', 'is_active',
            'assigned_by', 'assigned_by_name', 'assigned_at',
            'created_at', 'updated_at',
            'product_details', 'target_parameters'
        ]
        read_only_fields = ['assigned_at', 'created_at', 'updated_at']
    
    def get_employee_name(self, obj):
        return obj.employee.get_full_name() if obj.employee else None
    
    def get_employee_email(self, obj):
        if obj.employee and obj.employee.user:
            return obj.employee.user.email
        return None
    
    def get_employee_id_display(self, obj):
        return obj.employee.employee_id if obj.employee else None
    
    def get_assigned_by_name(self, obj):
        if obj.assigned_by:
            return getattr(obj.assigned_by, 'name', obj.assigned_by.email)
        return None
    
    def create(self, validated_data):
        product_details_data = validated_data.pop('product_details', [])
        target_parameters_data = validated_data.pop('target_parameters', [])
        route_target = RouteTargetPeriod.objects.create(**validated_data)
        
        # Create product details
        for product_detail_data in product_details_data:
            RouteTargetProductDetail.objects.create(
                route_target_period=route_target,
                **product_detail_data
            )
        
        # Create target parameters
        for parameter_data in target_parameters_data:
            TargetParameters.objects.create(
                route_target_period=route_target,
                **parameter_data
            )
        
        return route_target
    
    def update(self, instance, validated_data):
        product_details_data = validated_data.pop('product_details', None)
        target_parameters_data = validated_data.pop('target_parameters', None)
        
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
        
        # Update target parameters if provided
        if target_parameters_data is not None:
            # Delete existing target parameters
            instance.target_parameters.all().delete()
            
            # Create new target parameters
            for parameter_data in target_parameters_data:
                TargetParameters.objects.create(
                    route_target_period=instance,
                    **parameter_data
                )
        
        return instance


class RouteTargetPeriodDetailSerializer(RouteTargetPeriodSerializer):
    """Extended serializer with full product details and target parameters"""
    target_parameters = TargetParametersSerializer(many=True, read_only=True)
    product_details = RouteTargetProductDetailSerializer(many=True, read_only=True)
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
        # call_target_period is read-only: when used nested inside
        # CallTargetPeriodSerializer the parent assigns it via
        #   CallDailyTarget.objects.create(call_target_period=call_target, ...)
        # Leaving it writable makes DRF require it in every nested item sent
        # from the frontend (which doesn't know the ID yet) → 400 Bad Request.
        read_only_fields = ['call_target_period', 'created_at', 'updated_at']


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
        
        # Debug logging
        print(f"\n=== CREATING CALL TARGET ===")
        print(f"Employee: {validated_data.get('employee')}")
        print(f"Date range: {validated_data.get('start_date')} to {validated_data.get('end_date')}")
        print(f"Received {len(daily_targets_data)} daily targets")
        
        # Log first few daily targets
        for i, dt in enumerate(daily_targets_data[:3]):
            print(f"Daily target {i+1}: date={dt.get('target_date')}, calls={dt.get('target_calls')} (type: {type(dt.get('target_calls'))})")
        
        call_target = CallTargetPeriod.objects.create(**validated_data)
        
        # Create daily targets - ALWAYS create from provided data
        if daily_targets_data:
            print(f"Creating {len(daily_targets_data)} daily targets from provided data...")
            created_count = 0
            for daily_target_data in daily_targets_data:
                target_calls = daily_target_data.get('target_calls', 0)
                print(f"Creating daily target for {daily_target_data.get('target_date')} with {target_calls} calls")
                
                daily_target = CallDailyTarget.objects.create(
                    call_target_period=call_target,
                    target_date=daily_target_data.get('target_date'),
                    target_calls=int(target_calls) if target_calls else 0,
                    achieved_calls=int(daily_target_data.get('achieved_calls', 0)),
                    productive_calls=int(daily_target_data.get('productive_calls', 0)),
                    order_received=int(daily_target_data.get('order_received', 0)),
                    order_amount=float(daily_target_data.get('order_amount', 0)),
                    remarks=daily_target_data.get('remarks', '')
                )
                created_count += 1
                print(f"✅ Created daily target ID {daily_target.id} with {daily_target.target_calls} calls")
            
            print(f"Successfully created {created_count} daily targets")
        else:
            print("⚠️ No daily targets provided, auto-generating with default values")
            current_date = call_target.start_date
            while current_date <= call_target.end_date:
                day_of_week = current_date.weekday()  # Monday=0, Sunday=6
                default_calls = 20 if day_of_week in [5, 6] else 30  # Lower on weekends
                
                daily_target = CallDailyTarget.objects.create(
                    call_target_period=call_target,
                    target_date=current_date,
                    target_calls=default_calls
                )
                print(f"Auto-created daily target for {current_date} with {default_calls} calls")
                current_date += timedelta(days=1)
        
        # Verify the creation
        total_targets = call_target.total_target_calls
        print(f"✅ Call target created! Total target calls: {total_targets}")
        print(f"=== END CREATION ===")
        
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