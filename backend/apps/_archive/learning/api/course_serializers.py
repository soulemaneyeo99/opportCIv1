# backend/courses/serializers.py
from rest_framework import serializers
from django.db.models import Prefetch
from .models import Course, Lesson, UserProgress, Question, Answer, UserAnswer


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'text', 'is_correct']
        extra_kwargs = {
            'is_correct': {'write_only': True}
        }


class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'text', 'difficulty', 'points', 'explanation', 'answers']


class QuestionAdminSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True)

    class Meta:
        model = Question
        fields = ['id', 'lesson', 'text', 'difficulty', 'points', 'explanation', 'answers']
    
    def create(self, validated_data):
        answers_data = validated_data.pop('answers')
        question = Question.objects.create(**validated_data)
        
        # Use bulk_create for better performance
        Answer.objects.bulk_create([
            Answer(question=question, **answer_data)
            for answer_data in answers_data
        ])
        
        return question
    
    def update(self, instance, validated_data):
        answers_data = validated_data.pop('answers', None)
        
        # Update question fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update answers if provided
        if answers_data is not None:
            # Delete existing answers
            instance.answers.all().delete()
            
            # Create new answers
            Answer.objects.bulk_create([
                Answer(question=instance, **answer_data)
                for answer_data in answers_data
            ])
        
        return instance


class LessonSerializer(serializers.ModelSerializer):
    is_completed = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Lesson
        fields = [
            'id', 'title', 'slug', 'course', 'content', 'type',
            'video_url', 'duration_minutes', 'order', 'is_published',
            'created_at', 'updated_at', 'is_completed', 'progress_percentage'
        ]
        read_only_fields = ['slug']
    
    def get_is_completed(self, obj):
        user = self.context.get('request').user
        if not user or not user.is_authenticated:
            return False
            
        # Check if we have a prefetched progress cache
        if hasattr(obj, 'user_progress_cache'):
            return any(p.completed for p in obj.user_progress_cache if p.user_id == user.id)
        
        # Fallback to database query
        try:
            progress = UserProgress.objects.get(user=user, lesson=obj)
            return progress.completed
        except UserProgress.DoesNotExist:
            return False
    
    def get_progress_percentage(self, obj):
        user = self.context.get('request').user
        if not user or not user.is_authenticated:
            return 0
            
        # Check if we have a prefetched progress cache
        if hasattr(obj, 'user_progress_cache'):
            progress_list = [p for p in obj.user_progress_cache if p.user_id == user.id]
            if progress_list:
                progress = progress_list[0]
                if progress.completed:
                    return 100
                elif obj.type == 'video' and obj.duration_minutes > 0:
                    total_seconds = obj.duration_minutes * 60
                    if total_seconds > 0:
                        return min(int((progress.last_position_seconds / total_seconds) * 100), 99)
            return 0
        
        # Fallback to database query
        try:
            progress = UserProgress.objects.get(user=user, lesson=obj)
            if progress.completed:
                return 100
            elif obj.type == 'video' and obj.duration_minutes > 0:
                total_seconds = obj.duration_minutes * 60
                if total_seconds > 0:
                    return min(int((progress.last_position_seconds / total_seconds) * 100), 99)
            return 0
        except UserProgress.DoesNotExist:
            return 0


class LessonDetailSerializer(LessonSerializer):
    questions = serializers.SerializerMethodField()
    
    class Meta(LessonSerializer.Meta):
        fields = LessonSerializer.Meta.fields + ['questions']
    
    def get_questions(self, obj):
        if obj.type == 'quiz':
            # Use prefetched questions if available
            if hasattr(obj, 'prefetched_questions'):
                questions = obj.prefetched_questions
            else:
                questions = Question.objects.filter(lesson=obj).prefetch_related('answers')
                
            return QuestionSerializer(questions, many=True).data
        return []


class CourseSerializer(serializers.ModelSerializer):
    lessons_count = serializers.SerializerMethodField()
    formation_title = serializers.ReadOnlyField(source='formation.title')
    progress_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'description', 'formation', 'formation_title',
            'instructor', 'duration_minutes', 'difficulty', 'order',
            'is_published', 'created_at', 'updated_at', 'lessons_count',
            'progress_percentage'
        ]
        read_only_fields = ['slug']
    
    def get_lessons_count(self, obj):
        # Use annotation if available
        if hasattr(obj, 'published_lessons_count'):
            return obj.published_lessons_count
        return obj.lessons.filter(is_published=True).count()
    
    def get_progress_percentage(self, obj):
        user = self.context.get('request').user
        if not user or not user.is_authenticated:
            return 0
        
        # Get published lessons
        published_lessons = obj.lessons.filter(is_published=True)
        if not published_lessons:
            return 0
        
        # Use prefetched user_progress if available
        if hasattr(obj, 'prefetched_user_progress'):
            completed_lessons = len([
                p for p in obj.prefetched_user_progress 
                if p.completed and p.lesson.is_published
            ])
            total_lessons = len([l for l in obj.lessons.all() if l.is_published])
            
            if total_lessons > 0:
                return int((completed_lessons / total_lessons) * 100)
            return 0
            
        # Fallback to database query
        completed_lessons = UserProgress.objects.filter(
            user=user,
            lesson__course=obj,
            lesson__is_published=True,
            completed=True
        ).count()
        
        total_lessons = published_lessons.count()
        if total_lessons > 0:
            return int((completed_lessons / total_lessons) * 100)
        return 0


class CourseDetailSerializer(CourseSerializer):
    lessons = serializers.SerializerMethodField()
    
    class Meta(CourseSerializer.Meta):
        fields = CourseSerializer.Meta.fields + ['lessons']
    
    def get_lessons(self, obj):
        # Get lessons, potentially prefetched
        lessons = obj.lessons.filter(is_published=True)
        
        # Prepare context with user for progress calculations
        context = {'request': self.context.get('request')}
        
        # If we have the user, prefetch user progress for all lessons
        user = context['request'].user
        if user and user.is_authenticated:
            # If not already prefetched, prefetch user progress
            if not hasattr(obj, 'prefetched_lessons'):
                lessons = lessons.prefetch_related(
                    Prefetch(
                        'user_progress',
                        queryset=UserProgress.objects.filter(user=user),
                        to_attr='user_progress_cache'
                    )
                )
        
        serializer = LessonSerializer(lessons, many=True, context=context)
        return serializer.data


class UserProgressSerializer(serializers.ModelSerializer):
    lesson_title = serializers.ReadOnlyField(source='lesson.title')
    course_title = serializers.ReadOnlyField(source='lesson.course.title')
    
    class Meta:
        model = UserProgress
        fields = [
            'id', 'user', 'lesson', 'lesson_title', 'course_title',
            'completed', 'completion_date', 'last_position_seconds',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class UserAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAnswer
        fields = ['id', 'user', 'question', 'answer', 'is_correct', 'created_at']
        read_only_fields = ['user', 'is_correct', 'created_at']
    
    def create(self, validated_data):
        # Set current user
        validated_data['user'] = self.context['request'].user
        
        # Check if the answer is correct
        answer = validated_data.get('answer')
        validated_data['is_correct'] = answer.is_correct
        
        return super().create(validated_data)