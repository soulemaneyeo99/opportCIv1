"""
OpportuCI - Core Views
======================
Health check and system status endpoints.
"""
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
import time


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint for Docker/Kubernetes.

    Returns:
        - status: 'healthy' or 'unhealthy'
        - database: connection status
        - cache: Redis connection status
        - timestamp: current server time
    """
    health = {
        'status': 'healthy',
        'database': 'ok',
        'cache': 'ok',
        'timestamp': time.time(),
    }

    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
    except Exception as e:
        health['database'] = f'error: {str(e)}'
        health['status'] = 'unhealthy'

    # Check cache (Redis)
    try:
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') != 'ok':
            raise Exception('Cache read failed')
    except Exception as e:
        health['cache'] = f'error: {str(e)}'
        # Cache failure is not critical for health

    status_code = 200 if health['status'] == 'healthy' else 503
    return Response(health, status=status_code)


@api_view(['GET'])
@permission_classes([AllowAny])
def api_info(request):
    """
    API information endpoint.
    """
    return Response({
        'name': 'OpportuCI API',
        'version': '1.0.0',
        'description': 'AI-powered opportunity platform for Ivorian youth',
        'endpoints': {
            'health': '/api/health/',
            'accounts': '/api/accounts/',
            'opportunities': '/api/opportunities/',
            'prep': '/api/prep/',
            'notifications': '/api/notifications/',
        }
    })
