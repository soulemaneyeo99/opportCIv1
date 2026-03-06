# backend/courses/views.py
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Avg, Sum, Prefetch, Q
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import Course, Lesson, UserProgress, Question, Answer, UserAnswer
from .serializers import (
    CourseSerializer, CourseDetailSerializer,
    LessonSerializer, LessonDetailSerializer,
    UserProgressSerializer, QuestionSerializer,
    QuestionAdminSerializer, AnswerSerializer,
    UserAnswerSerializer
)
from .permissions import IsInstructorOrReadOnly, IsUserProgressOwner


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsInstructorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['formation', 'difficulty', 'is_published']
    search_fields = ['title', 'description', 'instructor']
    ordering_fields = ['created_at', 'title', 'order']
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CourseDetailSerializer
        return CourseSerializer
    
    def get_queryset(self):
        queryset = Course.objects.all()
        
        # Filter published courses for non-staff users
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_published=True)
        
        # Optimize with select_related for related models 
        queryset = queryset.select_related('formation')
        
        return queryset
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_courses(self, request):
        # Get courses accessible to the user through enrollments
        user_formations = request.user.formation_enrollments.filter(
            status__in=['approved', 'pending']
        ).values_list('formation_id', flat=True)
        
        courses = Course.objects.filter(
            formation_id__in=user_formations,
            is_published=True
        ).select_related('formation')  # Optimize database query
        
        page = self.paginate_queryset(courses)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(courses, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def progress(self, request, slug=None):
        course = self.get_object()
        
        # Get published lessons for this course
        lessons = course.lessons.filter(is_published=True)
        total_lessons = lessons.count()
        
        if total_lessons == 0:
            return Response({
                'progress_percentage': 0,
                'completed_lessons': 0,
                'total_lessons': 0,
                'course_title': course.title
            })
        
        # Efficiently count completed lessons with a single query
        completed_lessons = UserProgress.objects.filter(
            user=request.user,
            lesson__in=lessons,
            completed=True
        ).count()
        
        progress_percentage = int((completed_lessons / total_lessons) * 100) if total_lessons > 0 else 0
        
        return Response({
            'progress_percentage': progress_percentage,
            'completed_lessons': completed_lessons,
            'total_lessons': total_lessons,
            'course_title': course.title
        })


class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsInstructorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['course', 'type', 'is_published']
    ordering_fields = ['order', 'created_at', 'title']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return LessonDetailSerializer
        return LessonSerializer
    
    def get_queryset(self):
        queryset = Lesson.objects.all()
        
        # Filter published lessons for non-staff users
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_published=True)
        
        # Optimize with select_related for related models
        queryset = queryset.select_related('course')
        
        # If this is for detail view, prefetch questions and answers
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related(
                Prefetch('questions', 
                    queryset=Question.objects.prefetch_related('answers')
                )
            )
        
        return queryset
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def mark_complete(self, request, pk=None):
        lesson = self.get_object()
        
        # Check if user is enrolled in the associated formation
        user_enrolled = request.user.formation_enrollments.filter(
            formation=lesson.course.formation,
            status='approved'
        ).exists()
        
        if not user_enrolled:
            return Response(
                {"detail": "Vous n'êtes pas inscrit à cette formation."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get or create UserProgress object
        progress, created = UserProgress.objects.get_or_create(
            user=request.user,
            lesson=lesson,
            defaults={
                'completed': True,
                'completion_date': timezone.now()
            }
        )
        
        # Update if it already exists
        if not created and not progress.completed:
            progress.completed = True
            progress.completion_date = timezone.now()
            progress.save(update_fields=['completed', 'completion_date'])
        
        return Response({
            'status': 'success',
            'message': 'Leçon marquée comme terminée.'
        })
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def update_progress(self, request, pk=None):
        lesson = self.get_object()
        position = request.data.get('position', 0)
        
        try:
            position = int(position)
        except ValueError:
            return Response(
                {"detail": "La position doit être un nombre entier."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get or create UserProgress object
        progress, _ = UserProgress.objects.get_or_create(
            user=request.user,
            lesson=lesson
        )
        
        # Update fields to save
        update_fields = ['last_position_seconds']
        progress.last_position_seconds = position
        
        # Mark as completed if position is close to the end for videos
        if lesson.type == 'video' and lesson.duration_minutes > 0:
            total_seconds = lesson.duration_minutes * 60
            if position >= total_seconds * 0.9:  # 90% considered completed
                progress.completed = True
                progress.completion_date = timezone.now()
                update_fields.extend(['completed', 'completion_date'])
        
        progress.save(update_fields=update_fields)
        
        return Response({
            'status': 'success',
            'message': 'Progression mise à jour.'
        })


class UserProgressViewSet(viewsets.ModelViewSet):
    serializer_class = UserProgressSerializer
    permission_classes = [permissions.IsAuthenticated, IsUserProgressOwner]
    
    def get_queryset(self):
        return UserProgress.objects.filter(user=self.request.user).select_related(
            'lesson', 'lesson__course'
        )
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]
    
    def get_serializer_class(self):
        if self.request.user.is_staff:
            return QuestionAdminSerializer
        return QuestionSerializer
    
    def get_queryset(self):
        queryset = Question.objects.all()
        
        # Optimize with prefetch_related
        queryset = queryset.prefetch_related('answers')
        
        return queryset


class UserAnswerViewSet(viewsets.ModelViewSet):
    serializer_class = UserAnswerSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserAnswer.objects.filter(user=self.request.user).select_related(
            'question', 'answer'
        )
    
    def perform_create(self, serializer):
        answer = serializer.validated_data.get('answer')
        serializer.save(
            user=self.request.user,
            is_correct=answer.is_correct
        )
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def submit_quiz(self, request):
        lesson_id = request.data.get('lesson_id')
        answers = request.data.get('answers', [])
        
        if not lesson_id:
            return Response(
                {"detail": "ID de leçon manquant."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            lesson = Lesson.objects.get(id=lesson_id, type='quiz')
        except Lesson.DoesNotExist:
            return Response(
                {"detail": "Quiz non trouvé."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user has already submitted answers for this quiz
        existing_answers = UserAnswer.objects.filter(
            user=request.user,
            question__lesson=lesson
        ).exists()
        
        if existing_answers:
            return Response(
                {"detail": "Vous avez déjà répondu à ce quiz."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get questions efficiently
        questions_dict = {
            q.id: q for q in Question.objects.filter(lesson=lesson).select_related()
        }
        
        # Get answers efficiently
        question_ids = list(questions_dict.keys())
        all_answers = {
            a.id: a for a in Answer.objects.filter(question_id__in=question_ids)
        }
        
        # Process answers
        results = []
        total_points = 0
        earned_points = 0
        user_answers = []
        
        for answer_data in answers:
            question_id = answer_data.get('question_id')
            answer_id = answer_data.get('answer_id')
            
            if question_id not in questions_dict or answer_id not in all_answers:
                continue
                
            question = questions_dict[question_id]
            answer = all_answers[answer_id]
            
            if answer.question_id != question_id:
                continue
                
            # Create UserAnswer object (but don't save yet)
            user_answer = UserAnswer(
                user=request.user,
                question=question,
                answer=answer,
                is_correct=answer.is_correct
            )
            user_answers.append(user_answer)
            
            total_points += question.points
            if answer.is_correct:
                earned_points += question.points
            
            results.append({
                'question_id': question.id,
                'is_correct': answer.is_correct,
                'points': question.points if answer.is_correct else 0
            })
        
        # Bulk create user answers
        if user_answers:
            UserAnswer.objects.bulk_create(user_answers)
        
        # Calculate score
        score_percentage = int((earned_points / total_points) * 100) if total_points > 0 else 0
        
        # Mark lesson as completed if score is sufficient
        if score_percentage >= 70:  # 70% to pass
            progress, _ = UserProgress.objects.get_or_create(
                user=request.user,
                lesson=lesson
            )
            
            if not progress.completed:
                progress.completed = True
                progress.completion_date = timezone.now()
                progress.save(update_fields=['completed', 'completion_date'])
        
        return Response({
            'score': score_percentage,
            'earned_points': earned_points,
            'total_points': total_points,
            'results': results,
            'passed': score_percentage >= 70
        })