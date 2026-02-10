# target_management/urls.py - COMPLETE VERSION WITH ALL ENDPOINTS
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
    path('route-targets/<int:pk>/', views.RouteTargetPeriodDetailView.as_view(), name='route-target-detail'),
    path('route-targets/bulk-create/', views.bulk_create_route_targets, name='route-target-bulk-create'),
    
    # ==================== CALL TARGETS ====================
    path('call-targets/', views.CallTargetPeriodListCreateView.as_view(), name='call-target-list-create'),
    path('call-targets/<int:pk>/', views.CallTargetPeriodDetailView.as_view(), name='call-target-detail'),
    path('call-targets/bulk-create/', views.bulk_create_call_targets, name='call-target-bulk-create'),
    
    # ==================== CALL DAILY TARGETS ====================
     path('call-daily-targets/', views.CallDailyTargetListCreateView.as_view(), name='call-daily-target-list-create'),
     path('call-daily-targets/<int:pk>/', views.CallDailyTargetUpdateView.as_view(), name='call-daily-target-update'),

     # User-specific endpoints
     path('my-call-targets/', views.MyCallTargetsView.as_view(), name='my-call-targets'),
     path('my-route-targets/', views.MyRouteTargetsView.as_view(), name='my-route-targets'),
    
    # ==================== REPORTS & ANALYTICS ====================
    path('reports/route-summary/', views.route_target_summary, name='route-target-summary'),
    path('reports/call-summary/', views.call_target_summary, name='call-target-summary'),
    path('reports/employee/<int:employee_id>/dashboard/', views.employee_performance_dashboard, name='employee-performance-dashboard'),
    path('reports/achievement-logs/', views.target_achievement_logs, name='target-achievement-logs'),
    
    # ==================== PERFORMANCE REPORTS (MISSING ENDPOINTS) ====================
    # Detailed employee performance report
    path('performance/employee/<int:employee_id>/detailed-report/', 
         views.employee_performance_dashboard, 
         name='employee-detailed-report'),
    
    # Comparative performance report
    path('performance/comparative/', 
         views.comparative_performance_report, 
         name='comparative-performance-report'),
]