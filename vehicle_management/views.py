# vehicle_management/views.py
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Q, Sum, Count
from django.utils import timezone

from .models import Vehicle, Trip, VehicleChallan
from .serializers import (
    VehicleListSerializer,
    VehicleDetailSerializer,
    VehicleCreateUpdateSerializer,
    TripListSerializer,
    TripDetailSerializer,
    TripStartSerializer,
    TripEndSerializer,
    TripApprovalSerializer,
    VehicleChallanListSerializer,
    VehicleChallanDetailSerializer,
    VehicleChallanCreateSerializer,
    VehicleChallanUpdateSerializer,
    ChallanPaymentSerializer,
)


# ==================== VEHICLE VIEWS ====================

class VehicleListCreateAPIView(generics.ListCreateAPIView):
    """
    GET: List all vehicles
    POST: Create new vehicle
    """
    queryset = Vehicle.objects.all()
    permission_classes = [permissions.AllowAny]  # Change to IsAuthenticated in production
    parser_classes = [MultiPartParser, FormParser]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return VehicleCreateUpdateSerializer
        return VehicleListSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Search functionality
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(vehicle_name__icontains=search) |
                Q(registration_number__icontains=search) |
                Q(company__icontains=search)
            )
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Filter by vehicle type
        vehicle_type = self.request.query_params.get('vehicle_type', None)
        if vehicle_type:
            queryset = queryset.filter(vehicle_type=vehicle_type)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        """Save vehicle with created_by if user is authenticated"""
        if self.request.user.is_authenticated:
            serializer.save(created_by=self.request.user)
        else:
            serializer.save()


class VehicleDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve vehicle detail
    PUT/PATCH: Update vehicle
    DELETE: Delete vehicle
    """
    queryset = Vehicle.objects.all()
    permission_classes = [permissions.AllowAny]  # Change to IsAuthenticated in production
    parser_classes = [MultiPartParser, FormParser]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return VehicleCreateUpdateSerializer
        return VehicleDetailSerializer


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def vehicle_dropdown(request):
    """
    Get active vehicles for dropdown/select
    """
    vehicles = Vehicle.objects.filter(is_active=True).order_by('registration_number')
    
    result = []
    for vehicle in vehicles:
        result.append({
            'id': vehicle.id,
            'vehicle_name': vehicle.vehicle_name,
            'registration_number': vehicle.registration_number,
            'company': vehicle.company or '',
            'vehicle_type': vehicle.vehicle_type or '',
            'current_odometer': float(vehicle.current_odometer),
        })
    
    return Response(result)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def vehicle_stats(request):
    """
    Get vehicle statistics
    """
    total_vehicles = Vehicle.objects.count()
    active_vehicles = Vehicle.objects.filter(is_active=True).count()
    total_trips = Trip.objects.count()
    completed_trips = Trip.objects.filter(status='completed').count()
    
    total_distance = Trip.objects.filter(
        status='completed'
    ).aggregate(
        total=Sum('distance_km')
    )['total'] or 0
    
    total_fuel_cost = Trip.objects.filter(
        status='completed'
    ).aggregate(
        total=Sum('fuel_cost')
    )['total'] or 0
    
    return Response({
        'total_vehicles': total_vehicles,
        'active_vehicles': active_vehicles,
        'inactive_vehicles': total_vehicles - active_vehicles,
        'total_trips': total_trips,
        'completed_trips': completed_trips,
        'pending_trips': total_trips - completed_trips,
        'total_distance_km': float(total_distance),
        'total_fuel_cost': float(total_fuel_cost),
    })


# ==================== TRIP VIEWS ====================

class TripListAPIView(generics.ListAPIView):
    """
    GET: List all trips
    """
    queryset = Trip.objects.select_related(
        'vehicle', 'employee', 'approved_by'
    ).all()
    serializer_class = TripListSerializer
    permission_classes = [permissions.AllowAny]  # Change to IsAuthenticated in production
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by vehicle
        vehicle_id = self.request.query_params.get('vehicle', None)
        if vehicle_id:
            queryset = queryset.filter(vehicle_id=vehicle_id)
        
        # Filter by employee
        employee_id = self.request.query_params.get('employee', None)
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        # Search
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(vehicle__registration_number__icontains=search) |
                Q(client_name__icontains=search) |
                Q(purpose__icontains=search)
            )
        
        return queryset.order_by('-created_at')


class TripDetailAPIView(generics.RetrieveAPIView):
    """
    GET: Retrieve trip detail
    """
    queryset = Trip.objects.select_related(
        'vehicle', 'employee', 'approved_by'
    ).all()
    serializer_class = TripDetailSerializer
    permission_classes = [permissions.AllowAny]  # Change to IsAuthenticated in production


class TripStartAPIView(generics.CreateAPIView):
    """
    POST: Start a new trip
    """
    queryset = Trip.objects.all()
    serializer_class = TripStartSerializer
    permission_classes = [permissions.AllowAny]  # Change to IsAuthenticated in production
    parser_classes = [MultiPartParser, FormParser]


class TripEndAPIView(generics.UpdateAPIView):
    """
    PATCH: End/complete a trip
    """
    queryset = Trip.objects.all()
    serializer_class = TripEndSerializer
    permission_classes = [permissions.AllowAny]  # Change to IsAuthenticated in production
    parser_classes = [MultiPartParser, FormParser]
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Ensure trip is in started status
        if instance.status != 'started':
            return Response(
                {'error': f'Cannot complete trip. Current status is: {instance.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Return full trip details
        detail_serializer = TripDetailSerializer(instance, context={'request': request})
        return Response(detail_serializer.data)


class TripApprovalAPIView(generics.UpdateAPIView):
    """
    PATCH: Approve or reject a trip (Admin only)
    """
    queryset = Trip.objects.all()
    serializer_class = TripApprovalSerializer
    permission_classes = [permissions.AllowAny]  # Change to IsAuthenticated + IsAdminUser in production
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Ensure trip is in completed status
        if instance.status != 'completed':
            return Response(
                {'error': 'Only completed trips can be approved or rejected.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Return full trip details
        detail_serializer = TripDetailSerializer(instance, context={'request': request})
        return Response(detail_serializer.data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def my_trips(request):
    """
    Get trips for the current user (employee view)
    """
    if not request.user.is_authenticated:
        return Response(
            {'error': 'Authentication required'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    trips = Trip.objects.filter(
        employee=request.user
    ).select_related('vehicle', 'approved_by').order_by('-created_at')
    
    serializer = TripListSerializer(trips, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def trip_stats(request):
    """
    Get trip statistics
    """
    # Overall stats
    total_trips = Trip.objects.count()
    started_trips = Trip.objects.filter(status='started').count()
    completed_trips = Trip.objects.filter(status='completed').count()
    approved_trips = Trip.objects.filter(status='approved').count()
    rejected_trips = Trip.objects.filter(status='rejected').count()
    
    # Distance and cost
    total_distance = Trip.objects.filter(
        status__in=['completed', 'approved']
    ).aggregate(total=Sum('distance_km'))['total'] or 0
    
    total_fuel_cost = Trip.objects.filter(
        status__in=['completed', 'approved']
    ).aggregate(total=Sum('fuel_cost'))['total'] or 0
    
    # Average distance
    avg_distance = Trip.objects.filter(
        status__in=['completed', 'approved'],
        distance_km__isnull=False
    ).aggregate(avg=Sum('distance_km'))['avg'] or 0
    
    return Response({
        'total_trips': total_trips,
        'started_trips': started_trips,
        'completed_trips': completed_trips,
        'approved_trips': approved_trips,
        'rejected_trips': rejected_trips,
        'pending_approval': completed_trips,
        'total_distance_km': float(total_distance),
        'total_fuel_cost': float(total_fuel_cost),
        'average_distance_km': float(avg_distance) / max(completed_trips, 1),
    })


@api_view(['DELETE'])
@permission_classes([permissions.AllowAny])  # Change to IsAuthenticated + IsAdminUser in production
def delete_trip(request, pk):
    """
    Delete a trip (Admin only)
    """
    try:
        trip = Trip.objects.get(pk=pk)
        
        # Only allow deletion of started or rejected trips
        if trip.status in ['completed', 'approved']:
            return Response(
                {'error': 'Cannot delete completed or approved trips.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        trip.delete()
        return Response(
            {'message': 'Trip deleted successfully'},
            status=status.HTTP_204_NO_CONTENT
        )
    except Trip.DoesNotExist:
        return Response(
            {'error': 'Trip not found'},
            status=status.HTTP_404_NOT_FOUND
        )


# ==================== VEHICLE CHALLAN VIEWS ====================

class VehicleChallanListCreateAPIView(generics.ListCreateAPIView):
    """
    GET: List all challans
    POST: Create new challan
    """
    queryset = VehicleChallan.objects.select_related(
        'vehicle', 'owner', 'created_by'
    ).all()
    permission_classes = [permissions.AllowAny]  # Change to IsAuthenticated in production
    parser_classes = [MultiPartParser, FormParser]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return VehicleChallanCreateSerializer
        return VehicleChallanListSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by payment status
        payment_status = self.request.query_params.get('payment_status', None)
        if payment_status:
            queryset = queryset.filter(payment_status=payment_status)
        
        # Filter by vehicle
        vehicle_id = self.request.query_params.get('vehicle', None)
        if vehicle_id:
            queryset = queryset.filter(vehicle_id=vehicle_id)
        
        # Filter by owner
        owner_id = self.request.query_params.get('owner', None)
        if owner_id:
            queryset = queryset.filter(owner_id=owner_id)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        if start_date:
            queryset = queryset.filter(challan_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(challan_date__lte=end_date)
        
        # Search
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(vehicle__registration_number__icontains=search) |
                Q(challan_number__icontains=search) |
                Q(offence_type__icontains=search) |
                Q(location__icontains=search)
            )
        
        return queryset.order_by('-challan_date', '-created_at')
    
    def perform_create(self, serializer):
        """Save challan with created_by if user is authenticated"""
        if self.request.user.is_authenticated:
            serializer.save(created_by=self.request.user)
        else:
            serializer.save()


class VehicleChallanDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve challan detail
    PUT/PATCH: Update challan
    DELETE: Delete challan
    """
    queryset = VehicleChallan.objects.select_related(
        'vehicle', 'owner', 'created_by'
    ).all()
    permission_classes = [permissions.AllowAny]  # Change to IsAuthenticated in production
    parser_classes = [MultiPartParser, FormParser]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return VehicleChallanUpdateSerializer
        return VehicleChallanDetailSerializer


