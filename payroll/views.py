# payroll/views.py - FIXED: download_payslip with proper employee name handling

from calendar import calendar
import datetime
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum
from decimal import Decimal
from rest_framework import permissions
import logging
import traceback
import sys
from django.http import HttpResponse

from HR.models import Attendance, Holiday

from .models import Payroll, PayrollDeduction, PayrollAllowance
from .serializers import (
    PayrollSerializer, 
    PayrollListSerializer,
    PayrollDeductionSerializer,
    PayrollAllowanceSerializer
)
# Import PDF generator from dedicated module
try:
    from .payslip_pdf import generate_payslip_pdf
except ImportError:
    # Fallback to serializers if payslip_pdf doesn't exist
    from .serializers import generate_payslip_pdf

logger = logging.getLogger(__name__)

# Console handler for immediate debugging
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('📊 [%(levelname)s] %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.setLevel(logging.DEBUG)


class PayrollViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Payroll management
    """
    queryset = Payroll.objects.all().select_related('employee').prefetch_related(
        'deduction_items', 'allowance_items'
    )
    permission_classes = [permissions.AllowAny]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PayrollListSerializer
        return PayrollSerializer
    
    def get_queryset(self):
        """Filter queryset with query parameters - FIXED: Always prefetch related items"""
        queryset = Payroll.objects.all().select_related('employee').prefetch_related(
            'deduction_items', 'allowance_items'
        )
        
        employee_id = self.request.query_params.get('employee_id')
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        
        month = self.request.query_params.get('month')
        if month:
            queryset = queryset.filter(month=month)
        
        year = self.request.query_params.get('year')
        if year:
            queryset = queryset.filter(year=year)
        
        payroll_status = self.request.query_params.get('status')
        if payroll_status:
            queryset = queryset.filter(status=payroll_status)
        
        return queryset.order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        """Override list to use detailed serializer when specific payroll is queried"""
        queryset = self.get_queryset()
        
        # If filtering by employee + month + year, use detailed serializer
        employee_id = request.query_params.get('employee_id')
        month = request.query_params.get('month')
        year = request.query_params.get('year')
        
        if employee_id and month and year:
            # Use detailed serializer to include allowance_items and deduction_items
            serializer = PayrollSerializer(queryset, many=True)
        else:
            # Use list serializer for general listing
            serializer = self.get_serializer(queryset, many=True)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='employee_payrolls')
    def employee_payrolls(self, request):
        """Get all payroll records for a specific employee"""
        logger.info("=" * 80)
        logger.info("📊 EMPLOYEE_PAYROLLS endpoint called")
        
        employee_id = (
            request.query_params.get('employee_id') or
            request.query_params.get('user_id') or
            request.query_params.get('user') or
            request.query_params.get('emp') or
            request.query_params.get('employee')
        )
        
        logger.info(f"🔑 Employee ID: {employee_id}")
        
        if not employee_id:
            logger.error("❌ No employee_id provided")
            return Response(
                {'error': 'employee_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            payrolls = Payroll.objects.filter(
                employee_id=employee_id
            ).select_related('employee').prefetch_related(
                'deduction_items', 'allowance_items'
            ).order_by('-year', '-month')
            
            logger.info(f"✅ Found {payrolls.count()} payroll records")
            
            serializer = PayrollListSerializer(payrolls, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"❌ Error fetching employee payrolls: {e}")
            logger.error(traceback.format_exc())
            return Response(
                {'error': str(e), 'traceback': traceback.format_exc()},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get', 'post'], url_path='calculate_payroll_preview')
    def calculate_payroll_preview(self, request):
        """
        Calculate payroll preview WITHOUT saving to database
        
        Supports both GET (query params) and POST (body) requests
        """
        logger.info("=" * 80)
        logger.info(f"🧮 CALCULATE_PAYROLL_PREVIEW endpoint called - Method: {request.method}")
        
        try:
            # Step 1: Extract parameters - support both GET and POST
            if request.method == 'POST':
                logger.info("📦 Reading from POST body")
                employee_id = request.data.get('employee_id')
                month = request.data.get('month')
                year = request.data.get('year')
                allowances = request.data.get('allowances', 0)
                deductions = request.data.get('deductions', 0)
            else:  # GET
                logger.info("📦 Reading from query parameters")
                employee_id = request.query_params.get('employee_id')
                month = request.query_params.get('month')
                year = request.query_params.get('year')
                allowances = request.query_params.get('allowances', 0)
                deductions = request.query_params.get('deductions', 0)
            
            logger.info(f"  ✓ employee_id: {employee_id}")
            logger.info(f"  ✓ month: {month}")
            logger.info(f"  ✓ year: {year}")
            logger.info(f"  ✓ allowances: {allowances}")
            logger.info(f"  ✓ deductions: {deductions}")
            
            if not all([employee_id, month, year]):
                logger.error("❌ Missing required parameters")
                return Response(
                    {
                        'error': 'employee_id, month, and year are required',
                        'received': {
                            'employee_id': employee_id,
                            'month': month,
                            'year': year
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Convert to proper types
            try:
                allowances = Decimal(str(allowances))
                deductions = Decimal(str(deductions))
                logger.info(f"  ✓ Converted allowances: {allowances}")
                logger.info(f"  ✓ Converted deductions: {deductions}")
            except Exception as e:
                logger.error(f"❌ Error converting amounts: {e}")
                return Response(
                    {'error': f'Invalid allowances or deductions: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Step 2: Get employee
            logger.info("👤 Step 2: Fetching employee...")
            try:
                try:
                    from employee_management.models import Employee
                    logger.info("  ✓ Employee model imported successfully")
                except ImportError as ie:
                    logger.error(f"❌ Cannot import Employee model: {ie}")
                    return Response(
                        {'error': 'Employee management module not available', 'detail': str(ie)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                
                logger.info(f"  🔍 Querying Employee.objects.get(id={employee_id})")
                employee = Employee.objects.get(id=employee_id)
                logger.info(f"  ✅ Found employee: {employee}")
                
            except Employee.DoesNotExist:
                logger.error(f"❌ Employee with id={employee_id} not found")
                return Response(
                    {'error': f'Employee with id {employee_id} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            except Exception as e:
                logger.error(f"❌ Error fetching employee: {e}")
                logger.error(traceback.format_exc())
                return Response(
                    {'error': f'Error fetching employee: {str(e)}', 'traceback': traceback.format_exc()},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Step 3: Get base salary
            logger.info("💰 Step 3: Getting employee salary...")
            try:
                from .services import PayrollCalculationService
                logger.info("  ✓ PayrollCalculationService imported")
                
                base_salary = PayrollCalculationService.get_employee_salary(employee)
                logger.info(f"  ✓ Base salary: {base_salary}")
                
                if base_salary <= 0:
                    logger.error(f"❌ Employee has no salary configured (got {base_salary})")
                    return Response(
                        {
                            'error': 'Employee has no salary configured. Please set employee salary first.',
                            'employee_id': employee_id
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except Exception as e:
                logger.error(f"❌ Error getting salary: {e}")
                logger.error(traceback.format_exc())
                return Response(
                    {'error': f'Error getting employee salary: {str(e)}', 'traceback': traceback.format_exc()},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Step 4: Calculate preview
            logger.info("📊 Step 4: Calculating payroll preview...")
            try:
                preview_data = PayrollCalculationService.calculate_preview(
                    employee=employee,
                    month=month,
                    year=year,
                    base_salary=base_salary,
                    allowances=float(allowances),
                    deductions=float(deductions)
                )
                logger.info("  ✅ Preview calculated successfully")
                logger.info("=" * 80)
                return Response(preview_data, status=status.HTTP_200_OK)
                
            except Exception as e:
                logger.error(f"❌ Error calculating preview: {e}")
                logger.error(traceback.format_exc())
                return Response(
                    {
                        'error': 'Failed to calculate payroll preview',
                        'detail': str(e),
                        'traceback': traceback.format_exc()
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
        except Exception as e:
            logger.error(f"❌ UNEXPECTED ERROR in calculate_payroll_preview: {e}")
            logger.error(traceback.format_exc())
            return Response(
                {
                    'error': 'Unexpected error calculating payroll preview',
                    'detail': str(e),
                    'traceback': traceback.format_exc()
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], url_path='process_payroll')
    def process_payroll(self, request):
        """Process and SAVE payroll to database"""
        logger.info("=" * 80)
        logger.info("💾 PROCESS_PAYROLL endpoint called")
        
        try:
            employee_id = request.data.get('employee_id')
            month = request.data.get('month')
            year = request.data.get('year')
            allowances = Decimal(str(request.data.get('allowances', 0)))
            deductions = Decimal(str(request.data.get('deductions', 0)))
            
            if not all([employee_id, month, year]):
                return Response(
                    {'error': 'employee_id, month, and year are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                from employee_management.models import Employee
                employee = Employee.objects.get(id=employee_id)
            except Exception as e:
                logger.error(f"Employee not found: {e}")
                return Response(
                    {'error': f'Employee not found: {str(e)}'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            existing = Payroll.objects.filter(
                employee=employee,
                month=month,
                year=year
            ).first()
            
            if existing:
                return Response(
                    {'error': f'Payroll for {month} {year} already exists for this employee'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            from .services import PayrollCalculationService
            base_salary = PayrollCalculationService.get_employee_salary(employee)
            
            if base_salary <= 0:
                return Response(
                    {'error': 'Employee has no salary configured'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            preview_data = PayrollCalculationService.calculate_preview(
                employee=employee,
                month=month,
                year=year,
                base_salary=base_salary,
                allowances=float(allowances),
                deductions=float(deductions)
            )
            
            breakdown = preview_data['attendance_breakdown']
            salary_calc = preview_data['salary_calculation']
            
            payroll = Payroll.objects.create(
                employee=employee,
                month=month,
                year=int(year),
                salary=Decimal(str(base_salary)),
                attendance_days=breakdown['effective_paid_days'],
                working_days=breakdown['total_working_days'],
                earned_salary=Decimal(str(salary_calc['earned_salary'])),
                allowances=allowances,
                gross_pay=Decimal(str(salary_calc['gross_pay'])),
                deductions=deductions,
                tax=Decimal(str(salary_calc['tax'])),
                net_pay=Decimal(str(salary_calc['net_pay'])),
                status='Pending',
                created_by=request.user if request.user.is_authenticated else None
            )
            
            logger.info(f"✅ Payroll created: {payroll.id}")
            
            serializer = PayrollSerializer(payroll)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.exception(f"Error processing payroll: {e}")
            return Response(
                {
                    'error': 'Failed to process payroll',
                    'detail': str(e),
                    'traceback': traceback.format_exc()
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], url_path='mark_as_paid')
    def mark_as_paid(self, request, pk=None):
        """Mark a payroll as paid"""
        try:
            payroll = self.get_object()
            
            if payroll.status == 'Paid':
                return Response(
                    {'error': 'Payroll is already marked as paid'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            from django.utils import timezone
            payroll.status = 'Paid'
            payroll.paid_date = timezone.now().date()
            payroll.save()
            
            serializer = self.get_serializer(payroll)
            return Response(serializer.data)
            
        except Exception as e:
            logger.exception(f"Error marking payroll as paid: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        """Get payroll summary statistics"""
        try:
            queryset = self.get_queryset()
            
            total_count = queryset.count()
            paid_count = queryset.filter(status='Paid').count()
            pending_count = queryset.filter(status='Pending').count()
            
            aggregates = queryset.aggregate(
                total_gross=Sum('gross_pay'),
                total_tax=Sum('tax'),
                total_net=Sum('net_pay')
            )
            
            return Response({
                'total_count': total_count,
                'paid_count': paid_count,
                'pending_count': pending_count,
                'total_gross': float(aggregates['total_gross'] or 0),
                'total_tax': float(aggregates['total_tax'] or 0),
                'total_net': float(aggregates['total_net'] or 0),
            })
            
        except Exception as e:
            logger.exception(f"Error getting payroll summary: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'], url_path='add-allowance')
    def add_allowance(self, request):
        """Add allowance to payroll (employee + month + year)"""
        logger.info("=" * 80)
        logger.info("➕ ADD_ALLOWANCE endpoint called")
        
        employee_id = request.data.get('employee_id')
        month = request.data.get('month')
        year = request.data.get('year')
        allowance_type = request.data.get('allowance_type')
        amount = request.data.get('amount')
        description = request.data.get('description', '')

        logger.info(f"  🔍 employee_id: {employee_id}")
        logger.info(f"  🔍 month: {month}")
        logger.info(f"  🔍 year: {year}")
        logger.info(f"  🔍 allowance_type: {allowance_type}")
        logger.info(f"  🔍 amount: {amount}")

        if not all([employee_id, month, year, allowance_type, amount]):
            logger.error("❌ Missing required fields")
            return Response(
                {'error': 'employee_id, month, year, allowance_type, amount are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            try:
                from employee_management.models import Employee
                employee = Employee.objects.get(id=employee_id)
                logger.info(f"  ✅ Found employee: {employee}")
            except Employee.DoesNotExist:
                logger.error(f"❌ Employee {employee_id} not found")
                return Response(
                    {'error': f'Employee with id {employee_id} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            payroll, created = Payroll.objects.get_or_create(
                employee=employee,
                month=month,
                year=year,
                defaults={
                    'salary': Decimal('0.00'),
                    'attendance_days': 0,
                    'working_days': 22,
                    'earned_salary': Decimal('0.00'),
                    'allowances': Decimal('0.00'),
                    'gross_pay': Decimal('0.00'),
                    'deductions': Decimal('0.00'),
                    'tax': Decimal('0.00'),
                    'net_pay': Decimal('0.00'),
                    'status': 'Pending',
                    'created_by': request.user if request.user.is_authenticated else None
                }
            )

            if created:
                logger.info(f"  ✅ Created new payroll: {payroll.id}")
            else:
                logger.info(f"  ✅ Found existing payroll: {payroll.id}")

            allowance = PayrollAllowance.objects.create(
                payroll=payroll,
                allowance_type=allowance_type,
                amount=Decimal(str(amount)),
                description=description
            )

            logger.info(f"  ✅ Created allowance: {allowance.id}")

            from django.db.models import Sum
            total_allowances = payroll.allowance_items.aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0.00')

            payroll.allowances = total_allowances
            payroll.gross_pay = payroll.earned_salary + total_allowances
            payroll.net_pay = payroll.gross_pay - payroll.deductions - payroll.tax
            payroll.save(update_fields=['allowances', 'gross_pay', 'net_pay'])

            logger.info(f"  ✅ Updated payroll totals - allowances: {total_allowances}")
            logger.info("=" * 80)

            return Response(
                PayrollAllowanceSerializer(allowance).data,
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            logger.exception(f"❌ Error adding allowance: {e}")
            return Response(
                {'error': str(e), 'traceback': traceback.format_exc()},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'], url_path='add-deduction')
    def add_deduction(self, request):
        """Add deduction to payroll (employee + month + year)"""
        logger.info("=" * 80)
        logger.info("➖ ADD_DEDUCTION endpoint called")
        
        employee_id = request.data.get('employee_id')
        month = request.data.get('month')
        year = request.data.get('year')
        deduction_type = request.data.get('deduction_type')
        amount = request.data.get('amount')
        description = request.data.get('description', '')

        if not all([employee_id, month, year, deduction_type, amount]):
            return Response(
                {'error': 'employee_id, month, year, deduction_type, amount are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from employee_management.models import Employee
            employee = Employee.objects.get(id=employee_id)
            
            payroll, created = Payroll.objects.get_or_create(
                employee=employee,
                month=month,
                year=year,
                defaults={
                    'salary': Decimal('0.00'),
                    'attendance_days': 0,
                    'working_days': 22,
                    'earned_salary': Decimal('0.00'),
                    'allowances': Decimal('0.00'),
                    'gross_pay': Decimal('0.00'),
                    'deductions': Decimal('0.00'),
                    'tax': Decimal('0.00'),
                    'net_pay': Decimal('0.00'),
                    'status': 'Pending',
                    'created_by': request.user if request.user.is_authenticated else None
                }
            )

            deduction = PayrollDeduction.objects.create(
                payroll=payroll,
                deduction_type=deduction_type,
                amount=Decimal(str(amount)),
                description=description
            )

            from django.db.models import Sum
            total_deductions = payroll.deduction_items.aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0.00')

            payroll.deductions = total_deductions
            payroll.net_pay = payroll.gross_pay - total_deductions - payroll.tax
            payroll.save(update_fields=['deductions', 'net_pay'])

            return Response(
                PayrollDeductionSerializer(deduction).data,
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            logger.exception(f"Error adding deduction: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # FIXED: Properly integrated download_payslip with safe employee name handling
    @action(detail=True, methods=['get'], url_path='download_payslip')
    def download_payslip(self, request, pk=None):
        """Download payslip as PDF"""
        try:
            payroll = self.get_object()
            
            # Generate PDF
            pdf = generate_payslip_pdf(payroll)
            
            # FIXED: Get employee name safely using the same logic as serializer
            employee = payroll.employee
            employee_name = 'Employee'
            
            if employee:
                # Try get_full_name() method first
                if hasattr(employee, 'get_full_name') and callable(employee.get_full_name):
                    try:
                        name = employee.get_full_name()
                        if name and name.strip():
                            employee_name = name
                    except:
                        pass
                
                # Try full_name attribute
                if employee_name == 'Employee' and hasattr(employee, 'full_name') and employee.full_name:
                    employee_name = employee.full_name
                
                # Try name attribute
                if employee_name == 'Employee' and hasattr(employee, 'name') and employee.name:
                    employee_name = employee.name
                
                # Try first_name + last_name
                if employee_name == 'Employee':
                    first = getattr(employee, 'first_name', '')
                    last = getattr(employee, 'last_name', '')
                    if first or last:
                        employee_name = f"{first} {last}".strip()
                
                # Fallback to employee_id
                if employee_name == 'Employee':
                    emp_id = getattr(employee, 'employee_id', None) or getattr(employee, 'id', None)
                    if emp_id:
                        employee_name = f'Employee_{emp_id}'
            
            # Create filename with safe name
            safe_name = employee_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
            filename = f"Payslip_{safe_name}_{payroll.month}_{payroll.year}.pdf"
            
            # Create response
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            logger.info(f"✅ Generated payslip PDF for payroll {pk}")
            return response
            
        except Exception as e:
            logger.exception(f"❌ Error generating payslip PDF: {e}")
            return Response(
                {'error': f'Failed to generate payslip: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


def calculate_employee_attendance(user, month, year):
    attendances = Attendance.objects.filter(
        user=user,
        date__month=month,
        date__year=year,
        verification_status='verified'
    )

    full_days = attendances.filter(status='full').count()
    half_days = attendances.filter(status='half').count()

    attendance_days = full_days + (half_days * 0.5)

    holidays = Holiday.objects.filter(
        date__month=month,
        date__year=year,
        is_active=True
    ).count()

    sundays = sum(
        1 for d in range(1, calendar.monthrange(year, month)[1] + 1)
        if datetime(year, month, d).weekday() == 6
    )

    working_days = calendar.monthrange(year, month)[1] - holidays - sundays

    return {
        "attendance_days": attendance_days,
        "working_days": working_days
    }