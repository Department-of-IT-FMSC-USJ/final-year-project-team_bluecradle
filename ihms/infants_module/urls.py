from django.urls import path
from .import views

app_name = 'infants'

urlpatterns = [
    path('', views.InfantListCreateView.as_view(), name='infant-list-create'),
    path('<str:phn>', views.InfantDetailView.as_view(), name='infant-detail')
]