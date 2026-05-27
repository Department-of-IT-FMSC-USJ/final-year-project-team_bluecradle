from django.urls import path
from rest_framework import views
from . import views

app_name = 'clinic'

urlpatterns = [
    # Other clinic-related URLs
    path('phm/', views.phm_dashboard, name='dashboard'),
    path('phm/register/', views.infant_register, name='infant_register'),
    path('phm/infants/', views.infant_search, name='infant_search'),
    path('phm/infants/<str:phn>/', views.infant_detail, name='infant_detail'),
    path('phm/infants/<str:phn>/growth/', views.growth_record, name='growth_record'),
    path('phm/infants/<str:phn>/immunization/', views.immunization, name='immunization'),
    path('phm/reports/h523/', views.h523_report, name='h523_report'),

    # API endpoints
    path('sessions/', views.ClinicSessionListCreateView.as_view(), name='session-list-create'),
    path('sessions/<int:pk>/', views.ClinicSessionDetailView.as_view(), name='session-detail'),
    path('infants/<str:phn>/growth/', views.GrowthRecordListCreateView.as_view(), name='growth-list-create'),
    path('infants/<str:phn>/immunization/', views.ImmunizationEventListCreateView.as_view(), name='immunization-list-create'),
    path('immunization/<int:pk>/', views.ImmunizationEventDetailView.as_view(), name='immunization-detail'),
    path('events/', views.FHBAtomicEventCreateView.as_view(), name='atomic-event-create'),
    path('h523/', views.H523ReportView.as_view(), name='h523-report'),
]