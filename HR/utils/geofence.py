# HR/utils/geofence.py - TEMPORARY BYPASS FOR TESTING

from django.conf import settings
from .geolocation import haversine_distance
import logging

logger = logging.getLogger(__name__)


def validate_office_geofence(user_lat, user_lon, user=None):
    """
    ⚠️ GEOFENCE TEMPORARILY DISABLED FOR TESTING
    Validates if user is within office geofence radius.
    
    Args:
        user_lat (float): User's latitude
        user_lon (float): User's longitude  
        user (AppUser, optional): User object for logging
    
    Returns:
        tuple: (allowed: bool, distance_in_meters: float)
    """
    
    # 🔴 TEMPORARY BYPASS - REMOVE THIS IN PRODUCTION
    GEOFENCE_ENABLED = False  # Set to True to re-enable geofence
    
    if not GEOFENCE_ENABLED:
        logger.warning("[GEOFENCE] ⚠️ GEOFENCE DISABLED - ALLOWING ALL LOCATIONS")
        user_info = f"User {user.email}" if user else "Unknown user"
        logger.warning(f"[GEOFENCE] {user_info} - Location: ({user_lat}, {user_lon})")
        # Return True with a fake distance of 0
        return True, 0.0
    
    # ✅ Original geofence logic below (currently disabled)
    # ---------------------------------------------------
    
    # Verify settings are configured
    if not all([
        hasattr(settings, 'OFFICE_LATITUDE'),
        hasattr(settings, 'OFFICE_LONGITUDE'),
        hasattr(settings, 'OFFICE_GEOFENCE_RADIUS_METERS'),
    ]):
        logger.error("[GEOFENCE] ❌ Office location settings not configured!")
        return False, 0
    
    # Validate and convert coordinates
    try:
        user_lat = float(user_lat)
        user_lon = float(user_lon)
        office_lat = float(settings.OFFICE_LATITUDE)
        office_lon = float(settings.OFFICE_LONGITUDE)
        allowed_radius = float(settings.OFFICE_GEOFENCE_RADIUS_METERS)
    except (TypeError, ValueError) as e:
        logger.error(f"[GEOFENCE] ❌ Invalid coordinates: {e}")
        return False, 0
    
    # Validate coordinate ranges
    if not (-90 <= user_lat <= 90) or not (-180 <= user_lon <= 180):
        logger.error(f"[GEOFENCE] ❌ Invalid coordinates range")
        return False, 0
    
    # Calculate actual distance from office
    distance = haversine_distance(user_lat, user_lon, office_lat, office_lon)
    distance = round(distance, 2)
    
    # Log validation attempt
    user_info = f"User {user.email}" if user else "Unknown user"
    logger.info(f"[GEOFENCE] {'='*60}")
    logger.info(f"[GEOFENCE] Validating: {user_info}")
    logger.info(f"[GEOFENCE] User: ({user_lat:.6f}, {user_lon:.6f})")
    logger.info(f"[GEOFENCE] Office: ({office_lat:.6f}, {office_lon:.6f})")
    logger.info(f"[GEOFENCE] Distance: {distance}m | Allowed: {allowed_radius}m")
    logger.info(f"[GEOFENCE] {'='*60}")
    
    # STRICT VALIDATION
    if distance > allowed_radius:
        logger.warning(f"[GEOFENCE] ❌ REJECTED - {user_info}")
        logger.warning(f"[GEOFENCE] Distance {distance}m EXCEEDS {allowed_radius}m")
        logger.warning(f"[GEOFENCE] Excess: {distance - allowed_radius:.2f}m")
        return False, distance
    
    # SUCCESS
    logger.info(f"[GEOFENCE] ✅ ALLOWED - {user_info}")
    logger.info(f"[GEOFENCE] Buffer remaining: {allowed_radius - distance:.2f}m")
    return True, distance


def get_office_info():
    """Returns office location information for frontend display"""
    return {
        'latitude': float(settings.OFFICE_LATITUDE),
        'longitude': float(settings.OFFICE_LONGITUDE),
        'radius': float(settings.OFFICE_GEOFENCE_RADIUS_METERS),
        'address': getattr(settings, 'OFFICE_ADDRESS', 'Office Location')
    }