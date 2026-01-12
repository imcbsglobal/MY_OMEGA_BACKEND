from datetime import datetime
from decimal import Decimal

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.urls import reverse, NoReverseMatch

from .models import Payroll, PayrollDeduction, PayrollAllowance
from .serializers import (
    PayrollSerializer, PayrollListSerializer,
    PayrollDeductionSerializer, PayrollAllowanceSerializer
)
from django.db.models import Sum
from employee_management.models import Employee


from datetime import datetime
from decimal import Decimal

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Payroll, PayrollDeduction, PayrollAllowance
from .serializers import (
    PayrollSerializer, PayrollListSerializer,
    PayrollDeductionSerializer, PayrollAllowanceSerializer
)
from employee_management.models import Employee


class PayrollViewSet(viewsets.ModelViewSet):
    """Basic Payroll viewset with a few helper actions restored.

    This file provides minimal, safe implementations for endpoints
    referenced by `payroll/urls.py` so the project can start cleanly.
    """
    permission_classes = [permissions.AllowAny]
    queryset = Payroll.objects.select_related('employee').all()
    
    def get_serializer_class(self):
        # When listing for a specific employee (frontend passes employee_id)
        # return the full `PayrollSerializer` so `allowance_items` and
        # `deduction_items` are included in the response. Otherwise return
        # the lighter `PayrollListSerializer` for general listing.
        if self.action == 'list':
            if hasattr(self, 'request') and self.request and self.request.query_params.get('employee_id'):
                return PayrollSerializer
            return PayrollListSerializer
        return PayrollSerializer

    def get_queryset(self):
        qs = Payroll.objects.select_related('employee').all()
        # If client requests only for a specific employee, filter to that
        # employee and optionally by month/year.
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
        return qs

    @action(detail=False, methods=['get', 'post'], url_path='calculate_payroll_preview')
    def calculate_payroll_preview(self, request):
        """Return a lightweight payroll preview (no DB write)."""
        # Accept parameters via GET or POST
        data = request.data if request.method == 'POST' else request.query_params
        employee_id = data.get('employee_id')
        month = data.get('month')
        year = data.get('year')
        allowances = data.get('allowances', 0)
        deductions = data.get('deductions', 0)

        if not employee_id or not month or not year:
            return Response({'error': 'employee_id, month and year are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response({'error': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)

        # If a saved Payroll exists for this employee/month/year, prefer its stored
        # values and include linked allowance/deduction items in the preview.
        payroll_qs = Payroll.objects.filter(employee_id=employee_id, month=month, year=int(year))
        payroll_obj = payroll_qs.first()
        if payroll_obj:
            # aggregate totals from related items
            allowances_total = payroll_obj.allowances or Decimal('0.00')
            deductions_total = payroll_obj.deductions or Decimal('0.00')

            allowance_items = PayrollAllowanceSerializer(payroll_obj.allowance_items.all(), many=True).data
            deduction_items = PayrollDeductionSerializer(payroll_obj.deduction_items.all(), many=True).data

            preview = {
                'employee_id': employee.id,
                'employee_name': getattr(employee, 'get_full_name', lambda: None)() or getattr(employee, 'full_name', None) or getattr(employee, 'name', None) or f'Employee_{employee.id}',
                'month': payroll_obj.month,
                'year': payroll_obj.year,
                'salary': float(payroll_obj.salary),
                'attendance_days': float(payroll_obj.attendance_days or 0),
                'working_days': payroll_obj.working_days,
                'earned_salary': float(payroll_obj.earned_salary or 0),
                'allowances': float(allowances_total),
                'allowance_items': allowance_items,
                'gross_pay': float(payroll_obj.gross_pay or 0),
                'deductions': float(deductions_total),
                'deduction_items': deduction_items,
                'tax': float(payroll_obj.tax or 0),
                'net_pay': float(payroll_obj.net_pay or 0),
            }

            return Response(preview)

        try:
            base_salary = Decimal(str(getattr(employee, 'basic_salary', 0) or 0))
        except Exception as e:
            return Response({'error': f'Invalid numeric value for base salary: {e}'}, status=status.HTTP_400_BAD_REQUEST)

        # Allow clients to pass detailed items for preview: allowance_items and deduction_items
        # Each item should be an object with at least `amount` and optional `allowance_type`/`deduction_type`.
        allowance_items_raw = []
        deduction_items_raw = []
        try:
            # prefer POST body arrays, fall back to single numeric totals passed as allowances/deductions
            if isinstance(data.get('allowance_items'), (list, tuple)):
                allowance_items_raw = data.get('allowance_items')
            if isinstance(data.get('deduction_items'), (list, tuple)):
                deduction_items_raw = data.get('deduction_items')
        except Exception:
            allowance_items_raw = []
            deduction_items_raw = []

        # compute totals from provided items if present
        allowances_total = Decimal('0.00')
        deductions_total = Decimal('0.00')
        for ai in allowance_items_raw:
            try:
                allowances_total += Decimal(str(ai.get('amount', 0) or 0))
            except Exception:
                pass
        for di in deduction_items_raw:
            try:
                deductions_total += Decimal(str(di.get('amount', 0) or 0))
            except Exception:
                pass

        # If no item arrays provided, fall back to numeric totals in `allowances`/`deductions`
        if allowances_total == Decimal('0.00'):
            try:
                allowances_total = Decimal(str(allowances))
            except Exception:
                allowances_total = Decimal('0.00')
        if deductions_total == Decimal('0.00'):
            try:
                deductions_total = Decimal(str(deductions))
            except Exception:
                deductions_total = Decimal('0.00')

        # Simple default working days / attendance assumptions for preview
        working_days = int(data.get('working_days', 22))
        attendance_days = Decimal(str(data.get('attendance_days', working_days)))

        if working_days <= 0:
            return Response({'error': 'working_days must be > 0'}, status=status.HTTP_400_BAD_REQUEST)

        daily_rate = base_salary / Decimal(str(working_days)) if working_days else Decimal('0')
        earned_salary = (daily_rate * attendance_days).quantize(Decimal('0.01'))
        gross_pay = (earned_salary + allowances_total).quantize(Decimal('0.01'))
        taxable = (gross_pay - deductions_total).quantize(Decimal('0.01'))
        tax = (taxable * Decimal('0.15')).quantize(Decimal('0.01')) if taxable > 0 else Decimal('0.00')
        net_pay = (gross_pay - deductions_total - tax).quantize(Decimal('0.01'))

        # Build salary_calculation block similar to what frontend sometimes expects
        salary_calc = {
            'monthly_basic': float(base_salary),
            'earned_salary': float(earned_salary),
            'allowances_total': float(allowances_total),
            'deductions_total': float(deductions_total),
            'gross_pay': float(gross_pay),
            'tax': float(tax),
            'net_pay': float(net_pay),
        }

        preview = {
            'employee_id': employee.id,
            'employee_name': getattr(employee, 'get_full_name', lambda: None)() or getattr(employee, 'full_name', None) or getattr(employee, 'name', None) or f'Employee_{employee.id}',
            'month': month,
            'year': int(year),
            'salary': float(base_salary),
            'attendance_days': float(attendance_days),
            'working_days': working_days,
            'earned_salary': float(earned_salary),
            'allowances': float(allowances_total),
            'allowance_items': allowance_items_raw,
            'gross_pay': float(gross_pay),
            'deductions': float(deductions_total),
            'deduction_items': deduction_items_raw,
            'tax': float(tax),
            'net_pay': float(net_pay),
            'salary_calculation': salary_calc,
        }

        return Response(preview)

    @action(detail=False, methods=['post'], url_path='generate_preview_payslip')
    def generate_preview_payslip(self, request):
        """Generate a preview payslip. For now return the preview payload."""
        # Delegate to calculate_payroll_preview for a preview response
        resp = self.calculate_payroll_preview(request)
        if resp.status_code != 200:
            return resp
        # In future this could return a PDF; return JSON for now
        return resp

    def create(self, request, *args, **kwargs):
        """Create (or update) a Payroll record by computing earnings, deductions, tax and net_pay.

        Expected payload: { employee_id, month, year, working_days?, attendance_days? }
        """
        data = request.data or {}
        employee_id = data.get('employee_id')
        month = data.get('month')
        year = data.get('year')

        if not employee_id or not month or not year:
            return Response({'error': 'employee_id, month and year are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            employee = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            return Response({'error': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            base_salary = Decimal(str(getattr(employee, 'basic_salary', 0) or 0))
        except Exception:
            base_salary = Decimal('0.00')

        working_days = int(data.get('working_days', 22))
        attendance_days = Decimal(str(data.get('attendance_days', working_days)))

        if working_days <= 0:
            return Response({'error': 'working_days must be > 0'}, status=status.HTTP_400_BAD_REQUEST)

        daily_rate = base_salary / Decimal(str(working_days)) if working_days else Decimal('0')
        earned_salary = (daily_rate * attendance_days).quantize(Decimal('0.01'))

        # Sum existing allowance/deduction items if a payroll exists, otherwise accept numeric params
        payroll_qs = Payroll.objects.filter(employee=employee, month=month, year=int(year))
        payroll_obj = payroll_qs.first()

        if payroll_obj:
            allowances_total = payroll_obj.allowances or Decimal('0.00')
            deductions_total = payroll_obj.deductions or Decimal('0.00')
        else:
            # Allow callers to pass numeric totals
            try:
                allowances_total = Decimal(str(data.get('allowances', 0) or 0))
                deductions_total = Decimal(str(data.get('deductions', 0) or 0))
            except Exception:
                allowances_total = Decimal('0.00')
                deductions_total = Decimal('0.00')

        gross_pay = (earned_salary + allowances_total).quantize(Decimal('0.01'))
        taxable = (gross_pay - deductions_total).quantize(Decimal('0.01'))
        tax = (taxable * Decimal('0.15')).quantize(Decimal('0.01')) if taxable > 0 else Decimal('0.00')
        net_pay = (gross_pay - deductions_total - tax).quantize(Decimal('0.01'))

        # persist payroll
        payroll_vals = {
            'salary': base_salary,
            'attendance_days': int(attendance_days),
            'working_days': working_days,
            'earned_salary': earned_salary,
            'allowances': allowances_total,
            'gross_pay': gross_pay,
            'deductions': deductions_total,
            'tax': tax,
            'net_pay': net_pay,
        }

        payroll_obj, created = Payroll.objects.update_or_create(
            employee=employee, month=month, year=int(year), defaults=payroll_vals
        )

        serializer = PayrollSerializer(payroll_obj)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


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
        """Create a PayrollAllowance from collection POST to /allowances/ to match frontend."""
        data = request.data or {}
        emp_id = data.get('employee_id')
        month = data.get('month')
        year = data.get('year')
        allowance_type = data.get('allowance_type')
        amount = data.get('amount')
        description = data.get('description', '')

        if not emp_id or not month or not year or allowance_type is None or amount is None:
            return Response({'error': 'employee_id, month, year, allowance_type and amount are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            employee = Employee.objects.get(id=emp_id)
        except Employee.DoesNotExist:
            return Response({'error': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)

        payroll, _ = Payroll.objects.get_or_create(employee=employee, month=month, year=int(year), defaults={'salary': 0, 'attendance_days': 0, 'earned_salary': 0})

        atype = allowance_type
        try:
            pa = PayrollAllowance.objects.create(payroll=payroll, allowance_type=atype if atype in dict(PayrollAllowance.ALLOWANCE_TYPES) else 'Other', amount=Decimal(str(amount)), description=description)
        except Exception as e:
            return Response({'error': f'Failed to create allowance: {e}'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = PayrollAllowanceSerializer(pa)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AddDeductionView(APIView):
    """Create a deduction tied to a Payroll (create Payroll if missing)."""
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
            return Response({'error': 'employee_id, month, year, deduction_type and amount are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            employee = Employee.objects.get(id=emp_id)
        except Employee.DoesNotExist:
            return Response({'error': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)

        payroll, _ = Payroll.objects.get_or_create(employee=employee, month=month, year=int(year), defaults={'salary': 0, 'attendance_days': 0, 'earned_salary': 0})

        # accept free-text deduction_type and map to choice where possible; fallback to 'Other'
        dtype = deduction_type
        try:
            pd = PayrollDeduction.objects.create(payroll=payroll, deduction_type=dtype if dtype in dict(PayrollDeduction.DEDUCTION_TYPES) else 'Other', amount=Decimal(str(amount)), description=description)
        except Exception as e:
            return Response({'error': f'Failed to create deduction: {e}'}, status=status.HTTP_400_BAD_REQUEST)

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
            return Response({'error': 'employee_id, month, year, allowance_type and amount are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            employee = Employee.objects.get(id=emp_id)
        except Employee.DoesNotExist:
            return Response({'error': 'Employee not found'}, status=status.HTTP_404_NOT_FOUND)

        payroll, _ = Payroll.objects.get_or_create(employee=employee, month=month, year=int(year), defaults={'salary': 0, 'attendance_days': 0, 'earned_salary': 0})

        atype = allowance_type
        try:
            pa = PayrollAllowance.objects.create(payroll=payroll, allowance_type=atype if atype in dict(PayrollAllowance.ALLOWANCE_TYPES) else 'Other', amount=Decimal(str(amount)), description=description)
        except Exception as e:
            return Response({'error': f'Failed to create allowance: {e}'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = PayrollAllowanceSerializer(pa)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DebugRoutesView(APIView):
    """Return which named routes resolve successfully for payroll endpoints."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
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
from HR.models import Attendance, Holiday


class PayrollAllowanceViewSet(viewsets.ModelViewSet):
    """Provide list/create/retrieve/update/destroy for PayrollAllowance to match frontend expectations."""
    permission_classes = [permissions.AllowAny]
    queryset = PayrollAllowance.objects.select_related('payroll', 'payroll__employee').all()
    serializer_class = PayrollAllowanceSerializer
