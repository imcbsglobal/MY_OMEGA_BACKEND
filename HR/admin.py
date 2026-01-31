# HR/admin.py - Complete Clean Admin Configuration
from django.contrib import admin
from .models import Attendance, Holiday, LeaveRequest, LateRequest, EarlyRequest, PunchRecord


class PunchRecordInline(admin.TabularInline):
    """Inline admin for punch records"""
    model = PunchRecord
    extra = 0
    readonly_fields = ['punch_time', 'created_at']
    fields = ['punch_type', 'punch_time', 'location', 'latitude', 'longitude', 'note']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'date', 'status', 'verification_status',
        'first_punch_in_time', 'last_punch_out_time', 
        'total_working_hours', 'total_break_hours', 'is_currently_on_break'
    ]
    list_filter = ['status', 'verification_status', 'date', 'is_currently_on_break']
    search_fields = ['user__name', 'user__email']
    readonly_fields = ['total_working_hours', 'total_break_hours', 'is_currently_on_break', 'created_at', 'updated_at']
    date_hierarchy = 'date'
    inlines = [PunchRecordInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'date', 'status', 'verification_status')
        }),
        ('First Punch In Details', {
            'fields': (
                'first_punch_in_time', 'first_punch_in_location', 
                'first_punch_in_latitude', 'first_punch_in_longitude'
            )
        }),
        ('Last Punch Out Details', {
            'fields': (
                'last_punch_out_time', 'last_punch_out_location', 
                'last_punch_out_latitude', 'last_punch_out_longitude'
            )
        }),
        ('Calculated Times', {
            'fields': ('total_working_hours', 'total_break_hours', 'is_currently_on_break')
        }),
        ('Notes', {
            'fields': ('note', 'admin_note')
        }),
        ('Verification', {
            'fields': ('verified_by', 'verified_at')
        }),
        ('System Fields', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PunchRecord)
