from django.conf import settings
from .utils.geolocation import haversine_distance

def validate_office_geofence(user_lat, user_lon):
    """
    Returns (allowed: bool, distance_in_meters: float)
    """

    # Safety check
    if not all([
        hasattr(settings, "OFFICE_LATITUDE"),
        hasattr(settings, "OFFICE_LONGITUDE"),
        hasattr(settings, "OFFICE_GEOFENCE_RADIUS_METERS"),
    ]):
        return False, 0

    distance = haversine_distance(
        float(user_lat),
        float(user_lon),
        float(settings.OFFICE_LATITUDE),
        float(settings.OFFICE_LONGITUDE)
    )

    if distance > settings.OFFICE_GEOFENCE_RADIUS_METERS:
        return False, round(distance, 2)

    return True, round(distance, 2)
