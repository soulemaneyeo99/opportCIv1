"""
OpportuCI - Simulations WebSocket Routing
==========================================
"""
from django.urls import re_path
from apps.simulations.consumers.interview_consumer import InterviewConsumer

websocket_urlpatterns = [
    re_path(r'ws/interviews/(?P<simulation_id>[0-9a-f-]+)/$', InterviewConsumer.as_asgi()),
]