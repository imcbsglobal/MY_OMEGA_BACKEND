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
    
    # Cancel the delivery
    delivery.status = 'cancelled'
    delivery.end_notes = request.data.get('notes', '')
    delivery.save()
    
    # Return updated delivery
    serializer = DeliveryDetailSerializer(delivery)
    return Response(serializer.data, status=status.HTTP_200_OK)


# ==================== DELIVERY PRODUCTS ====================

class DeliveryProductListAPIView(generics.ListAPIView):
    """List all products for a specific delivery"""
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
    """Bulk update delivery products (mainly delivered quantities)"""
    delivery = get_object_or_404(Delivery, pk=pk)
    
    # Validate input
    serializer = DeliveryUpdateProductsSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    products_data = serializer.validated_data['products']
    updated_products = []
    
    # Update each product
    for product_data in products_data:
        try:
            delivery_product = DeliveryProduct.objects.get(
                id=product_data['id'],
                delivery=delivery
            )
            delivery_product.delivered_quantity = Decimal(str(product_data['delivered_quantity']))
            delivery_product.save()
            updated_products.append(delivery_product)
            
        except DeliveryProduct.DoesNotExist:
            return Response(
                {'error': f'Product with id {product_data["id"]} not found in this delivery'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Recalculate delivery totals
    total_delivered = sum(p.delivered_quantity for p in updated_products)
    total_balance = sum(p.balance_quantity for p in updated_products)
    
    delivery.total_delivered_boxes = total_delivered
    delivery.total_balance_boxes = total_balance
    delivery.save()
    
    # Return updated products
    response_serializer = DeliveryProductSerializer(updated_products, many=True)
    return Response(response_serializer.data, status=status.HTTP_200_OK)


# ==================== DELIVERY STOPS ====================

class DeliveryStopListAPIView(generics.ListCreateAPIView):
    """
    GET: List all stops for a delivery
    POST: Create a new stop for a delivery
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
        ).order_by('stop_sequence')
    
    def perform_create(self, serializer):
        delivery_id = self.kwargs.get('delivery_id')
        delivery = get_object_or_404(Delivery, pk=delivery_id)
        
        # Auto-assign sequence number if not provided or if it conflicts
        stop_sequence = serializer.validated_data.get('stop_sequence')
        
        if not stop_sequence or DeliveryStop.objects.filter(
            delivery=delivery, 
            stop_sequence=stop_sequence
        ).exists():
            # Get the next available sequence number
            from django.db.models import Max
            max_sequence = DeliveryStop.objects.filter(
                delivery=delivery
            ).aggregate(Max('stop_sequence'))['stop_sequence__max']
            
            stop_sequence = (max_sequence or 0) + 1
            serializer.validated_data['stop_sequence'] = stop_sequence
        
        serializer.save(delivery=delivery)


class DeliveryStopDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Get stop details
    PUT/PATCH: Update stop
    DELETE: Delete stop
    """
    queryset = DeliveryStop.objects.all()
    serializer_class = DeliveryStopSerializer
    permission_classes = [IsAuthenticated]


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_delivery_stop(request, pk):
    """Complete a delivery stop - FIXED VERSION"""
    stop = get_object_or_404(DeliveryStop, pk=pk)
    
    # Update stop details
    stop.delivered_boxes = request.data.get('delivered_boxes', 0)
    stop.collected_amount = request.data.get('collected_amount', 0)
    
    # Parse datetime fields properly - THIS IS THE FIX
    actual_arrival = request.data.get('actual_arrival')
    if actual_arrival:
        if isinstance(actual_arrival, str):
            stop.actual_arrival = parse_datetime(actual_arrival)
        else:
            stop.actual_arrival = actual_arrival
    else:
        stop.actual_arrival = timezone.now()
    
    departure_time = request.data.get('departure_time')
    if departure_time:
        if isinstance(departure_time, str):
            stop.departure_time = parse_datetime(departure_time)
        else:
            stop.departure_time = departure_time
    else:
        stop.departure_time = timezone.now()
    
    stop.status = request.data.get('status', 'delivered')
    stop.notes = request.data.get('notes', '')
    stop.failure_reason = request.data.get('failure_reason', '')
    
    # Handle location
    if 'latitude' in request.data:
        stop.latitude = request.data['latitude']
    if 'longitude' in request.data:
        stop.longitude = request.data['longitude']
    
    stop.save()
    
    # Return updated stop
    serializer = DeliveryStopSerializer(stop)
    return Response(serializer.data, status=status.HTTP_200_OK)


# ==================== STATISTICS & REPORTS ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def delivery_statistics(request):
    """Get overall delivery statistics"""
    
    # Get date range from query params
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    queryset = Delivery.objects.all()
    
    if start_date:
        queryset = queryset.filter(scheduled_date__gte=start_date)
    if end_date:
        queryset = queryset.filter(scheduled_date__lte=end_date)
    
    # Calculate statistics (excluding delivery_efficiency which is a property)
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