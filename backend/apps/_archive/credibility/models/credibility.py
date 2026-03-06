# backend/credibility/models.py
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Badge(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='badges/')
    points_required = models.PositiveIntegerField(default=0)
    category = models.CharField(max_length=100, default='general')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Achievement(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    image = models.ImageField(upload_to='achievements/')
    points = models.PositiveIntegerField(default=10)
    category = models.CharField(max_length=100, default='general')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class UserBadge(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='users')
    awarded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'badge']
    
    def __str__(self):
        return f"{self.user.username} - {self.badge.name}"


class UserAchievement(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE, related_name='users')
    awarded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'achievement']
    
    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"


class CredibilityPoints(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='credibility')
    points = models.PositiveIntegerField(default=0)
    level = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Credibility Points"
    
    def __str__(self):
        return f"{self.user.username} - {self.points} points"
    
    def add_points(self, points):
        """Ajoute des points et met à jour le niveau"""
        self.points += points
        self.update_level()
        self.save()
    
    def update_level(self):
        """Met à jour le niveau en fonction des points"""
        # Formule de calcul du niveau (à ajuster selon vos besoins)
        # Exemple: chaque niveau nécessite 100 points * le niveau
        new_level = 1
        points_needed = 0
        
        while True:
            next_level_points = 100 * new_level
            if self.points >= points_needed + next_level_points:
                new_level += 1
                points_needed += next_level_points
            else:
                break
        
        self.level = new_level


class PointsHistory(models.Model):
    OPERATION_CHOICES = (
        ('add', 'Points ajoutés'),
        ('subtract', 'Points retirés'),
    )
    
    SOURCE_CHOICES = (
        ('course_completion', 'Achèvement de cours'),
        ('formation_completion', 'Achèvement de formation'),
        ('achievement', 'Réalisation'),
        ('daily_login', 'Connexion quotidienne'),
        ('profile_completion', 'Profil complété'),
        ('admin_adjustment', 'Ajustement administratif'),
        ('other', 'Autre'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='points_history')
    operation = models.CharField(max_length=10, choices=OPERATION_CHOICES)
    points = models.PositiveIntegerField()
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES)
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Points History"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.operation} {self.points} points - {self.source}"
