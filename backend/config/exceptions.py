"""
OpportuCI - Custom Exceptions & Error Handling
===============================================
Gestion centralisée des erreurs avec réponses standardisées
"""
from rest_framework.views import exception_handler
from rest_framework import status
from rest_framework.response import Response
from django.core.exceptions import ValidationError as DjangoValidationError
import logging

logger = logging.getLogger(__name__)


class OpportuCIException(Exception):
    """Exception de base pour toutes les erreurs OpportuCI"""
    default_message = "Une erreur est survenue"
    default_code = "error"
    status_code = status.HTTP_400_BAD_REQUEST
    
    def __init__(self, message=None, code=None, status_code=None, extra_data=None):
        self.message = message or self.default_message
        self.code = code or self.default_code
        self.status_code = status_code or self.status_code
        self.extra_data = extra_data or {}
        super().__init__(self.message)


class ValidationError(OpportuCIException):
    """Erreur de validation des données"""
    default_message = "Les données fournies sont invalides"
    default_code = "validation_error"
    status_code = status.HTTP_400_BAD_REQUEST


class AuthenticationError(OpportuCIException):
    """Erreur d'authentification"""
    default_message = "Authentification échouée"
    default_code = "authentication_error"
    status_code = status.HTTP_401_UNAUTHORIZED


class PermissionDeniedError(OpportuCIException):
    """Erreur de permission"""
    default_message = "Vous n'avez pas les permissions nécessaires"
    default_code = "permission_denied"
    status_code = status.HTTP_403_FORBIDDEN


class NotFoundError(OpportuCIException):
    """Ressource non trouvée"""
    default_message = "Ressource non trouvée"
    default_code = "not_found"
    status_code = status.HTTP_404_NOT_FOUND


class ConflictError(OpportuCIException):
    """Conflit de données"""
    default_message = "Conflit avec les données existantes"
    default_code = "conflict_error"
    status_code = status.HTTP_409_CONFLICT


class RateLimitError(OpportuCIException):
    """Limite de taux dépassée"""
    default_message = "Trop de requêtes. Réessayez plus tard"
    default_code = "rate_limit_exceeded"
    status_code = status.HTTP_429_TOO_MANY_REQUESTS


class ExternalServiceError(OpportuCIException):
    """Erreur de service externe (Gemini, etc.)"""
    default_message = "Service externe temporairement indisponible"
    default_code = "external_service_error"
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE


class InsufficientCreditsError(OpportuCIException):
    """Crédits insuffisants"""
    default_message = "Points de crédibilité insuffisants"
    default_code = "insufficient_credits"
    status_code = status.HTTP_402_PAYMENT_REQUIRED


class LearningPathGenerationError(OpportuCIException):
    """Erreur lors de la génération d'un parcours"""
    default_message = "Impossible de générer le parcours d'apprentissage"
    default_code = "learning_path_generation_error"
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


class SimulationError(OpportuCIException):
    """Erreur durant une simulation"""
    default_message = "Erreur durant la simulation"
    default_code = "simulation_error"
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


def custom_exception_handler(exc, context):
    """
    Gestionnaire d'exceptions personnalisé pour DRF
    Standardise toutes les réponses d'erreur
    """
    # Appel du handler par défaut de DRF
    response = exception_handler(exc, context)
    
    # Gestion des exceptions OpportuCI
    if isinstance(exc, OpportuCIException):
        response_data = {
            'success': False,
            'error': {
                'code': exc.code,
                'message': exc.message,
                'details': exc.extra_data
            }
        }
        
        # Log selon la sévérité
        if exc.status_code >= 500:
            logger.error(f"Server Error: {exc.message}", exc_info=True, extra={
                'context': context,
                'code': exc.code
            })
        else:
            logger.warning(f"Client Error: {exc.message}", extra={
                'context': context,
                'code': exc.code
            })
        
        return Response(response_data, status=exc.status_code)
    
    # Gestion des ValidationError Django
    if isinstance(exc, DjangoValidationError):
        response_data = {
            'success': False,
            'error': {
                'code': 'validation_error',
                'message': 'Erreur de validation',
                'details': exc.message_dict if hasattr(exc, 'message_dict') else {'non_field_errors': exc.messages}
            }
        }
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
    
    # Si DRF a déjà géré l'exception
    if response is not None:
        # Standardiser le format de réponse
        custom_response_data = {
            'success': False,
            'error': {
                'code': response.status_code,
                'message': response.data.get('detail', 'Une erreur est survenue'),
                'details': {k: v for k, v in response.data.items() if k != 'detail'}
            }
        }
        response.data = custom_response_data
        
        # Log erreurs serveur
        if response.status_code >= 500:
            logger.error(f"Server Error: {response.status_code}", exc_info=True, extra={
                'context': context,
                'response': response.data
            })
        
        return response
    
    # Erreurs non gérées (500)
    logger.error("Unhandled Exception", exc_info=True, extra={
        'exception': str(exc),
        'context': context
    })
    
    return Response({
        'success': False,
        'error': {
            'code': 'internal_server_error',
            'message': 'Une erreur interne est survenue. Notre équipe a été notifiée.',
            'details': {}
        }
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def handle_exception_with_notification(exc, user=None):
    """
    Gère une exception et envoie une notification à l'utilisateur si applicable
    """
    from apps.notifications.services import NotificationService
    
    logger.exception("Exception with user notification", extra={
        'user': user.id if user else None,
        'exception': str(exc)
    })
    
    if user and isinstance(exc, OpportuCIException):
        # Notifier l'utilisateur pour certaines erreurs
        if isinstance(exc, (ExternalServiceError, LearningPathGenerationError)):
            NotificationService.create_notification(
                user=user,
                title="Erreur temporaire",
                message="Nous avons rencontré un problème. Réessayez dans quelques instants.",
                notification_type='system'
            )