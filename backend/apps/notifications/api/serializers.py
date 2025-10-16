# notifications/serializers.py
from rest_framework import serializers
from ..models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les notifications"""
    content_type_name = serializers.ReadOnlyField(source='content_type.model')
    
    class Meta:
        model = Notification
        fields = ('id', 'user', 'title', 'message', 'notification_type', 
                 'is_read', 'created_at', 'content_type', 'content_type_name', 
                 'object_id', 'link', 'extra_data')
        read_only_fields = ('id', 'user', 'created_at')
