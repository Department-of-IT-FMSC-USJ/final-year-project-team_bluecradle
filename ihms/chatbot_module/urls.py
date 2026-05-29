from django.urls import path
from .views import PHMChatView, ParentChatView, ChatHistoryView

app_name = 'chatbot'

urlpatterns = [
    path('phm/', PHMChatView.as_view(), name='phm_chat'),
    path('parent/', ParentChatView.as_view(), name='parent_chat'),
    path('history/', ChatHistoryView.as_view(), name='chat_history'),
]