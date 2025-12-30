from django.conf import settings
from .geolocation import haversine_distance

def validate_office_geofence(user_lat, user_lon):
    """
    Returns (allowed: bool, distance_in_meters: float)
    """
    distance = haversine_distance(
        user_lat,
        user_lon,
        settings.OFFICE_LATITUDE,
        settings.OFFICE_LONGITUDE
    )

    if distance > settings.OFFICE_GEOFENCE_RADIUS_METERS:
        return False, round(distance, 2)

    return True, round(distance, 2)
