# backend/courses/permissions.py
from rest_framework import permissions


class IsInstructorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow instructors to edit.
    Optimized to check for admin status before checking specific permissions.
    """
    
    def has_permission(self, request, view):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Staff/admin can do anything
        if request.user.is_staff:
            return True
            
        # Otherwise check if user is instructor (could be cached or checked via role-based auth)
        return request.user.is_authenticated and hasattr(request.user, 'is_instructor') and request.user.is_instructor
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Staff/admin can do anything
        if request.user.is_staff:
            return True
            
        # Instructor of this specific course
        if hasattr(obj, 'instructor'):
            return obj.instructor == request.user.username
            
        # For course-related objects
        if hasattr(obj, 'course') and hasattr(obj.course, 'instructor'):
            return obj.course.instructor == request.user.username
            
        return False


class IsUserProgressOwner(permissions.BasePermission):
    """
    Custom permission to only allow users to view their own progress.
    """
    
    def has_object_permission(self, request, view, obj):
        # Staff can access any progress
        if request.user.is_staff:
            return True
            
        # Regular users can only access their own progress
        return obj.user == request.user


class CanAccessCourse(permissions.BasePermission):
    """
    Permission to check if user has access to a course via enrollment.
    """
    
    def has_object_permission(self, request, view, obj):
        # Staff can access any course
        if request.user.is_staff:
            return True
            
        # If this is a course object
        if hasattr(obj, 'formation'):
            formation = obj.formation
        # If this is a lesson or related object
        elif hasattr(obj, 'course') and hasattr(obj.course, 'formation'):
            formation = obj.course.formation
        # If this is a question or other related object
        elif hasattr(obj, 'lesson') and hasattr(obj.lesson, 'course') and hasattr(obj.lesson.course, 'formation'):
            formation = obj.lesson.course.formation
        else:
            return False
            
        # Check if user is enrolled in the formation
        return request.user.formation_enrollments.filter(
            formation=formation,
            status='approved'
        ).exists()