# target_management/views.py
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.db.models import Q, Sum, Avg, Count
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta

from .models import (
    Route, Product, RouteTargetPeriod, RouteTargetProductDetail,
    CallTargetPeriod, CallDailyTarget, TargetAchievementLog
)
from .serializers import (
    RouteSerializer, RouteDetailSerializer,
    ProductSerializer, ProductDetailSerializer,
    RouteTargetPeriodSerializer, RouteTargetPeriodDetailSerializer,
    RouteTargetProductDetailSerializer,
    CallTargetPeriodSerializer, CallTargetPeriodDetailSerializer,
    CallDailyTargetSerializer,
    TargetAchievementLogSerializer
)


# ==================== ROUTE MASTER VIEWS ====================

class RouteListCreateView(generics.ListCreateAPIView):
    """
    GET: List all routes
    POST: Create new route
    """
    queryset = Route.objects.select_related('created_by').all()
    permission_classes = [permissions.AllowAny]  # Change to IsAuthenticated in production
    serializer_class = RouteSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Search
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(origin__icontains=search) |
                Q(destination__icontains=search) |
                Q(route_code__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset.order_by('origin', 'destination')
    
    def perform_create(self, serializer):
        try:
            if self.request.user.is_authenticated:
                serializer.save(created_by=self.request.user)
            else:
                serializer.save()
        except IntegrityError as e:
            # Handle unique constraint violations that weren't caught by serializer
            error_message = str(e).lower()
            
            if 'unique_together' in error_message or 'unique constraint' in error_message:
                if 'origin' in error_message and 'destination' in error_message:
                    raise ValidationError({
                        'detail': 'A route with this origin and destination already exists.'
                    })
                elif 'route_code' in error_message:
                    raise ValidationError({
                        'route_code': 'This route code already exists. Please use a unique code.'
                    })
            
            # Generic integrity error
            raise ValidationError({
                'detail': 'Unable to create route due to a database constraint. Please check your input.'
            })


class RouteDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve route detail
    PUT/PATCH: Update route
    DELETE: Delete route
    """
    queryset = Route.objects.select_related('created_by').all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RouteDetailSerializer
    
    def perform_update(self, serializer):
        try:
            serializer.save()
        except IntegrityError as e:
            error_message = str(e).lower()
            
            if 'unique_together' in error_message or 'unique constraint' in error_message:
                if 'origin' in error_message and 'destination' in error_message:
                    raise ValidationError({
                        'detail': 'A route with this origin and destination already exists.'
                    })
                elif 'route_code' in error_message:
                    raise ValidationError({
                        'route_code': 'This route code already exists. Please use a unique code.'
                    })
            
            raise ValidationError({
                'detail': 'Unable to update route due to a database constraint.'
            })


# ==================== PRODUCT MASTER VIEWS ====================

class ProductListCreateView(generics.ListCreateAPIView):
    """
    GET: List all products
    POST: Create new product
    """
    queryset = Product.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = ProductSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Search
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(product_name__icontains=search) |
                Q(product_code__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset.order_by('product_name')


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve product detail
    PUT/PATCH: Update product
    DELETE: Delete product
    """
    queryset = Product.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = ProductDetailSerializer


# ==================== ROUTE TARGET VIEWS ====================

class RouteTargetPeriodListCreateView(generics.ListCreateAPIView):
    """
    GET: List all route target periods
    POST: Create new route target period
    """
    queryset = RouteTargetPeriod.objects.select_related(
        'employee', 'route', 'assigned_by'
    ).prefetch_related('product_details__product').all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RouteTargetPeriodSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by employee
        employee_id = self.request.query_params.get('employee', None)
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        
        # Filter by route
        route_id = self.request.query_params.get('route', None)
        if route_id:
            queryset = queryset.filter(route_id=route_id)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        if start_date:
            queryset = queryset.filter(start_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(end_date__lte=end_date)
        
        return queryset.order_by('-start_date')
    
    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(assigned_by=self.request.user)
        else:
            serializer.save()


class RouteTargetPeriodDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve route target period detail
    PUT/PATCH: Update route target period
    DELETE: Delete route target period
    """
    queryset = RouteTargetPeriod.objects.select_related(
        'employee', 'route', 'assigned_by'
    ).prefetch_related('product_details__product').all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RouteTargetPeriodDetailSerializer


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def bulk_create_route_targets(request):
    """
    Bulk create route targets for multiple employees
    Expects: {
        "employees": [1, 2, 3],
        "start_date": "2024-01-01",
        "end_date": "2024-01-07",
        "route": 1,
        "target_boxes": 100,
        "target_amount": 50000,
        "notes": "Weekly target",
        "product_details": [...]
    }
    """
    employee_ids = request.data.get('employees', [])
    if not employee_ids:
        return Response(
            {'error': 'No employees selected'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    created_targets = []
    errors = []
    
    for emp_id in employee_ids:
        try:
            data = request.data.copy()
            data['employee'] = emp_id
            
            serializer = RouteTargetPeriodSerializer(data=data, context={'request': request})
            if serializer.is_valid():
                target = serializer.save(
                    assigned_by=request.user if request.user.is_authenticated else None
                )
                created_targets.append(serializer.data)
            else:
                errors.append({
                    'employee_id': emp_id,
                    'errors': serializer.errors
                })
        except Exception as e:
            errors.append({
                'employee_id': emp_id,
                'errors': str(e)
            })
    
    return Response({
        'created': len(created_targets),
        'failed': len(errors),
        'targets': created_targets,
        'errors': errors
    }, status=status.HTTP_201_CREATED if created_targets else status.HTTP_400_BAD_REQUEST)


# ==================== CALL TARGET VIEWS ====================

class CallTargetPeriodListCreateView(generics.ListCreateAPIView):
    """
    GET: List all call target periods
    POST: Create new call target period
    """
    queryset = CallTargetPeriod.objects.select_related(
        'employee', 'assigned_by'
    ).prefetch_related('daily_targets').all()
    permission_classes = [permissions.AllowAny]
    serializer_class = CallTargetPeriodSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by employee
        employee_id = self.request.query_params.get('employee', None)
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        if start_date:
            queryset = queryset.filter(start_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(end_date__lte=end_date)
        
        return queryset.order_by('-start_date')
    
    def perform_create(self, serializer):
        if self.request.user.is_authenticated:
            serializer.save(assigned_by=self.request.user)
        else:
            serializer.save()


class CallTargetPeriodDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve call target period detail
    PUT/PATCH: Update call target period
    DELETE: Delete call target period
    """
    queryset = CallTargetPeriod.objects.select_related(
        'employee', 'assigned_by'
    ).prefetch_related('daily_targets').all()
    permission_classes = [permissions.AllowAny]
    serializer_class = CallTargetPeriodDetailSerializer


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def bulk_create_call_targets(request):
    """
    Bulk create call targets for multiple employees
    Expects: {
        "employees": [1, 2, 3],
        "start_date": "2024-01-01",
        "end_date": "2024-01-07",
        "notes": "Weekly call targets",
        "daily_targets": [...]
    }
    """
    employee_ids = request.data.get('employees', [])
    if not employee_ids:
        return Response(
            {'error': 'No employees selected'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    created_targets = []
    errors = []
    
    for emp_id in employee_ids:
        try:
            data = request.data.copy()
            data['employee'] = emp_id
            
            serializer = CallTargetPeriodSerializer(data=data, context={'request': request})
            if serializer.is_valid():
                target = serializer.save(
                    assigned_by=request.user if request.user.is_authenticated else None
                )
                created_targets.append(serializer.data)
            else:
                errors.append({
                    'employee_id': emp_id,
                    'errors': serializer.errors
                })
        except Exception as e:
            errors.append({
                'employee_id': emp_id,
                'errors': str(e)
            })
    
    return Response({
        'created': len(created_targets),
        'failed': len(errors),
        'targets': created_targets,
        'errors': errors
    }, status=status.HTTP_201_CREATED if created_targets else status.HTTP_400_BAD_REQUEST)


# ==================== CALL DAILY TARGET VIEWS ====================

class CallDailyTargetUpdateView(generics.RetrieveUpdateAPIView):
    """
    GET: Retrieve call daily target
    PATCH: Update achievement for a specific day
    """
    queryset = CallDailyTarget.objects.select_related(
        'call_target_period__employee'
    ).all()
    permission_classes = [permissions.AllowAny]
    serializer_class = CallDailyTargetSerializer


# ==================== REPORTS & ANALYTICS ====================

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def route_target_summary(request):
    """
    Get summary of route targets
    """
    queryset = RouteTargetPeriod.objects.filter(is_active=True)
    
    # Filter by employee
    employee_id = request.query_params.get('employee', None)
    if employee_id:
        queryset = queryset.filter(employee_id=employee_id)
    
    # Filter by date range
    start_date = request.query_params.get('start_date', None)
    end_date = request.query_params.get('end_date', None)
    if start_date:
        queryset = queryset.filter(start_date__gte=start_date)
    if end_date:
        queryset = queryset.filter(end_date__lte=end_date)
    
    summary = queryset.aggregate(
        total_targets=Count('id'),
        total_target_boxes=Sum('target_boxes'),
        total_target_amount=Sum('target_amount'),
        total_achieved_boxes=Sum('achieved_boxes'),
        total_achieved_amount=Sum('achieved_amount'),
    )
    
    # Calculate percentages
    if summary['total_target_boxes'] and summary['total_target_boxes'] > 0:
        summary['boxes_achievement_percentage'] = (
            summary['total_achieved_boxes'] / summary['total_target_boxes']
        ) * 100
    else:
        summary['boxes_achievement_percentage'] = 0
    
    if summary['total_target_amount'] and summary['total_target_amount'] > 0:
        summary['amount_achievement_percentage'] = (
            summary['total_achieved_amount'] / summary['total_target_amount']
        ) * 100
    else:
        summary['amount_achievement_percentage'] = 0
    
    return Response(summary)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def call_target_summary(request):
    """
    Get summary of call targets
    """
    queryset = CallTargetPeriod.objects.filter(is_active=True)
    
    # Filter by employee
    employee_id = request.query_params.get('employee', None)
    if employee_id:
        queryset = queryset.filter(employee_id=employee_id)
    
    # Filter by date range
    start_date = request.query_params.get('start_date', None)
    end_date = request.query_params.get('end_date', None)
    if start_date:
        queryset = queryset.filter(start_date__gte=start_date)
    if end_date:
        queryset = queryset.filter(end_date__lte=end_date)
    
    # Get daily targets
    daily_targets = CallDailyTarget.objects.filter(
        call_target_period__in=queryset
    ).aggregate(
        total_target_calls=Sum('target_calls'),
        total_achieved_calls=Sum('achieved_calls'),
        total_productive_calls=Sum('productive_calls'),
        total_orders=Sum('order_received'),
        total_order_amount=Sum('order_amount'),
    )
    
    # Calculate percentages
    if daily_targets['total_target_calls'] and daily_targets['total_target_calls'] > 0:
        daily_targets['call_achievement_percentage'] = (
            daily_targets['total_achieved_calls'] / daily_targets['total_target_calls']
        ) * 100
    else:
        daily_targets['call_achievement_percentage'] = 0
    
    if daily_targets['total_achieved_calls'] and daily_targets['total_achieved_calls'] > 0:
        daily_targets['productivity_percentage'] = (
            daily_targets['total_productive_calls'] / daily_targets['total_achieved_calls']
        ) * 100
    else:
        daily_targets['productivity_percentage'] = 0
    
    return Response({
        'total_periods': queryset.count(),
        **daily_targets
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def employee_performance_dashboard(request, employee_id):
    """
    Get comprehensive performance dashboard for an employee
    """
    from employee_management.models import Employee
    
    employee = get_object_or_404(Employee, pk=employee_id)
    
    # Route targets
    route_targets = RouteTargetPeriod.objects.filter(
        employee=employee,
        is_active=True
    ).select_related('route').prefetch_related('product_details__product')
    
    # Call targets
    call_targets = CallTargetPeriod.objects.filter(
        employee=employee,
        is_active=True
    ).prefetch_related('daily_targets')
    
    # Serialize data
    route_data = RouteTargetPeriodSerializer(route_targets, many=True).data
    call_data = CallTargetPeriodSerializer(call_targets, many=True).data
    
    # Calculate summary
    route_summary = route_targets.aggregate(
        total_target_boxes=Sum('target_boxes'),
        total_target_amount=Sum('target_amount'),
        total_achieved_boxes=Sum('achieved_boxes'),
        total_achieved_amount=Sum('achieved_amount'),
    )
    
    daily_targets = CallDailyTarget.objects.filter(
        call_target_period__in=call_targets
    ).aggregate(
        total_target_calls=Sum('target_calls'),
        total_achieved_calls=Sum('achieved_calls'),
        total_productive_calls=Sum('productive_calls'),
    )
    
    return Response({
        'employee': {
            'id': employee.id,
            'employee_id': employee.employee_id,
            'name': employee.get_full_name(),
            'designation': employee.designation,
            'department': employee.department,
        },
        'route_targets': route_data,
        'call_targets': call_data,
        'summary': {
            'route': route_summary,
            'calls': daily_targets
        }
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def target_achievement_logs(request):
    """
    Get target achievement logs
    """
    queryset = TargetAchievementLog.objects.select_related(
        'employee', 'recorded_by', 'route_target', 'call_daily_target'
    ).all()
    
    # Filter by employee
    employee_id = request.query_params.get('employee', None)
    if employee_id:
        queryset = queryset.filter(employee_id=employee_id)
    
    # Filter by log type
    log_type = request.query_params.get('log_type', None)
    if log_type:
        queryset = queryset.filter(log_type=log_type)
    
    # Filter by date range
    start_date = request.query_params.get('start_date', None)
    end_date = request.query_params.get('end_date', None)
    if start_date:
        queryset = queryset.filter(achievement_date__gte=start_date)
    if end_date:
        queryset = queryset.filter(achievement_date__lte=end_date)
    
    serializer = TargetAchievementLogSerializer(queryset, many=True)
    return Response(serializer.data)