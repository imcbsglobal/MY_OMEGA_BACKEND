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
)

router = DefaultRouter()
# Changed from 'payroll' to '' to avoid double "payroll" in URLs
router.register(r'', PayrollViewSet, basename='payroll')
# Expose allowances as a full REST resource to match frontend expectations
router.register(r'allowances', PayrollAllowanceViewSet, basename='payroll-allowances')

urlpatterns = [
    # Expose preview at top-level so frontend can call /api/payroll/calculate_payroll_preview/
    path('calculate_payroll_preview/', PayrollViewSet.as_view({'get': 'calculate_payroll_preview', 'post': 'calculate_payroll_preview'}), name='calculate-payroll-preview'),
    path('generate_preview_payslip/', PayrollViewSet.as_view({'post': 'generate_preview_payslip'}), name='generate-preview-payslip'),
    path('deductions/', DeductionListView.as_view(), name='deduction-list'),
    path('allowances/', AllowanceListView.as_view(), name='allowance-list'),
    # explicit list/detail endpoints to support clients calling /api/payroll/payroll/... and /api/payroll/
    path('', PayrollViewSet.as_view({'get': 'list', 'post': 'create'}), name='payroll-list'),
    path('<int:pk>/', PayrollViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='payroll-detail'),
    path('payroll/', PayrollViewSet.as_view({'get': 'list', 'post': 'create'}), name='payroll-list-alt'),
    path('payroll/<int:pk>/', PayrollViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='payroll-detail-alt'),
    # convenience endpoints for adding single deduction/allowance from frontend
    path('add-deduction/', AddDeductionView.as_view(), name='add-deduction'),
    path('add-allowance/', AddAllowanceView.as_view(), name='add-allowance'),
    # debug helper to check which named routes are registered
    path('debug_routes/', DebugRoutesView.as_view(), name='debug-routes'),
    # include router last so explicit paths take precedence (router may match arbitrary segments)
    path('', include(router.urls)),
    # also expose router under 'payroll/' to support clients calling /api/payroll/payroll/...
    path('payroll/', include(router.urls)),
]
