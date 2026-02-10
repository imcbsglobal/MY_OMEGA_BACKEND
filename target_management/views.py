# target_management/views.py
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.db.models import Q, Sum, Avg, Count
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q, Sum, Avg, Count, F, Case, When, DecimalField, IntegerField
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta
from decimal import Decimal

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
    TargetAchievementLogSerializer,
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





@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def route_performance_summary(request):
    """
    Comprehensive Route Target Performance Summary
    
    Query Parameters:
    - employee: Filter by employee ID
    - route: Filter by route ID
    - start_date: Filter targets starting from this date
    - end_date: Filter targets ending before this date
    - period: Quick filter (today, week, month, quarter, year)
    """
    
    # Base queryset
    queryset = RouteTargetPeriod.objects.filter(is_active=True).select_related(
        'employee', 'route', 'assigned_by'
    ).prefetch_related('product_details__product')
    
    # Apply filters
    employee_id = request.query_params.get('employee')
    if employee_id:
        queryset = queryset.filter(employee_id=employee_id)
    
    route_id = request.query_params.get('route')
    if route_id:
        queryset = queryset.filter(route_id=route_id)
    
    # Date range filters
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    # Quick period filter
    period = request.query_params.get('period')
    if period:
        today = datetime.now().date()
        if period == 'today':
            queryset = queryset.filter(start_date__lte=today, end_date__gte=today)
        elif period == 'week':
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            queryset = queryset.filter(
                Q(start_date__range=[week_start, week_end]) |
                Q(end_date__range=[week_start, week_end]) |
                Q(start_date__lte=week_start, end_date__gte=week_end)
            )
        elif period == 'month':
            month_start = today.replace(day=1)
            next_month = month_start.replace(day=28) + timedelta(days=4)
            month_end = next_month - timedelta(days=next_month.day)
            queryset = queryset.filter(
                Q(start_date__range=[month_start, month_end]) |
                Q(end_date__range=[month_start, month_end]) |
                Q(start_date__lte=month_start, end_date__gte=month_end)
            )
        elif period == 'quarter':
            quarter = (today.month - 1) // 3
            quarter_start = datetime(today.year, quarter * 3 + 1, 1).date()
            quarter_end = (quarter_start + timedelta(days=92)).replace(day=1) - timedelta(days=1)
            queryset = queryset.filter(
                Q(start_date__range=[quarter_start, quarter_end]) |
                Q(end_date__range=[quarter_start, quarter_end]) |
                Q(start_date__lte=quarter_start, end_date__gte=quarter_end)
            )
        elif period == 'year':
            year_start = datetime(today.year, 1, 1).date()
            year_end = datetime(today.year, 12, 31).date()
            queryset = queryset.filter(
                Q(start_date__range=[year_start, year_end]) |
                Q(end_date__range=[year_start, year_end]) |
                Q(start_date__lte=year_start, end_date__gte=year_end)
            )
    else:
        if start_date:
            queryset = queryset.filter(start_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(end_date__lte=end_date)
    
    # Overall Summary
    overall_summary = queryset.aggregate(
        total_targets=Count('id'),
        total_employees=Count('employee', distinct=True),
        total_routes=Count('route', distinct=True),
        total_target_boxes=Coalesce(Sum('target_boxes'), Decimal('0')),
        total_target_amount=Coalesce(Sum('target_amount'), Decimal('0')),
        total_achieved_boxes=Coalesce(Sum('achieved_boxes'), Decimal('0')),
        total_achieved_amount=Coalesce(Sum('achieved_amount'), Decimal('0')),
    )
    
    # Calculate overall percentages
    if overall_summary['total_target_boxes'] > 0:
        overall_summary['boxes_achievement_percentage'] = float(
            (overall_summary['total_achieved_boxes'] / overall_summary['total_target_boxes']) * 100
        )
    else:
        overall_summary['boxes_achievement_percentage'] = 0.0
    
    if overall_summary['total_target_amount'] > 0:
        overall_summary['amount_achievement_percentage'] = float(
            (overall_summary['total_achieved_amount'] / overall_summary['total_target_amount']) * 100
        )
    else:
        overall_summary['amount_achievement_percentage'] = 0.0
    
    # Performance by Employee
    employee_performance = queryset.values(
        'employee__id',
        'employee__employee_id',
        'employee__first_name',
        'employee__last_name',
        'employee__designation'
    ).annotate(
        total_targets=Count('id'),
        target_boxes=Coalesce(Sum('target_boxes'), Decimal('0')),
        target_amount=Coalesce(Sum('target_amount'), Decimal('0')),
        achieved_boxes=Coalesce(Sum('achieved_boxes'), Decimal('0')),
        achieved_amount=Coalesce(Sum('achieved_amount'), Decimal('0')),
    ).order_by('-achieved_amount')
    
    # Calculate percentages for each employee
    for emp in employee_performance:
        emp['employee_name'] = f"{emp['employee__first_name']} {emp['employee__last_name']}"
        emp['boxes_achievement_percentage'] = float(
            (emp['achieved_boxes'] / emp['target_boxes'] * 100) if emp['target_boxes'] > 0 else 0
        )
        emp['amount_achievement_percentage'] = float(
            (emp['achieved_amount'] / emp['target_amount'] * 100) if emp['target_amount'] > 0 else 0
        )
    
    # Performance by Route
    route_performance = queryset.values(
        'route__id',
        'route__origin',
        'route__destination',
        'route__route_code'
    ).annotate(
        total_targets=Count('id'),
        target_boxes=Coalesce(Sum('target_boxes'), Decimal('0')),
        target_amount=Coalesce(Sum('target_amount'), Decimal('0')),
        achieved_boxes=Coalesce(Sum('achieved_boxes'), Decimal('0')),
        achieved_amount=Coalesce(Sum('achieved_amount'), Decimal('0')),
    ).order_by('-achieved_amount')
    
    # Calculate percentages for each route
    for route in route_performance:
        route['route_name'] = f"{route['route__origin']} → {route['route__destination']}"
        route['boxes_achievement_percentage'] = float(
            (route['achieved_boxes'] / route['target_boxes'] * 100) if route['target_boxes'] > 0 else 0
        )
        route['amount_achievement_percentage'] = float(
            (route['achieved_amount'] / route['target_amount'] * 100) if route['target_amount'] > 0 else 0
        )
    
    # Product-wise Performance
    product_performance = RouteTargetProductDetail.objects.filter(
        route_target_period__in=queryset
    ).values(
        'product__id',
        'product__product_name',
        'product__product_code',
        'product__unit'
    ).annotate(
        target_quantity=Coalesce(Sum('target_quantity'), Decimal('0')),
        achieved_quantity=Coalesce(Sum('achieved_quantity'), Decimal('0')),
    ).order_by('-achieved_quantity')
    
    # Calculate percentages for each product
    for product in product_performance:
        product['achievement_percentage'] = float(
            (product['achieved_quantity'] / product['target_quantity'] * 100) 
            if product['target_quantity'] > 0 else 0
        )
    
    # Achievement Status Distribution
    achievement_distribution = {
        'excellent': queryset.filter(
            achieved_amount__gte=F('target_amount') * 0.9
        ).count(),  # 90%+
        'good': queryset.filter(
            achieved_amount__gte=F('target_amount') * 0.75,
            achieved_amount__lt=F('target_amount') * 0.9
        ).count(),  # 75-89%
        'average': queryset.filter(
            achieved_amount__gte=F('target_amount') * 0.5,
            achieved_amount__lt=F('target_amount') * 0.75
        ).count(),  # 50-74%
        'poor': queryset.filter(
            achieved_amount__lt=F('target_amount') * 0.5
        ).count(),  # <50%
    }
    
    # Recent Targets
    recent_targets = queryset.order_by('-created_at')[:10]
    recent_targets_data = RouteTargetPeriodSerializer(recent_targets, many=True).data
    
    return Response({
        'summary': {
            'overall': overall_summary,
            'achievement_distribution': achievement_distribution,
        },
        'performance': {
            'by_employee': list(employee_performance),
            'by_route': list(route_performance),
            'by_product': list(product_performance),
        },
        'recent_targets': recent_targets_data,
        'filters_applied': {
            'employee_id': employee_id,
            'route_id': route_id,
            'start_date': start_date,
            'end_date': end_date,
            'period': period,
        }
    })


# ==================== CALL TARGET PERFORMANCE SUMMARY ====================

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def call_performance_summary(request):
    """
    Comprehensive Call Target Performance Summary
    
    Query Parameters:
    - employee: Filter by employee ID
    - start_date: Filter targets starting from this date
    - end_date: Filter targets ending before this date
    - period: Quick filter (today, week, month, quarter, year)
    """
    
    # Base queryset
    queryset = CallTargetPeriod.objects.filter(is_active=True).select_related(
        'employee', 'assigned_by'
    ).prefetch_related('daily_targets')
    
    # Apply filters
    employee_id = request.query_params.get('employee')
    if employee_id:
        queryset = queryset.filter(employee_id=employee_id)
    
    # Date range filters
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    # Quick period filter
    period = request.query_params.get('period')
    if period:
        today = datetime.now().date()
        if period == 'today':
            queryset = queryset.filter(start_date__lte=today, end_date__gte=today)
        elif period == 'week':
            week_start = today - timedelta(days=today.weekday())
            week_end = week_start + timedelta(days=6)
            queryset = queryset.filter(
                Q(start_date__range=[week_start, week_end]) |
                Q(end_date__range=[week_start, week_end]) |
                Q(start_date__lte=week_start, end_date__gte=week_end)
            )
        elif period == 'month':
            month_start = today.replace(day=1)
            next_month = month_start.replace(day=28) + timedelta(days=4)
            month_end = next_month - timedelta(days=next_month.day)
            queryset = queryset.filter(
                Q(start_date__range=[month_start, month_end]) |
                Q(end_date__range=[month_start, month_end]) |
                Q(start_date__lte=month_start, end_date__gte=month_end)
            )
    else:
        if start_date:
            queryset = queryset.filter(start_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(end_date__lte=end_date)
    
    # Get all daily targets for the filtered periods
    daily_targets_queryset = CallDailyTarget.objects.filter(
        call_target_period__in=queryset
    )
    
    # Overall Summary
    overall_summary = daily_targets_queryset.aggregate(
        total_periods=Count('call_target_period', distinct=True),
        total_employees=Count('call_target_period__employee', distinct=True),
        total_days=Count('id'),
        total_target_calls=Coalesce(Sum('target_calls'), 0),
        total_achieved_calls=Coalesce(Sum('achieved_calls'), 0),
        total_productive_calls=Coalesce(Sum('productive_calls'), 0),
        total_orders=Coalesce(Sum('order_received'), 0),
        total_order_amount=Coalesce(Sum('order_amount'), Decimal('0')),
        avg_daily_calls=Coalesce(Avg('achieved_calls'), 0),
    )
    
    # Calculate overall percentages
    if overall_summary['total_target_calls'] > 0:
        overall_summary['call_achievement_percentage'] = float(
            (overall_summary['total_achieved_calls'] / overall_summary['total_target_calls']) * 100
        )
    else:
        overall_summary['call_achievement_percentage'] = 0.0
    
    if overall_summary['total_achieved_calls'] > 0:
        overall_summary['productivity_percentage'] = float(
            (overall_summary['total_productive_calls'] / overall_summary['total_achieved_calls']) * 100
        )
        overall_summary['conversion_rate'] = float(
            (overall_summary['total_orders'] / overall_summary['total_achieved_calls']) * 100
        )
    else:
        overall_summary['productivity_percentage'] = 0.0
        overall_summary['conversion_rate'] = 0.0
    
    # Average order value
    if overall_summary['total_orders'] > 0:
        overall_summary['avg_order_value'] = float(
            overall_summary['total_order_amount'] / overall_summary['total_orders']
        )
    else:
        overall_summary['avg_order_value'] = 0.0
    
    # Performance by Employee
    employee_performance = daily_targets_queryset.values(
        'call_target_period__employee__id',
        'call_target_period__employee__employee_id',
        'call_target_period__employee__first_name',
        'call_target_period__employee__last_name',
        'call_target_period__employee__designation'
    ).annotate(
        total_days=Count('id'),
        target_calls=Coalesce(Sum('target_calls'), 0),
        achieved_calls=Coalesce(Sum('achieved_calls'), 0),
        productive_calls=Coalesce(Sum('productive_calls'), 0),
        total_orders=Coalesce(Sum('order_received'), 0),
        total_order_amount=Coalesce(Sum('order_amount'), Decimal('0')),
        avg_daily_calls=Coalesce(Avg('achieved_calls'), 0),
    ).order_by('-achieved_calls')
    
    # Calculate percentages for each employee
    for emp in employee_performance:
        emp['employee_name'] = f"{emp['call_target_period__employee__first_name']} {emp['call_target_period__employee__last_name']}"
        emp['achievement_percentage'] = float(
            (emp['achieved_calls'] / emp['target_calls'] * 100) if emp['target_calls'] > 0 else 0
        )
        emp['productivity_percentage'] = float(
            (emp['productive_calls'] / emp['achieved_calls'] * 100) if emp['achieved_calls'] > 0 else 0
        )
        emp['conversion_rate'] = float(
            (emp['total_orders'] / emp['achieved_calls'] * 100) if emp['achieved_calls'] > 0 else 0
        )
        emp['avg_order_value'] = float(
            emp['total_order_amount'] / emp['total_orders'] if emp['total_orders'] > 0 else 0
        )
    
    # Daily Trend Analysis (last 30 days or filtered period)
    if period == 'today':
        trend_days = 1
    elif period == 'week':
        trend_days = 7
    elif period == 'month':
        trend_days = 30
    else:
        trend_days = 30
    
    trend_start = datetime.now().date() - timedelta(days=trend_days)
    
    daily_trend = CallDailyTarget.objects.filter(
        call_target_period__in=queryset,
        target_date__gte=trend_start
    ).values('target_date').annotate(
        target_calls=Coalesce(Sum('target_calls'), 0),
        achieved_calls=Coalesce(Sum('achieved_calls'), 0),
        productive_calls=Coalesce(Sum('productive_calls'), 0),
        orders=Coalesce(Sum('order_received'), 0),
        order_amount=Coalesce(Sum('order_amount'), Decimal('0')),
    ).order_by('target_date')
    
    # Calculate trend percentages
    for day in daily_trend:
        day['achievement_percentage'] = float(
            (day['achieved_calls'] / day['target_calls'] * 100) if day['target_calls'] > 0 else 0
        )
        day['productivity_percentage'] = float(
            (day['productive_calls'] / day['achieved_calls'] * 100) if day['achieved_calls'] > 0 else 0
        )
    
    # Achievement Status Distribution
    achievement_distribution = {
        'excellent': daily_targets_queryset.filter(
            achieved_calls__gte=F('target_calls') * 0.9
        ).count(),  # 90%+
        'good': daily_targets_queryset.filter(
            achieved_calls__gte=F('target_calls') * 0.75,
            achieved_calls__lt=F('target_calls') * 0.9
        ).count(),  # 75-89%
        'average': daily_targets_queryset.filter(
            achieved_calls__gte=F('target_calls') * 0.5,
            achieved_calls__lt=F('target_calls') * 0.75
        ).count(),  # 50-74%
        'poor': daily_targets_queryset.filter(
            achieved_calls__lt=F('target_calls') * 0.5
        ).count(),  # <50%
    }
    
    # Top Performers (by achievement percentage)
    top_days = daily_targets_queryset.annotate(
        achievement_pct=Case(
            When(target_calls__gt=0, then=F('achieved_calls') * 100.0 / F('target_calls')),
            default=0.0,
            output_field=DecimalField()
        )
    ).filter(achievement_pct__gte=90).select_related(
        'call_target_period__employee'
    ).order_by('-achievement_pct')[:10]
    
    top_performers = CallDailyTargetSerializer(top_days, many=True).data
    
    # Recent Activity
    recent_activity = daily_targets_queryset.order_by('-target_date')[:10]
    recent_activity_data = CallDailyTargetSerializer(recent_activity, many=True).data
    
    return Response({
        'summary': {
            'overall': overall_summary,
            'achievement_distribution': achievement_distribution,
        },
        'performance': {
            'by_employee': list(employee_performance),
            'daily_trend': list(daily_trend),
        },
        'top_performers': top_performers,
        'recent_activity': recent_activity_data,
        'filters_applied': {
            'employee_id': employee_id,
            'start_date': start_date,
            'end_date': end_date,
            'period': period,
        }
    })


# ==================== DETAILED EMPLOYEE REPORTS ====================

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def employee_detailed_report(request, employee_id):
    """
    Comprehensive detailed report for a specific employee
    Includes both Route Targets and Call Targets
    """
    from employee_management.models import Employee
    
    employee = get_object_or_404(Employee, pk=employee_id)
    
    # Get date range from query params
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    # Route Targets
    route_targets_queryset = RouteTargetPeriod.objects.filter(
        employee=employee,
        is_active=True
    ).select_related('route', 'assigned_by').prefetch_related('product_details__product')
    
    if start_date:
        route_targets_queryset = route_targets_queryset.filter(start_date__gte=start_date)
    if end_date:
        route_targets_queryset = route_targets_queryset.filter(end_date__lte=end_date)
    
    # Call Targets
    call_targets_queryset = CallTargetPeriod.objects.filter(
        employee=employee,
        is_active=True
    ).prefetch_related('daily_targets')
    
    if start_date:
        call_targets_queryset = call_targets_queryset.filter(start_date__gte=start_date)
    if end_date:
        call_targets_queryset = call_targets_queryset.filter(end_date__lte=end_date)
    
    # Route Summary
    route_summary = route_targets_queryset.aggregate(
        total_targets=Count('id'),
        total_routes=Count('route', distinct=True),
        target_boxes=Coalesce(Sum('target_boxes'), Decimal('0')),
        target_amount=Coalesce(Sum('target_amount'), Decimal('0')),
        achieved_boxes=Coalesce(Sum('achieved_boxes'), Decimal('0')),
        achieved_amount=Coalesce(Sum('achieved_amount'), Decimal('0')),
    )
    
    # Calculate route percentages
    if route_summary['target_boxes'] > 0:
        route_summary['boxes_achievement_percentage'] = float(
            (route_summary['achieved_boxes'] / route_summary['target_boxes']) * 100
        )
    else:
        route_summary['boxes_achievement_percentage'] = 0.0
    
    if route_summary['target_amount'] > 0:
        route_summary['amount_achievement_percentage'] = float(
            (route_summary['achieved_amount'] / route_summary['target_amount']) * 100
        )
    else:
        route_summary['amount_achievement_percentage'] = 0.0
    
    # Call Summary
    daily_calls = CallDailyTarget.objects.filter(
        call_target_period__in=call_targets_queryset
    )
    
    call_summary = daily_calls.aggregate(
        total_periods=Count('call_target_period', distinct=True),
        total_days=Count('id'),
        target_calls=Coalesce(Sum('target_calls'), 0),
        achieved_calls=Coalesce(Sum('achieved_calls'), 0),
        productive_calls=Coalesce(Sum('productive_calls'), 0),
        total_orders=Coalesce(Sum('order_received'), 0),
        total_order_amount=Coalesce(Sum('order_amount'), Decimal('0')),
    )
    
    # Calculate call percentages
    if call_summary['target_calls'] > 0:
        call_summary['achievement_percentage'] = float(
            (call_summary['achieved_calls'] / call_summary['target_calls']) * 100
        )
    else:
        call_summary['achievement_percentage'] = 0.0
    
    if call_summary['achieved_calls'] > 0:
        call_summary['productivity_percentage'] = float(
            (call_summary['productive_calls'] / call_summary['achieved_calls']) * 100
        )
        call_summary['conversion_rate'] = float(
            (call_summary['total_orders'] / call_summary['achieved_calls']) * 100
        )
    else:
        call_summary['productivity_percentage'] = 0.0
        call_summary['conversion_rate'] = 0.0
    
    # Detailed Route Targets
    route_targets = RouteTargetPeriodSerializer(
        route_targets_queryset.order_by('-start_date'), many=True
    ).data
    
    # Detailed Call Targets
    call_targets = CallTargetPeriodSerializer(
        call_targets_queryset.order_by('-start_date'), many=True
    ).data
    
    # Performance by Route
    route_performance = route_targets_queryset.values(
        'route__id',
        'route__origin',
        'route__destination',
        'route__route_code'
    ).annotate(
        target_boxes=Coalesce(Sum('target_boxes'), Decimal('0')),
        target_amount=Coalesce(Sum('target_amount'), Decimal('0')),
        achieved_boxes=Coalesce(Sum('achieved_boxes'), Decimal('0')),
        achieved_amount=Coalesce(Sum('achieved_amount'), Decimal('0')),
    ).order_by('-achieved_amount')
    
    for route in route_performance:
        route['route_name'] = f"{route['route__origin']} → {route['route__destination']}"
        route['boxes_achievement_percentage'] = float(
            (route['achieved_boxes'] / route['target_boxes'] * 100) if route['target_boxes'] > 0 else 0
        )
        route['amount_achievement_percentage'] = float(
            (route['achieved_amount'] / route['target_amount'] * 100) if route['target_amount'] > 0 else 0
        )
    
    return Response({
        'employee': {
            'id': employee.id,
            'employee_id': employee.employee_id,
            'name': employee.get_full_name(),
            'designation': employee.designation,
            'department': employee.department,
            'email': employee.email,
            'phone': employee.phone,
        },
        'summary': {
            'route_targets': route_summary,
            'call_targets': call_summary,
        },
        'detailed_data': {
            'route_targets': route_targets,
            'call_targets': call_targets,
            'route_performance': list(route_performance),
        },
        'filters_applied': {
            'start_date': start_date,
            'end_date': end_date,
        }
    })


# ==================== COMPARISON REPORTS ====================

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def comparative_performance_report(request):
    """
    Compare performance across multiple employees
    
    Query Parameters:
    - employees: Comma-separated list of employee IDs
    - start_date: Start date for comparison
    - end_date: End date for comparison
    - metric: route_targets, call_targets, or both (default: both)
    """
    
    employee_ids = request.query_params.get('employees', '').split(',')
    employee_ids = [eid.strip() for eid in employee_ids if eid.strip()]
    
    if not employee_ids:
        return Response({
            'error': 'Please provide at least one employee ID'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    metric = request.query_params.get('metric', 'both')
    
    comparison_data = []
    
    from employee_management.models import Employee
    
    for emp_id in employee_ids:
        try:
            employee = Employee.objects.get(pk=emp_id)
            emp_data = {
                'employee_id': employee.id,
                'employee_code': employee.employee_id,
                'name': employee.get_full_name(),
                'designation': employee.designation,
            }
            
            # Route Targets
            if metric in ['route_targets', 'both']:
                route_queryset = RouteTargetPeriod.objects.filter(
                    employee=employee,
                    is_active=True
                )
                if start_date:
                    route_queryset = route_queryset.filter(start_date__gte=start_date)
                if end_date:
                    route_queryset = route_queryset.filter(end_date__lte=end_date)
                
                route_data = route_queryset.aggregate(
                    target_boxes=Coalesce(Sum('target_boxes'), Decimal('0')),
                    target_amount=Coalesce(Sum('target_amount'), Decimal('0')),
                    achieved_boxes=Coalesce(Sum('achieved_boxes'), Decimal('0')),
                    achieved_amount=Coalesce(Sum('achieved_amount'), Decimal('0')),
                )
                
                route_data['boxes_achievement_percentage'] = float(
                    (route_data['achieved_boxes'] / route_data['target_boxes'] * 100) 
                    if route_data['target_boxes'] > 0 else 0
                )
                route_data['amount_achievement_percentage'] = float(
                    (route_data['achieved_amount'] / route_data['target_amount'] * 100) 
                    if route_data['target_amount'] > 0 else 0
                )
                
                emp_data['route_performance'] = route_data
            
            # Call Targets
            if metric in ['call_targets', 'both']:
                call_queryset = CallTargetPeriod.objects.filter(
                    employee=employee,
                    is_active=True
                )
                if start_date:
                    call_queryset = call_queryset.filter(start_date__gte=start_date)
                if end_date:
                    call_queryset = call_queryset.filter(end_date__lte=end_date)
                
                call_daily = CallDailyTarget.objects.filter(
                    call_target_period__in=call_queryset
                )
                
                call_data = call_daily.aggregate(
                    target_calls=Coalesce(Sum('target_calls'), 0),
                    achieved_calls=Coalesce(Sum('achieved_calls'), 0),
                    productive_calls=Coalesce(Sum('productive_calls'), 0),
                    total_orders=Coalesce(Sum('order_received'), 0),
                    total_order_amount=Coalesce(Sum('order_amount'), Decimal('0')),
                )
                
                call_data['achievement_percentage'] = float(
                    (call_data['achieved_calls'] / call_data['target_calls'] * 100) 
                    if call_data['target_calls'] > 0 else 0
                )
                call_data['productivity_percentage'] = float(
                    (call_data['productive_calls'] / call_data['achieved_calls'] * 100) 
                    if call_data['achieved_calls'] > 0 else 0
                )
                
                emp_data['call_performance'] = call_data
            
            comparison_data.append(emp_data)
            
        except Employee.DoesNotExist:
            continue
    
    return Response({
        'comparison': comparison_data,
        'filters_applied': {
            'employee_ids': employee_ids,
            'start_date': start_date,
            'end_date': end_date,
            'metric': metric,
        }
    })










# ==================== EMPLOYEE VIEWS - MY TARGETS ====================

@api_view(['GET'])
@permission_classes([permissions.AllowAny])  # Change to IsAuthenticated in production
def employee_my_targets(request):
    """
    Get current employee's assigned targets (both route and call targets)
    
    Query Parameters:
    - status: active, completed, upcoming, all (default: active)
    - type: route, call, both (default: both)
    """
    # In production, get employee from authenticated user
    # For now, require employee_id as a parameter
    employee_id = request.query_params.get('employee_id')
    
    if not employee_id:
        return Response({
            'error': 'employee_id parameter is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    from employee_management.models import Employee
    
    try:
        employee = Employee.objects.get(pk=employee_id)
    except Employee.DoesNotExist:
        return Response({
            'error': 'Employee not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    target_status = request.query_params.get('status', 'active')
    target_type = request.query_params.get('type', 'both')
    
    from datetime import date
    today = date.today()
    
    response_data = {
        'employee': {
            'id': employee.id,
            'employee_id': employee.employee_id,
            'name': employee.get_full_name(),
            'designation': employee.designation,
            'department': employee.department,
        }
    }
    
    # Route Targets
    if target_type in ['route', 'both']:
        route_queryset = RouteTargetPeriod.objects.filter(
            employee=employee
        ).select_related('route', 'assigned_by').prefetch_related('product_details__product')
        
        # Filter by status
        if target_status == 'active':
            route_queryset = route_queryset.filter(
                is_active=True,
                start_date__lte=today,
                end_date__gte=today
            )
        elif target_status == 'completed':
            route_queryset = route_queryset.filter(end_date__lt=today)
        elif target_status == 'upcoming':
            route_queryset = route_queryset.filter(start_date__gt=today)
        elif target_status == 'all':
            pass  # No additional filter
        
        from .serializers import EmployeeRouteTargetSerializer
        route_targets = EmployeeRouteTargetSerializer(
            route_queryset.order_by('-start_date'), many=True
        ).data
        
        response_data['route_targets'] = route_targets
    
    # Call Targets
    if target_type in ['call', 'both']:
        call_queryset = CallTargetPeriod.objects.filter(
            employee=employee
        ).select_related('assigned_by').prefetch_related('daily_targets')
        
        # Filter by status
        if target_status == 'active':
            call_queryset = call_queryset.filter(
                is_active=True,
                start_date__lte=today,
                end_date__gte=today
            )
        elif target_status == 'completed':
            call_queryset = call_queryset.filter(end_date__lt=today)
        elif target_status == 'upcoming':
            call_queryset = call_queryset.filter(start_date__gt=today)
        elif target_status == 'all':
            pass
        
        from .serializers import EmployeeCallTargetSerializer
        call_targets = EmployeeCallTargetSerializer(
            call_queryset.order_by('-start_date'), many=True
        ).data
        
        response_data['call_targets'] = call_targets
    
    return Response(response_data)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])  # Change to IsAuthenticated in production
def update_route_achievement(request, target_id):
    """
    Update route target achievement
    
    POST Body:
    {
        "achieved_boxes": 100.50,
        "achieved_amount": 50000.00,
        "product_achievements": [
            {"product_id": 1, "achieved_quantity": 50},
            {"product_id": 2, "achieved_quantity": 30}
        ],
        "notes": "Updated achievement for today"
    }
    """
    from .serializers import UpdateRouteAchievementSerializer, EmployeeRouteTargetSerializer
    
    try:
        route_target = RouteTargetPeriod.objects.select_related(
            'route', 'employee'
        ).prefetch_related('product_details__product').get(pk=target_id)
    except RouteTargetPeriod.DoesNotExist:
        return Response({
            'error': 'Route target not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # In production, verify that the employee owns this target
    # if route_target.employee != request.user.employee:
    #     return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    serializer = UpdateRouteAchievementSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    
    # Update main achievement fields
    if 'achieved_boxes' in data:
        route_target.achieved_boxes = data['achieved_boxes']
    if 'achieved_amount' in data:
        route_target.achieved_amount = data['achieved_amount']
    if 'notes' in data:
        route_target.notes = data['notes']
    
    route_target.save()
    
    # Update product-wise achievements
    if 'product_achievements' in data:
        for prod_achievement in data['product_achievements']:
            product_id = prod_achievement['product_id']
            achieved_qty = prod_achievement['achieved_quantity']
            
            # Update or create product detail
            RouteTargetProductDetail.objects.update_or_create(
                route_target_period=route_target,
                product_id=product_id,
                defaults={'achieved_quantity': achieved_qty}
            )
    
    # Create achievement log
    TargetAchievementLog.objects.create(
        log_type='route',
        employee=route_target.employee,
        route_target=route_target,
        achievement_date=timezone.now().date(),
        achievement_value=data.get('achieved_amount', route_target.achieved_amount),
        remarks=data.get('notes', ''),
        recorded_by=request.user if request.user.is_authenticated else None
    )
    
    # Return updated target
    updated_target = EmployeeRouteTargetSerializer(route_target).data
    
    return Response({
        'message': 'Route achievement updated successfully',
        'target': updated_target
    })


@api_view(['POST'])
@permission_classes([permissions.AllowAny])  # Change to IsAuthenticated in production
def update_call_daily_achievement(request, daily_target_id):
    """
    Update daily call target achievement
    
    POST Body:
    {
        "achieved_calls": 15,
        "productive_calls": 12,
        "order_received": 5,
        "order_amount": 25000.00,
        "remarks": "Good day, most clients were responsive"
    }
    """
    from .serializers import UpdateCallDailyAchievementSerializer
    
    try:
        daily_target = CallDailyTarget.objects.select_related(
            'call_target_period__employee'
        ).get(pk=daily_target_id)
    except CallDailyTarget.DoesNotExist:
        return Response({
            'error': 'Call daily target not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # In production, verify that the employee owns this target
    # if daily_target.call_target_period.employee != request.user.employee:
    #     return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    serializer = UpdateCallDailyAchievementSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    
    # Update fields
    if 'achieved_calls' in data:
        daily_target.achieved_calls = data['achieved_calls']
    if 'productive_calls' in data:
        daily_target.productive_calls = data['productive_calls']
    if 'order_received' in data:
        daily_target.order_received = data['order_received']
    if 'order_amount' in data:
        daily_target.order_amount = data['order_amount']
    if 'remarks' in data:
        daily_target.remarks = data['remarks']
    
    daily_target.save()
    
    # Create achievement log
    TargetAchievementLog.objects.create(
        log_type='call',
        employee=daily_target.call_target_period.employee,
        call_daily_target=daily_target,
        achievement_date=daily_target.target_date,
        achievement_value=data.get('achieved_calls', daily_target.achieved_calls),
        remarks=data.get('remarks', ''),
        recorded_by=request.user if request.user.is_authenticated else None
    )
    
    # Return updated daily target
    from .serializers import CallDailyTargetSerializer
    updated_daily_target = CallDailyTargetSerializer(daily_target).data
    
    return Response({
        'message': 'Daily call achievement updated successfully',
        'daily_target': updated_daily_target
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def employee_today_targets(request):
    """
    Get today's targets for an employee (quick view for daily operations)
    
    Query Parameters:
    - employee_id: Required employee ID
    
    Returns:
    - Today's call targets
    - Active route targets
    - Quick summary
    """
    employee_id = request.query_params.get('employee_id')
    
    if not employee_id:
        return Response({
            'error': 'employee_id parameter is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    from employee_management.models import Employee
    from datetime import date
    
    try:
        employee = Employee.objects.get(pk=employee_id)
    except Employee.DoesNotExist:
        return Response({
            'error': 'Employee not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    today = date.today()
    
    # Get today's call target
    from .serializers import CallDailyTargetSerializer
    today_call_target = CallDailyTarget.objects.filter(
        call_target_period__employee=employee,
        call_target_period__is_active=True,
        target_date=today
    ).select_related('call_target_period').first()
    
    # Get active route targets
    from .serializers import EmployeeRouteTargetSerializer
    active_route_targets = RouteTargetPeriod.objects.filter(
        employee=employee,
        is_active=True,
        start_date__lte=today,
        end_date__gte=today
    ).select_related('route').prefetch_related('product_details__product')
    
    response_data = {
        'employee': {
            'id': employee.id,
            'employee_id': employee.employee_id,
            'name': employee.get_full_name(),
            'designation': employee.designation,
        },
        'date': str(today),
        'day_name': today.strftime('%A'),
        'today_call_target': CallDailyTargetSerializer(today_call_target).data if today_call_target else None,
        'active_route_targets': EmployeeRouteTargetSerializer(active_route_targets, many=True).data,
        'summary': {
            'total_calls_target': today_call_target.target_calls if today_call_target else 0,
            'calls_achieved': today_call_target.achieved_calls if today_call_target else 0,
            'active_route_targets_count': active_route_targets.count(),
        }
    }
    
    return Response(response_data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def employee_achievement_history(request):
    """
    Get employee's achievement history/logs
    
    Query Parameters:
    - employee_id: Required
    - log_type: route, call, or both (default: both)
    - start_date: Filter from date
    - end_date: Filter to date
    - limit: Number of records (default: 50)
    """
    employee_id = request.query_params.get('employee_id')
    
    if not employee_id:
        return Response({
            'error': 'employee_id parameter is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    from employee_management.models import Employee
    
    try:
        employee = Employee.objects.get(pk=employee_id)
    except Employee.DoesNotExist:
        return Response({
            'error': 'Employee not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    log_type = request.query_params.get('log_type', 'both')
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    limit = int(request.query_params.get('limit', 50))
    
    queryset = TargetAchievementLog.objects.filter(
        employee=employee
    ).select_related('recorded_by', 'route_target', 'call_daily_target')
    
    if log_type != 'both':
        queryset = queryset.filter(log_type=log_type)
    
    if start_date:
        queryset = queryset.filter(achievement_date__gte=start_date)
    if end_date:
        queryset = queryset.filter(achievement_date__lte=end_date)
    
    queryset = queryset.order_by('-achievement_date', '-created_at')[:limit]
    
    serializer = TargetAchievementLogSerializer(queryset, many=True)
    
    return Response({
        'employee': {
            'id': employee.id,
            'employee_id': employee.employee_id,
            'name': employee.get_full_name(),
        },
        'total_logs': queryset.count(),
        'logs': serializer.data
    })