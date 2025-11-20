from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import transaction
from .models import SalaryCertificate
from .serializers import SalaryCertificateSerializer
from User.models import AppUser


def success_response(message, data=None, status_code=status.HTTP_200_OK):
    return Response({
        'success': True,
        'message': message,
        'data': data
    }, status=status_code)


def error_response(message, error_code='ERROR', details=None, status_code=status.HTTP_400_BAD_REQUEST):
    return Response({
        'success': False,
        'message': message,
        'error': error_code,
        'details': details
    }, status=status_code)

@api_view(['GET'])
def employee_list(request):
    """Get all employees (AppUser) available for salary certificates"""
    employees = AppUser.objects.filter()
    
    # Simple serialization for employee list
    data = [{
        'id': emp.id,
        'name': emp.name,
        'email': emp.email,
        'job_title': emp.job_title,
        'joining_date': emp.joining_date,
        'address': emp.address
    } for emp in employees]
    
    return success_response(
        message=f"Found {len(data)} active employee(s)",
        data=data
    )


#Salary Certificate
@api_view(['GET', 'POST'])
def salary_certificate_list_create(request):
    """
    GET: List all salary certificates with optional filtering
    POST: Create a new salary certificate
    """
    if request.method == 'GET':
        queryset = SalaryCertificate.objects.select_related('employee', 'generated_by')
        
        # Filter by employee
        employee_id = request.query_params.get('employee')
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        
        serializer = SalaryCertificateSerializer(queryset, many=True)
        return success_response(
            message="Salary certificate(s)",
            data=serializer.data
        )   
    
    elif request.method == 'POST':
        serializer = SalaryCertificateSerializer(data=request.data)
        if serializer.is_valid():
            with transaction.atomic():
                # Auto-set generated_by to current user
                salary_certificate = serializer.save(generated_by=request.user)
                return success_response(
                    message=f"Salary certificate created for {salary_certificate.employee.name}",
                    data=SalaryCertificateSerializer(salary_certificate).data,
                    status_code=status.HTTP_201_CREATED
                )
        return error_response(
            message="Invalid data provided",
            error_code="VALIDATION_ERROR",
            details=serializer.errors
        )


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
def salary_certificate_detail(request, pk):
    """
    GET: Retrieve a specific salary certificate
    PUT/PATCH: Update a salary certificate
    DELETE: Delete a salary certificate
    """
    try:
        salary_certificate = SalaryCertificate.objects.select_related(
            'employee', 'generated_by'
        ).get(pk=pk)
    except SalaryCertificate.DoesNotExist:
        return error_response(
            message="Salary certificate not found",
            error_code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND
        )
    
    if request.method == 'GET':
        serializer = SalaryCertificateSerializer(salary_certificate)
        return success_response(
            message="Salary certificate retrieved successfully",
            data=serializer.data
        )
    
    elif request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = SalaryCertificateSerializer(
            salary_certificate, 
            data=request.data, 
            partial=partial
        )
        if serializer.is_valid():
            serializer.save()
            return success_response(
                message="Salary certificate updated successfully",
                data=serializer.data
            )
        return error_response(
            message="Invalid data provided",
            error_code="VALIDATION_ERROR",
            details=serializer.errors
        )
    
    elif request.method == 'DELETE':
        employee_name = salary_certificate.employee.name
        salary_certificate.delete()
        return success_response(
            message=f"Salary certificate for {employee_name} deleted successfully"
        )


#Experience Certificate
@api_view(['GET','POST'])
def experience_certificate_list_create(request):
    