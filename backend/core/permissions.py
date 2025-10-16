"""
OpportuCI - Custom Permissions
================================
"""
from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission qui autorise uniquement le propriétaire à modifier.
    Lecture autorisée pour tous les utilisateurs authentifiés.
    """
    
    def has_object_permission(self, request, view, obj):
        # Lecture autorisée pour tout le monde
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Écriture uniquement pour le propriétaire
        # Vérifie si l'objet a un attribut 'user'
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # Sinon, vérifie si l'objet EST l'utilisateur
        return obj == request.user