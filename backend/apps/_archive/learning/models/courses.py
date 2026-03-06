#apps/learning/models/courses.py


"""
OpportuCI - Courses Models
===========================
Cours, leçons, quiz et progression
"""
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils.functional import cached_property


class Course(models.Model):
    """Cours avec leçons séquentielles"""
    
    DIFFICULTY_CHOICES = [
        ('beginner', _('Débutant')),
        ('intermediate', _('Intermédiaire')),
        ('advanced', _('Avancé')),
        ('expert', _('Expert')),
    ]
    
    # Identification
    title = models.CharField(_('titre'), max_length=255)
    slug = models.SlugField(_('slug'), unique=True, blank=True)
    description = models.TextField(_('description'))
    
    # Relation avec formation
    formation = models.ForeignKey(
        'learning.Formation',
        on_delete=models.CASCADE,
        related_name='courses',
        verbose_name=_('formation')
    )
    
    # Métadonnées
    instructor = models.CharField(_('formateur'), max_length=255)
    duration_minutes = models.PositiveIntegerField(_('durée (minutes)'))
    difficulty = models.CharField(
        _('difficulté'),
        max_length=15,
        choices=DIFFICULTY_CHOICES,
        default='beginner'
    )
    
    # Ordre dans la formation
    order = models.PositiveIntegerField(_('ordre'), default=1)
    
    # État
    is_published = models.BooleanField(_('publié'), default=False, db_index=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('modifié le'), auto_now=True)

    class Meta:
        app_label = 'learning'
        db_table = 'learning_courses'
        verbose_name = _('cours')
        verbose_name_plural = _('cours')
        ordering = ['formation', 'order']
        unique_together = [('formation', 'order')]
        indexes = [
            models.Index(fields=['is_published', 'formation']),
            models.Index(fields=['formation', 'order']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Course.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
    
    @cached_property
    def published_lessons_count(self):
        """Nombre de leçons publiées"""
        return self.lessons.filter(is_published=True).count()
    
    @cached_property
    def total_duration(self):
        """Durée totale du cours"""
        return self.lessons.filter(is_published=True).aggregate(
            total=models.Sum('duration_minutes')
        )['total'] or 0


class Lesson(models.Model):
    """Leçon individuelle dans un cours"""
    
    TYPE_CHOICES = [
        ('video', _('Vidéo')),
        ('article', _('Article')),
        ('quiz', _('Quiz')),
        ('exercise', _('Exercice')),
        ('project', _('Projet')),
    ]
    
    # Identification
    title = models.CharField(_('titre'), max_length=255)
    slug = models.SlugField(_('slug'), blank=True)
    
    # Relation
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name=_('cours')
    )
    
    # Contenu
    content = models.TextField(_('contenu'))
    type = models.CharField(
        _('type'),
        max_length=10,
        choices=TYPE_CHOICES,
        default='video'
    )
    video_url = models.URLField(_('URL vidéo'), blank=True, null=True)
    duration_minutes = models.PositiveIntegerField(_('durée (minutes)'), default=0)
    
    # Ordre
    order = models.PositiveIntegerField(_('ordre'), default=1)
    
    # État
    is_published = models.BooleanField(_('publié'), default=False, db_index=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('modifié le'), auto_now=True)

    class Meta:
        app_label = 'learning'
        db_table = 'learning_lessons'
        verbose_name = _('leçon')
        verbose_name_plural = _('leçons')
        ordering = ['course', 'order']
        unique_together = [('course', 'order')]
        indexes = [
            models.Index(fields=['course', 'is_published']),
            models.Index(fields=['type']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    @cached_property
    def question_count(self):
        """Nombre de questions (pour quiz)"""
        if self.type == 'quiz':
            return self.questions.count()
        return 0


class UserProgress(models.Model):
    """Progression d'un utilisateur sur une leçon"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='course_progress',
        verbose_name=_('utilisateur')
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='user_progress',
        verbose_name=_('leçon')
    )
    
    # État
    completed = models.BooleanField(_('complété'), default=False, db_index=True)
    completion_date = models.DateTimeField(_('date de complétion'), blank=True, null=True)
    
    # Position (pour vidéos)
    last_position_seconds = models.PositiveIntegerField(
        _('dernière position (secondes)'),
        default=0
    )
    
    # Notes personnelles
    notes = models.TextField(_('notes'), blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('modifié le'), auto_now=True)

    class Meta:
        app_label = 'learning'
        db_table = 'learning_user_progress'
        verbose_name = _('progression utilisateur')
        verbose_name_plural = _('progressions utilisateurs')
        unique_together = [('user', 'lesson')]
        indexes = [
            models.Index(fields=['user', 'completed']),
            models.Index(fields=['lesson', 'user']),
        ]

    def __str__(self):
        return f"{self.user.username} → {self.lesson.title}"


class Question(models.Model):
    """Question de quiz"""
    
    DIFFICULTY_CHOICES = [
        ('easy', _('Facile')),
        ('medium', _('Moyen')),
        ('hard', _('Difficile')),
    ]
    
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name=_('leçon')
    )
    text = models.TextField(_('question'))
    difficulty = models.CharField(
        _('difficulté'),
        max_length=10,
        choices=DIFFICULTY_CHOICES,
        default='medium'
    )
    points = models.PositiveIntegerField(_('points'), default=1)
    explanation = models.TextField(_('explication'), blank=True)
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('modifié le'), auto_now=True)

    class Meta:
        app_label = 'learning'
        db_table = 'learning_questions'
        verbose_name = _('question')
        verbose_name_plural = _('questions')
        indexes = [
            models.Index(fields=['lesson']),
        ]

    def __str__(self):
        return f"Question {self.id} - {self.lesson.title}"
    
    @cached_property
    def correct_answer(self):
        """Réponse correcte"""
        return self.answers.filter(is_correct=True).first()


class Answer(models.Model):
    """Réponse possible à une question"""
    
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name=_('question')
    )
    text = models.CharField(_('réponse'), max_length=255)
    is_correct = models.BooleanField(_('correcte'), default=False, db_index=True)
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('modifié le'), auto_now=True)

    class Meta:
        app_label = 'learning'
        db_table = 'learning_answers'
        verbose_name = _('réponse')
        verbose_name_plural = _('réponses')
        indexes = [
            models.Index(fields=['question', 'is_correct']),
        ]

    def __str__(self):
        return f"Réponse {self.id} - Q{self.question.id}"


class UserAnswer(models.Model):
    """Réponse d'un utilisateur à une question"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name=_('utilisateur')
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='user_answers',
        verbose_name=_('question')
    )
    answer = models.ForeignKey(
        Answer,
        on_delete=models.CASCADE,
        related_name='user_selections',
        verbose_name=_('réponse')
    )
    is_correct = models.BooleanField(_('correcte'), default=False, db_index=True)
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)

    class Meta:
        app_label = 'learning'
        db_table = 'learning_user_answers'
        verbose_name = _('réponse utilisateur')
        verbose_name_plural = _('réponses utilisateurs')
        unique_together = [('user', 'question')]
        indexes = [
            models.Index(fields=['user', 'is_correct']),
            models.Index(fields=['question', 'is_correct']),
        ]

    def __str__(self):
        return f"{self.user.username} - Q{self.question.id}"
    
    def save(self, *args, **kwargs):
        # Auto-définir is_correct
        if self.answer and (not self.pk or 'answer' in kwargs.get('update_fields', [])):
            self.is_correct = self.answer.is_correct
        super().save(*args, **kwargs)