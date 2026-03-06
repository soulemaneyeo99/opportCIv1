"""
OpportuCI - Custom Exception Handler
=====================================
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF.
    Provides consistent error response format.
    """
    response = exception_handler(exc, context)

    if response is not None:
        # Wrap single error messages in a consistent format
        if isinstance(response.data, dict):
            error_data = {
                'success': False,
                'errors': response.data
            }
        elif isinstance(response.data, list):
            error_data = {
                'success': False,
                'errors': {'detail': response.data}
            }
        else:
            error_data = {
                'success': False,
                'errors': {'detail': str(response.data)}
            }

        response.data = error_data

    return response
