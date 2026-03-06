# backend/credibility/permissions.py
from rest_framework import permissions

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission permettant uniquement au propriétaire ou à un administrateur d'accéder.
    """
    def has_object_permission(self, request, view, obj):
        # Vérifier si l'utilisateur est admin
        if request.user.is_staff:
            return True
        
        # Vérifier si l'utilisateur est le propriétaire
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False