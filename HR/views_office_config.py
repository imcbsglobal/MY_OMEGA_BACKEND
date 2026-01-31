# HR/views_office_config.py - New file for office configuration endpoints

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db import transaction
from .models import OfficeLocation
from .Serializers import (
    OfficeLocationSerializer,
    OfficeLocationCreateSerializer,
    OfficeLocationTestSerializer
)
from .utils.geofence import get_office_info, test_geofence_validation
import logging

logger = logging.getLogger(__name__)


class OfficeLocationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing office locations and geofence configuration.
    Admin-only access.
    """
    queryset = OfficeLocation.objects.all()
    serializer_class = OfficeLocationSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        """Order by active status and creation date"""
        return OfficeLocation.objects.all().order_by('-is_active', '-configured_at')
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'create':
            return OfficeLocationCreateSerializer
        return OfficeLocationSerializer
    
    def perform_create(self, serializer):
        """Set configured_by to current user"""
        serializer.save(configured_by=self.request.user)
    
    @action(detail=False, methods=['get'], url_path='active')
    def active(self, request):
        """Get the currently active office location"""
        office = OfficeLocation.get_active_office()
        
        if not office:
            return Response({
                'success': False,
                'error': 'No active office location configured',
                'message': 'Please configure an office location in the admin panel'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(office)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @action(detail=True, methods=['post'], url_path='set-active')
    @transaction.atomic
    def set_active(self, request, pk=None):
        """Set this office location as active (deactivates others)"""
        office = self.get_object()
        
        # Deactivate all others
        OfficeLocation.objects.exclude(pk=office.pk).update(is_active=False)
        
        # Activate this one
        office.is_active = True
        office.save()
        
        logger.info(f"[OFFICE CONFIG] Office '{office.name}' set as active by {request.user.email}")
        
        serializer = self.get_serializer(office)
        return Response({
            'success': True,
            'message': f"Office '{office.name}' is now active",
            'data': serializer.data
        })
    
    @action(detail=True, methods=['post'], url_path='test-location')
    def test_location(self, request, pk=None):
        """
        Test a location against this office's geofence.
        Useful for debugging and testing.
        """
        office = self.get_object()
        
        serializer = OfficeLocationTestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        test_lat = serializer.validated_data['latitude']
        test_lon = serializer.validated_data['longitude']
        
        # Temporarily set this office as active for testing
        original_active = OfficeLocation.get_active_office()
        if original_active != office:
            office.is_active = True
            office.save()
        
        try:
            # Test the geofence
            result = test_geofence_validation(test_lat, test_lon)
            
            return Response({
                'success': True,
                'test_results': result,
                'office': {
                    'name': office.name,
                    'coordinates': f"{office.latitude}, {office.longitude}",
                    'radius': office.geofence_radius_meters
                }
            })
        finally:
            # Restore original active office if changed
            if original_active and original_active != office:
                office.is_active = False
                office.save()
                original_active.is_active = True
                original_active.save()
    
    @action(detail=False, methods=['post'], url_path='detect-my-location')
    def detect_my_location(self, request):
        """
        Endpoint for admin to submit their current GPS location
        during office setup. This creates a new office configuration.
        
        Expected payload:
        {
            "name": "Office Name",
            "address": "Office Address",
            "latitude": 11.618002662095822,
            "longitude": 76.08151476129609,
            "geofence_radius_meters": 100,
            "detection_method": "gps",  # or "map"
            "gps_accuracy_meters": 10.5,  # optional
            "notes": "Optional notes"  # optional
        }
        """
        # Log the incoming request
        logger.info(f"[OFFICE CONFIG] ====== DETECT MY LOCATION REQUEST ======")
        logger.info(f"[OFFICE CONFIG] User: {request.user.email}")
        logger.info(f"[OFFICE CONFIG] Request data: {request.data}")
        
        # Validate the data
        serializer = OfficeLocationCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            logger.error(f"[OFFICE CONFIG] ❌ Validation failed!")
            logger.error(f"[OFFICE CONFIG] Errors: {serializer.errors}")
            
            # Return detailed error information
            return Response({
                'success': False,
                'error': 'Validation failed',
                'details': serializer.errors,
                'message': 'Please check the form data and try again'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create the office location
        try:
            # Don't override detection_method - use what the frontend sent
            office = serializer.save(
                configured_by=request.user
            )
            
            logger.info(f"[OFFICE CONFIG] ✅ Office location created successfully!")
            logger.info(f"[OFFICE CONFIG] Name: {office.name}")
            logger.info(f"[OFFICE CONFIG] Address: {office.address}")
            logger.info(f"[OFFICE CONFIG] Coordinates: ({office.latitude}, {office.longitude})")
            logger.info(f"[OFFICE CONFIG] Radius: {office.geofence_radius_meters}m")
            logger.info(f"[OFFICE CONFIG] Detection method: {office.detection_method}")
            logger.info(f"[OFFICE CONFIG] GPS accuracy: {office.gps_accuracy_meters}m")
            logger.info(f"[OFFICE CONFIG] Is active: {office.is_active}")
            logger.info(f"[OFFICE CONFIG] ==========================================")
            
            # Return the created office
            response_serializer = OfficeLocationSerializer(office)
            return Response({
                'success': True,
                'message': 'Office location configured successfully',
                'data': response_serializer.data
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            logger.error(f"[OFFICE CONFIG] ❌ Error creating office location!")
            logger.error(f"[OFFICE CONFIG] Exception: {str(e)}")
            logger.error(f"[OFFICE CONFIG] Exception type: {type(e).__name__}")
            
            import traceback
            logger.error(f"[OFFICE CONFIG] Traceback:\n{traceback.format_exc()}")
            
            return Response({
                'success': False,
                'error': 'Failed to create office location',
                'details': str(e),
                'message': 'An error occurred while saving the office location'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_office_geofence_info(request):
    """
    Get office geofence configuration for display purposes.
    Frontend should NOT use this for validation - validation happens server-side.
    Available to all authenticated users.
    """
    office_info = get_office_info()
    
    if not office_info:
        return Response({
            'success': False,
            'error': 'No office location configured',
            'message': 'Office location has not been set up yet'
        }, status=status.HTTP_404_NOT_FOUND)
    
    return Response({
        'success': True,
        'data': office_info,
        'message': 'You must be within the office radius to punch in/out'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def update_geofence_radius(request):
    """
    Quick endpoint to update just the geofence radius of the active office.
    Admin only.
    """
    office = OfficeLocation.get_active_office()
    
    if not office:
        return Response({
            'success': False,
            'error': 'No active office location configured'
        }, status=status.HTTP_404_NOT_FOUND)
    
    new_radius = request.data.get('radius_meters')
    
    if not new_radius:
        return Response({
            'success': False,
            'error': 'radius_meters is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        new_radius = int(new_radius)
        if not (10 <= new_radius <= 500):
            raise ValueError("Radius must be between 10 and 500 meters")
    except (ValueError, TypeError) as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    
    old_radius = office.geofence_radius_meters
    office.geofence_radius_meters = new_radius
    office.save()
    
    logger.info(f"[OFFICE CONFIG] Geofence radius updated by {request.user.email}")
    logger.info(f"[OFFICE CONFIG] Office: {office.name}")
    logger.info(f"[OFFICE CONFIG] Old radius: {old_radius}m → New radius: {new_radius}m")
    
    serializer = OfficeLocationSerializer(office)
    return Response({
        'success': True,
        'message': f'Geofence radius updated from {old_radius}m to {new_radius}m',
        'data': serializer.data
    })