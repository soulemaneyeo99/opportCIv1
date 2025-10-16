# accounts/permissions.py
from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission pour autoriser uniquement les propriétaires d'un objet à le modifier.
    Les requêtes en lecture sont autorisées pour toute personne authentifiée.
    """

    def has_object_permission(self, request, view, obj):
        # Les requêtes en lecture sont autorisées pour tout utilisateur authentifié
        if request.method in permissions.SAFE_METHODS:
            return True

        # Les permissions d'écriture sont uniquement pour le propriétaire
        return obj.id == request.user.id

class IsAdminOrSelf(permissions.BasePermission):
    """
    Permission pour autoriser uniquement l'administrateur ou l'utilisateur lui-même.
    """

    def has_object_permission(self, request, view, obj):
        # Vérifier si l'utilisateur est un administrateur ou s'il s'agit de son propre objet
        return request.user.is_admin or obj.id == request.user.id