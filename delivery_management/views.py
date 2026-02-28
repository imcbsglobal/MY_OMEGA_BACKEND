# delivery_management/views.py
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.db.models import Sum, Count, Q, Avg
from decimal import Decimal
from datetime import datetime, timedelta
from rest_framework.exceptions import PermissionDenied

from .models import Delivery, DeliveryProduct, DeliveryStop
from .serializers import (
    DeliveryListSerializer,
    DeliveryDetailSerializer,
    DeliveryCreateSerializer,
    DeliveryUpdateSerializer,
    DeliveryProductSerializer,
    DeliveryProductUpdateSerializer,
    DeliveryStopSerializer,
    DeliveryStopCreateSerializer,
    DeliveryStopUpdateSerializer,
    DeliveryStartSerializer,
    DeliveryCompleteSerializer,
    DeliveryUpdateProductsSerializer,
    DeliveryStatsSerializer
)


def _ensure_user_has_access(user, delivery):
    """Raise PermissionDenied if user is not allowed to access/update the delivery."""
    # Staff/superuser may access everything
    if getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False):
        return True

    # If delivery has assigned_to set, require it to match request.user
    if getattr(delivery, 'assigned_to', None) and delivery.assigned_to_id == getattr(user, 'id', None):
        return True

    # Otherwise deny with explicit 403
    raise PermissionDenied('You do not have permission to access this delivery.')


# ==================== MAIN DELIVERY VIEWS ====================

