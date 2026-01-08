# Create a new file: myomega_backend/exception_handler.py

from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Custom exception handler that wraps DRF's default handler
    """
    # Call DRF's default exception handler first
    response = drf_exception_handler(exc, context)

    # If DRF didn't handle it, create a generic error response
    if response is None:
        return Response(
            {
                'error': str(exc),
                'detail': 'An error occurred processing your request.'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return response