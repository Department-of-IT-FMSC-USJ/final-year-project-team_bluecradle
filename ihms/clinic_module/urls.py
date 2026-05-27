from django.urls import path
from rest_framework import views
from . import views

app_name = 'clinic'

urlpatterns = [
    path('phm/register/', views.infant_register, name='infant_register'),
    path('phm/infants/', views.infant_search, name='infant_search'),
    path('phm/infants/<str:phn>/', views.infant_detail, name='infant_detail'),
]