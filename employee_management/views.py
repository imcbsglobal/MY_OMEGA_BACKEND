# employee_management/views.py
# TEMPORARY: Authentication disabled for development
from rest_framework import generics, permissions, status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
import logging

logger = logging.getLogger(__name__)
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
    # TEMPORARY: Allow any access for development
    permission_classes = [permissions.AllowAny]  # Change back to IsAuthenticated in production!
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
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
                Q(employee_id__icontains=search) |
                Q(user__name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(designation__icontains=search) |
                Q(department__name__icontains=search)
            )

        # Filter by employee is_active status only (Employee.is_active is independent of AppUser.is_active)
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            active_flag = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=active_flag)
        else:
            # Default: show only active employees
            queryset = queryset.filter(is_active=True)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        # Log incoming payload for debugging
        try:
            logger.info("Employee create payload: %s", getattr(self.request, 'data', {}))
        except Exception:
            pass

        # Save without created_by if user is not authenticated
        if self.request.user.is_authenticated:
            serializer.save(created_by=self.request.user)
        else:
            serializer.save()

    def create(self, request, *args, **kwargs):
        # Override to log validation errors when creation fails
        logger.info("Employee POST received: files=%s data=%s", bool(request.FILES), request.data)
        # Coerce repeated 'department' fields from multipart/form into a list
        data = request.data
        try:
            # QueryDict supports getlist; make a mutable copy
            if hasattr(request.data, 'getlist'):
                data = request.data.copy()
                dept_list = request.data.getlist('department')
                if dept_list:
                    data.setlist('department', dept_list)
        except Exception:
            pass

        # Ensure single string department becomes a list for serializer without clobbering getlist
        dept_value = None
        try:
            dept_value = data.get('department', None)
        except Exception:
            dept_value = None
        if dept_value is not None and not isinstance(dept_value, (list, tuple)):
            try:
                if hasattr(data, 'getlist') and data.getlist('department'):
                    data.setlist('department', data.getlist('department'))
                else:
                    data['department'] = [dept_value]
            except Exception:
                pass

        serializer = self.get_serializer(data=data)
        if not serializer.is_valid():
            logger.error("Employee create validation errors: %s", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class EmployeeDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve employee detail
    PUT/PATCH: Update employee
    DELETE: Delete employee
    """
    queryset = Employee.objects.select_related(
        'user', 'reporting_manager'
    ).prefetch_related('additional_documents')
    # TEMPORARY: Allow any access for development
    permission_classes = [permissions.AllowAny]  # Change back to IsAuthenticated in production!
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return EmployeeCreateUpdateSerializer
        return EmployeeDetailSerializer

    def update(self, request, *args, **kwargs):
        # Log incoming payload for debugging
        logger.info("Employee UPDATE received: files=%s data=%s", bool(request.FILES), request.data)
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        data = request.data
        try:
            if hasattr(request.data, 'getlist'):
                data = request.data.copy()
                dept_list = request.data.getlist('department')
                if dept_list:
                    data.setlist('department', dept_list)
        except Exception:
            pass

        # Ensure single string department becomes a list for serializer without clobbering getlist
        dept_value = None
        try:
            dept_value = data.get('department', None)
        except Exception:
            dept_value = None
        if dept_value is not None and not isinstance(dept_value, (list, tuple)):
            try:
                if hasattr(data, 'getlist') and data.getlist('department'):
                    data.setlist('department', data.getlist('department'))
                else:
                    data['department'] = [dept_value]
            except Exception:
                pass

        serializer = self.get_serializer(instance, data=data, partial=partial)
        if not serializer.is_valid():
            logger.error("Employee update validation errors: %s", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        self.perform_update(serializer)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])  # TEMPORARY
def employees_sidebar(request):
    """
    Returns employee list for sidebar/dropdown
    """
    queryset = Employee.objects.select_related('user').filter(
        is_active=True
    ).order_by('employee_id')[:200]
    
    result = []
    for emp in queryset:
        avatar_url = None
        if emp.user and hasattr(emp.user, 'photo') and emp.user.photo:
            try:
                avatar_url = request.build_absolute_uri(emp.user.photo.url)
            except:
                pass
        
        try:
            dept_list = [d.name for d in emp.department.all()]
        except Exception:
            dept_list = [emp.department] if emp.department else []

        result.append({
            'id': emp.id,
            'employee_id': emp.employee_id or '',
            'name': emp.get_full_name(),
            'designation': emp.designation or '',
            'department': dept_list,
            'avatar': avatar_url
        })
    
    return Response(result)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])  # TEMPORARY
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