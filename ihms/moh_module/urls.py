from django.urls import path
from . import views

app_name = 'moh'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('nutrition/', views.nutrition, name='nutrition'),
    path('vaccination/', views.vaccination, name='vaccination'),
    path('phm-activity/', views.phm_activity, name='phm_activity'),
    path('clinics/', views.clinics, name='clinics'),
    path('reports/', views.moh_reports, name='reports'),
    path('reports/download/summary/', views.download_division_summary, name='download_summary'),
    path('reports/download/nutrition/', views.download_nutrition_report, name='download_nutrition'),
    path('reports/download/vaccination/', views.download_vaccination_report, name='download_vaccination'),
    path('reports/download/phm-activity/', views.download_phm_activity_report, name='download_phm_activity'),
]