class ChallanPaymentAPIView(generics.UpdateAPIView):
    """
    PATCH: Mark challan as paid
    """
    queryset = VehicleChallan.objects.all()
    serializer_class = ChallanPaymentSerializer
    permission_classes = [permissions.AllowAny]  # Change to IsAuthenticated in production
    parser_classes = [MultiPartParser, FormParser]
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Check if already paid
        if instance.payment_status == 'paid':
            return Response(
                {'error': 'Challan is already marked as paid.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Return full challan details
        detail_serializer = VehicleChallanDetailSerializer(instance, context={'request': request})
        return Response(detail_serializer.data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def challan_stats(request):
    """
    Get challan statistics
    """
    # Overall stats
    total_challans = VehicleChallan.objects.count()
    paid_challans = VehicleChallan.objects.filter(payment_status='paid').count()
    unpaid_challans = VehicleChallan.objects.filter(payment_status='unpaid').count()
    
    # Fine amounts
    total_fine_amount = VehicleChallan.objects.aggregate(
        total=Sum('fine_amount')
    )['total'] or 0
    
    paid_amount = VehicleChallan.objects.filter(
        payment_status='paid'
    ).aggregate(
        total=Sum('fine_amount')
    )['total'] or 0
    
    unpaid_amount = VehicleChallan.objects.filter(
        payment_status='unpaid'
    ).aggregate(
        total=Sum('fine_amount')
    )['total'] or 0
    
    # Top offence types
    top_offences = VehicleChallan.objects.values('offence_type').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    # Recent unpaid challans
    recent_unpaid = VehicleChallan.objects.filter(
        payment_status='unpaid'
    ).order_by('-challan_date')[:5].count()
    
    return Response({
        'total_challans': total_challans,
        'paid_challans': paid_challans,
        'unpaid_challans': unpaid_challans,
        'total_fine_amount': float(total_fine_amount),
        'paid_amount': float(paid_amount),
        'unpaid_amount': float(unpaid_amount),
        'top_offences': list(top_offences),
        'recent_unpaid_count': recent_unpaid,
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def vehicle_challans(request, vehicle_id):
    """
    Get all challans for a specific vehicle
    """
    try:
        vehicle = Vehicle.objects.get(pk=vehicle_id)
    except Vehicle.DoesNotExist:
        return Response(
            {'error': 'Vehicle not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    challans = VehicleChallan.objects.filter(
        vehicle=vehicle
    ).select_related('owner', 'created_by').order_by('-challan_date')
    
    serializer = VehicleChallanListSerializer(challans, many=True, context={'request': request})
    
    # Also return summary
    total_challans = challans.count()
    unpaid_count = challans.filter(payment_status='unpaid').count()
    total_fine = challans.aggregate(total=Sum('fine_amount'))['total'] or 0
    unpaid_fine = challans.filter(payment_status='unpaid').aggregate(total=Sum('fine_amount'))['total'] or 0
    
    return Response({
        'vehicle': {
            'id': vehicle.id,
            'vehicle_name': vehicle.vehicle_name,
            'registration_number': vehicle.registration_number,
        },
        'summary': {
            'total_challans': total_challans,
            'unpaid_challans': unpaid_count,
            'total_fine_amount': float(total_fine),
            'unpaid_fine_amount': float(unpaid_fine),
        },
        'challans': serializer.data,
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def owner_challans(request):
    """
    Get challans for the current user (owner view)
    """
    if not request.user.is_authenticated:
        return Response(
            {'error': 'Authentication required'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    challans = VehicleChallan.objects.filter(
        owner=request.user
    ).select_related('vehicle', 'created_by').order_by('-challan_date')
    
    serializer = VehicleChallanListSerializer(challans, many=True, context={'request': request})
    return Response(serializer.data)