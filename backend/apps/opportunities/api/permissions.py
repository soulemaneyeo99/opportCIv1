from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Staff can edit any object
        if request.user.is_staff:
            return True

        # Write permissions are only allowed to the owner of the opportunity
        return obj.created_by == request.user


class IsVerifiedUser(permissions.BasePermission):
    """
    Custom permission to only allow verified users to create opportunities.
    Used to prevent spam by requiring email verification or account age.
    """
    
    def has_permission(self, request, view):
        # Allow read-only for anyone
        if request.method in permissions.SAFE_METHODS:
            return True

        # For write operations, check if user is authenticated
        if not request.user.is_authenticated:
            return False
        
        # Staff can always create
        if request.user.is_staff:
            return True
        
        # Check if user profile is verified
        # This assumes you have a profile with a is_verified field
        # Modify this according to your user model structure
        try:
            return request.user.profile.is_verified
        except AttributeError:
            # If no profile exists or no is_verified attribute, fall back to checking account age
            from django.utils import timezone
            from datetime import timedelta
            
            account_age = timezone.now() - request.user.date_joined
            # Allow creation if account is older than 3 days
            return account_age > timedelta(days=3)