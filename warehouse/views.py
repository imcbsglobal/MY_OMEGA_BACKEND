from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import WarehouseTask
from .serializers import (
    WarehouseTaskSerializer,
    WarehouseTaskCreateSerializer,
    WarehouseTaskUpdateSerializer,
)


def _is_admin(user):
    return (
        getattr(user, 'is_staff', False)
        or getattr(user, 'is_superuser', False)
        or getattr(user, 'user_level', '') in ('Admin', 'Super Admin')
    )


# ─────────────────────────────────────────────
# 1. Admin – Assign Task
# POST /api/warehouse/assign/
# ─────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_task(request):
    if not _is_admin(request.user):
        return Response({'detail': 'Admin access required.'}, status=status.HTTP_403_FORBIDDEN)

    serializer = WarehouseTaskCreateSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        task = serializer.save()
        return Response(
            WarehouseTaskSerializer(task).data,
            status=status.HTTP_201_CREATED,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────
# 2. Employee – My Task List
# GET /api/warehouse/my-tasks/
# ─────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_tasks(request):
    tasks = WarehouseTask.objects.filter(assigned_to=request.user).select_related(
        'assigned_by', 'assigned_to'
    )
    serializer = WarehouseTaskSerializer(tasks, many=True)
    return Response(serializer.data)


# ─────────────────────────────────────────────
# 3. Employee – Update Task
# PATCH /api/warehouse/update/<id>/
# ─────────────────────────────────────────────
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_task(request, pk):
    task = get_object_or_404(WarehouseTask, pk=pk)

    # Employees can only update their own tasks; admins can update any
    if not _is_admin(request.user) and task.assigned_to != request.user:
        return Response(
            {'detail': 'You do not have permission to update this task.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    serializer = WarehouseTaskUpdateSerializer(task, data=request.data, partial=True)
    if serializer.is_valid():
        updated = serializer.save()
        return Response(WarehouseTaskSerializer(updated).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────
# 4. Admin – Dashboard (all tasks)
# GET /api/warehouse/admin-tasks/
# ─────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_tasks(request):
    if not _is_admin(request.user):
        return Response({'detail': 'Admin access required.'}, status=status.HTTP_403_FORBIDDEN)

    tasks = WarehouseTask.objects.select_related('assigned_by', 'assigned_to').all()

    # Optional filters
    status_filter = request.query_params.get('status')
    employee_filter = request.query_params.get('employee_id')
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    if employee_filter:
        tasks = tasks.filter(assigned_to_id=employee_filter)

    serializer = WarehouseTaskSerializer(tasks, many=True)
    return Response(serializer.data)


# ─────────────────────────────────────────────
# 5. Admin – Employee List (for assign dropdown)
# GET /api/warehouse/employees/
# ─────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def employee_list(request):
    if not _is_admin(request.user):
        return Response({'detail': 'Admin access required.'}, status=status.HTTP_403_FORBIDDEN)
    # Fetch employees from the employee_management app (only active employees)
    from employee_management.models import Employee

    qs = Employee.objects.filter(is_active=True).select_related('user')
    data = []
    for emp in qs:
        user = getattr(emp, 'user', None)
        user_id = user.id if user else None
        name = emp.full_name or (user.name if user and hasattr(user, 'name') else (user.email if user and hasattr(user, 'email') else emp.employee_id))
        email = user.email if user and hasattr(user, 'email') else None
        data.append({
            'id': user_id,
            'employee_id': emp.employee_id,
            'name': name,
            'email': email,
        })

    return Response(data)