class DeliveryListCreateAPIView(generics.ListCreateAPIView):
    """
    GET: List all deliveries
    POST: Create a new delivery
    """
    queryset = Delivery.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DeliveryCreateSerializer
        return DeliveryListSerializer
    
    def get_queryset(self):
        queryset = Delivery.objects.select_related(
            'employee', 'vehicle', 'route', 'created_by', 'completed_by'
        ).prefetch_related('products', 'stops')
        
        # Filter by status
        status_param = self.request.query_params.get('status', None)
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        if start_date:
            queryset = queryset.filter(scheduled_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(scheduled_date__lte=end_date)
        
        # Filter by employee
        employee_id = self.request.query_params.get('employee_id', None)
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        
        # Filter by vehicle
        vehicle_id = self.request.query_params.get('vehicle_id', None)
        if vehicle_id:
            queryset = queryset.filter(vehicle_id=vehicle_id)
        
        # Filter by route
        route_id = self.request.query_params.get('route_id', None)
        if route_id:
            queryset = queryset.filter(route_id=route_id)
        
        # If the user is not staff, restrict list to deliveries assigned to their employee record
        try:
            user = self.request.user
            if not (user.is_staff or user.is_superuser):
                # Resolve employee for current user
                from employee_management.models import Employee
                try:
                    employee = Employee.objects.get(user=user)
                    queryset = queryset.filter(employee=employee)
                except Employee.DoesNotExist:
                    # No employee profile -> return empty queryset
                    return Delivery.objects.none()
        except Exception:
            # In case of unexpected errors, fall back to the safe queryset
            pass

        return queryset.order_by('-scheduled_date', '-scheduled_time')
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class DeliveryDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Get delivery details
    PUT/PATCH: Update delivery
    DELETE: Delete delivery
    """
    queryset = Delivery.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        """Use different serializers for read vs write operations"""
        if self.request.method in ['PUT', 'PATCH']:
            return DeliveryUpdateSerializer
        return DeliveryDetailSerializer

    def get_object(self):
        obj = super().get_object()
        # Enforce assigned_to access control for non-staff users
        _ensure_user_has_access(self.request.user, obj)
        return obj

    def perform_update(self, serializer):
        """Save delivery updates and ensure derived totals are recalculated."""
        # Ensure user may update this delivery
        delivery_obj = self.get_object()
        _ensure_user_has_access(self.request.user, delivery_obj)

        delivery = serializer.save()

        # Recalculate derived totals when totals are manually overridden
        # total_balance_boxes = max(0, total_loaded_boxes - total_delivered_boxes)
        # total_pending_amount = max(0, total_amount - collected_amount)
        try:
            # Ensure Decimal arithmetic safety
            td = delivery.total_delivered_boxes or Decimal('0.00')
            tl = delivery.total_loaded_boxes or Decimal('0.00')
            ca = delivery.collected_amount or Decimal('0.00')
            ta = delivery.total_amount or Decimal('0.00')

            delivery.total_balance_boxes = max(Decimal('0.00'), tl - td)
            delivery.total_pending_amount = max(Decimal('0.00'), ta - ca)
            delivery.save(update_fields=['total_balance_boxes', 'total_pending_amount'])
        except Exception:
            # If anything goes wrong during recalculation, still return the saved object
            delivery.save()
    
    def get_queryset(self):
        return Delivery.objects.select_related(
            'employee', 'vehicle', 'route', 'created_by', 'completed_by'
        ).prefetch_related(
            'products__product',
            'stops'
        )


# ==================== DELIVERY ACTIONS ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_delivery(request, pk):
    """Start a delivery or update location for in-progress delivery"""
    delivery = get_object_or_404(Delivery, pk=pk)
    _ensure_user_has_access(request.user, delivery)
    
    # Validate input data
    serializer = DeliveryStartSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Handle based on current status
    if delivery.status == 'scheduled':
        # Start the delivery
        delivery.start_delivery(
            user=request.user,
            odometer_reading=serializer.validated_data.get('odometer_reading'),
            fuel_level=serializer.validated_data.get('fuel_level'),
            notes=serializer.validated_data.get('notes', ''),
            start_location=serializer.validated_data.get('start_location', ''),
            start_latitude=serializer.validated_data.get('start_latitude'),
            start_longitude=serializer.validated_data.get('start_longitude')
        )
        message = "Delivery started successfully"
    elif delivery.status == 'in_progress':
        # Update location for in-progress delivery
        delivery.start_location = serializer.validated_data.get('start_location', delivery.start_location)
        delivery.start_latitude = serializer.validated_data.get('start_latitude', delivery.start_latitude)
        delivery.start_longitude = serializer.validated_data.get('start_longitude', delivery.start_longitude)
        if serializer.validated_data.get('notes'):
            delivery.start_notes = serializer.validated_data.get('notes')
        delivery.save()
        message = "Location updated successfully"
    else:
        return Response(
            {'error': f'Cannot start delivery with status: {delivery.status}. Only scheduled or in_progress deliveries can be started.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Return updated delivery
    response_serializer = DeliveryDetailSerializer(delivery)
    return Response({
        'message': message,
        **response_serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_delivery(request, pk):
    """Complete a delivery"""
    delivery = get_object_or_404(Delivery, pk=pk)
    _ensure_user_has_access(request.user, delivery)
    
    # Check if delivery can be completed
    if delivery.status != 'in_progress':
        return Response(
            {'error': f'Cannot complete delivery with status: {delivery.status}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate input data
    serializer = DeliveryCompleteSerializer(
        data=request.data,
        context={'delivery': delivery}
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Update product delivered quantities (if provided by caller)
    products_data = serializer.validated_data.get('products', [])
    
    for product_data in products_data:
        try:
            delivery_product = DeliveryProduct.objects.get(
                delivery=delivery,
                product_id=product_data['product_id']
            )
            delivery_product.delivered_quantity = Decimal(str(product_data['delivered_quantity']))
            delivery_product.save()
        except DeliveryProduct.DoesNotExist:
            return Response(
                {'error': f'Product {product_data["product_id"]} not found in this delivery'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # ── Recalculate totals: PRIORITIZE STOPS over empty products ──────────────────
    # Total delivered/balance boxes: use stops as primary source (actual workflow)
    # Only fall back to products if stops have no data
    
    all_stops = delivery.stops.all()
    total_delivered_from_stops = all_stops.aggregate(
        s=Sum('delivered_boxes'))['s'] or Decimal('0.00')
    
    all_products = DeliveryProduct.objects.filter(delivery=delivery)
    total_delivered_from_products = all_products.aggregate(
        s=Sum('delivered_quantity'))['s'] or Decimal('0.00')
    total_balance_from_products = all_products.aggregate(
        s=Sum('balance_quantity'))['s'] or Decimal('0.00')

    # Decision logic: STOPS are the source of truth (actual delivery workflow)
    # Only use products if no stop data exists
    if total_delivered_from_stops > Decimal('0.00'):
        # Stops have delivery data (normal workflow) - use stops as source of truth
        total_delivered = total_delivered_from_stops
        # Calculate balance properly: loaded - delivered from stops
        total_balance = max(Decimal('0.00'), delivery.total_loaded_boxes - total_delivered)
    elif all_products.exists() and total_delivered_from_products > Decimal('0.00'):
        # Products have been updated with delivery quantities (alternative workflow) - use products
        total_delivered = total_delivered_from_products
        total_balance = total_balance_from_products
    else:
        # No delivery data anywhere - everything is balance
        total_delivered = Decimal('0.00')
        total_balance = delivery.total_loaded_boxes

    # Total cash collected: sum from all stops
    stops_collected = all_stops.aggregate(
        s=Sum('collected_amount'))['s'] or Decimal('0.00')
    stops_pending = all_stops.aggregate(
        s=Sum('pending_amount'))['s'] or Decimal('0.00')

    # Use stops data if available, otherwise preserve existing
    total_collected = stops_collected if stops_collected > Decimal('0.00') else delivery.collected_amount

    # Complete the delivery with correctly computed totals
    delivery.complete_delivery(
        user=request.user,
        odometer_reading=serializer.validated_data.get('odometer_reading'),
        fuel_level=serializer.validated_data.get('fuel_level'),
        notes=serializer.validated_data.get('notes', ''),
        delivered_boxes=total_delivered,
        balance_boxes=total_balance,
        collected_amount=total_collected,
        completion_location=serializer.validated_data.get('completion_location', ''),
        completion_latitude=serializer.validated_data.get('completion_latitude'),
        completion_longitude=serializer.validated_data.get('completion_longitude'),
    )
    
    # Return updated delivery
    response_serializer = DeliveryDetailSerializer(delivery)
    return Response(response_serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_delivery(request, pk):
    """Cancel a delivery"""
    delivery = get_object_or_404(Delivery, pk=pk)
    _ensure_user_has_access(request.user, delivery)
    
    # Check if delivery can be cancelled
    if delivery.status == 'completed':
        return Response(
            {'error': 'Cannot cancel a completed delivery'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    reason = request.data.get('reason', '')
    delivery.cancel_delivery(reason)
    
    serializer = DeliveryDetailSerializer(delivery)
    return Response(serializer.data, status=status.HTTP_200_OK)


# ==================== DELIVERY PRODUCTS ====================

class DeliveryProductListAPIView(generics.ListAPIView):
    """List all products for a delivery"""
    serializer_class = DeliveryProductSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        delivery_id = self.kwargs.get('delivery_id')
        return DeliveryProduct.objects.filter(
            delivery_id=delivery_id
        ).select_related('product', 'delivery')


class DeliveryProductUpdateAPIView(generics.UpdateAPIView):
    """Update a single delivery product"""
    queryset = DeliveryProduct.objects.all()
    serializer_class = DeliveryProductUpdateSerializer
    permission_classes = [IsAuthenticated]


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_delivery_products_bulk(request, pk):
    """Bulk update delivery products"""
    delivery = get_object_or_404(Delivery, pk=pk)
    _ensure_user_has_access(request.user, delivery)
    
    # Validate input
    serializer = DeliveryUpdateProductsSerializer(
        data=request.data,
        context={'delivery': delivery}
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Update products
    products_data = serializer.validated_data.get('products', [])
    for product_data in products_data:
        try:
            delivery_product = DeliveryProduct.objects.get(
                id=product_data['id']
            )
            if 'delivered_quantity' in product_data:
                delivery_product.delivered_quantity = product_data['delivered_quantity']
            if 'loaded_quantity' in product_data:
                delivery_product.loaded_quantity = product_data['loaded_quantity']
            if 'unit_price' in product_data:
                delivery_product.unit_price = product_data['unit_price']
            delivery_product.save()
        except DeliveryProduct.DoesNotExist:
            return Response(
                {'error': f'Product {product_data["id"]} not found'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Return updated products
    updated_products = DeliveryProduct.objects.filter(delivery=delivery)
    response_serializer = DeliveryProductSerializer(updated_products, many=True)
    return Response(response_serializer.data, status=status.HTTP_200_OK)


# ==================== DELIVERY STOPS ====================

class DeliveryStopListAPIView(generics.ListCreateAPIView):
    """
    GET: List all stops for a delivery
    POST: Create a new stop (only allowed when delivery is in_progress)
    """
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DeliveryStopCreateSerializer
        return DeliveryStopSerializer
    
    def get_queryset(self):
        delivery_id = self.kwargs.get('delivery_id')
        return DeliveryStop.objects.filter(
            delivery_id=delivery_id
        ).select_related('delivery').order_by('stop_sequence')
    
    def perform_create(self, serializer):
        delivery_id = self.kwargs.get('delivery_id')
        delivery = get_object_or_404(Delivery, pk=delivery_id)
        
        # ✅ NEW: Check if delivery is in progress
        if delivery.status != 'in_progress':
            from rest_framework.exceptions import ValidationError
            raise ValidationError({
                'error': 'Stops can only be added when delivery is in progress. Please start the delivery first.'
            })
        
        # Auto-assign sequence number
        max_sequence = DeliveryStop.objects.filter(
            delivery=delivery
        ).aggregate(max_seq=Count('stop_sequence'))['max_seq'] or 0
        
        serializer.save(
            delivery=delivery,
            stop_sequence=max_sequence + 1
        )


class DeliveryStopDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Get stop details
    PUT/PATCH: Update stop (only allowed when delivery is in_progress or scheduled)
    DELETE: Delete stop (only allowed when delivery is in_progress or scheduled)
    """
    queryset = DeliveryStop.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return DeliveryStopUpdateSerializer
        return DeliveryStopSerializer
    
    def perform_update(self, serializer):
        stop = self.get_object()
        
        # ✅ NEW: Check if delivery allows stop editing
        if stop.delivery.status not in ['scheduled', 'in_progress']:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({
                'error': 'Stops can only be edited when delivery is scheduled or in progress.'
            })
        
        updated_stop = serializer.save()

        # After a stop is updated, recalculate delivery-level running totals
        delivery = updated_stop.delivery
        all_stops = delivery.stops.all()

        # Sum collected cash and pending from all stops so far
        stops_collected = all_stops.aggregate(
            s=Sum('collected_amount'))['s'] or Decimal('0.00')
        stops_pending   = all_stops.aggregate(
            s=Sum('pending_amount'))['s']   or Decimal('0.00')

        # Sum delivered/balance boxes from all stops
        stops_delivered = all_stops.aggregate(
            s=Sum('delivered_boxes'))['s'] or Decimal('0.00')
        stops_balance   = all_stops.aggregate(
            s=Sum('balance_boxes'))['s']   or Decimal('0.00')

        # Update delivery totals
        delivery.total_delivered_boxes = stops_delivered
        delivery.total_balance_boxes   = max(Decimal('0.00'), delivery.total_loaded_boxes - stops_delivered)
        delivery.collected_amount      = stops_collected
        delivery.total_pending_amount  = stops_pending
        delivery.save(update_fields=[
            'total_delivered_boxes', 'total_balance_boxes',
            'collected_amount', 'total_pending_amount'
        ])
    
    def perform_destroy(self, instance):
        # ✅ NEW: Check if delivery allows stop deletion
        if instance.delivery.status not in ['scheduled', 'in_progress']:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({
                'error': 'Stops can only be deleted when delivery is scheduled or in progress.'
            })
        
        instance.delete()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_delivery_stop(request, pk):
    """Mark a delivery stop as completed"""
    stop = get_object_or_404(DeliveryStop, pk=pk)
    
    # Check delivery is in progress
    if stop.delivery.status != 'in_progress':
        return Response(
            {'error': 'Can only complete stops for in-progress deliveries'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate input
    serializer = DeliveryStopUpdateSerializer(
        stop,
        data=request.data,
        partial=True
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Update stop and set arrival time if not already set
    updated_stop = serializer.save()
    if not updated_stop.actual_arrival:
        updated_stop.actual_arrival = timezone.now()
        updated_stop.save(update_fields=['actual_arrival'])
    
    # ── After each stop, recalculate delivery-level running totals ────────────
    delivery = updated_stop.delivery
    all_stops = delivery.stops.all()

    # Sum collected cash and pending from all stops so far
    stops_collected = all_stops.aggregate(
        s=Sum('collected_amount'))['s'] or Decimal('0.00')
    stops_pending   = all_stops.aggregate(
        s=Sum('pending_amount'))['s']   or Decimal('0.00')

    # Sum delivered/balance boxes from all stops
    stops_delivered = all_stops.aggregate(
        s=Sum('delivered_boxes'))['s'] or Decimal('0.00')
    stops_balance   = all_stops.aggregate(
        s=Sum('balance_boxes'))['s']   or Decimal('0.00')

    # Update delivery totals
    delivery.total_delivered_boxes = stops_delivered
    delivery.total_balance_boxes   = max(Decimal('0.00'), delivery.total_loaded_boxes - stops_delivered)
    delivery.collected_amount      = stops_collected
    delivery.total_pending_amount  = stops_pending
    delivery.save(update_fields=[
        'total_delivered_boxes', 'total_balance_boxes',
        'collected_amount', 'total_pending_amount'
    ])

    # Return stop data plus updated delivery summary
    response_data = serializer.data
    response_data['delivery_summary'] = {
        'total_delivered_boxes': str(delivery.total_delivered_boxes),
        'total_balance_boxes':   str(delivery.total_balance_boxes),
        'collected_amount':      str(delivery.collected_amount),
        'total_pending_amount':  str(delivery.total_pending_amount),
    }

    return Response(response_data, status=status.HTTP_200_OK)


# ==================== STATISTICS & REPORTS ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def delivery_statistics(request):
    """Get delivery statistics for a date range"""
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    # Default to current month if no dates provided
    if not start_date or not end_date:
        today = timezone.now().date()
        start_date = today.replace(day=1)
        end_date = today
    
    # Build queryset
    queryset = Delivery.objects.filter(
        scheduled_date__gte=start_date,
        scheduled_date__lte=end_date
    )
    
    # Calculate statistics
    stats = queryset.aggregate(
        total_deliveries=Count('id'),
        scheduled_deliveries=Count('id', filter=Q(status='scheduled')),
        in_progress_deliveries=Count('id', filter=Q(status='in_progress')),
        completed_deliveries=Count('id', filter=Q(status='completed')),
        cancelled_deliveries=Count('id', filter=Q(status='cancelled')),
        total_boxes_loaded=Sum('total_loaded_boxes') or Decimal('0.00'),
        total_boxes_delivered=Sum('total_delivered_boxes') or Decimal('0.00'),
        total_boxes_returned=Sum('total_balance_boxes') or Decimal('0.00'),
        total_amount=Sum('total_amount') or Decimal('0.00'),
        total_collected=Sum('collected_amount') or Decimal('0.00')
    )
    
    # Calculate average efficiency manually (since it's a property, not a field)
    completed_deliveries = queryset.filter(status='completed')
    if completed_deliveries.exists():
        efficiencies = [d.delivery_efficiency for d in completed_deliveries if d.total_loaded_boxes > 0]
        if efficiencies:
            stats['average_efficiency'] = Decimal(str(sum(efficiencies) / len(efficiencies)))
        else:
            stats['average_efficiency'] = Decimal('0.00')
    else:
        stats['average_efficiency'] = Decimal('0.00')
    
    serializer = DeliveryStatsSerializer(stats)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def today_deliveries(request):
    """Get today's deliveries"""
    today = timezone.now().date()
    deliveries = Delivery.objects.filter(
        scheduled_date=today
    ).select_related(
        'employee', 'vehicle', 'route'
    ).order_by('scheduled_time')
    
    serializer = DeliveryListSerializer(deliveries, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def upcoming_deliveries(request):
    """Get upcoming deliveries (next 7 days)"""
    today = timezone.now().date()
    end_date = today + timedelta(days=7)
    
    deliveries = Delivery.objects.filter(
        scheduled_date__gte=today,
        scheduled_date__lte=end_date,
        status='scheduled'
    ).select_related(
        'employee', 'vehicle', 'route'
    ).order_by('scheduled_date', 'scheduled_time')
    
    serializer = DeliveryListSerializer(deliveries, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def employee_deliveries(request, employee_id):
    """Get deliveries for a specific employee"""
    deliveries = Delivery.objects.filter(
        employee_id=employee_id
    ).select_related(
        'employee', 'vehicle', 'route'
    ).order_by('-scheduled_date', '-scheduled_time')
    
    serializer = DeliveryListSerializer(deliveries, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_assigned_deliveries(request):
    """Get deliveries assigned to the current logged-in employee"""
    # Get employee associated with current user
    # Assuming employee has a user field or you have a way to map user to employee
    from employee_management.models import Employee
    
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        return Response(
            {'error': 'No employee profile found for this user'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Filter deliveries for this employee
    status_param = request.query_params.get('status', None)
    queryset = Delivery.objects.filter(employee=employee).select_related(
        'employee', 'vehicle', 'route'
    ).prefetch_related('products', 'stops')
    
    if status_param:
        queryset = queryset.filter(status=status_param)
    else:
        # Default: show only scheduled and in_progress deliveries
        queryset = queryset.filter(status__in=['scheduled', 'in_progress'])
    
    queryset = queryset.order_by('-scheduled_date', '-scheduled_time')
    
    serializer = DeliveryListSerializer(queryset, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_deliveries(request):
    """GET: Return deliveries assigned to the logged-in application user.

    This endpoint intentionally ignores any user_id provided by the client
    and always uses request.user for filtering to prevent elevation of privilege.
    """
    status_param = request.query_params.get('status', None)

    queryset = Delivery.objects.filter(assigned_to=request.user).select_related(
        'employee', 'vehicle', 'route'
    ).prefetch_related('stops')

    if status_param:
        queryset = queryset.filter(status=status_param)

    queryset = queryset.order_by('-scheduled_date', '-scheduled_time')

    results = []
    for d in queryset:
        # pick first stop shop name if present
        first_stop = d.stops.order_by('stop_sequence').first()
        shop_name = first_stop.shop_name if first_stop else ''

        results.append({
            'id': d.id,
            'delivery_number': d.delivery_number,
            'shop_name': shop_name,
            'status': d.status,
            'collected_amount': float(d.collected_amount or 0),
            'delivery_date': d.scheduled_date,
            'can_update': True,
            'vehicle_number': getattr(d.vehicle, 'registration_number', ''),
            'route_name': getattr(d.route, 'route_name', ''),
            'total_loaded_boxes': float(d.total_loaded_boxes or 0),
            'total_delivered_boxes': float(d.total_delivered_boxes or 0),
            'total_balance_boxes': float(d.total_balance_boxes or 0),
        })

    return Response(results, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def vehicle_deliveries(request, vehicle_id):
    """Get deliveries for a specific vehicle"""
    deliveries = Delivery.objects.filter(
        vehicle_id=vehicle_id
    ).select_related(
        'employee', 'vehicle', 'route'
    ).order_by('-scheduled_date', '-scheduled_time')
    
    serializer = DeliveryListSerializer(deliveries, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def route_deliveries(request, route_id):
    """Get deliveries for a specific route"""
    deliveries = Delivery.objects.filter(
        route_id=route_id
    ).select_related(
        'employee', 'vehicle', 'route'
    ).order_by('-scheduled_date', '-scheduled_time')
    
    serializer = DeliveryListSerializer(deliveries, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_next_stop(request, pk):
    """Get the next pending stop for a delivery"""
    delivery = get_object_or_404(Delivery, pk=pk)
    _ensure_user_has_access(request.user, delivery)
    
    # Check delivery is in progress
    if delivery.status != 'in_progress':
        return Response(
            {'error': 'Delivery is not in progress'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Find next pending stop
    next_stop = delivery.stops.filter(
        status='pending'
    ).order_by('stop_sequence').first()
    
    if not next_stop:
        return Response(
            {'message': 'No pending stops remaining'},
            status=status.HTTP_200_OK
        )
    
    serializer = DeliveryStopSerializer(next_stop)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def delivery_summary(request, pk):
    """Get comprehensive delivery summary for admin/reporting"""
    delivery = get_object_or_404(Delivery.objects.select_related(
        'employee', 'vehicle', 'route'
    ).prefetch_related('products', 'stops'), pk=pk)
    _ensure_user_has_access(request.user, delivery)

    summary = _build_delivery_summary(delivery)
    return Response(summary, status=status.HTTP_200_OK)


def _build_delivery_summary(delivery):
    """Build and return a delivery summary dict for a Delivery instance."""
    # Calculate stop-wise summary (defensive: handle nulls)
    stops_summary = []
    for stop in delivery.stops.all().order_by('stop_sequence'):
        stops_summary.append({
            'stop_sequence': stop.stop_sequence,
            'customer_name': stop.customer_name or '',
            'planned_boxes': float(stop.planned_boxes or 0),
            'delivered_boxes': float(stop.delivered_boxes or 0),
            'balance_boxes': float(stop.balance_boxes or 0),
            'planned_amount': float(stop.planned_amount or 0),
            'collected_amount': float(stop.collected_amount or 0),
            'pending_amount': float(stop.pending_amount or 0),
            'status': stop.status,
        })

    # Product-wise summary (defensive)
    products_summary = []
    for product in delivery.products.all():
        products_summary.append({
            'product_name': (getattr(product.product, 'product_name', '') if getattr(product, 'product', None) else ''),
            'loaded_quantity': float(product.loaded_quantity or 0),
            'delivered_quantity': float(product.delivered_quantity or 0),
            'balance_quantity': float(product.balance_quantity or 0),
            'unit_price': float(product.unit_price or 0),
            'total_amount': float(product.total_amount or 0),
        })

    # Defensive access to related fields
    employee_name = ''
    try:
        employee_name = delivery.employee.get_full_name() if getattr(delivery, 'employee', None) else (getattr(delivery, 'employee_name', '') or '')
    except Exception:
        employee_name = getattr(delivery, 'employee_name', '') or ''

    vehicle_number = ''
    try:
        vehicle_number = delivery.vehicle.registration_number if getattr(delivery, 'vehicle', None) else (getattr(delivery, 'vehicle_number', '') or '')
    except Exception:
        vehicle_number = getattr(delivery, 'vehicle_number', '') or ''

    route_name = ''
    try:
        route_name = delivery.route.route_name if getattr(delivery, 'route', None) else (getattr(delivery, 'route_name', '') or '')
    except Exception:
        route_name = getattr(delivery, 'route_name', '') or ''

    summary = {
        'id': delivery.id,
        'delivery_number': delivery.delivery_number or '',
        'employee_name': employee_name,
        'vehicle_number': vehicle_number,
        'route_name': route_name,
        'scheduled_date': delivery.scheduled_date,
        'status': delivery.status,
        'totals': {
            'total_loaded_boxes': float(delivery.total_loaded_boxes or 0),
            'total_delivered_boxes': float(delivery.total_delivered_boxes or 0),
            'total_balance_boxes': float(delivery.total_balance_boxes or 0),
            'total_amount': float(delivery.total_amount or 0),
            'collected_amount': float(delivery.collected_amount or 0),
            'total_pending_amount': float(delivery.total_pending_amount or 0),
        },
        'stops': stops_summary,
        'products': products_summary,
    }

    return summary


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_delivery_totals(request, pk):
    """Allow manual override of total_delivered_boxes and collected_amount.

    Recalculates dependent fields and returns updated delivery summary.
    """
    delivery = get_object_or_404(Delivery, pk=pk)

    # Parse incoming values (only allow these two fields)
    td = request.data.get('total_delivered_boxes', None)
    ca = request.data.get('collected_amount', None)

    # Validate numerical input and bounds
    try:
        tl = delivery.total_loaded_boxes or Decimal('0.00')
        ta = delivery.total_amount or Decimal('0.00')

        if td is not None:
            td = Decimal(str(td))
            if td < 0:
                return Response({'error': 'total_delivered_boxes cannot be negative'}, status=status.HTTP_400_BAD_REQUEST)
            # Do not allow delivered > loaded
            if td > tl:
                return Response({'error': 'total_delivered_boxes cannot exceed total_loaded_boxes'}, status=status.HTTP_400_BAD_REQUEST)
            delivery.total_delivered_boxes = td

        if ca is not None:
            ca = Decimal(str(ca))
            if ca < 0:
                return Response({'error': 'collected_amount cannot be negative'}, status=status.HTTP_400_BAD_REQUEST)
            # Do not allow collected > total amount
            if ca > ta:
                return Response({'error': 'collected_amount cannot exceed total_amount'}, status=status.HTTP_400_BAD_REQUEST)
            delivery.collected_amount = ca
    except Exception:
        return Response({'error': 'Invalid numeric values provided'}, status=status.HTTP_400_BAD_REQUEST)

    # Recalculate derived totals
    delivery.total_balance_boxes = max(Decimal('0.00'), (delivery.total_loaded_boxes or Decimal('0.00')) - (delivery.total_delivered_boxes or Decimal('0.00')))
    delivery.total_pending_amount = max(Decimal('0.00'), (delivery.total_amount or Decimal('0.00')) - (delivery.collected_amount or Decimal('0.00')))
    delivery.save(update_fields=['total_delivered_boxes', 'collected_amount', 'total_balance_boxes', 'total_pending_amount'])

    # Return updated summary (use helper to avoid calling decorated view)
    summary = _build_delivery_summary(delivery)
    return Response(summary, status=status.HTTP_200_OK)