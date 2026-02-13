# delivery_management/urls.py
from django.urls import path
from . import views

app_name = 'delivery-management'

urlpatterns = [
    # ==================== MAIN DELIVERY ENDPOINTS ====================
    
    # Delivery List & Create
    path('deliveries/', 
         views.DeliveryListCreateAPIView.as_view(), 
         name='delivery-list-create'),
    
    # My Assigned Deliveries (MUST come before <int:pk> pattern)
    path('deliveries/my-assigned/', 
         views.my_assigned_deliveries, 
         name='my-assigned-deliveries'),
    
    # Delivery Detail, Update, Delete
    path('deliveries/<int:pk>/', 
         views.DeliveryDetailAPIView.as_view(), 
         name='delivery-detail'),
    
    
    # ==================== DELIVERY ACTIONS ====================
    
    # Start Delivery
    path('deliveries/<int:pk>/start/', 
         views.start_delivery, 
         name='delivery-start'),
    
    # Complete Delivery
    path('deliveries/<int:pk>/complete/', 
         views.complete_delivery, 
         name='delivery-complete'),
    
    # Cancel Delivery
    path('deliveries/<int:pk>/cancel/', 
         views.cancel_delivery, 
         name='delivery-cancel'),
    
    
    # ==================== DELIVERY PRODUCTS ====================
    
    # List Products for a Delivery
    path('deliveries/<int:delivery_id>/products/', 
         views.DeliveryProductListAPIView.as_view(), 
         name='delivery-products-list'),
    
    # Update Single Product
    path('delivery-products/<int:pk>/', 
         views.DeliveryProductUpdateAPIView.as_view(), 
         name='delivery-product-update'),
    
    # Bulk Update Products
    path('deliveries/<int:pk>/products/bulk-update/', 
         views.update_delivery_products_bulk, 
         name='delivery-products-bulk-update'),
    
    
    # ==================== DELIVERY STOPS ====================
    
    # List & Create Stops for a Delivery
    path('deliveries/<int:delivery_id>/stops/', 
         views.DeliveryStopListAPIView.as_view(), 
         name='delivery-stops-list-create'),
    
    # Stop Detail, Update, Delete
    path('delivery-stops/<int:pk>/', 
         views.DeliveryStopDetailAPIView.as_view(), 
         name='delivery-stop-detail'),
    
    # Complete Delivery Stop
    path('delivery-stops/<int:pk>/complete/', 
         views.complete_delivery_stop, 
         name='delivery-stop-complete'),
    
    
    # ==================== STATISTICS & REPORTS ====================
    
    # Overall Delivery Statistics
    path('deliveries/statistics/', 
         views.delivery_statistics, 
         name='delivery-statistics'),
    
    # Today's Deliveries
    path('deliveries/today/', 
         views.today_deliveries, 
         name='delivery-today'),
    
    # Upcoming Deliveries
    path('deliveries/upcoming/', 
         views.upcoming_deliveries, 
         name='delivery-upcoming'),
    
    # Employee-specific Deliveries
    path('deliveries/employee/<int:employee_id>/', 
         views.employee_deliveries, 
         name='employee-deliveries'),
    
    # Vehicle-specific Deliveries
    path('deliveries/vehicle/<int:vehicle_id>/', 
         views.vehicle_deliveries, 
         name='vehicle-deliveries'),
    
    # Route-specific Deliveries
    path('deliveries/route/<int:route_id>/', 
         views.route_deliveries, 
         name='route-deliveries'),
    
    # Employee's Assigned Deliveries (for logged-in employee)
    path('deliveries/my-assigned/', 
         views.my_assigned_deliveries, 
         name='my-assigned-deliveries'),
    
    # Get Next Pending Stop
    path('deliveries/<int:pk>/next-stop/', 
         views.get_next_stop, 
         name='delivery-next-stop'),
    
    # Delivery Summary (for admin reporting)
    path('deliveries/<int:pk>/summary/', 
         views.delivery_summary, 
         name='delivery-summary'),
]