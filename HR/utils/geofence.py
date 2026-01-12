# HR/utils/geofence.py - Enhanced with optional admin bypass
from django.conf import settings
from .geolocation import haversine_distance

def validate_office_geofence(user_lat, user_lon, user=None):
    """
    Validates if user is within office geofence radius.
    
    Args:
        user_lat (float): User's latitude
        user_lon (float): User's longitude
        user (AppUser, optional): User object for admin bypass
    
    Returns:
        tuple: (allowed: bool, distance_in_meters: float)
    """
    # Calculate actual distance from office
    distance = haversine_distance(
        user_lat,
        user_lon,
        settings.OFFICE_LATITUDE,
        settings.OFFICE_LONGITUDE
    )

    # 🔧 OPTIONAL: Admin bypass for testing (remove in production if not needed)
    if user and hasattr(user, 'user_level'):
        if user.user_level in ('Super Admin', 'Admin') or user.is_superuser:
            # Allow admins to punch from anywhere for testing purposes
            print(f"[GEOFENCE] Admin bypass - {user.username} at {distance:.0f}m")
            return True, round(distance, 2)

    # Regular geofence validation
    if distance > settings.OFFICE_GEOFENCE_RADIUS_METERS:
        print(f"[GEOFENCE] ❌ REJECTED - Distance: {distance:.0f}m > Allowed: {settings.OFFICE_GEOFENCE_RADIUS_METERS}m")
        return False, round(distance, 2)

    print(f"[GEOFENCE] ✅ ALLOWED - Distance: {distance:.0f}m within {settings.OFFICE_GEOFENCE_RADIUS_METERS}m")
    return True, round(distance, 2)