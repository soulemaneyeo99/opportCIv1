# notifications/admin.py
from django.contrib import admin
from .models import Notification
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'user_email',
        'notification_type',
        'short_message',
        'is_read_display',
        'created_at',
        'linked_object',
    )
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'user__email')
    readonly_fields = ('created_at', 'user', 'notification_type', 'message', 'content_type', 'object_id', 'content_object', 'link', 'extra_data')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = _('utilisateur')

    def short_message(self, obj):
        return (obj.message[:75] + '...') if len(obj.message) > 75 else obj.message
    short_message.short_description = _('aperçu du message')

    def is_read_display(self, obj):
        if obj.is_read:
            return format_html('<span style="color: green;">✔</span>')
        return format_html('<span style="color: red;">✘</span>')
    is_read_display.short_description = _('lue')
    is_read_display.admin_order_field = 'is_read'

    def linked_object(self, obj):
        if obj.content_object:
            return str(obj.content_object)
        return "-"
    linked_object.short_description = _('objet lié')
