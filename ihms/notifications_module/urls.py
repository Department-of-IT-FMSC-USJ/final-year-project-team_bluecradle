from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('subscribe/', views.PushSubscribeView.as_view(), name='subscribe'),
    path('', views.NotificationListView.as_view(), name='list'),
    path('<int:pk>/read/', views.NotificationMarkReadView.as_view(), name='mark_read'),
    path('sync-confirm/', views.SyncConfirmView.as_view(), name='sync_confirm'),
]