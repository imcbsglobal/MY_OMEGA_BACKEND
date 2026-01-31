# vehicle_management/urls.py
from django.urls import path
from . import views

app_name = 'vehicle-management'

urlpatterns = [
    # ==================== VEHICLE ENDPOINTS ====================
    
    # Vehicle List & Create
    path('vehicles/', 
         views.VehicleListCreateAPIView.as_view(), 
         name='vehicle-list-create'),
    
    # Vehicle Detail, Update, Delete
    path('vehicles/<int:pk>/', 
         views.VehicleDetailAPIView.as_view(), 
         name='vehicle-detail'),
    
    # Vehicle Dropdown (for select inputs)
    path('vehicles/dropdown/', 
         views.vehicle_dropdown, 
         name='vehicle-dropdown'),
    
    # Vehicle Statistics
    path('vehicles/stats/', 
         views.vehicle_stats, 
         name='vehicle-stats'),
    
    # Vehicle Challans (get all challans for a specific vehicle)
    path('vehicles/<int:vehicle_id>/challans/', 
         views.vehicle_challans, 
         name='vehicle-challans'),
    
    
    # ==================== TRIP ENDPOINTS ====================
    
    # Trip List (with filters)
    path('trips/', 
         views.TripListAPIView.as_view(), 
         name='trip-list'),
    
    # Trip Detail
    path('trips/<int:pk>/', 
         views.TripDetailAPIView.as_view(), 
         name='trip-detail'),
    
    # Start New Trip
    path('trips/start/', 
         views.TripStartAPIView.as_view(), 
         name='trip-start'),
    
    # End/Complete Trip
    path('trips/<int:pk>/end/', 
         views.TripEndAPIView.as_view(), 
         name='trip-end'),
    
    # Approve/Reject Trip (Admin)
    path('trips/<int:pk>/approve/', 
         views.TripApprovalAPIView.as_view(), 
         name='trip-approve'),
    
    # Delete Trip (Admin)
    path('trips/<int:pk>/delete/', 
         views.delete_trip, 
         name='trip-delete'),
    
    # My Trips (Current user's trips)
    path('trips/my-trips/', 
         views.my_trips, 
         name='my-trips'),
    
    # Trip Statistics
    path('trips/stats/', 
         views.trip_stats, 
         name='trip-stats'),
    
    
    # ==================== VEHICLE CHALLAN ENDPOINTS ====================
    
    # Challan List & Create
    path('challans/', 
         views.VehicleChallanListCreateAPIView.as_view(), 
         name='challan-list-create'),
    
    # Challan Detail, Update, Delete
    path('challans/<int:pk>/', 
         views.VehicleChallanDetailAPIView.as_view(), 
         name='challan-detail'),
    
    # Mark Challan as Paid
    path('challans/<int:pk>/pay/', 
         views.ChallanPaymentAPIView.as_view(), 
         name='challan-pay'),
    
    # Challan Statistics
    path('challans/stats/', 
         views.challan_stats, 
         name='challan-stats'),
    
    # My Challans (Current user's challans)
    path('challans/my-challans/', 
         views.owner_challans, 
         name='my-challans'),
]