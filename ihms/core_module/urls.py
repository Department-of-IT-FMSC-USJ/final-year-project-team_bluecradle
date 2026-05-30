from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name = 'home'),
    path('features/', views.features, name = 'features'),
    path('sw.js', views.service_worker, name='service_worker'),
]