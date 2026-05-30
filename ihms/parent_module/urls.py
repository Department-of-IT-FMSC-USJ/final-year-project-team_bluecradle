from django.urls import path
from .import views

app_name = 'parent'

urlpatterns = [
    # Other HTML Pages
    path('', views.dashboard_page, name='dashboard'),
    path('growth/', views.growth_page, name='growth'),
    path('vaccinations/', views.vaccinations_page, name='vaccinations'),
    path('clinic-sessions/', views.clinic_sessions_page, name='clinic_sessions'),
    path('notifications/', views.notifications_page, name='notifications'),
    path('chdr/', views.chdr_page, name='chdr'),
    path('chdr/download/', views.chdr_download, name='chdr_download'),
]