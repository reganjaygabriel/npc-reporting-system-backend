"""
Centralized Error Handling
Provides consistent error responses and logging
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError, PermissionDenied
from django.http import Http404
import logging
import traceback

logger = logging.getLogger(__name__)


class ErrorCode:
    """Standard error codes for the application"""
    
    # Authentication & Authorization
    UNAUTHORIZED = 'UNAUTHORIZED'
    FORBIDDEN = 'FORBIDDEN'
    INVALID_CREDENTIALS = 'INVALID_CREDENTIALS'
    TOKEN_EXPIRED = 'TOKEN_EXPIRED'
    
    # Validation
    VALIDATION_ERROR = 'VALIDATION_ERROR'
    INVALID_INPUT = 'INVALID_INPUT'
    MISSING_FIELD = 'MISSING_FIELD'
    
    # File Operations
    FILE_TOO_LARGE = 'FILE_TOO_LARGE'
    INVALID_FILE_FORMAT = 'INVALID_FILE_FORMAT'
    FILE_UPLOAD_FAILED = 'FILE_UPLOAD_FAILED'
    FILE_PROCESSING_ERROR = 'FILE_PROCESSING_ERROR'
    
    # Data Operations
    DUPLICATE_ENTRY = 'DUPLICATE_ENTRY'
    NOT_FOUND = 'NOT_FOUND'
    DATABASE_ERROR = 'DATABASE_ERROR'
    
    # Business Logic
    INVALID_DATE_RANGE = 'INVALID_DATE_RANGE'
    PLANT_NOT_FOUND = 'PLANT_NOT_FOUND'
    UNIT_NOT_FOUND = 'UNIT_NOT_FOUND'
    NOMINATION_CONFLICT = 'NOMINATION_CONFLICT'
    
    # System
    INTERNAL_ERROR = 'INTERNAL_ERROR'
    SERVICE_UNAVAILABLE = 'SERVICE_UNAVAILABLE'


class AppError(Exception):
    """Base application error"""
    
    def __init__(self, message, code=ErrorCode.INTERNAL_ERROR, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, details=None):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(AppError):
    """Validation error"""
    
    def __init__(self, message, details=None):
        super().__init__(
            message=message,
            code=ErrorCode.VALIDATION_ERROR,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class AuthenticationError(AppError):
    """Authentication error"""
    
    def __init__(self, message="Authentication failed"):
        super().__init__(
            message=message,
            code=ErrorCode.UNAUTHORIZED,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class PermissionError(AppError):
    """Permission error"""
    
    def __init__(self, message="You don't have permission to perform this action"):
        super().__init__(
            message=message,
            code=ErrorCode.FORBIDDEN,
            status_code=status.HTTP_403_FORBIDDEN
        )


class NotFoundError(AppError):
    """Resource not found error"""
    
    def __init__(self, message="Resource not found", resource_type=None):
        details = {'resource_type': resource_type} if resource_type else {}
        super().__init__(
            message=message,
            code=ErrorCode.NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details
        )


class FileError(AppError):
    """File operation error"""
    
    def __init__(self, message, code=ErrorCode.FILE_UPLOAD_FAILED):
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_400_BAD_REQUEST
        )


def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # Log the exception
    logger.error(
        f"Exception: {exc.__class__.__name__}: {str(exc)}",
        exc_info=True,
        extra={'context': context}
    )
    
    # Handle custom AppError
    if isinstance(exc, AppError):
        return Response({
            'success': False,
            'error': {
                'code': exc.code,
                'message': exc.message,
                'details': exc.details
            }
        }, status=exc.status_code)
    
    # Handle Django validation errors
    if isinstance(exc, ValidationError):
        return Response({
            'success': False,
            'error': {
                'code': ErrorCode.VALIDATION_ERROR,
                'message': 'Validation error',
                'details': {'validation_errors': exc.messages}
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Handle Django permission denied
    if isinstance(exc, PermissionDenied):
        return Response({
            'success': False,
            'error': {
                'code': ErrorCode.FORBIDDEN,
                'message': str(exc) or 'Permission denied',
                'details': {}
            }
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Handle Django 404
    if isinstance(exc, Http404):
        return Response({
            'success': False,
            'error': {
                'code': ErrorCode.NOT_FOUND,
                'message': 'Resource not found',
                'details': {}
            }
        }, status=status.HTTP_404_NOT_FOUND)
    
    # If response is already handled by DRF
    if response is not None:
        # Standardize the error response format
        error_data = {
            'success': False,
            'error': {
                'code': ErrorCode.VALIDATION_ERROR,
                'message': 'Request validation failed',
                'details': response.data
            }
        }
        response.data = error_data
        return response
    
    # Handle unexpected errors
    logger.critical(
        f"Unhandled exception: {exc.__class__.__name__}: {str(exc)}",
        exc_info=True,
        extra={
            'context': context,
            'traceback': traceback.format_exc()
        }
    )
    
    return Response({
        'success': False,
        'error': {
            'code': ErrorCode.INTERNAL_ERROR,
            'message': 'An unexpected error occurred. Please try again later.',
            'details': {'error_type': exc.__class__.__name__} if context.get('request').user.is_staff else {}
        }
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def handle_file_upload_error(error, filename):
    """
    Handle file upload errors with specific messages
    """
    error_str = str(error).lower()
    
    if 'size' in error_str or 'large' in error_str:
        raise FileError(
            f"File '{filename}' is too large. Maximum size is 25MB.",
            code=ErrorCode.FILE_TOO_LARGE
        )
    elif 'format' in error_str or 'invalid' in error_str:
        raise FileError(
            f"File '{filename}' has an invalid format. Please upload a valid Excel file (.xlsx).",
            code=ErrorCode.INVALID_FILE_FORMAT
        )
    elif 'corrupt' in error_str:
        raise FileError(
            f"File '{filename}' appears to be corrupted. Please try uploading again.",
            code=ErrorCode.FILE_PROCESSING_ERROR
        )
    else:
        raise FileError(
            f"Failed to process file '{filename}': {str(error)}",
            code=ErrorCode.FILE_PROCESSING_ERROR
        )


def handle_database_error(error, operation='database operation'):
    """
    Handle database errors
    """
    error_str = str(error).lower()
    
    if 'unique' in error_str or 'duplicate' in error_str:
        raise AppError(
            f"Duplicate entry detected. This record already exists.",
            code=ErrorCode.DUPLICATE_ENTRY,
            status_code=status.HTTP_409_CONFLICT
        )
    else:
        logger.error(f"Database error during {operation}: {str(error)}")
        raise AppError(
            f"Database error occurred during {operation}. Please try again.",
            code=ErrorCode.DATABASE_ERROR,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def success_response(data=None, message=None, status_code=status.HTTP_200_OK):
    """
    Standard success response format
    """
    response_data = {
        'success': True,
    }
    
    if message:
        response_data['message'] = message
    
    if data is not None:
        response_data['data'] = data
    
    return Response(response_data, status=status_code)


def error_response(message, code=ErrorCode.INTERNAL_ERROR, details=None, status_code=status.HTTP_400_BAD_REQUEST):
    """
    Standard error response format
    """
    return Response({
        'success': False,
        'error': {
            'code': code,
            'message': message,
            'details': details or {}
        }
    }, status=status_code)
