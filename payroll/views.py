# payroll/views.py - ENHANCED WITH LEAVE INTEGRATION

from datetime import datetime
from decimal import Decimal

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import HttpResponse
from django.db.models import Sum

from .models import Payroll, PayrollDeduction, PayrollAllowance
from .serializers import (
    PayrollSerializer, PayrollListSerializer,
    PayrollDeductionSerializer, PayrollAllowanceSerializer,
    generate_payslip_pdf
)
from .services import PayrollCalculationService
from employee_management.models import Employee


class PayrollViewSet(viewsets.ModelViewSet):
    """
    Enhanced Payroll viewset with complete leave integration
    """
    permission_classes = [permissions.AllowAny]
    queryset = Payroll.objects.select_related('employee').all()
    
    def get_serializer_class(self):
        if self.action == 'list':
            if hasattr(self, 'request') and self.request and self.request.query_params.get('employee_id'):
                return PayrollSerializer
            return PayrollListSerializer
        return PayrollSerializer

    def get_queryset(self):
        qs = Payroll.objects.select_related('employee').all()
        if hasattr(self, 'request') and self.request:
            emp = self.request.query_params.get('employee_id')
            month = self.request.query_params.get('month')
            year = self.request.query_params.get('year')
            if emp:
                qs = qs.filter(employee_id=emp)
                if month:
                    qs = qs.filter(month=month)
                if year:
                    try:
                        qs = qs.filter(year=int(year))
                    except Exception:
                        pass
        return qs.order_by('-year', '-created_at')

    @action(detail=False, methods=['get', 'post'], url_path='calculate_payroll_preview')
    def calculate_payroll_preview(self, request):
        """
        Calculate comprehensive payroll preview with full leave breakdown
        """
        data = request.data if request.method == 'POST' else request.query_params
        employee_id = data.get('employee_id')
        month = data.get('month')
        year = data.get('year')
        
        if not employee_id or not month or not year:
            return Response({
                'error': 'employee_id, month and year are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response({
                'error': 'Employee not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get base salary
        base_salary = PayrollCalculationService.get_employee_salary(employee)
        if base_salary == 0:
            return Response({
                'error': 'Employee has no salary configured'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get allowances and deductions from data or from existing payroll
        try:
            allowances = Decimal(str(data.get('allowances', 0) or 0))
            deductions = Decimal(str(data.get('deductions', 0) or 0))
        except Exception:
            allowances = Decimal('0.00')
            deductions = Decimal('0.00')

        # Check if payroll already exists
        payroll_qs = Payroll.objects.filter(
            employee_id=employee_id, 
            month=month, 
            year=int(year)
        )
        payroll_obj = payroll_qs.first()
        
        if payroll_obj:
            # If payroll exists, get allowances and deductions from related items
            allowances_total = payroll_obj.allowance_items.aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0.00')
            
            deductions_total = payroll_obj.deduction_items.aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0.00')
            
            allowances = allowances_total
            deductions = deductions_total

        try:
            # Calculate comprehensive payroll preview
            preview = PayrollCalculationService.calculate_preview(
                employee=employee,
                month=month,
                year=int(year),
                base_salary=base_salary,
                allowances=allowances,
                deductions=deductions
            )
            
            # Get employee name safely
            employee_name = (
                employee.get_full_name() if hasattr(employee, 'get_full_name') and callable(employee.get_full_name)
                else getattr(employee, 'full_name', None)
                or getattr(employee, 'name', None)
                or f'Employee_{employee.id}'
            )
            
            # Build response with all details
            response_data = {
                'employee_id': employee.id,
                'employee_name': employee_name,
                'month': month,
                'year': int(year),
                
                # Salary details
                'salary': float(base_salary),
                'earned_salary': preview['salary_calculation']['earned_salary'],
                'allowances': preview['salary_calculation']['allowances'],
                'gross_pay': preview['salary_calculation']['gross_pay'],
                'deductions': preview['salary_calculation']['deductions'],
                'tax': preview['salary_calculation']['tax'],
                'net_pay': preview['salary_calculation']['net_pay'],
                
                # Days breakdown
                'total_days_in_month': preview['attendance_breakdown']['total_days_in_month'],
                'total_working_days': preview['attendance_breakdown']['total_working_days'],
                'attendance_days': preview['attendance_breakdown']['effective_paid_days'],
                'working_days': preview['attendance_breakdown']['total_working_days'],
                
                # Detailed attendance
                'attendance_breakdown': {
                    'full_days_worked': preview['attendance_breakdown']['full_days_worked'],
                    'half_days_worked': preview['attendance_breakdown']['half_days_worked'],
                    'wfh_days': preview['attendance_breakdown']['wfh_days'],
                    'sundays': preview['attendance_breakdown']['sundays'],
                    'mandatory_holidays': preview['attendance_breakdown']['mandatory_holidays'],
                    'special_holidays': preview['attendance_breakdown']['special_holidays'],
                    'total_paid_holidays': preview['attendance_breakdown']['total_paid_holidays'],
                },
                
                # Leave breakdown
                'leave_breakdown': {
                    'casual_leave_paid': preview['attendance_breakdown']['casual_leave_days'],
                    'sick_leave_paid': preview['attendance_breakdown']['sick_leave_days'],
                    'special_leave_paid': preview['attendance_breakdown']['special_leave_days'],
                    'mandatory_holiday_leaves': preview['attendance_breakdown']['mandatory_holiday_leaves'],
                    'unpaid_leave': preview['attendance_breakdown']['unpaid_leave_days'],
                    'not_marked': preview['attendance_breakdown']['not_marked_days'],
                },
                
                # Leave balance
                'leave_balance': preview['attendance_breakdown']['leave_balance'],
                
                # This month's usage
                'this_month_usage': preview['attendance_breakdown']['this_month_usage'],
                
                # Summary
                'summary': preview['summary'],
                
                # Complete salary calculation
                'salary_calculation': preview['salary_calculation'],
                
                # Items if payroll exists
                'allowance_items': [],
                'deduction_items': [],
            }
            
            # Add items if payroll exists
            if payroll_obj:
                response_data['allowance_items'] = PayrollAllowanceSerializer(
                    payroll_obj.allowance_items.all(), 
                    many=True
                ).data
                response_data['deduction_items'] = PayrollDeductionSerializer(
                    payroll_obj.deduction_items.all(), 
                    many=True
                ).data
            
            return Response(response_data)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({
                'error': f'Failed to calculate payroll: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='generate_preview_payslip')
    def generate_preview_payslip(self, request):
        """
        Generate PDF payslip from preview data
        """
        try:
            # Get preview data first
            preview_response = self.calculate_payroll_preview(request)
            
            if preview_response.status_code != 200:
                return preview_response
            
            preview_data = preview_response.data
            
            # Create a temporary payroll object for PDF generation
            employee = Employee.objects.get(id=preview_data['employee_id'])
            
            # Create or get existing payroll
            payroll, _ = Payroll.objects.get_or_create(
                employee=employee,
                month=preview_data['month'],
                year=preview_data['year'],
                defaults={
                    'salary': Decimal(str(preview_data['salary'])),
                    'attendance_days': int(preview_data['attendance_days']),
                    'working_days': preview_data['working_days'],
                    'earned_salary': Decimal(str(preview_data['earned_salary'])),
                    'allowances': Decimal(str(preview_data['allowances'])),
                    'gross_pay': Decimal(str(preview_data['gross_pay'])),
                    'deductions': Decimal(str(preview_data['deductions'])),
                    'tax': Decimal(str(preview_data['tax'])),
                    'net_pay': Decimal(str(preview_data['net_pay'])),
                }
            )
            
            # Generate PDF
            pdf = generate_payslip_pdf(payroll)
            
            # Return PDF response
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="payslip_{employee.id}_{preview_data["month"]}_{preview_data["year"]}.pdf"'
            
            return response
            
        except Exception as e:
            return Response({
                'error': f'Failed to generate payslip: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request, *args, **kwargs):
        """
        Create or update payroll with full leave calculation
        """
        data = request.data or {}
        employee_id = data.get('employee_id')
        month = data.get('month')
        year = data.get('year')

        if not employee_id or not month or not year:
            return Response({
                'error': 'employee_id, month and year are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response({
                'error': 'Employee not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get base salary
        base_salary = PayrollCalculationService.get_employee_salary(employee)

        # Get allowances and deductions
        allowances_total = Decimal('0.00')
        deductions_total = Decimal('0.00')
        
        # Check if payroll exists
        payroll_qs = Payroll.objects.filter(employee=employee, month=month, year=int(year))
        payroll_obj = payroll_qs.first()

        if payroll_obj:
            # Sum from related items
            allowances_total = payroll_obj.allowance_items.aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0.00')
            
            deductions_total = payroll_obj.deduction_items.aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0.00')
        else:
            # Get from request data
            try:
                allowances_total = Decimal(str(data.get('allowances', 0) or 0))
                deductions_total = Decimal(str(data.get('deductions', 0) or 0))
            except Exception:
                pass

        # Calculate using service
        preview = PayrollCalculationService.calculate_preview(
            employee=employee,
            month=month,
            year=int(year),
            base_salary=base_salary,
            allowances=allowances_total,
            deductions=deductions_total
        )

        # Create or update payroll
        payroll_vals = {
            'salary': base_salary,
            'attendance_days': int(preview['attendance_breakdown']['effective_paid_days']),
            'working_days': preview['attendance_breakdown']['total_working_days'],
            'earned_salary': Decimal(str(preview['salary_calculation']['earned_salary'])),
            'allowances': Decimal(str(preview['salary_calculation']['allowances'])),
            'gross_pay': Decimal(str(preview['salary_calculation']['gross_pay'])),
            'deductions': Decimal(str(preview['salary_calculation']['deductions'])),
            'tax': Decimal(str(preview['salary_calculation']['tax'])),
            'net_pay': Decimal(str(preview['salary_calculation']['net_pay'])),
        }

        payroll_obj, created = Payroll.objects.update_or_create(
            employee=employee, 
            month=month, 
            year=int(year), 
            defaults=payroll_vals
        )

        serializer = PayrollSerializer(payroll_obj)
        return Response(
            serializer.data, 
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )

    @action(detail=True, methods=['get'], url_path='download_payslip')
    def download_payslip(self, request, pk=None):
        """
        Download payslip PDF for existing payroll
        """
        try:
            payroll = self.get_object()
            pdf = generate_payslip_pdf(payroll)
            
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="payslip_{payroll.employee.id}_{payroll.month}_{payroll.year}.pdf"'
            
            return response
            
        except Exception as e:
            return Response({
                'error': f'Failed to generate payslip: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Keep existing views
class DeductionListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        deductions = PayrollDeduction.objects.select_related('payroll', 'payroll__employee').all()
        serializer = PayrollDeductionSerializer(deductions, many=True)
        return Response(serializer.data)


class AllowanceListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        allowances = PayrollAllowance.objects.select_related('payroll', 'payroll__employee').all()
        serializer = PayrollAllowanceSerializer(allowances, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        data = request.data or {}
        emp_id = data.get('employee_id')
        month = data.get('month')
        year = data.get('year')
        allowance_type = data.get('allowance_type')
        amount = data.get('amount')
        description = data.get('description', '')

        if not emp_id or not month or not year or allowance_type is None or amount is None:
            return Response({
                'error': 'employee_id, month, year, allowance_type and amount are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            employee = Employee.objects.get(id=emp_id)
        except Employee.DoesNotExist:
            return Response({
                'error': 'Employee not found'
            }, status=status.HTTP_404_NOT_FOUND)

        payroll, _ = Payroll.objects.get_or_create(
            employee=employee, 
            month=month, 
            year=int(year), 
            defaults={'salary': 0, 'attendance_days': 0, 'earned_salary': 0}
        )

        atype = allowance_type
        try:
            pa = PayrollAllowance.objects.create(
                payroll=payroll, 
                allowance_type=atype if atype in dict(PayrollAllowance.ALLOWANCE_TYPES) else 'Other', 
                amount=Decimal(str(amount)), 
                description=description
            )
        except Exception as e:
            return Response({
                'error': f'Failed to create allowance: {e}'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = PayrollAllowanceSerializer(pa)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AddDeductionView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data = request.data or {}
        emp_id = data.get('employee_id')
        month = data.get('month')
        year = data.get('year')
        deduction_type = data.get('deduction_type')
        amount = data.get('amount')
        description = data.get('description', '')

        if not emp_id or not month or not year or deduction_type is None or amount is None:
            return Response({
                'error': 'employee_id, month, year, deduction_type and amount are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            employee = Employee.objects.get(id=emp_id)
        except Employee.DoesNotExist:
            return Response({
                'error': 'Employee not found'
            }, status=status.HTTP_404_NOT_FOUND)

        payroll, _ = Payroll.objects.get_or_create(
            employee=employee, 
            month=month, 
            year=int(year), 
            defaults={'salary': 0, 'attendance_days': 0, 'earned_salary': 0}
        )

        dtype = deduction_type
        try:
            pd = PayrollDeduction.objects.create(
                payroll=payroll, 
                deduction_type=dtype if dtype in dict(PayrollDeduction.DEDUCTION_TYPES) else 'Other', 
                amount=Decimal(str(amount)), 
                description=description
            )
        except Exception as e:
            return Response({
                'error': f'Failed to create deduction: {e}'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = PayrollDeductionSerializer(pd)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AddAllowanceView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data = request.data or {}
        emp_id = data.get('employee_id')
        month = data.get('month')
        year = data.get('year')
        allowance_type = data.get('allowance_type')
        amount = data.get('amount')
        description = data.get('description', '')

        if not emp_id or not month or not year or allowance_type is None or amount is None:
            return Response({
                'error': 'employee_id, month, year, allowance_type and amount are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            employee = Employee.objects.get(id=emp_id)
        except Employee.DoesNotExist:
            return Response({
                'error': 'Employee not found'
            }, status=status.HTTP_404_NOT_FOUND)

        payroll, _ = Payroll.objects.get_or_create(
            employee=employee, 
            month=month, 
            year=int(year), 
            defaults={'salary': 0, 'attendance_days': 0, 'earned_salary': 0}
        )

        atype = allowance_type
        try:
            pa = PayrollAllowance.objects.create(
                payroll=payroll, 
                allowance_type=atype if atype in dict(PayrollAllowance.ALLOWANCE_TYPES) else 'Other', 
                amount=Decimal(str(amount)), 
                description=description
            )
        except Exception as e:
            return Response({
                'error': f'Failed to create allowance: {e}'
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = PayrollAllowanceSerializer(pa)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PayrollAllowanceViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.AllowAny]
    queryset = PayrollAllowance.objects.select_related('payroll', 'payroll__employee').all()
    serializer_class = PayrollAllowanceSerializer


class DebugRoutesView(APIView):
    """Return which named routes resolve successfully for payroll endpoints."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from django.urls import reverse, NoReverseMatch
        
        names = [
            'allowance-list', 'allowance-list-alt',
            'deduction-list', 'deduction-list-alt',
            'calculate-payroll-preview', 'calculate-payroll-preview-alt',
            'generate-preview-payslip', 'generate-preview-payslip-alt',
            'add-deduction', 'add-deduction-alt', 'add-allowance', 'add-allowance-alt'
        ]
        result = {}
        for n in names:
            try:
                result[n] = reverse(n)
            except NoReverseMatch:
                result[n] = None
        return Response(result)