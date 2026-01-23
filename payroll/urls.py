# payroll/urls.py - UPDATED WITH ATTENDANCE SUMMARY ENDPOINTS

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PayrollViewSet,
    PayrollAllowanceViewSet,
    DeductionListView,
    AllowanceListView,
    AddDeductionView,
    AddAllowanceView,
    DebugRoutesView,
    get_attendance_summary_for_payroll,
    get_all_employees_attendance_summary,
)

router = DefaultRouter()
router.register(r'', PayrollViewSet, basename='payroll')
router.register(r'allowances', PayrollAllowanceViewSet, basename='payroll-allowances')

urlpatterns = [
    # ==================== NEW ATTENDANCE SUMMARY ENDPOINTS ====================
    # Get attendance summary for single employee
    path('attendance-summary/', 
         get_attendance_summary_for_payroll, 
         name='attendance-summary'),
    
    # Get attendance summaries for all employees
    path('attendance-summaries/all/', 
         get_all_employees_attendance_summary, 
         name='attendance-summaries-all'),
    
    # ==================== EXISTING ENDPOINTS ====================
    # Payroll preview and payslip generation
    path('calculate_payroll_preview/', 
         PayrollViewSet.as_view({'get': 'calculate_payroll_preview', 'post': 'calculate_payroll_preview'}), 
         name='calculate-payroll-preview'),
    
    path('generate_preview_payslip/', 
         PayrollViewSet.as_view({'post': 'generate_preview_payslip'}), 
         name='generate-preview-payslip'),
    
    # Deductions and Allowances
    path('deductions/', DeductionListView.as_view(), name='deduction-list'),
    path('allowances/', AllowanceListView.as_view(), name='allowance-list'),
    path('add-deduction/', AddDeductionView.as_view(), name='add-deduction'),
    path('add-allowance/', AddAllowanceView.as_view(), name='add-allowance'),
    
    # Payroll CRUD
    path('', PayrollViewSet.as_view({'get': 'list', 'post': 'create'}), name='payroll-list'),
    path('<int:pk>/', PayrollViewSet.as_view({
        'get': 'retrieve', 
        'put': 'update', 
        'patch': 'partial_update', 
        'delete': 'destroy'
    }), name='payroll-detail'),
    
    # Alternative routes for compatibility
    path('payroll/', PayrollViewSet.as_view({'get': 'list', 'post': 'create'}), name='payroll-list-alt'),
    path('payroll/<int:pk>/', PayrollViewSet.as_view({
        'get': 'retrieve', 
        'put': 'update', 
        'patch': 'partial_update', 
        'delete': 'destroy'
    }), name='payroll-detail-alt'),
    
    # Debug helper
    path('debug_routes/', DebugRoutesView.as_view(), name='debug-routes'),
    
    # Include router
    path('', include(router.urls)),
    path('payroll/', include(router.urls)),
]