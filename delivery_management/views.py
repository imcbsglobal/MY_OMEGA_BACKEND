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
    """Start a delivery"""
    delivery = get_object_or_404(Delivery, pk=pk)
    
    # Check if delivery can be started
    if delivery.status != 'scheduled':
        return Response(
            {'error': f'Cannot start delivery with status: {delivery.status}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate input data
    serializer = DeliveryStartSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Start the delivery - FIXED: Added user parameter
    delivery.start_delivery(
        user=request.user,  # ✅ Added this line
        odometer_reading=serializer.validated_data.get('odometer_reading'),
        fuel_level=serializer.validated_data.get('fuel_level'),
        notes=serializer.validated_data.get('notes', '')
    )
    
    # Return updated delivery
    response_serializer = DeliveryDetailSerializer(delivery)
    return Response(response_serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_delivery(request, pk):
    """Complete a delivery"""
    delivery = get_object_or_404(Delivery, pk=pk)
    
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
    
    # Update product delivered quantities
    products_data = serializer.validated_data.get('products', [])
    total_delivered = Decimal('0.00')
    total_balance = Decimal('0.00')
    total_collected = Decimal('0.00')
    
    for product_data in products_data:
        try:
            delivery_product = DeliveryProduct.objects.get(
                delivery=delivery,
                product_id=product_data['product_id']
            )
            delivery_product.delivered_quantity = Decimal(str(product_data['delivered_quantity']))
            delivery_product.save()
            
            total_delivered += delivery_product.delivered_quantity
            total_balance += delivery_product.balance_quantity
            
            if delivery_product.unit_price:
                total_collected += delivery_product.delivered_quantity * delivery_product.unit_price
                
        except DeliveryProduct.DoesNotExist:
            return Response(
                {'error': f'Product {product_data["product_id"]} not found in this delivery'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Complete the delivery
    delivery.complete_delivery(
        user=request.user,  # ✅ This was already correct
        odometer_reading=serializer.validated_data.get('odometer_reading'),
        fuel_level=serializer.validated_data.get('fuel_level'),
        notes=serializer.validated_data.get('notes', ''),
        delivered_boxes=total_delivered,
        balance_boxes=total_balance,
        collected_amount=total_collected
    )
    
    # Return updated delivery
    response_serializer = DeliveryDetailSerializer(delivery)
    return Response(response_serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_delivery(request, pk):
    """Cancel a delivery"""
    delivery = get_object_or_404(Delivery, pk=pk)
    
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
        
        serializer.save()
    
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
    
    # Update stop
    serializer.save()
    
    return Response(serializer.data, status=status.HTTP_200_OK)


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
    
    # Calculate stop-wise summary
    stops_summary = []
    for stop in delivery.stops.all().order_by('stop_sequence'):
        stops_summary.append({
            'stop_sequence': stop.stop_sequence,
            'customer_name': stop.customer_name,
            'planned_boxes': float(stop.planned_boxes),
            'delivered_boxes': float(stop.delivered_boxes),
            'balance_boxes': float(stop.balance_boxes),
            'planned_amount': float(stop.planned_amount),
            'collected_amount': float(stop.collected_amount),
            'pending_amount': float(stop.pending_amount),
            'status': stop.status,
        })
    
    # Product-wise summary
    products_summary = []
    for product in delivery.products.all():
        products_summary.append({
            'product_name': product.product.product_name,
            'loaded_quantity': float(product.loaded_quantity),
            'delivered_quantity': float(product.delivered_quantity),
            'balance_quantity': float(product.balance_quantity),
            'unit_price': float(product.unit_price) if product.unit_price else 0,
            'total_amount': float(product.total_amount),
        })
    
    summary = {
        'delivery_number': delivery.delivery_number,
        'employee_name': delivery.employee.get_full_name(),
        'vehicle_number': delivery.vehicle.registration_number,
        'route_name': delivery.route.route_name,
        'scheduled_date': delivery.scheduled_date,
        'status': delivery.status,
        'totals': {
            'total_loaded_boxes': float(delivery.total_loaded_boxes),
            'total_delivered_boxes': float(delivery.total_delivered_boxes),
            'total_balance_boxes': float(delivery.total_balance_boxes),
            'total_amount': float(delivery.total_amount),
            'collected_amount': float(delivery.collected_amount),
            'total_pending_amount': float(delivery.total_pending_amount),
        },
        'stops': stops_summary,
        'products': products_summary,
    }
    
    return Response(summary, status=status.HTTP_200_OK)