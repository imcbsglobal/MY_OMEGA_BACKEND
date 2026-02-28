from django.contrib import admin

# Register your models here.
# delivery_management/admin.py
from django.contrib import admin
from .models import Delivery, DeliveryProduct, DeliveryStop


class DeliveryProductInline(admin.TabularInline):
    """Inline for delivery products"""
    model = DeliveryProduct
    extra = 1
    fields = [
        'product', 
        'loaded_quantity', 
        'delivered_quantity', 
        'balance_quantity',
        'unit_price', 
        'total_amount',
        'notes'
    ]
    readonly_fields = ['balance_quantity', 'total_amount']


class DeliveryStopInline(admin.TabularInline):
    """Inline for delivery stops"""
    model = DeliveryStop
    extra = 0
    fields = [
        'stop_sequence',
        'customer_name',
        'customer_address',
        'planned_boxes',
        'delivered_boxes',
        'status',
        'actual_arrival'
    ]


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    """Admin for Delivery model"""
    list_display = [
        'delivery_number',
        'assigned_to',
        'employee',
        'vehicle',
        'route',
        'scheduled_date',
        'scheduled_time',
        'status',
        'total_loaded_boxes',
        'total_delivered_boxes',
        'total_balance_boxes',
        'collected_amount',
        'total_pending_amount',
        'delivery_efficiency_display',
        'created_at'
    ]
    
    list_filter = [
        'assigned_to',
        'status',
        'scheduled_date',
        'created_at',
        'employee',
        'vehicle',
        'route'
    ]
    
    search_fields = [
        'delivery_number',
        'assigned_to__email',
        'employee__employee_id',
        'employee__full_name',
        'vehicle__registration_number',
        'route__origin',
        'route__destination'
    ]
    
    readonly_fields = [
        'delivery_number',
        'created_at',
        'updated_at',
        'duration_minutes',
        'distance_traveled',
        'fuel_consumed',
        'delivery_efficiency'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'delivery_number',
                'employee',
                'assigned_to',
                'vehicle',
                'route',
                'status'
            )
        }),
        ('Schedule', {
            'fields': (
                'scheduled_date',
                'scheduled_time'
            )
        }),
        ('Start Details', {
            'fields': (
                'start_datetime',
                'odometer_start',
                'fuel_start',
                'start_notes'
            )
        }),
        ('End Details', {
            'fields': (
                'end_datetime',
                'odometer_end',
                'fuel_end',
                'end_notes'
            )
        }),
        ('Summary', {
            'fields': (
                'total_loaded_boxes',
                'total_delivered_boxes',
                'total_balance_boxes',
                'total_amount',
                'collected_amount',
                'total_pending_amount'
            )
        }),
        ('Calculated Metrics', {
            'fields': (
                'duration_minutes',
                'distance_traveled',
                'fuel_consumed',
                'delivery_efficiency'
            )
        }),
        ('Additional Info', {
            'fields': (
                'remarks',
                'created_by',
                'created_at',
                'updated_at',
                'completed_by'
            )
        }),
    )
    
    inlines = [DeliveryProductInline, DeliveryStopInline]
    
    def delivery_efficiency_display(self, obj):
        """Display efficiency as percentage"""
        return f"{obj.delivery_efficiency:.2f}%"
    delivery_efficiency_display.short_description = 'Efficiency'
    
    def save_model(self, request, obj, form, change):
        """Set created_by on creation"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(DeliveryProduct)
class DeliveryProductAdmin(admin.ModelAdmin):
    """Admin for DeliveryProduct model"""
    list_display = [
        'delivery',
        'product',
        'loaded_quantity',
        'delivered_quantity',
        'balance_quantity',
        'unit_price',
        'total_amount',
        'delivery_percentage_display'
    ]
    
    list_filter = [
        'delivery__status',
        'product',
        'delivery__scheduled_date'
    ]
    
    search_fields = [
        'delivery__delivery_number',
        'product__product_name',
        'product__product_code'
    ]
    
    readonly_fields = [
        'balance_quantity',
        'total_amount',
        'delivery_percentage'
    ]
    
    fieldsets = (
        ('References', {
            'fields': ('delivery', 'product')
        }),
        ('Quantities', {
            'fields': (
                'loaded_quantity',
                'delivered_quantity',
                'balance_quantity',
                'delivery_percentage'
            )
        }),
        ('Pricing', {
            'fields': (
                'unit_price',
                'total_amount'
            )
        }),
        ('Additional Info', {
            'fields': ('notes', 'created_at', 'updated_at')
        }),
    )
    
    def delivery_percentage_display(self, obj):
        """Display delivery percentage"""
        return f"{obj.delivery_percentage:.2f}%"
    delivery_percentage_display.short_description = 'Delivery %'


@admin.register(DeliveryStop)
class DeliveryStopAdmin(admin.ModelAdmin):
    """Admin for DeliveryStop model"""
    list_display = [
        'delivery',
        'stop_sequence',
        'customer_name',
        'status',
        'planned_boxes',
        'delivered_boxes',
        'balance_boxes',
        'collected_amount',
        'pending_amount',
        'actual_arrival',
        'stop_duration_display'
    ]
    
    list_filter = [
        'status',
        'delivery__scheduled_date',
        'actual_arrival'
    ]
    
    search_fields = [
        'delivery__delivery_number',
        'customer_name',
        'customer_address',
        'customer_phone'
    ]
    
    readonly_fields = [
        'balance_boxes',
        'pending_amount',
        'stop_duration',
        'is_completed',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Delivery & Sequence', {
            'fields': ('delivery', 'stop_sequence')
        }),
        ('Customer Information', {
            'fields': (
                'customer_name',
                'customer_address',
                'customer_phone'
            )
        }),
        ('Planned Details', {
            'fields': (
                'planned_boxes',
                'planned_amount',
                'estimated_arrival'
            )
        }),
        ('Actual Details', {
            'fields': (
                'delivered_boxes',
                'balance_boxes',
                'collected_amount',
                'pending_amount',
                'actual_arrival',
                'departure_time',
                'stop_duration'
            )
        }),
        ('Status & Notes', {
            'fields': (
                'status',
                'notes',
                'failure_reason',
                'is_completed'
            )
        }),
        ('Proof', {
            'fields': (
                'signature_image',
                'proof_image'
            )
        }),
        ('Location', {
            'fields': (
                'latitude',
                'longitude'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def stop_duration_display(self, obj):
        """Display stop duration"""
        duration = obj.stop_duration
        if duration:
            return f"{duration} mins"
        return "-"
    stop_duration_display.short_description = 'Duration'