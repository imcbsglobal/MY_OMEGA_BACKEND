# HR/utils/geofence.py - FIXED GEOFENCE VALIDATION

from django.conf import settings
from .geolocation import haversine_distance
import logging

logger = logging.getLogger(__name__)


def validate_office_geofence(user_lat, user_lon, user=None):
    """
    Validates if user is within office geofence radius.
    STRICT ENFORCEMENT - NO ADMIN BYPASS
    
    Args:
        user_lat (float): User's latitude
        user_lon (float): User's longitude  
        user (AppUser, optional): User object
    
    Returns:
        tuple: (allowed: bool, distance_in_meters: float)
    """
    
    # Safety check - ensure settings are configured
    if not all([
        hasattr(settings, 'OFFICE_LATITUDE'),
        hasattr(settings, 'OFFICE_LONGITUDE'),
        hasattr(settings, 'OFFICE_GEOFENCE_RADIUS_METERS'),
    ]):
        logger.error("[GEOFENCE] ❌ Office location settings not configured!")
        return False, 0
    
    # Validate and convert input coordinates
    try:
        user_lat = float(user_lat)
        user_lon = float(user_lon)
        office_lat = float(settings.OFFICE_LATITUDE)
        office_lon = float(settings.OFFICE_LONGITUDE)
    except (TypeError, ValueError) as e:
        logger.error(f"[GEOFENCE] ❌ Invalid coordinates: {e}")
        logger.error(f"[GEOFENCE] Received: user_lat={user_lat}, user_lon={user_lon}")
        return False, 0
    
    # Validate coordinate ranges
    if not (-90 <= user_lat <= 90):
        logger.error(f"[GEOFENCE] ❌ Invalid latitude: {user_lat}")
        return False, 0
    
    if not (-180 <= user_lon <= 180):
        logger.error(f"[GEOFENCE] ❌ Invalid longitude: {user_lon}")
        return False, 0
    
    # Calculate actual distance from office
    distance = haversine_distance(
        user_lat,
        user_lon,
        office_lat,
        office_lon
    )
    
    # Round distance to 2 decimal places
    distance = round(distance, 2)
    
    # Get allowed radius from settings
    allowed_radius = settings.OFFICE_GEOFENCE_RADIUS_METERS
    
    # Log the validation attempt
    user_info = f"User {user.email}" if user else "Unknown user"
    logger.info(f"[GEOFENCE] ========================")
    logger.info(f"[GEOFENCE] Validating {user_info}")
    logger.info(f"[GEOFENCE] User Location: ({user_lat}, {user_lon})")
    logger.info(f"[GEOFENCE] Office Location: ({office_lat}, {office_lon})")
    logger.info(f"[GEOFENCE] Distance: {distance}m | Allowed: {allowed_radius}m")
    logger.info(f"[GEOFENCE] ========================")
    
    # STRICT VALIDATION - NO EXCEPTIONS
    if distance > allowed_radius:
        logger.warning(f"[GEOFENCE] ❌ REJECTED - {user_info}")
        logger.warning(f"[GEOFENCE] Distance {distance}m exceeds limit {allowed_radius}m")
        return False, distance
    
    # Success
    logger.info(f"[GEOFENCE] ✅ ALLOWED - {user_info} within {allowed_radius}m radius")
    return True, distance


def get_office_info():
    """
    Returns office location information for frontend display
    """
    return {
        'latitude': settings.OFFICE_LATITUDE,
        'longitude': settings.OFFICE_LONGITUDE,
        'radius': settings.OFFICE_GEOFENCE_RADIUS_METERS,
        'address': getattr(settings, 'OFFICE_ADDRESS', 'Office Location')
    }


def calculate_distance_from_office(user_lat, user_lon):
    """
    Calculate distance from office without validation
    Useful for displaying distance to user
    """
    try:
        distance = haversine_distance(
            float(user_lat),
            float(user_lon),
            float(settings.OFFICE_LATITUDE),
            float(settings.OFFICE_LONGITUDE)
        )
        return round(distance, 2)
    except Exception as e:
        logger.error(f"[GEOFENCE] Error calculating distance: {e}")
        return None