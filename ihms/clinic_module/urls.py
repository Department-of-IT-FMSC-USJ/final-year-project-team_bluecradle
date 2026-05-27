from django.urls import path
from rest_framework import views
from . import views

app_name = 'clinic'

urlpatterns = [
    path('phm/register/', views.infant_register, name='infant_register'),
    path('phm/infants/', views.infant_search, name='infant_search'),
    path('phm/infants/<str:phn>/', views.infant_detail, name='infant_detail'),
    path('phm/infants/<str:phn>/growth/', views.growth_record, name='growth_record'),
    path('phm/infants/<str:phn>/immunization/', views.immunization, name='immunization'),

    # API endpoints
    path('sessions/', views.ClinicSessionListCreateView.as_view(), name='session-list-create'),
    path('sessions/<int:pk>/', views.ClinicSessionDetailView.as_view(), name='session-detail'),
    path('infants/<str:phn>/growth/', views.GrowthRecordListCreateView.as_view(), name='growth-list-create'),
    path('infants/<str:phn>/immunization/', views.ImmunizationEventListCreateView.as_view(), name='immunization-list-create'),
    path('immunization/<int:pk>/', views.ImmunizationEventDetailView.as_view(), name='immunization-detail'),
]