from django.contrib import admin

# Register your models here.
# vehicle_management/admin.py
from django.contrib import admin
from .models import Vehicle, Trip, VehicleChallan


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = [
        'registration_number',
        'vehicle_name',
        'company',
        'vehicle_type',
        'fuel_type',
        'current_odometer',
        'is_active',
        'insurance_expiry_date',
        'next_service_date',
        'created_at',
    ]
    
    list_filter = [
        'is_active',
        'vehicle_type',
        'fuel_type',
        'created_at',
    ]
    
    search_fields = [
        'registration_number',
        'vehicle_name',
        'company',
        'owner_name',
        'chassis_number',
        'engine_number',
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'vehicle_name',
                'company',
                'registration_number',
                'vehicle_type',
                'fuel_type',
                'color',
                'manufacturing_year',
                'seating_capacity',
                'photo',
            )
        }),
        ('Ownership & Insurance', {
            'fields': (
                'owner_name',
                'insurance_number',
                'insurance_expiry_date',
            )
        }),
        ('Maintenance', {
            'fields': (
                'last_service_date',
                'next_service_date',
                'current_odometer',
            )
        }),
        ('Technical Details', {
            'fields': (
                'chassis_number',
                'engine_number',
            )
        }),
        ('Additional Information', {
            'fields': (
                'notes',
                'is_active',
            )
        }),
        ('Audit Information', {
            'fields': (
                'created_by',
                'created_at',
                'updated_at',
            )
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'vehicle',
        'employee',
        'date',
        'start_time',
        'end_time',
        'client_name',
        'distance_km',
        'fuel_cost',
        'status',
        'created_at',
    ]
    
    list_filter = [
        'status',
        'date',
        'created_at',
    ]
    
    search_fields = [
        'vehicle__registration_number',
        'vehicle__vehicle_name',
        'employee__email',
        'client_name',
        'purpose',
    ]
    
    readonly_fields = [
        'distance_km',
        'duration_hours',
        'created_at',
        'updated_at',
        'completed_at',
    ]
    
    fieldsets = (
        ('Trip Basic Information', {
            'fields': (
                'vehicle',
                'employee',
                'date',
                'start_time',
                'time_period',
            )
        }),
        ('Client & Purpose', {
            'fields': (
                'client_name',
                'purpose',
            )
        }),
        ('Trip Start Details', {
            'fields': (
                'fuel_cost',
                'odometer_start',
                'odometer_start_image',
            )
        }),
        ('Trip End Details', {
            'fields': (
                'end_time',
                'odometer_end',
                'odometer_end_image',
            )
        }),
        ('Calculated Values', {
            'fields': (
                'distance_km',
                'duration_hours',
            )
        }),
        ('Status & Approval', {
            'fields': (
                'status',
                'approved_by',
                'approved_at',
                'admin_notes',
            )
        }),
        ('Audit Information', {
            'fields': (
                'created_at',
                'updated_at',
                'completed_at',
            )
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Make certain fields readonly after trip is approved"""
        readonly = list(self.readonly_fields)
        if obj and obj.status == 'approved':
            readonly.extend([
                'vehicle',
                'employee',
                'date',
                'start_time',
                'fuel_cost',
                'odometer_start',
                'odometer_end',
            ])
        return readonly


@admin.register(VehicleChallan)
class VehicleChallanAdmin(admin.ModelAdmin):
    list_display = [
        'challan_number',
        'vehicle',
        'owner',
        'detail_date',
        'challan_date',
        'offence_type',
        'location',
        'fine_amount',
        'payment_status',
        'payment_date',
        'created_at',
    ]
    
    list_filter = [
        'payment_status',
        'challan_date',
        'detail_date',
        'created_at',
    ]
    
    search_fields = [
        'challan_number',
        'vehicle__registration_number',
        'vehicle__vehicle_name',
        'owner__email',
        'offence_type',
        'location',
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'days_since_challan',
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'vehicle',
                'owner',
            )
        }),
        ('Challan Details', {
            'fields': (
                'detail_date',
                'challan_number',
                'challan_date',
            )
        }),
        ('Violation Details', {
            'fields': (
                'offence_type',
                'location',
            )
        }),
        ('Fine Details', {
            'fields': (
                'fine_amount',
                'payment_status',
                'payment_date',
            )
        }),
        ('Additional Information', {
            'fields': (
                'remarks',
            )
        }),
        ('Attachments', {
            'fields': (
                'challan_document',
                'payment_receipt',
            )
        }),
        ('Audit Information', {
            'fields': (
                'created_by',
                'created_at',
                'updated_at',
                'days_since_challan',
            )
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_readonly_fields(self, request, obj=None):
        """Make certain fields readonly after payment is made"""
        readonly = list(self.readonly_fields)
        if obj and obj.payment_status == 'paid':
            readonly.extend([
                'vehicle',
                'owner',
                'detail_date',
                'challan_number',
                'challan_date',
                'offence_type',
                'location',
                'fine_amount',
            ])
        return readonly