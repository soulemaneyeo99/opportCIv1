# backend/formations/permissions.py
from rest_framework import permissions

class IsEnrollmentOwner(permissions.BasePermission):
    """
    Autorise uniquement le propriétaire de l'inscription à la modifier ou la supprimer.
    """
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user

class IsFormationInstructor(permissions.BasePermission):
    """
    Autorise uniquement l'instructeur de la formation à effectuer certaines actions.
    """
    def has_object_permission(self, request, view, obj):
        return request.user == obj.instructor
