from django.urls import path
from . import views

urlpatterns = [
    # List and create offer letters
    path('', views.offer_letter_list_create, name='offer-letter-list-create'),
    
    # Retrieve, update, and delete a specific offer letter
    path('<int:pk>/', views.offer_letter_detail, name='offer-letter-detail'),
    
    # Get selected candidates available for offer letters
    path('selected-candidates/', views.selected_candidates_list, name='selected-candidates-list'),
    
    # Send offer letter
    path('<int:pk>/send-offer/', views.send_offer, name='send-offer'),
    
    # Accept offer letter
    path('<int:pk>/accept-offer/', views.accept_offer, name='accept-offer'),
    
    # Reject offer letter
    path('<int:pk>/reject-offer/', views.reject_offer, name='reject-offer'),
]