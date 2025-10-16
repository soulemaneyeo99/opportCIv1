# backend/chat/urls.py
from django.urls import path
from .views import (
    ChatSendMessageView,
    ChatHistoryView,
    ChatConversationsListView,
    ChatNewConversationView
)

urlpatterns = [
    path('send/', ChatSendMessageView.as_view(), name='chat-send-message'),
    path('history/', ChatHistoryView.as_view(), name='chat-history'),
    path('history/<uuid:conversation_id>/', ChatHistoryView.as_view(), name='chat-history-specific'),
    path('conversations/', ChatConversationsListView.as_view(), name='chat-conversations'),
    path('new/', ChatNewConversationView.as_view(), name='chat-new-conversation'),
]
