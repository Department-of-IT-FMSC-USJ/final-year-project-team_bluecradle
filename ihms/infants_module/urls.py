from django.urls import path
from . import views

app_name = 'infants'

urlpatterns = [
    # Web pages for infant management
    path('', views.infant_home, name='infant-home'),

    # API endpoints for infant management
    path('', views.InfantListCreateView.as_view(), name='infant-list-create'),
    path('<str:phn>/', views.InfantDetailView.as_view(), name='infant-detail'),
]