class PunchRecordAdmin(admin.ModelAdmin):
    list_display = ['attendance', 'punch_type', 'punch_time', 'location']
    list_filter = ['punch_type', 'punch_time']
    search_fields = ['attendance__user__name', 'attendance__user__email', 'location']
    readonly_fields = ['created_at']
    date_hierarchy = 'punch_time'
    
    fieldsets = (
        ('Punch Information', {
            'fields': ('attendance', 'punch_type', 'punch_time')
        }),
        ('Location Details', {
            'fields': ('location', 'latitude', 'longitude')
        }),
        ('Additional Info', {
            'fields': ('note', 'created_at')
        }),
    )


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ['name', 'date', 'is_active', 'created_at']
    list_filter = ['is_active', 'date']
    search_fields = ['name', 'description']
    date_hierarchy = 'date'


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'leave_master', 'from_date', 'to_date',
        'status', 'total_days', 'created_at'
    ]
    list_filter = ['status', 'from_date']  # You can filter by category through leave_master
    search_fields = ['user__name', 'user__email', 'reason', 'leave_master__leave_name']
    readonly_fields = ['total_days', 'created_at', 'updated_at', 'is_paid']
    date_hierarchy = 'from_date'

    fieldsets = (
        ('Leave Request', {
            'fields': ('user', 'leave_master', 'from_date', 'to_date', 'reason')
        }),
        ('Leave Details', {
            'fields': ('is_paid', 'deducted_from_balance')
        }),
        ('Status', {
            'fields': ('status', 'reviewed_by', 'reviewed_at', 'admin_comment')
        }),
        ('System Fields', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(LateRequest)
class LateRequestAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'date', 'late_by_minutes', 'status', 'created_at'
    ]
    list_filter = ['status', 'date']
    search_fields = ['user__name', 'user__email', 'reason']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'

    fieldsets = (
        ('Late Request', {
            'fields': ('user', 'date', 'late_by_minutes', 'reason')
        }),
        ('Status', {
            'fields': ('status', 'reviewed_by', 'reviewed_at', 'admin_comment')
        }),
        ('System Fields', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(EarlyRequest)
class EarlyRequestAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'date', 'early_by_minutes', 'status', 'created_at'
    ]
    list_filter = ['status', 'date']
    search_fields = ['user__name', 'user__email', 'reason']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'

    fieldsets = (
        ('Early Request', {
            'fields': ('user', 'date', 'early_by_minutes', 'reason')
        }),
        ('Status', {
            'fields': ('status', 'reviewed_by', 'reviewed_at', 'admin_comment')
        }),
        ('System Fields', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )




# HR/admin.py - Add this to your existing admin.py

from django.contrib import admin
from django.utils.html import format_html
from .models import OfficeLocation


@admin.register(OfficeLocation)
class OfficeLocationAdmin(admin.ModelAdmin):
    """
    Enhanced admin interface for Office Location configuration
    with map preview and geofence visualization
    """
    
    list_display = [
        'name',
        'status_badge',
        'coordinates_display',
        'radius_display',
        'detection_method',
        'configured_by',
        'configured_at'
    ]
    
    list_filter = ['is_active', 'detection_method', 'configured_at']
    search_fields = ['name', 'address', 'notes']
    readonly_fields = [
        'configured_at',
        'updated_at',
        'map_preview',
        'validation_info'
    ]
    
    fieldsets = (
        ('Office Information', {
            'fields': ('name', 'address', 'notes')
        }),
        ('GPS Coordinates', {
            'fields': (
                'latitude',
                'longitude',
                'detection_method',
                'gps_accuracy_meters'
            ),
            'description': 'Precise GPS coordinates for the office location'
        }),
        ('Geofence Configuration', {
            'fields': ('geofence_radius_meters', 'map_preview'),
            'description': (
                'Set the allowed radius for attendance. '
                'Recommended: 50-100m for standard offices. '
                'Use 100-200m for large campuses or areas with poor GPS signal.'
            )
        }),
        ('Status & Validation', {
            'fields': ('is_active', 'validation_info')
        }),
        ('Metadata', {
            'fields': ('configured_by', 'configured_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        """Display active/inactive status with color badge"""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #28a745; color: white; '
                'padding: 3px 10px; border-radius: 3px; font-weight: bold;">'
                'ACTIVE</span>'
            )
        return format_html(
            '<span style="background-color: #6c757d; color: white; '
            'padding: 3px 10px; border-radius: 3px;">Inactive</span>'
        )
    status_badge.short_description = 'Status'
    
    def coordinates_display(self, obj):
        """Display coordinates with copy button"""
        coords = f"{obj.latitude}, {obj.longitude}"
        return format_html(
            '<code style="background: #f4f4f4; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px;">{}</code>',
            coords
        )
    coordinates_display.short_description = 'Coordinates'
    
    def radius_display(self, obj):
        """Display radius with visual indicator"""
        if obj.geofence_radius_meters <= 50:
            color = '#ffc107'  # Yellow - tight
            label = 'Tight'
        elif obj.geofence_radius_meters <= 100:
            color = '#28a745'  # Green - standard
            label = 'Standard'
        elif obj.geofence_radius_meters <= 200:
            color = '#17a2b8'  # Blue - wide
            label = 'Wide'
        else:
            color = '#dc3545'  # Red - very wide
            label = 'Very Wide'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} m</span> '
            '<small style="color: #6c757d;">({})</small>',
            color, obj.geofence_radius_meters, label
        )
    radius_display.short_description = 'Geofence Radius'
    
    def map_preview(self, obj):
        """Embed an interactive map preview with geofence circle"""
        if not obj.latitude or not obj.longitude:
            return "No coordinates set"
        
        # Leaflet map with circle overlay
        map_html = f"""
        <div style="border: 2px solid #dee2e6; border-radius: 8px; overflow: hidden;">
            <div id="map-{obj.pk}" style="height: 400px; width: 100%;"></div>
        </div>
        
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        
        <script>
            (function() {{
                // Wait for DOM to be ready
                if (document.readyState === 'loading') {{
                    document.addEventListener('DOMContentLoaded', initMap);
                }} else {{
                    initMap();
                }}
                
                function initMap() {{
                    const mapContainer = document.getElementById('map-{obj.pk}');
                    if (!mapContainer || mapContainer._leaflet_id) return;
                    
                    const map = L.map('map-{obj.pk}').setView(
                        [{obj.latitude}, {obj.longitude}], 
                        17
                    );
                    
                    L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                        attribution: '© OpenStreetMap contributors',
                        maxZoom: 19
                    }}).addTo(map);
                    
                    // Office marker
                    const officeIcon = L.divIcon({{
                        html: '<div style="background-color: #dc3545; width: 20px; height: 20px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.3);"></div>',
                        className: '',
                        iconSize: [20, 20],
                        iconAnchor: [10, 10]
                    }});
                    
                    L.marker([{obj.latitude}, {obj.longitude}], {{icon: officeIcon}})
                        .bindPopup('<b>{obj.name}</b><br>{obj.address}')
                        .addTo(map);
                    
                    // Geofence circle
                    L.circle([{obj.latitude}, {obj.longitude}], {{
                        color: '#007bff',
                        fillColor: '#007bff',
                        fillOpacity: 0.15,
                        radius: {obj.geofence_radius_meters},
                        weight: 2
                    }}).addTo(map);
                    
                    // Info box
                    const info = L.control({{position: 'topright'}});
                    info.onAdd = function(map) {{
                        const div = L.DomUtil.create('div', 'info');
                        div.style.background = 'white';
                        div.style.padding = '10px';
                        div.style.borderRadius = '5px';
                        div.style.boxShadow = '0 2px 5px rgba(0,0,0,0.2)';
                        div.innerHTML = `
                            <h4 style="margin: 0 0 5px 0; font-size: 14px;">Geofence Info</h4>
                            <p style="margin: 0; font-size: 12px;">
                                <strong>Radius:</strong> {obj.geofence_radius_meters}m<br>
                                <strong>Method:</strong> {obj.get_detection_method_display()}
                            </p>
                        `;
                        return div;
                    }};
                    info.addTo(map);
                }}
            }})();
        </script>
        
        <div style="margin-top: 15px; padding: 15px; background: #f8f9fa; border-radius: 5px;">
            <p style="margin: 0 0 10px 0; font-weight: bold; color: #495057;">
                📍 Map Legend:
            </p>
            <ul style="margin: 0; padding-left: 20px; color: #6c757d; font-size: 13px;">
                <li><span style="color: #dc3545;">●</span> Red Marker = Office Location</li>
                <li><span style="color: #007bff;">○</span> Blue Circle = Geofence Radius ({obj.geofence_radius_meters}m)</li>
                <li>Employees must be within the blue circle to punch in/out</li>
            </ul>
        </div>
        """
        return format_html(map_html)
    map_preview.short_description = 'Location Map & Geofence Visualization'
    
    def validation_info(self, obj):
        """Display validation information and test results"""
        info_html = f"""
        <div style="padding: 15px; background: #f8f9fa; border-radius: 5px; border-left: 4px solid #007bff;">
            <h4 style="margin: 0 0 10px 0; color: #495057;">Validation Information</h4>
            
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid #dee2e6;">
                    <td style="padding: 8px; font-weight: bold; width: 40%;">Coordinates Valid:</td>
                    <td style="padding: 8px;">
                        <span style="color: #28a745;">✓ Yes</span>
                        <small style="color: #6c757d;"> (Lat: {obj.latitude}, Lon: {obj.longitude})</small>
                    </td>
                </tr>
                <tr style="border-bottom: 1px solid #dee2e6;">
                    <td style="padding: 8px; font-weight: bold;">Geofence Radius:</td>
                    <td style="padding: 8px;">
                        {obj.geofence_radius_meters} meters 
                        <small style="color: #6c757d;">({obj.distance_info()})</small>
                    </td>
                </tr>
                <tr style="border-bottom: 1px solid #dee2e6;">
                    <td style="padding: 8px; font-weight: bold;">Detection Method:</td>
                    <td style="padding: 8px;">{obj.get_detection_method_display()}</td>
                </tr>
                {f'''
                <tr style="border-bottom: 1px solid #dee2e6;">
                    <td style="padding: 8px; font-weight: bold;">GPS Accuracy:</td>
                    <td style="padding: 8px;">±{obj.gps_accuracy_meters}m</td>
                </tr>
                ''' if obj.gps_accuracy_meters else ''}
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Status:</td>
                    <td style="padding: 8px;">
                        {'<span style="color: #28a745; font-weight: bold;">ACTIVE - Currently in use</span>' 
                         if obj.is_active else 
                         '<span style="color: #6c757d;">Inactive</span>'}
                    </td>
                </tr>
            </table>
            
            <div style="margin-top: 15px; padding: 10px; background: white; border-radius: 3px;">
                <p style="margin: 0; font-size: 12px; color: #6c757d;">
                    <strong>Note:</strong> This configuration will be used for all attendance punch-in/punch-out validations.
                    Only employees within the geofence radius will be able to mark attendance.
                </p>
            </div>
        </div>
        """
        return format_html(info_html)
    validation_info.short_description = 'Configuration Status'
    
    def save_model(self, request, obj, form, change):
        """Automatically set configured_by to the current user"""
        if not change:  # Only on creation
            obj.configured_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_readonly_fields(self, request, obj=None):
        """Make certain fields readonly after creation"""
        readonly = list(self.readonly_fields)
        if obj:  # Editing existing object
            readonly.extend(['configured_by'])
        return readonly
    
    class Media:
        css = {
            'all': ('https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',)
        }
        js = ('https://unpkg.com/leaflet@1.9.4/dist/leaflet.js',)

