from django.urls import path
from . import views

urlpatterns = [
    # List and create offer letters
    path('', views.offer_letter_list_create, name='offer-letter-list-create'),
    
    # Retrieve, update, and delete a specific offer letter
    path('<int:pk>/', views.offer_letter_detail, name='offer-letter-detail'),
    
    # Get selected candidates available for offer letters
    path('selected-candidates/', views.selected_candidates_list, name='selected-candidates-list'),
]