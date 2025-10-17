"""
OpportuCI - Custom Middleware
==============================
"""
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from jwt import decode as jwt_decode
from django.conf import settings

User = get_user_model()


class JWTAuthMiddleware(BaseMiddleware):
    """Middleware pour authentifier les WebSockets avec JWT"""
    
    async def __call__(self, scope, receive, send):
        # Extraire le token des query params
        query_string = scope.get('query_string', b'').decode()
        params = dict(param.split('=') for param in query_string.split('&') if '=' in param)
        token = params.get('token')
        
        if token:
            try:
                # Valider le token
                UntypedToken(token)
                
                # Décoder pour obtenir user_id
                decoded_data = jwt_decode(
                    token, 
                    settings.SECRET_KEY, 
                    algorithms=["HS256"]
                )
                
                # Récupérer l'utilisateur
                user = await self.get_user(decoded_data['user_id'])
                scope['user'] = user
            except (InvalidToken, TokenError, KeyError):
                scope['user'] = AnonymousUser()
        else:
            scope['user'] = AnonymousUser()
        
        return await super().__call__(scope, receive, send)
    
    @database_sync_to_async
    def get_user(self, user_id):
        """Récupère l'utilisateur de manière async"""
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return AnonymousUser()


# Fonction helper pour utiliser dans routing.py
def JWTAuthMiddlewareStack(inner):
    return JWTAuthMiddleware(inner)