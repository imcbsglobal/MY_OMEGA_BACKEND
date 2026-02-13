# target_management/urls.py — FIXED VERSION
# KEY FIX: bulk-create/ paths MUST come BEFORE <int:pk>/ paths.
# Django matches URLs in order. If <int:pk>/ is first, 'bulk-create' gets
# parsed as an integer, causing a 404/400 error.

from django.urls import path
from . import views

app_name = 'target-management'

urlpatterns = [
    # ==================== ROUTE MASTER ====================
    path('routes/', views.RouteListCreateView.as_view(), name='route-list-create'),
    path('routes/<int:pk>/', views.RouteDetailView.as_view(), name='route-detail'),

    # ==================== PRODUCT MASTER ====================
    path('products/', views.ProductListCreateView.as_view(), name='product-list-create'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),

    # ==================== ROUTE TARGETS ====================
    path('route-targets/', views.RouteTargetPeriodListCreateView.as_view(), name='route-target-list-create'),
    # FIX B-01: bulk-create MUST be before <int:pk>/
    path('route-targets/bulk-create/', views.bulk_create_route_targets, name='route-target-bulk-create'),
    path('route-targets/<int:pk>/', views.RouteTargetPeriodDetailView.as_view(), name='route-target-detail'),

    # ==================== CALL TARGETS ====================
    path('call-targets/', views.CallTargetPeriodListCreateView.as_view(), name='call-target-list-create'),
    # FIX B-01: bulk-create MUST be before <int:pk>/
    path('call-targets/bulk-create/', views.bulk_create_call_targets, name='call-target-bulk-create'),
    path('call-targets/<int:pk>/', views.CallTargetPeriodDetailView.as_view(), name='call-target-detail'),

    # ==================== CALL DAILY TARGETS ====================
    path('call-daily-targets/', views.CallDailyTargetListCreateView.as_view(), name='call-daily-target-list-create'),
    path('call-daily-targets/<int:pk>/', views.CallDailyTargetUpdateView.as_view(), name='call-daily-target-update'),

    # ==================== USER-SPECIFIC ENDPOINTS ====================
    path('my-call-targets/', views.MyCallTargetsView.as_view(), name='my-call-targets'),
    path('my-route-targets/', views.MyRouteTargetsView.as_view(), name='my-route-targets'),

    # ==================== REPORTS & ANALYTICS ====================
    path('reports/route-summary/', views.route_target_summary, name='route-target-summary'),
    path('reports/call-summary/', views.call_target_summary, name='call-target-summary'),
    path('reports/employee/<int:employee_id>/dashboard/', views.employee_performance_dashboard, name='employee-performance-dashboard'),
    path('reports/achievement-logs/', views.target_achievement_logs, name='target-achievement-logs'),

    # ==================== PERFORMANCE REPORTS ====================
    path('performance/employee/<int:employee_id>/detailed-report/',
         views.employee_detailed_report,
         name='employee-detailed-report'),
    path('performance/comparative/',
         views.comparative_performance_report,
         name='comparative-performance-report'),

    # ==================== EMPLOYEE SELF-SERVICE ====================
    path('employee/my-targets/', views.employee_my_targets, name='employee-my-targets'),
    path('employee/today-targets/', views.employee_today_targets, name='employee-today-targets'),
    path('employee/route-targets/<int:target_id>/update-achievement/',
         views.update_route_achievement, name='employee-update-route-achievement'),
    path('employee/call-daily-targets/<int:daily_target_id>/update-achievement/',
         views.update_call_daily_achievement, name='employee-update-call-achievement'),
    path('employee/achievement-history/', views.employee_achievement_history, name='employee-achievement-history'),
]