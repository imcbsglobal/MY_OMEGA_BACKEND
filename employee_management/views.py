# employee_management/views.py
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q

from .models import Employee
from .serializers import (
    EmployeeDetailSerializer,
    EmployeeListSerializer,
    EmployeeCreateUpdateSerializer
)


class EmployeeListAPIView(generics.ListCreateAPIView):
    """
    GET: List all employees
    POST: Create new employee
    """
    queryset = Employee.objects.select_related('user').all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return EmployeeCreateUpdateSerializer
        return EmployeeListSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Search
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(employee_code__icontains=search) |
                Q(user__name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(designation__icontains=search) |
                Q(department__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class EmployeeDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve employee detail
    PUT/PATCH: Update employee
    DELETE: Delete employee
    """
    queryset = Employee.objects.select_related(
        'user', 'reporting_manager'
    ).prefetch_related('additional_documents')
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return EmployeeCreateUpdateSerializer
        return EmployeeDetailSerializer


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def employees_sidebar(request):
    """
    Returns employee list for sidebar/dropdown
    """
    queryset = Employee.objects.select_related('user').filter(
        is_active=True
    ).order_by('employee_code')[:200]
    
    result = []
    for emp in queryset:
        avatar_url = None
        if emp.user and hasattr(emp.user, 'photo') and emp.user.photo:
            try:
                avatar_url = request.build_absolute_uri(emp.user.photo.url)
            except:
                pass
        
        result.append({
            'id': emp.id,
            'employee_code': emp.employee_code or '',
            'name': emp.get_full_name(),
            'designation': emp.designation or '',
            'department': emp.department or '',
            'avatar': avatar_url
        })
    
    return Response(result)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def employee_stats(request):
    """
    Get employee statistics
    """
    total = Employee.objects.count()
    active = Employee.objects.filter(is_active=True).count()
    
    return Response({
        'total_employees': total,
        'active_employees': active,
        'inactive_employees': total - active,
    })