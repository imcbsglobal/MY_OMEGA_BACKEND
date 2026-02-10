# HR/utils/geofence.py - FIXED VERSION with proper imports

from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Returns distance in meters between two GPS coordinates.
    """
    import math
    
    R = 6371000  # Earth radius in meters

    phi1 = math.radians(float(lat1))
    phi2 = math.radians(float(lat2))
    d_phi = math.radians(float(lat2) - float(lat1))
    d_lambda = math.radians(float(lon2) - float(lon1))

    a = (
        math.sin(d_phi / 2) ** 2 +
        math.cos(phi1) * math.cos(phi2) *
        math.sin(d_lambda / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def validate_office_geofence(user_lat, user_lon, user=None):
    """
    Validates if user is within office geofence radius.
    Now uses OfficeLocation model from database instead of settings.py
    
    Args:
        user_lat (float): User's latitude
        user_lon (float): User's longitude  
        user (AppUser, optional): User object for logging
    
    Returns:
        tuple: (allowed: bool, distance_in_meters: float)
    """
    from HR.models import OfficeLocation
    
    # Get active office configuration from database
    office = OfficeLocation.get_active_office()
    
    if not office:
        logger.error("[GEOFENCE] ❌ No active office location configured in database!")
        logger.error("[GEOFENCE] Please configure office location in Django Admin.")
        # Fallback to settings.py if available
        return _validate_from_settings(user_lat, user_lon, user)
    
    # Validate and convert coordinates
    try:
        user_lat = float(user_lat)
        user_lon = float(user_lon)
        office_lat = float(office.latitude)
        office_lon = float(office.longitude)
        allowed_radius = float(office.geofence_radius_meters)
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
    logger.info(f"[GEOFENCE] Office: {office.name}")
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


def _validate_from_settings(user_lat, user_lon, user=None):
    """
    Fallback validation using settings.py configuration
    Used only if no OfficeLocation is configured in database
    """
    # Safety check
    if not all([
        hasattr(settings, 'OFFICE_LATITUDE'),
        hasattr(settings, 'OFFICE_LONGITUDE'),
        hasattr(settings, 'OFFICE_GEOFENCE_RADIUS_METERS'),
    ]):
        logger.error("[GEOFENCE] ❌ No office configuration found!")
        return False, 0
    
    try:
        user_lat = float(user_lat)
        user_lon = float(user_lon)
        office_lat = float(settings.OFFICE_LATITUDE)
        office_lon = float(settings.OFFICE_LONGITUDE)
        allowed_radius = float(settings.OFFICE_GEOFENCE_RADIUS_METERS)
    except (TypeError, ValueError) as e:
        logger.error(f"[GEOFENCE] ❌ Invalid coordinates in settings: {e}")
        return False, 0
    
    distance = haversine_distance(user_lat, user_lon, office_lat, office_lon)
    distance = round(distance, 2)
    
    user_info = f"User {user.email}" if user else "Unknown user"
    logger.warning(f"[GEOFENCE] ⚠️ Using fallback settings.py configuration")
    logger.info(f"[GEOFENCE] {user_info} - Distance: {distance}m | Allowed: {allowed_radius}m")
    
    if distance > allowed_radius:
        logger.warning(f"[GEOFENCE] ❌ REJECTED - {user_info}")
        return False, distance
    
    logger.info(f"[GEOFENCE] ✅ ALLOWED - {user_info}")
    return True, distance


def get_office_info():
    """
    Returns office location information for frontend display.
    Prioritizes database configuration over settings.py
    """
    from HR.models import OfficeLocation
    
    office = OfficeLocation.get_active_office()
    
    if office:
        return {
            'latitude': float(office.latitude),
            'longitude': float(office.longitude),
            'radius': float(office.geofence_radius_meters),
            'address': office.address,
            'name': office.name,
            'source': 'database'
        }
    
    # Fallback to settings.py
    if all([
        hasattr(settings, 'OFFICE_LATITUDE'),
        hasattr(settings, 'OFFICE_LONGITUDE'),
        hasattr(settings, 'OFFICE_GEOFENCE_RADIUS_METERS'),
    ]):
        return {
            'latitude': float(settings.OFFICE_LATITUDE),
            'longitude': float(settings.OFFICE_LONGITUDE),
            'radius': float(settings.OFFICE_GEOFENCE_RADIUS_METERS),
            'address': getattr(settings, 'OFFICE_ADDRESS', 'Office Location'),
            'name': 'Office',
            'source': 'settings'
        }
    
    return None


def test_geofence_validation(test_lat, test_lon):
    """
    Test function to validate coordinates against geofence.
    Useful for debugging and testing.
    
    Args:
        test_lat (float): Test latitude
        test_lon (float): Test longitude
    
    Returns:
        dict: Validation results with detailed information
    """
    from HR.models import OfficeLocation
    
    office = OfficeLocation.get_active_office()
    
    if not office:
        return {
            'success': False,
            'error': 'No active office location configured',
            'recommendation': 'Configure office location in Django Admin'
        }
    
    allowed, distance = validate_office_geofence(test_lat, test_lon)
    
    return {
        'success': True,
        'allowed': allowed,
        'distance_meters': distance,
        'office_name': office.name,
        'office_coordinates': f"{office.latitude}, {office.longitude}",
        'geofence_radius': office.geofence_radius_meters,
        'excess_distance': max(0, distance - office.geofence_radius_meters),
        'buffer_remaining': max(0, office.geofence_radius_meters - distance) if allowed else 0,
        'test_coordinates': f"{test_lat}, {test_lon}",
        'verdict': 'ALLOWED ✅' if allowed else 'REJECTED ❌'
    }