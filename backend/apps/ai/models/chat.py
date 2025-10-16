# backend/chat/models.py
from django.db import models
from django.conf import settings
import uuid

class ChatConversation(models.Model):
    """Conversation de chat avec l'IA"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_conversations')
    title = models.CharField(max_length=255, blank=True)  # Titre auto-généré
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # Contexte pour l'IA
    context_type = models.CharField(max_length=50, choices=[
        ('general', 'Discussion générale'),
        ('career_advice', 'Conseils de carrière'),
        ('opportunity_help', 'Aide opportunités'),
        ('skill_development', 'Développement compétences'),
    ], default='general')
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Chat {self.user.username} - {self.title or 'Sans titre'}"

class ChatMessage(models.Model):
    """Message dans une conversation"""
    ROLE_CHOICES = [
        ('user', 'Utilisateur'),
        ('assistant', 'Assistant IA'),
        ('system', 'Système'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(ChatConversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Métadonnées pour l'IA
    tokens_used = models.PositiveIntegerField(null=True, blank=True)
    response_time_ms = models.PositiveIntegerField(null=True, blank=True)
    model_version = models.CharField(max_length=50, default='gemini-pro')
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."