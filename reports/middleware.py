"""
Comprehensive audit logging middleware for the NPC Reporting System
"""

import time
import json
import logging
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from django.urls import resolve, Resolver404
from django.http import JsonResponse
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

class AuditLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to automatically log all requests and responses for audit purposes
    """
    
    # URLs to exclude from audit logging (to avoid noise)
    EXCLUDED_PATHS = [
        '/static/',
        '/media/',
        '/favicon.ico',
        '/admin/jsi18n/',
        '/api/health/',
        '/api/ping/',
    ]
    
    # Actions that should be logged with higher severity
    HIGH_SEVERITY_ACTIONS = [
        'DELETE', 'REJECT', 'REVOKE', 'DEACTIVATE'
    ]
    
    CRITICAL_SEVERITY_ACTIONS = [
        'USER_DELETE', 'SYSTEM_CONFIG_CHANGE', 'SECURITY_VIOLATION'
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        """Process incoming request"""
        try:
            request._audit_start_time = time.time()
            
            # Skip excluded paths
            if any(request.path.startswith(path) for path in self.EXCLUDED_PATHS):
                return None
            
            # Log page access for GET requests (only for non-API endpoints)
            if request.method == 'GET' and not request.path.startswith('/api/'):
                self._log_page_access(request)
        except Exception as e:
            logger.error(f"Error in process_request: {e}")
        
        return None
        
    def process_response(self, request, response):
        """Process outgoing response"""
        try:
            # Skip excluded paths
            if any(request.path.startswith(path) for path in self.EXCLUDED_PATHS):
                return response
            
            # Calculate duration
            duration_ms = None
            if hasattr(request, '_audit_start_time'):
                duration_ms = int((time.time() - request._audit_start_time) * 1000)
            
            # Log API calls
            if request.path.startswith('/api/'):
                self._log_api_call(request, response, duration_ms)
        except Exception as e:
            logger.error(f"Error in process_response: {e}")
        
        return response
    
    def process_exception(self, request, exception):
        """Process exceptions"""
        try:
            # Log system errors
            duration_ms = None
            if hasattr(request, '_audit_start_time'):
                duration_ms = int((time.time() - request._audit_start_time) * 1000)
            
            # Import AuditLog here to avoid circular imports
            from .models import AuditLog
            
            AuditLog.log_action(
                user=self._get_user_safely(request),
                action='SYSTEM_ERROR',
                description=f'Exception occurred: {str(exception)}',
                request=request,
                category='system',
                severity='HIGH',
                success=False,
                error_message=str(exception),
                duration_ms=duration_ms,
                response_status=500
            )
        except Exception as e:
            logger.error(f"Failed to log exception audit: {e}")
        
        return None
    
    def _get_user_safely(self, request):
        """Safely get user from request"""
        try:
            if hasattr(request, 'user') and request.user and not isinstance(request.user, AnonymousUser):
                return request.user
        except Exception:
            pass
        return None
    
    def _log_page_access(self, request):
        """Log page access events"""
        try:
            # Import AuditLog here to avoid circular imports
            from .models import AuditLog
            
            # Determine page category
            category = self._get_page_category(request.path)
            
            # Get page name from URL resolver
            try:
                resolved = resolve(request.path)
                page_name_raw = getattr(resolved, 'url_name', None) or getattr(resolved, 'view_name', None) or 'Unknown'
            except (Resolver404, AttributeError):
                page_name_raw = request.path
            
            # Map raw page names to user-friendly names
            page_map = {
                'landing': 'Home Page',
                'dashboard': 'System Dashboard',
                'upload': 'Data Upload Page',
                'generate-report': 'Report Generation',
                'view-reports': 'View Reports',
                'audit-logs': 'Audit Logs View',
                'user-management': 'User Management',
                'signature-setup': 'Signature Setup',
                'authorization-request': 'Signature Authorization',
                'password-reset': 'Password Reset Page',
                'login': 'Login Page',
                'register': 'Registration Page',
            }
            
            # Try to clean up path-based names
            clean_name = page_name_raw.strip('/').replace('/', ' ').replace('-', ' ').replace('_', ' ').title()
            page_name = page_map.get(page_name_raw.lower(), clean_name)
            
            AuditLog.log_action(
                user=self._get_user_safely(request),
                action='PAGE_ACCESS',
                description=f'Accessed {page_name}',
                request=request,
                category=category,
                severity='LOW',
                success=True
            )
        except Exception as e:
            logger.error(f"Failed to log page access: {e}")
    
    def _log_api_call(self, request, response, duration_ms):
        """Log API call events"""
        try:
            # Import AuditLog here to avoid circular imports
            from .models import AuditLog
            
            # Determine action based on HTTP method and URL
            action = self._determine_api_action(request)
            
            # Determine category
            category = self._get_api_category(request.path)
            
            # Determine severity
            severity = self._get_action_severity(action)
            
            # Check if successful
            success = 200 <= response.status_code < 400
            
            # Get error message if failed
            error_message = ''
            if not success:
                try:
                    if hasattr(response, 'content') and response.content:
                        content = json.loads(response.content.decode('utf-8'))
                        error_message = content.get('error', content.get('detail', ''))
                except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
                    error_message = f'HTTP {response.status_code}'
            
            AuditLog.log_action(
                user=self._get_user_safely(request),
                action=action,
                description=self._get_api_description(request, action),
                request=request,
                category=category,
                severity=severity,
                success=success,
                error_message=error_message,
                duration_ms=duration_ms,
                response_status=response.status_code
            )
        except Exception as e:
            logger.error(f"Failed to log API call: {e}")
    
    def _determine_api_action(self, request):
        """Determine the action based on the API endpoint and method"""
        path = request.path.lower()
        method = request.method.upper()
        
        # Authentication endpoints
        if '/auth/login' in path or '/token/' in path:
            return 'LOGIN'
        elif '/auth/logout' in path:
            return 'LOGOUT'
        elif '/auth/register' in path:
            return 'USER_CREATE'
        elif '/auth/password' in path:
            if 'reset' in path:
                return 'PASSWORD_RESET_REQUEST'
            else:
                return 'PASSWORD_CHANGE'
        
        # File operations
        elif '/uploaded-files/' in path:
            if method == 'POST':
                return 'FILE_UPLOAD'
            elif method == 'DELETE':
                return 'FILE_DELETE'
            elif 'archive' in path:
                return 'FILE_ARCHIVE'
            elif 'restore' in path:
                return 'FILE_RESTORE'
            elif method == 'GET':
                # Similar to generation-reports, a simple GET is often just loading a list
                # for the dashboard or tables, not necessarily "viewing" a specific file content.
                if request.GET.get('page') or 'summary' in path:
                     return 'DATA_VIEW'
                return 'FILE_VIEW'
        
        # Report operations
        elif '/generation-reports/' in path:
            if 'generate-report' in path:
                return 'REPORT_GENERATE'
            elif 'preview-report' in path:
                return 'REPORT_PREVIEW'
            elif method == 'GET':
                # Avoid logging simple dashboard data loads as "REPORT_VIEW" 
                # to prevent spamming logs right after login
                if 'summary' in path or 'dashboard' in path or request.GET.get('page'):
                    return 'DATA_VIEW'
                return 'REPORT_VIEW'
            elif method == 'DELETE':
                return 'REPORT_DELETE'
        
        # E-signature operations
        elif '/e-signatures/' in path:
            if method == 'POST':
                return 'SIGNATURE_CREATE'
            elif method == 'PUT' or method == 'PATCH':
                return 'SIGNATURE_UPDATE'
            elif method == 'DELETE':
                return 'SIGNATURE_DELETE'
            elif method == 'GET':
                return 'SIGNATURE_VIEW'
        
        # Report signatures
        elif '/report-signatures/' in path:
            if 'sign-report' in path:
                return 'REPORT_SIGN'
            elif method == 'GET':
                return 'SIGNATURE_VIEW'
        
        # Authorization operations
        elif '/signatory-authorizations/' in path or '/signature-requests/' in path:
            if 'request' in path and method == 'POST':
                return 'AUTH_REQUEST_CREATE'
            elif 'approve-request' in path or 'approve' in path:
                return 'AUTH_REQUEST_APPROVE'
            elif 'reject-request' in path or 'reject' in path:
                return 'AUTH_REQUEST_REJECT'
            elif 'cancel-request' in path or 'cancel' in path:
                return 'AUTH_REQUEST_CANCEL'
            elif 'approve-with-existing' in path:
                return 'AUTH_APPROVE_EXISTING'
            elif 'signature-setup' in path:
                return 'SIGNATURE_SETUP_ACCESS'
            elif 'save-signature' in path:
                return 'SIGNATURE_SETUP_COMPLETE'
            elif method == 'DELETE':
                return 'AUTH_REVOKE'
            elif method == 'GET':
                if request.GET.get('page') or 'summary' in path:
                    return 'DATA_VIEW'
                return 'AUTH_REQUEST_VIEW'
            elif method == 'POST':
                return 'AUTH_REQUEST_CREATE'
        
        # User management
        elif '/users/' in path:
            if method == 'POST':
                return 'USER_CREATE'
            elif method == 'PUT' or method == 'PATCH':
                return 'USER_UPDATE'
            elif method == 'DELETE':
                return 'USER_DELETE'
            elif method == 'GET':
                return 'DATA_VIEW'
                
        # Document/Storage operations
        elif '/documents/' in path:
            if 'request_signatures' in path or 'request-signatures' in path:
                return 'AUTH_REQUEST_CREATE'
            elif method == 'POST':
                return 'DOCUMENT_CREATE'
            elif method == 'PUT' or method == 'PATCH':
                return 'DOCUMENT_UPDATE'
            elif method == 'DELETE':
                return 'DOCUMENT_DELETE'
            elif method == 'GET':
                if request.GET.get('page') or 'summary' in path:
                    return 'DATA_VIEW'
                return 'DOCUMENT_VIEW'
        
        # Generic CRUD operations
        else:
            if method == 'POST':
                return 'DATA_CREATE'
            elif method == 'PUT' or method == 'PATCH':
                return 'DATA_UPDATE'
            elif method == 'DELETE':
                return 'DATA_DELETE'
            elif method == 'GET':
                return 'DATA_VIEW'
        
        return 'API_CALL'
    
    def _get_api_description(self, request, action):
        """Generate description for API action"""
        path = request.path.lower()
        method = request.method.upper()
        
        # Try to extract meaningful identifiers
        path_parts = [part for part in path.split('/') if part and not part.isdigit()]
        resource_raw = path_parts[-1] if path_parts else 'resource'
        
        # Map raw resource names to user-friendly names
        resource_map = {
            'audit-logs': 'audit logs',
            'pending_reset_count': 'pending password reset count',
            'uploaded-files': 'uploaded files',
            'generation-reports': 'generation reports',
            'plants': 'power plants',
            'units': 'generation units',
            'plant-capacities': 'plant capacities',
            'historical-data': 'historical data',
            'water-nominations': 'water nominations',
            'actual-generations': 'actual generations',
            'testimonials': 'user testimonials',
            'profiles': 'user profiles',
            'users': 'system users',
            'password-reset-requests': 'password reset requests',
            'e-signatures': 'electronic signatures',
            'report-signatures': 'report signatures',
            'signatory-authorizations': 'signatory authorizations',
            'authorization-requests': 'authorization requests',
            'signature-verification-tokens': 'security tokens',
            'signature-security-settings': 'security settings',
            'documents': 'system documents',
            'analytics': 'system analytics',
            'dashboard-stats': 'dashboard statistics',
            'plant-status': 'plant status information',
        }
        
        resource = resource_map.get(resource_raw, resource_raw.replace('-', ' ').replace('_', ' '))
        
        # Specialized descriptions for common actions
        descriptions = {
            'LOGIN': 'User logged into the system',
            'LOGOUT': 'User logged out of the system',
            'USER_CREATE': f'Created new user account: {resource}',
            'PASSWORD_RESET_REQUEST': 'Requested a password reset',
            'PASSWORD_CHANGE': 'Changed account password',
            'FILE_UPLOAD': 'Uploaded a new file to the system',
            'FILE_DELETE': 'Deleted a file from the system',
            'FILE_ARCHIVE': 'Moved a file to the archive',
            'FILE_RESTORE': 'Restored a file from the archive',
            'FILE_VIEW': f'Accessed or viewed file: {resource}',
            'REPORT_GENERATE': 'Generated a new system report',
            'REPORT_PREVIEW': 'Previewed a report',
            'REPORT_VIEW': 'Viewed a system report',
            'REPORT_DELETE': 'Deleted a report',
            'SIGNATURE_CREATE': 'Created a new electronic signature',
            'SIGNATURE_UPDATE': 'Updated electronic signature details',
            'SIGNATURE_DELETE': 'Deleted an electronic signature',
            'SIGNATURE_VIEW': 'Viewed electronic signature details',
            'REPORT_SIGN': 'Applied an electronic signature to a report',
            'AUTH_REQUEST_CREATE': 'Submitted a request for signature authorization',
            'AUTH_REQUEST_APPROVE': 'Approved a signature authorization request',
            'AUTH_REQUEST_REJECT': 'Rejected a signature authorization request',
            'AUTH_REQUEST_CANCEL': 'Cancelled a signature authorization request',
            'AUTH_APPROVE_EXISTING': 'Approved authorization using an existing signature',
            'SIGNATURE_SETUP_ACCESS': 'Accessed the signature setup page',
            'SIGNATURE_SETUP_COMPLETE': 'Successfully completed signature setup',
            'AUTH_REVOKE': 'Revoked a signature authorization',
            'AUTH_REQUEST_VIEW': 'Viewed a signature authorization request',
            'USER_UPDATE': 'Updated user account information',
            'USER_DELETE': 'Deleted a user account',
            'DOCUMENT_CREATE': 'Saved a report to storage',
            'DOCUMENT_UPDATE': 'Updated a stored report',
            'DOCUMENT_DELETE': 'Deleted a stored report',
            'DOCUMENT_VIEW': 'Viewed a stored report',
            'DATA_CREATE': f'Created new {resource} record',
            'DATA_UPDATE': f'Updated {resource} information',
            'DATA_DELETE': f'Deleted {resource} record',
            'DATA_VIEW': f'Viewed {resource}',
            'PAGE_ACCESS': f'Accessed page: {resource}',
            'DASHBOARD_VIEW': 'Viewed system dashboard',
            'SYSTEM_ERROR': 'A system error occurred',
        }
        
        # Fallback for generic DATA_VIEW to make it more natural
        if action == 'DATA_VIEW':
            if method == 'GET':
                return f'Viewed {resource}'
        
        # Return mapped description or a cleaned-up fallback
        fallback = f'{method} operation on {resource}'
        return descriptions.get(action, fallback)
    
    def _get_page_category(self, path):
        """Determine page category"""
        if path == '/' or 'landing' in path:
            return 'landing'
        elif 'dashboard' in path:
            return 'dashboard'
        elif 'upload' in path:
            return 'file_management'
        elif 'generate' in path or 'report' in path:
            return 'reporting'
        elif 'signature' in path or 'authorization' in path:
            return 'e_signature'
        elif 'user' in path or 'admin' in path:
            return 'administration'
        elif 'archive' in path:
            return 'archive'
        else:
            return 'general'
    
    def _get_api_category(self, path):
        """Determine API category"""
        if '/auth/' in path:
            return 'authentication'
        elif '/uploaded-files/' in path:
            return 'file_management'
        elif '/generation-reports/' in path or '/report-signatures/' in path:
            return 'reporting'
        elif '/e-signatures/' in path or '/signatory-authorizations/' in path:
            return 'e_signature'
        elif '/users/' in path:
            return 'user_management'
        else:
            return 'api'
    
    def _get_action_severity(self, action):
        """Determine severity level for action"""
        if action in self.CRITICAL_SEVERITY_ACTIONS:
            return 'CRITICAL'
        elif action in self.HIGH_SEVERITY_ACTIONS:
            return 'HIGH'
        elif action in ['LOGIN_FAILED', 'UNAUTHORIZED_ACCESS', 'PERMISSION_DENIED']:
            return 'MEDIUM'
        else:
            return 'LOW'


class SecurityAuditMiddleware(MiddlewareMixin):
    """
    Middleware specifically for security-related audit logging
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        """Check for security violations"""
        try:
            # Log suspicious patterns
            self._check_suspicious_patterns(request)
        except Exception as e:
            logger.error(f"Error in SecurityAuditMiddleware: {e}")
        return None
    
    def _get_user_safely(self, request):
        """Safely get user from request"""
        try:
            if hasattr(request, 'user') and request.user and not isinstance(request.user, AnonymousUser):
                return request.user
        except Exception:
            pass
        return None
    
    def _check_suspicious_patterns(self, request):
        """Check for suspicious request patterns"""
        try:
            # Import AuditLog here to avoid circular imports
            from .models import AuditLog
            
            # Check for SQL injection attempts
            if self._contains_sql_injection(request):
                AuditLog.log_action(
                    user=self._get_user_safely(request),
                    action='SECURITY_VIOLATION',
                    description='Potential SQL injection attempt detected',
                    request=request,
                    category='security',
                    severity='CRITICAL',
                    success=False
                )
            
            # Check for XSS attempts
            if self._contains_xss(request):
                AuditLog.log_action(
                    user=self._get_user_safely(request),
                    action='SECURITY_VIOLATION',
                    description='Potential XSS attempt detected',
                    request=request,
                    category='security',
                    severity='HIGH',
                    success=False
                )
            
            # Check for unusual request patterns
            if self._is_unusual_request(request):
                AuditLog.log_action(
                    user=self._get_user_safely(request),
                    action='SECURITY_VIOLATION',
                    description='Unusual request pattern detected',
                    request=request,
                    category='security',
                    severity='MEDIUM',
                    success=False
                )
        except Exception as e:
            logger.error(f"Failed to check security patterns: {e}")
    
    def _contains_sql_injection(self, request):
        """Check for SQL injection patterns"""
        try:
            sql_patterns = [
                'union select', 'drop table', 'delete from', 'insert into',
                'update set', 'exec(', 'execute(', '--', '/*', '*/',
                'xp_cmdshell', 'sp_executesql'
            ]
            
            # Check URL parameters and POST data
            all_data = []
            if hasattr(request, 'GET') and request.GET:
                all_data.extend(request.GET.values())
            if hasattr(request, 'POST') and request.POST:
                all_data.extend(request.POST.values())
            
            for value in all_data:
                if isinstance(value, str):
                    for pattern in sql_patterns:
                        if pattern in value.lower():
                            return True
        except Exception as e:
            logger.error(f"Error checking SQL injection: {e}")
        return False
    
    def _contains_xss(self, request):
        """Check for XSS patterns"""
        try:
            xss_patterns = [
                '<script', 'javascript:', 'onload=', 'onerror=', 'onclick=',
                'onmouseover=', 'onfocus=', 'onblur=', 'eval(', 'alert('
            ]
            
            # Check URL parameters and POST data
            all_data = []
            if hasattr(request, 'GET') and request.GET:
                all_data.extend(request.GET.values())
            if hasattr(request, 'POST') and request.POST:
                all_data.extend(request.POST.values())
            
            for value in all_data:
                if isinstance(value, str):
                    for pattern in xss_patterns:
                        if pattern in value.lower():
                            return True
        except Exception as e:
            logger.error(f"Error checking XSS: {e}")
        return False
    
    def _is_unusual_request(self, request):
        """Check for unusual request patterns"""
        try:
            # Check for unusually long URLs
            if hasattr(request, 'path') and len(request.path) > 1000:
                return True
            
            # Check for too many parameters
            total_params = 0
            if hasattr(request, 'GET') and request.GET:
                total_params += len(request.GET)
            if hasattr(request, 'POST') and request.POST:
                total_params += len(request.POST)
            
            if total_params > 50:
                return True
            
            # Check for binary data in text fields
            if hasattr(request, 'POST') and request.POST:
                for value in request.POST.values():
                    if isinstance(value, str) and len(value) > 1000:
                        # Check for binary patterns
                        if sum(1 for c in value if ord(c) < 32 or ord(c) > 126) > len(value) * 0.3:
                            return True
        except Exception as e:
            logger.error(f"Error checking unusual request: {e}")
        
        return False