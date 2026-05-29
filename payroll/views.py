# payroll/views.py - ENHANCED WITH LEAVE INTEGRATION

from datetime import datetime
from decimal import Decimal

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import HttpResponse
from django.db.models import Sum, Q

from .models import Payroll, PayrollDeduction, PayrollAllowance, SalaryIncrement, AutomationRule
from .serializers import (
    PayrollSerializer, PayrollListSerializer,
    PayrollDeductionSerializer, PayrollAllowanceSerializer,
    SalaryIncrementSerializer, SalaryIncrementListSerializer,
    AutomationRuleSerializer, AutomationRuleListSerializer,
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
            
            deductions_total = payroll_obj.deduction_items.exclude(
                deduction_type='ATTENDANCE PENALTY'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
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
                'penalty_deduction': preview.get('penalty_deduction', {}),
                
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

            penalty_items = preview.get('penalty_deduction', {}).get('items', []) or []
            if penalty_items:
                response_data['deduction_items'].extend(penalty_items)
            
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
                if penalty_items:
                    existing_keys = {
                        (item.get('what') or item.get('deduction_type') or '').strip().lower()
                        for item in response_data['deduction_items']
                    }
                    for item in penalty_items:
                        item_key = (item.get('what') or item.get('deduction_type') or '').strip().lower()
                        if item_key and item_key not in existing_keys:
                            response_data['deduction_items'].append(item)
            
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

            penalty_info = preview_data.get('penalty_deduction', {}) or {}
            penalty_amount = Decimal(str(penalty_info.get('amount', 0) or 0))
            if penalty_amount > 0:
                PayrollDeduction.objects.update_or_create(
                    payroll=payroll,
                    deduction_type='ATTENDANCE PENALTY',
                    defaults={
                        'amount': penalty_amount,
                        'description': f'Attendance penalties for {preview_data["month"]} {preview_data["year"]}',
                    }
                )
            else:
                PayrollDeduction.objects.filter(payroll=payroll, deduction_type='ATTENDANCE PENALTY').delete()
            
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
            
            deductions_total = payroll_obj.deduction_items.exclude(
                deduction_type='ATTENDANCE PENALTY'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
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
        penalty_info = preview.get('penalty_deduction', {}) or {}
        penalty_amount = Decimal(str(penalty_info.get('amount', 0) or 0))

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

        if penalty_amount > 0:
            PayrollDeduction.objects.update_or_create(
                payroll=payroll_obj,
                deduction_type='ATTENDANCE PENALTY',
                defaults={
                    'amount': penalty_amount,
                    'description': f'Attendance penalties for {month} {year}',
                }
            )
        else:
            PayrollDeduction.objects.filter(payroll=payroll_obj, deduction_type='ATTENDANCE PENALTY').delete()

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
                allowance_type=atype if atype and atype.strip() else 'Other', 
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
                deduction_type=dtype if dtype and dtype.strip() else 'Other', 
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
                allowance_type=atype if atype and atype.strip() else 'Other', 
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


class PayrollSettingsUniversalView(APIView):
    """Read-only universal payroll settings payload built from existing payroll data."""
    permission_classes = [permissions.AllowAny]

    def _get_employee_name(self, employee):
        if not employee:
            return 'Unknown'

        if hasattr(employee, 'get_full_name') and callable(employee.get_full_name):
            try:
                full_name = employee.get_full_name()
                if full_name and full_name.strip():
                    return full_name
            except Exception:
                pass

        for field in ('full_name', 'name'):
            value = getattr(employee, field, None)
            if value:
                return value

        first_name = getattr(employee, 'first_name', '') or ''
        last_name = getattr(employee, 'last_name', '') or ''
        if first_name or last_name:
            return f"{first_name} {last_name}".strip()

        employee_code = getattr(employee, 'employee_id', None) or getattr(employee, 'id', None)
        return f'Employee_{employee_code}' if employee_code else 'Unknown'

    def _serialize_payroll(self, payroll_obj):
        if not payroll_obj:
            return None

        return {
            'id': payroll_obj.id,
            'employee_id': payroll_obj.employee_id,
            'employee_name': self._get_employee_name(getattr(payroll_obj, 'employee', None)),
            'month': payroll_obj.month,
            'year': payroll_obj.year,
            'salary': str(payroll_obj.salary),
            'attendance_days': payroll_obj.attendance_days,
            'working_days': payroll_obj.working_days,
            'earned_salary': str(payroll_obj.earned_salary),
            'allowances': str(payroll_obj.allowances),
            'gross_pay': str(payroll_obj.gross_pay),
            'deductions': str(payroll_obj.deductions),
            'tax': str(payroll_obj.tax),
            'net_pay': str(payroll_obj.net_pay),
            'status': payroll_obj.status,
            'paid_date': payroll_obj.paid_date,
            'created_at': payroll_obj.created_at,
            'updated_at': payroll_obj.updated_at,
            'allowance_items': PayrollAllowanceSerializer(
                payroll_obj.allowance_items.all(),
                many=True
            ).data,
            'deduction_items': PayrollDeductionSerializer(
                payroll_obj.deduction_items.all(),
                many=True
            ).data,
        }

    def get(self, request):
        payroll_id = request.query_params.get('payroll_id') or request.query_params.get('id')
        employee_id = request.query_params.get('employee_id')
        month = request.query_params.get('month')
        year = request.query_params.get('year')

        payroll_qs = Payroll.objects.select_related('employee').prefetch_related('allowance_items', 'deduction_items')
        payroll_obj = None
        resolved_by = 'latest'

        if payroll_id:
            payroll_obj = payroll_qs.filter(id=payroll_id).first()
            resolved_by = 'payroll_id'
        elif employee_id:
            payroll_qs = payroll_qs.filter(employee_id=employee_id)
            resolved_by = 'employee_id'
            if month:
                payroll_qs = payroll_qs.filter(month=month)
            if year:
                try:
                    payroll_qs = payroll_qs.filter(year=int(year))
                except Exception:
                    pass
            payroll_obj = payroll_qs.order_by('-year', '-created_at').first()
        else:
            payroll_obj = payroll_qs.order_by('-year', '-created_at').first()

        if payroll_id and not payroll_obj:
            return Response({
                'success': False,
                'message': 'Payroll not found',
                'data': None,
            }, status=status.HTTP_404_NOT_FOUND)

        latest_payrolls = [self._serialize_payroll(item) for item in payroll_qs.order_by('-year', '-created_at')[:5]]
        payroll_count = Payroll.objects.count()
        total_allowances = Payroll.objects.aggregate(total=Sum('allowances'))['total'] or Decimal('0.00')
        total_deductions = Payroll.objects.aggregate(total=Sum('deductions'))['total'] or Decimal('0.00')
        allowance_items_total = PayrollAllowance.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        deduction_items_total = PayrollDeduction.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        summary = {
            'payroll_count': payroll_count,
            'paid_count': Payroll.objects.filter(status='Paid').count(),
            'pending_count': Payroll.objects.filter(status='Pending').count(),
            'cancelled_count': Payroll.objects.filter(status='Cancelled').count(),
            'total_allowances': str(total_allowances),
            'total_deductions': str(total_deductions),
            'allowance_items_total': str(allowance_items_total),
            'deduction_items_total': str(deduction_items_total),
        }

        data = {
            'resolved_by': resolved_by,
            'payroll': self._serialize_payroll(payroll_obj),
            'summary': summary,
            'latest_payrolls': latest_payrolls,
            'filters': {
                'payroll_id': payroll_id,
                'employee_id': employee_id,
                'month': month,
                'year': year,
            },
            'available_months': list(
                Payroll.objects.order_by('month').values_list('month', flat=True).distinct()
            ),
            'available_employee_ids': list(
                Payroll.objects.order_by('employee_id').values_list('employee_id', flat=True).distinct()
            ),
        }

        return Response({
            'success': True,
            'message': 'Payroll settings loaded successfully',
            'data': data,
        })


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





# payroll/views.py - ADD THIS TO YOUR EXISTING VIEWS FILE

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from employee_management.models import Employee
from .services import PayrollCalculationService


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_attendance_summary_for_payroll(request):
    """
    Get detailed attendance summary for payroll calculation
    
    Query Parameters:
    - employee_id: Required - Employee ID
    - month: Required - Month name (e.g., "November")
    - year: Required - Year (e.g., 2024)
    
    Returns comprehensive attendance breakdown including:
    - Total days, working days, sundays, holidays
    - Full days, half days, WFH days
    - All leave types (casual, sick, special, mandatory)
    - Leave balance information
    - Days breakdown for salary calculation
    """
    employee_id = request.query_params.get('employee_id')
    month = request.query_params.get('month')
    year = request.query_params.get('year')
    
    if not employee_id or not month or not year:
        return Response({
            'error': 'employee_id, month, and year are required parameters'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        employee = Employee.objects.get(id=employee_id)
    except Employee.DoesNotExist:
        return Response({
            'error': 'Employee not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Convert month name to number
    month_number = PayrollCalculationService.MONTH_NAME_TO_NUMBER.get(month)
    if not month_number:
        return Response({
            'error': f'Invalid month name: {month}. Use full month names like "November"'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Get comprehensive attendance data
        attendance_data = PayrollCalculationService.calculate_employee_payroll_data(
            employee=employee,
            year=int(year),
            month=month_number
        )
        base_salary = PayrollCalculationService.get_employee_salary(employee)
        penalty_info = PayrollCalculationService.calculate_attendance_penalty_deduction(
            employee=employee,
            year=int(year),
            month_number=month_number,
            working_days=attendance_data['total_working_days'],
            base_salary=base_salary,
        )
        
        # Get employee name safely
        employee_name = (
            employee.get_full_name() if hasattr(employee, 'get_full_name') and callable(employee.get_full_name)
            else getattr(employee, 'full_name', None)
            or getattr(employee, 'name', None)
            or f'Employee_{employee.id}'
        )
        
        # Format response
        response_data = {
            'success': True,
            'employee': {
                'id': employee.id,
                'name': employee_name,
                'employee_id': getattr(employee, 'employee_id', None),
            },
            'period': {
                'month': month,
                'month_number': month_number,
                'year': int(year),
            },
            
            # Days breakdown
            'days_summary': {
                'total_days_in_month': attendance_data['total_days_in_month'],
                'total_working_days': attendance_data['total_working_days'],
                'sundays': attendance_data['sundays'],
                'holidays': {
                    'mandatory': attendance_data['mandatory_holidays'],
                    'special': attendance_data['special_holidays'],
                    'total_paid': attendance_data['total_paid_holidays'],
                },
            },
            
            # Attendance breakdown
            'attendance': {
                'full_days_worked': attendance_data['full_days_worked'],
                'half_days_worked': attendance_data['half_days_worked'],
                'wfh_days': attendance_data['wfh_days'],
                'total_worked': (
                    attendance_data['full_days_worked'] + 
                    attendance_data['half_days_worked'] + 
                    attendance_data['wfh_days']
                ),
            },
            
            # Leave breakdown
            'leaves': {
                'casual_leave': {
                    'taken_paid': attendance_data['casual_leave_days'],
                    'taken_this_month': attendance_data['this_month_usage']['casual_used'],
                    'balance': attendance_data['leave_balance']['casual_balance'],
                    'used_total': attendance_data['leave_balance']['casual_used'],
                    'remaining': attendance_data['leave_balance']['casual_remaining'],
                },
                'sick_leave': {
                    'taken_paid': attendance_data['sick_leave_days'],
                    'taken_this_month': attendance_data['this_month_usage']['sick_used'],
                    'balance': attendance_data['leave_balance']['sick_balance'],
                    'used_total': attendance_data['leave_balance']['sick_used'],
                    'remaining': attendance_data['leave_balance']['sick_remaining'],
                },
                'special_leave': {
                    'taken_paid': attendance_data['special_leave_days'],
                    'taken_this_month': attendance_data['this_month_usage']['special_used'],
                    'balance': attendance_data['leave_balance']['special_balance'],
                    'used_total': attendance_data['leave_balance']['special_used'],
                    'remaining': attendance_data['leave_balance']['special_remaining'],
                },
                'mandatory_holiday_leaves': attendance_data['mandatory_holiday_leaves'],
                'unpaid_leave': {
                    'this_month': attendance_data['unpaid_leave_days'],
                    'total_year': attendance_data['leave_balance']['unpaid_taken'],
                },
            },
            
            # Salary calculation summary
            'payroll_summary': {
                'paid_working_days': attendance_data['paid_working_days'],
                'total_paid_days': attendance_data['total_paid_days'],
                'effective_paid_days': attendance_data['effective_paid_days'],
                'days_to_deduct': attendance_data['days_to_deduct'],
                'not_marked_days': attendance_data['not_marked_days'],
                'attendance_penalty_days': penalty_info['total_days'],
                'attendance_penalty_amount': float(penalty_info['amount']),
            },
            
            # Quick stats
            'quick_stats': {
                'attendance_percentage': round(
                    (attendance_data['effective_paid_days'] / attendance_data['total_working_days'] * 100)
                    if attendance_data['total_working_days'] > 0 else 0,
                    2
                ),
                'total_leaves_taken': (
                    attendance_data['casual_leave_days'] +
                    attendance_data['sick_leave_days'] +
                    attendance_data['special_leave_days'] +
                    attendance_data['mandatory_holiday_leaves'] +
                    attendance_data['unpaid_leave_days']
                ),
                'paid_leaves_taken': (
                    attendance_data['casual_leave_days'] +
                    attendance_data['sick_leave_days'] +
                    attendance_data['special_leave_days'] +
                    attendance_data['mandatory_holiday_leaves']
                ),
            }
        }
        
        return Response(response_data)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            'error': f'Failed to calculate attendance summary: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_employees_attendance_summary(request):
    """
    Get attendance summary for ALL employees for a specific month/year
    
    Query Parameters:
    - month: Required - Month name (e.g., "November")
    - year: Required - Year (e.g., 2024)
    - department: Optional - Filter by department
    
    Returns array of attendance summaries for all employees
    """
    month = request.query_params.get('month')
    year = request.query_params.get('year')
    department = request.query_params.get('department')
    
    if not month or not year:
        return Response({
            'error': 'month and year are required parameters'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Convert month name to number
    month_number = PayrollCalculationService.MONTH_NAME_TO_NUMBER.get(month)
    if not month_number:
        return Response({
            'error': f'Invalid month name: {month}. Use full month names like "November"'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Get all employees (default: only active employees)
        employees_qs = Employee.objects.all()
        is_active = request.query_params.get('is_active', None)
        if is_active is not None:
            active_flag = is_active.lower() == 'true'
            employees_qs = employees_qs.filter(is_active=active_flag)
            # Also respect linked AppUser active state when present
            employees_qs = employees_qs.filter(Q(user__isnull=True) | Q(user__is_active=active_flag))
        else:
            employees_qs = employees_qs.filter(is_active=True)
            employees_qs = employees_qs.filter(Q(user__isnull=True) | Q(user__is_active=True))
        
        # Filter by department if provided
        if department:
            employees_qs = employees_qs.filter(department=department)
        
        employees_qs = employees_qs.order_by('id')
        
        summaries = []
        
        for employee in employees_qs:
            try:
                # Get attendance data for each employee
                attendance_data = PayrollCalculationService.calculate_employee_payroll_data(
                    employee=employee,
                    year=int(year),
                    month=month_number
                )
                
                # Get employee name safely
                employee_name = (
                    employee.get_full_name() if hasattr(employee, 'get_full_name') and callable(employee.get_full_name)
                    else getattr(employee, 'full_name', None)
                    or getattr(employee, 'name', None)
                    or f'Employee_{employee.id}'
                )
                
                # Get base salary
                base_salary = PayrollCalculationService.get_employee_salary(employee)
                
                summary = {
                    'employee_id': employee.id,
                    'employee_name': employee_name,
                    'department': getattr(employee, 'department', None),
                    'designation': getattr(employee, 'designation', None),
                    'base_salary': float(base_salary),
                    
                    'attendance_summary': {
                        'total_working_days': attendance_data['total_working_days'],
                        'full_days': attendance_data['full_days_worked'],
                        'half_days': attendance_data['half_days_worked'],
                        'wfh_days': attendance_data['wfh_days'],
                        'casual_leave': attendance_data['casual_leave_days'],
                        'sick_leave': attendance_data['sick_leave_days'],
                        'special_leave': attendance_data['special_leave_days'],
                        'unpaid_leave': attendance_data['unpaid_leave_days'],
                        'not_marked': attendance_data['not_marked_days'],
                        'effective_paid_days': attendance_data['effective_paid_days'],
                    },
                    
                    'leave_balance': {
                        'casual_remaining': attendance_data['leave_balance']['casual_remaining'],
                        'sick_remaining': attendance_data['leave_balance']['sick_remaining'],
                        'special_remaining': attendance_data['leave_balance']['special_remaining'],
                    },
                    
                    'attendance_percentage': round(
                        (attendance_data['effective_paid_days'] / attendance_data['total_working_days'] * 100)
                        if attendance_data['total_working_days'] > 0 else 0,
                        2
                    ),
                }
                
                summaries.append(summary)
                
            except Exception as e:
                print(f"Error calculating for employee {employee.id}: {e}")
                continue
        
        return Response({
            'success': True,
            'period': {
                'month': month,
                'month_number': month_number,
                'year': int(year),
            },
            'total_employees': len(summaries),
            'summaries': summaries
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            'error': f'Failed to calculate attendance summaries: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Add this to your existing PayrollViewSet class
@action(detail=False, methods=['get'], url_path='attendance_summary')
def attendance_summary(self, request):
    """
    Get attendance summary for payroll calculation
    Can be called as: /api/payroll/attendance_summary/?employee_id=1&month=November&year=2024
    """
    return get_attendance_summary_for_payroll(request)


@action(detail=False, methods=['get'], url_path='all_attendance_summaries')
def all_attendance_summaries(self, request):
    """
    Get attendance summaries for all employees
    Can be called as: /api/payroll/all_attendance_summaries/?month=November&year=2024
    """
    return get_all_employees_attendance_summary(request)        


# =========================
# SALARY INCREMENT VIEWSET
# =========================
class SalaryIncrementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing employee salary increments
    Endpoints:
    - GET /api/payroll/salary-increments/ - List all increments
    - POST /api/payroll/salary-increments/ - Create new increment
    - GET /api/payroll/salary-increments/{id}/ - Get specific increment
    - PUT /api/payroll/salary-increments/{id}/ - Update increment
    - DELETE /api/payroll/salary-increments/{id}/ - Delete increment
    - GET /api/payroll/salary-increments/employee/{employee_id}/ - Get all increments for employee
    """
    permission_classes = [permissions.AllowAny]
    queryset = SalaryIncrement.objects.select_related('employee', 'created_by').all()
    
    def get_serializer_class(self):
        if self.action == 'list':
            return SalaryIncrementListSerializer
        return SalaryIncrementSerializer

    def get_queryset(self):
        qs = SalaryIncrement.objects.select_related('employee', 'created_by').all()
        
        # Filter by employee if provided
        employee_id = self.request.query_params.get('employee_id')
        if employee_id:
            qs = qs.filter(employee_id=employee_id)
        
        # Filter by date range if provided
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            qs = qs.filter(increment_date__gte=date_from)
        if date_to:
            qs = qs.filter(increment_date__lte=date_to)
        
        return qs.order_by('-increment_date')

    @action(detail=False, methods=['get'], url_path='employee/(?P<employee_id>[^/.]+)')
    def by_employee(self, request, employee_id=None):
        """
        Get all increments for a specific employee
        GET /api/payroll/salary-increments/employee/{employee_id}/
        """
        if not employee_id:
            return Response(
                {'error': 'employee_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response(
                {'error': 'Employee not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        increments = SalaryIncrement.objects.filter(
            employee=employee
        ).select_related('employee', 'created_by').order_by('-increment_date')
        
        # Get employee current salary from latest increment
        latest_increment = increments.first()
        current_salary = latest_increment.new_salary if latest_increment else (employee.basic_salary or employee.gross_salary or 0)
        
        # Get employee details
        emp_name = getattr(employee, 'full_name', None) or getattr(employee, 'name', None) or getattr(employee, 'employee_id', f'Employee_{employee_id}')
        emp_code = getattr(employee, 'employee_id', 'N/A')
        emp_role = getattr(employee, 'designation', None) or getattr(employee, 'role', 'N/A')
        try:
            emp_dept = ', '.join(
                department.name
                for department in employee.department.all()
                if getattr(department, 'name', None)
            ) or 'N/A'
        except Exception:
            emp_dept = 'N/A'
        
        if not current_salary:
            current_salary = 0
        
        serializer = SalaryIncrementListSerializer(increments, many=True)
        
        return Response({
            'success': True,
            'employee': {
                'id': employee.id,
                'name': emp_name,
                'code': emp_code,
                'role': emp_role,
                'department': emp_dept,
            },
            'current_salary': float(current_salary) if current_salary else 0,
            'total_increments': increments.count(),
            'increments': serializer.data,
        })

    def create(self, request, *args, **kwargs):
        """
        Create a new salary increment
        POST /api/payroll/salary-increments/
        
        Request body:
        {
            "employee_id": 1,
            "increment_date": "2026-05-14",
            "previous_salary": 25000,
            "new_salary": 28000,
            "increment_cycle": "Custom / Manual",
            "next_increment_date": "2026-06-10",
            "notes": "Annual performance increment"
        }
        """
        data = request.data
        
        # Validate required fields
        required_fields = ['employee_id', 'increment_date', 'previous_salary', 'new_salary']
        for field in required_fields:
            if field not in data or data[field] is None:
                return Response(
                    {'error': f'{field} is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        try:
            employee = Employee.objects.get(id=data['employee_id'])
        except Employee.DoesNotExist:
            return Response(
                {'error': 'Employee not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Calculate increment values
        try:
            prev_salary = Decimal(str(data['previous_salary']))
            new_salary = Decimal(str(data['new_salary']))
            increment_amount = new_salary - prev_salary
            increment_percent = (increment_amount / prev_salary * 100) if prev_salary > 0 else Decimal('0')
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid salary values'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create increment
        try:
            increment = SalaryIncrement.objects.create(
                employee=employee,
                increment_date=data['increment_date'],
                previous_salary=prev_salary,
                new_salary=new_salary,
                increment_amount=increment_amount,
                increment_percent=increment_percent,
                increment_cycle=data.get('increment_cycle', 'Custom / Manual'),
                next_increment_date=data.get('next_increment_date'),
                notes=data.get('notes', ''),
                created_by=request.user if request.user.is_authenticated else None,
            )
            
            serializer = SalaryIncrementSerializer(increment)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to create increment: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    def update(self, request, *args, **kwargs):
        """
        Update an existing salary increment
        PUT /api/payroll/salary-increments/{id}/
        """
        increment = self.get_object()
        data = request.data
        
        # Update fields if provided
        if 'increment_date' in data:
            increment.increment_date = data['increment_date']
        
        if 'previous_salary' in data and 'new_salary' in data:
            prev_salary = Decimal(str(data['previous_salary']))
            new_salary = Decimal(str(data['new_salary']))
            increment.previous_salary = prev_salary
            increment.new_salary = new_salary
            increment.increment_amount = new_salary - prev_salary
            increment.increment_percent = (increment.increment_amount / prev_salary * 100) if prev_salary > 0 else Decimal('0')
        
        if 'increment_cycle' in data:
            increment.increment_cycle = data['increment_cycle']
        
        if 'next_increment_date' in data:
            increment.next_increment_date = data['next_increment_date']
        
        if 'notes' in data:
            increment.notes = data['notes']
        
        try:
            increment.save()
            serializer = SalaryIncrementSerializer(increment)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': f'Failed to update increment: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )



# =========================
# AUTOMATION RULE VIEWSET
# =========================
class AutomationRuleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing payroll automation rules (Late Entry, Early Exit, Overtime, etc.)
    
    Endpoints:
    - GET /api/payroll/automation-rules/ - List all rules
    - POST /api/payroll/automation-rules/ - Create new rule
    - GET /api/payroll/automation-rules/{id}/ - Get specific rule
    - PUT /api/payroll/automation-rules/{id}/ - Update rule
    - PATCH /api/payroll/automation-rules/{id}/ - Partial update rule
    - DELETE /api/payroll/automation-rules/{id}/ - Delete rule
    - GET /api/payroll/automation-rules/by_type/{rule_type}/ - Get rules by type
    """
    permission_classes = [permissions.AllowAny]
    queryset = AutomationRule.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'list':
            return AutomationRuleListSerializer
        return AutomationRuleSerializer

    def get_queryset(self):
        qs = AutomationRule.objects.all()
        
        # Filter by rule_type if provided
        rule_type = self.request.query_params.get('rule_type')
        if rule_type:
            qs = qs.filter(rule_type=rule_type)
        
        # Filter by is_active if provided
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() in ['true', '1', 'yes'])
        
        return qs.order_by('rule_type', '-created_at')

    @action(detail=False, methods=['get'], url_path='by_type/(?P<rule_type>[^/.]+)')
    def by_type(self, request, rule_type=None):
        """
        Get all rules for a specific type
        GET /api/payroll/automation-rules/by_type/{rule_type}/
        
        Valid rule_types: late, early, overtime, breaks, earlyOvertime
        """
        if not rule_type:
            return Response(
                {'error': 'rule_type is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate rule_type
        valid_types = ['late', 'early', 'overtime', 'breaks', 'earlyOvertime']
        if rule_type not in valid_types:
            return Response(
                {'error': f'Invalid rule_type. Must be one of: {", ".join(valid_types)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        rules = AutomationRule.objects.filter(rule_type=rule_type).order_by('-created_at')
        serializer = AutomationRuleListSerializer(rules, many=True)
        
        return Response({
            'success': True,
            'rule_type': rule_type,
            'total_rules': rules.count(),
            'active_rules': rules.filter(is_active=True).count(),
            'rules': serializer.data,
        })

    def create(self, request, *args, **kwargs):
        """
        Create a new automation rule
        POST /api/payroll/automation-rules/
        
        Request body:
        {
            "rule_type": "late",
            "rule_name": "Late Entry Penalty",
            "threshold_hours": 0,
            "threshold_minutes": 15,
            "deduct_salary": true,
            "deduction_type": "Fixed Amount",
            "deduction_amount": 100,
            "deduct_half_day": false,
            "deduct_full_day": false,
            "set_occurrences": true,
            "max_occurrences": 3,
            "is_active": true
        }
        """
        data = request.data
        
        # Validate required fields
        required_fields = ['rule_type', 'rule_name']
        for field in required_fields:
            if field not in data or not data[field]:
                return Response(
                    {'error': f'{field} is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Validate rule_type
        valid_types = ['late', 'early', 'overtime', 'breaks', 'earlyOvertime']
        if data['rule_type'] not in valid_types:
            return Response(
                {'error': f'Invalid rule_type. Must be one of: {", ".join(valid_types)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create serializer with context
        serializer = AutomationRuleSerializer(data=data, context={'request': request})
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        """
        Update an existing automation rule
        PUT /api/payroll/automation-rules/{id}/
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = AutomationRuleSerializer(
            instance, 
            data=request.data, 
            partial=partial,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        """
        Partially update an automation rule
        PATCH /api/payroll/automation-rules/{id}/
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='toggle_active')
    def toggle_active(self, request, pk=None):
        """
        Toggle the is_active status of a rule
        POST /api/payroll/automation-rules/{id}/toggle_active/
        """
        rule = self.get_object()
        rule.is_active = not rule.is_active
        rule.save()
        
        serializer = AutomationRuleSerializer(rule)
        return Response({
            'success': True,
            'message': f'Rule {"activated" if rule.is_active else "deactivated"} successfully',
            'rule': serializer.data,
        })

    def destroy(self, request, *args, **kwargs):
        """
        Delete an automation rule
        DELETE /api/payroll/automation-rules/{id}/
        """
        instance = self.get_object()
        rule_name = instance.rule_name
        self.perform_destroy(instance)
        
        return Response({
            'success': True,
            'message': f'Rule "{rule_name}" deleted successfully',
        }, status=status.HTTP_200_OK)
