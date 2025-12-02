# payroll/views.py
# TEMPORARY: Authentication disabled for development
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from datetime import datetime
from decimal import Decimal
from .models import Payroll, PayrollDeduction, PayrollAllowance
from .serializers import PayrollSerializer, PayrollListSerializer
from employee_management.models import Employee


class PayrollViewSet(viewsets.ModelViewSet):
    # TEMPORARY: Allow any access for development
    permission_classes = [permissions.AllowAny]  # Change back to IsAuthenticated in production!
    queryset = Payroll.objects.select_related('employee', 'employee__user').all()
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PayrollListSerializer
        return PayrollSerializer
    
    def perform_create(self, serializer):
        # Save with created_by only if user is authenticated
        if self.request.user.is_authenticated:
            serializer.save(created_by=self.request.user)
        else:
            serializer.save()
    
    @action(detail=False, methods=['post'])
    def process_payroll(self, request):
        """Process payroll for an employee"""
        try:
            employee_id = request.data.get('employee_id')
            month = request.data.get('month')
            year = request.data.get('year')
            attendance_days = int(request.data.get('attendance_days'))
            working_days = int(request.data.get('working_days', 22))
            allowances = Decimal(str(request.data.get('allowances', 0)))
            deductions = Decimal(str(request.data.get('deductions', 0)))
            
            # Validate inputs
            if not employee_id or not month or not year:
                return Response(
                    {'error': 'Employee, month, and year are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get employee
            try:
                employee = Employee.objects.get(id=employee_id)
            except Employee.DoesNotExist:
                return Response(
                    {'error': 'Employee not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Use basic_salary
            if not employee.basic_salary:
                return Response(
                    {'error': 'Employee does not have a basic salary configured'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            base_salary = Decimal(str(employee.basic_salary))
            
            # Check if payroll already exists
            year_int = int(year) if isinstance(year, str) else year
            existing = Payroll.objects.filter(
                employee=employee,
                month=month,
                year=year_int
            ).exists()
            
            if existing:
                return Response(
                    {'error': f'Payroll already processed for {employee.get_full_name()} - {month} {year}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Calculate payroll
            if working_days <= 0:
                return Response(
                    {'error': 'Working days must be greater than 0'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            daily_rate = base_salary / Decimal(str(working_days))
            earned_salary = daily_rate * Decimal(str(attendance_days))
            gross_pay = earned_salary + allowances
            taxable_amount = gross_pay - deductions
            tax = taxable_amount * Decimal('0.15')  # 15% tax
            net_pay = gross_pay - deductions - tax
            
            # Create payroll
            payroll_data = {
                'employee': employee,
                'month': month,
                'year': year_int,
                'salary': base_salary,
                'attendance_days': attendance_days,
                'working_days': working_days,
                'earned_salary': earned_salary,
                'allowances': allowances,
                'gross_pay': gross_pay,
                'deductions': deductions,
                'tax': tax,
                'net_pay': net_pay,
                'status': 'Pending',
            }
            
            # Add created_by only if user is authenticated
            if request.user.is_authenticated:
                payroll_data['created_by'] = request.user
            
            payroll = Payroll.objects.create(**payroll_data)
            
            serializer = PayrollSerializer(payroll)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except ValueError as e:
            return Response(
                {'error': f'Invalid numeric value: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Error processing payroll: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def mark_as_paid(self, request, pk=None):
        """Mark payroll as paid"""
        try:
            payroll = self.get_object()
            
            if payroll.status == 'Paid':
                return Response(
                    {'message': 'Payroll is already marked as paid'},
                    status=status.HTTP_200_OK
                )
            
            payroll.status = 'Paid'
            payroll.paid_date = datetime.now().date()
            payroll.save()
            
            serializer = self.get_serializer(payroll)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': f'Error marking payroll as paid: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get payroll summary"""
        try:
            payrolls = self.get_queryset()
            
            month_filter = request.query_params.get('month')
            year_filter = request.query_params.get('year')
            status_filter = request.query_params.get('status')
            
            if month_filter:
                payrolls = payrolls.filter(month=month_filter)
            if year_filter:
                payrolls = payrolls.filter(year=int(year_filter))
            if status_filter:
                payrolls = payrolls.filter(status=status_filter)
            
            total_gross = sum(p.gross_pay for p in payrolls)
            total_tax = sum(p.tax for p in payrolls)
            total_net = sum(p.net_pay for p in payrolls)
            total_count = payrolls.count()
            
            return Response({
                'total_gross': float(total_gross),
                'total_tax': float(total_tax),
                'total_net': float(total_net),
                'total_count': total_count,
                'paid_count': payrolls.filter(status='Paid').count(),
                'pending_count': payrolls.filter(status='Pending').count(),
            })
        except Exception as e:
            return Response(
                {'error': f'Error loading summary: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def employee_payrolls(self, request):
        """Get payrolls for a specific employee"""
        employee_id = request.query_params.get('employee_id')
        if not employee_id:
            return Response(
                {'error': 'employee_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            payrolls = self.get_queryset().filter(employee_id=employee_id)
            serializer = self.get_serializer(payrolls, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': f'Error loading employee payrolls: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )