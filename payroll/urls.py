from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PayrollViewSet, DeductionListView, AllowanceListView

router = DefaultRouter()
router.register(r'payroll', PayrollViewSet, basename='payroll')

urlpatterns = [
    path('', include(router.urls)),
    # Expose preview at top-level so frontend can call /api/payroll/calculate_payroll_preview/
    path('calculate_payroll_preview/', PayrollViewSet.as_view({'get': 'calculate_payroll_preview', 'post': 'calculate_payroll_preview'}), name='calculate-payroll-preview'),
    path('generate_preview_payslip/', PayrollViewSet.as_view({'post': 'generate_preview_payslip'}), name='generate-preview-payslip'),
    path('deductions/', DeductionListView.as_view(), name='deduction-list'),
    path('allowances/', AllowanceListView.as_view(), name='allowance-list'),
]
