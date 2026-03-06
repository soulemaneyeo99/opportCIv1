from django.db import models
from django.conf import settings
from django.utils import timezone

class UserModuleProgress(models.Model):
    """Suivi de progression sur un module"""
    
    STATUS_CHOICES = [
        ('not_started', 'Pas commencé'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminé'),
        ('needs_review', 'À revoir'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    module = models.ForeignKey('learning.MicroLearningModule', on_delete=models.CASCADE)
    
    # Progression
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    progress_percentage = models.IntegerField(default=0)
    
    # Résultats
    attempts = models.IntegerField(default=0)
    best_score = models.FloatField(null=True, blank=True)
    time_spent_minutes = models.IntegerField(default=0)
    
    # Timestamps
    started_at = models.DateTimeField(null=True, blank=True)
    last_accessed = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['user', 'module']
        verbose_name = "Progression Module"
        verbose_name_plural = "Progressions Modules"
        indexes = [
            models.Index(fields=['user', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.module.title}"