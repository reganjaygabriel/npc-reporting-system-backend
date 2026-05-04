"""
Comprehensive audit logging utilities for the NPC Reporting System
"""

import time
import functools
import logging
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from .models import AuditLog

logger = logging.getLogger(__name__)

class AuditLogger:
    """
    Centralized audit logging utility
    """
    
    @staticmethod
    def log_user_action(user, action, description, category='user_action', **kwargs):
        """Log user-initiated actions"""
        return AuditLog.log_action(
            user=user,
            action=action,
            description=description,
            category=category,
            **kwargs
        )
    
    @staticmethod
    def log_system_action(action, description, category='system', **kwargs):
        """Log system-initiated actions"""
        return AuditLog.log_action(
            user=None,
            action=action,
            description=description,
            category=category,
            **kwargs
        )
    
    @staticmethod
    def log_security_event(user, action, description, severity='HIGH', category='security', **kwargs):
        """Log security-related events"""
        return AuditLog.log_action(
            user=user,
            action=action,
            description=description,
            category=category,
            severity=severity,
            **kwargs
        )
    
    @staticmethod
    def log_data_access(user, model_name, object_id, action='DATA_VIEW', description='', **kwargs):
        """Log data access events"""
        if not description:
            description = f'Accessed {model_name} with ID {object_id}'
        
        return AuditLog.log_action(
            user=user,
            action=action,
            description=description,
            model_name=model_name,
            object_id=object_id,
            category='data_access',
            **kwargs
        )
    
    @staticmethod
    def log_file_operation(user, action, filename, description='', category='file_operation', **kwargs):
        """Log file operations"""
        if not description:
            description = f'File operation: {action} on {filename}'
        
        return AuditLog.log_action(
            user=user,
            action=action,
            description=description,
            category=category,
            **kwargs
        )
    
    @staticmethod
    def log_authentication(user, action, success=True, ip_address=None, user_agent='', category='authentication', **kwargs):
        """Log authentication events"""
        severity = 'LOW' if success else 'MEDIUM'
        
        return AuditLog.log_action(
            user=user,
            action=action,
            description=f'Authentication attempt: {action}',
            category=category,
            severity=severity,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent,
            **kwargs
        )
    
    @staticmethod
    def log_report_operation(user, action, report_info, category='reporting', **kwargs):
        """Log report-related operations"""
        description = f'Report operation: {action}'
        if isinstance(report_info, dict):
            if 'date' in report_info:
                description += f' for date {report_info["date"]}'
            if 'type' in report_info:
                description += f' (type: {report_info["type"]})'
        
        return AuditLog.log_action(
            user=user,
            action=action,
            description=description,
            category=category,
            **kwargs
        )
    
    @staticmethod
    def log_signature_operation(user, action, signatory_name, category='e_signature', **kwargs):
        """Log e-signature operations"""
        description = f'E-signature operation: {action} for {signatory_name}'
        
        return AuditLog.log_action(
            user=user,
            action=action,
            description=description,
            category=category,
            **kwargs
        )


def audit_action(action, description='', category='', severity='LOW', log_args=False, log_result=False):
    """
    Decorator to automatically audit function calls
    
    Usage:
    @audit_action('DATA_CREATE', 'Creating new record', category='data')
    def create_record(user, data):
        # function implementation
        pass
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            user = None
            request = None
            success = True
            error_message = ''
            result = None
            
            # Try to extract user and request from arguments
            for arg in args:
                if hasattr(arg, 'user') and not isinstance(arg.user, AnonymousUser):
                    user = arg.user
                    request = arg
                    break
                elif hasattr(arg, 'username'):  # Direct user object
                    user = arg
                    break
            
            # Try to extract user from kwargs
            if not user and 'user' in kwargs:
                user = kwargs['user']
            if not request and 'request' in kwargs:
                request = kwargs['request']
            
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                success = False
                error_message = str(e)
                raise
            finally:
                duration_ms = int((time.time() - start_time) * 1000)
                
                # Build audit description
                audit_description = description or f'Function {func.__name__} executed'
                
                if log_args and args:
                    audit_description += f' with args: {str(args)[:200]}'
                
                if log_result and result and success:
                    audit_description += f' result: {str(result)[:200]}'
                
                # Log the action
                try:
                    AuditLog.log_action(
                        user=user,
                        action=action,
                        description=audit_description,
                        category=category or 'function_call',
                        severity=severity,
                        success=success,
                        error_message=error_message,
                        duration_ms=duration_ms,
                        request=request
                    )
                except Exception as audit_error:
                    logger.error(f"Failed to log audit for {func.__name__}: {audit_error}")
            
            return result
        return wrapper
    return decorator


def audit_model_changes(model_class):
    """
    Class decorator to automatically audit model changes
    
    Usage:
    @audit_model_changes
    class MyModel(models.Model):
        # model definition
        pass
    """
    original_save = model_class.save
    original_delete = model_class.delete
    
    def audited_save(self, *args, **kwargs):
        is_new = self.pk is None
        action = 'DATA_CREATE' if is_new else 'DATA_UPDATE'
        
        # Get user from kwargs if available
        user = kwargs.pop('audit_user', None)
        
        result = original_save(self, *args, **kwargs)
        
        # Log the action
        try:
            AuditLog.log_action(
                user=user,
                action=action,
                description=f'{action.replace("_", " ").title()}: {model_class.__name__} {self.pk}',
                model_name=model_class.__name__,
                object_id=self.pk,
                category='data_modification',
                severity='LOW' if action == 'DATA_UPDATE' else 'MEDIUM'
            )
        except Exception as e:
            logger.error(f"Failed to audit {action} for {model_class.__name__}: {e}")
        
        return result
    
    def audited_delete(self, *args, **kwargs):
        # Get user from kwargs if available
        user = kwargs.pop('audit_user', None)
        object_id = self.pk
        
        result = original_delete(self, *args, **kwargs)
        
        # Log the action
        try:
            AuditLog.log_action(
                user=user,
                action='DATA_DELETE',
                description=f'Deleted: {model_class.__name__} {object_id}',
                model_name=model_class.__name__,
                object_id=object_id,
                category='data_modification',
                severity='HIGH'
            )
        except Exception as e:
            logger.error(f"Failed to audit DELETE for {model_class.__name__}: {e}")
        
        return result
    
    model_class.save = audited_save
    model_class.delete = audited_delete
    
    return model_class


class AuditContext:
    """
    Context manager for grouping related audit events
    """
    
    def __init__(self, user, operation, description=''):
        self.user = user
        self.operation = operation
        self.description = description
        self.start_time = None
        self.events = []
    
    def __enter__(self):
        self.start_time = time.time()
        AuditLogger.log_user_action(
            self.user,
            'OPERATION_START',
            f'Started operation: {self.operation}. {self.description}',
            severity='LOW'
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = int((time.time() - self.start_time) * 1000)
        success = exc_type is None
        
        if success:
            AuditLogger.log_user_action(
                self.user,
                'OPERATION_COMPLETE',
                f'Completed operation: {self.operation}. Duration: {duration_ms}ms',
                severity='LOW',
                duration_ms=duration_ms
            )
        else:
            AuditLogger.log_user_action(
                self.user,
                'OPERATION_FAILED',
                f'Failed operation: {self.operation}. Error: {str(exc_val)}',
                severity='MEDIUM',
                success=False,
                error_message=str(exc_val),
                duration_ms=duration_ms
            )
    
    def log_event(self, action, description, **kwargs):
        """Log an event within this operation context"""
        AuditLogger.log_user_action(
            self.user,
            action,
            f'[{self.operation}] {description}',
            **kwargs
        )


# Convenience functions for common audit scenarios
def audit_login(user, success=True, ip_address=None, user_agent=''):
    """Audit login attempts"""
    action = 'LOGIN' if success else 'LOGIN_FAILED'
    return AuditLogger.log_authentication(
        user=user if success else None,
        action=action,
        success=success,
        ip_address=ip_address,
        user_agent=user_agent
    )

def audit_logout(user, ip_address=None):
    """Audit logout events"""
    return AuditLogger.log_authentication(
        user=user,
        action='LOGOUT',
        success=True,
        ip_address=ip_address
    )

def audit_file_upload(user, filename, file_size=None, **kwargs):
    """Audit file uploads"""
    description = f'Uploaded file: {filename}'
    if file_size:
        description += f' (size: {file_size} bytes)'
    
    return AuditLogger.log_file_operation(
        user=user,
        action='FILE_UPLOAD',
        filename=filename,
        description=description,
        **kwargs
    )

def audit_report_generation(user, report_date, report_type='PSR', **kwargs):
    """Audit report generation"""
    return AuditLogger.log_report_operation(
        user=user,
        action='REPORT_GENERATE',
        report_info={'date': report_date, 'type': report_type},
        **kwargs
    )

def audit_signature_creation(user, signatory_name, **kwargs):
    """Audit e-signature creation"""
    return AuditLogger.log_signature_operation(
        user=user,
        action='SIGNATURE_CREATE',
        signatory_name=signatory_name,
        **kwargs
    )

def audit_authorization_request(user, signatory_name, role, **kwargs):
    """Audit authorization requests"""
    description = f'Authorization request for {signatory_name} as {role}'
    return AuditLogger.log_user_action(
        user=user,
        action='AUTH_REQUEST_CREATE',
        description=description,
        category='authorization',
        **kwargs
    )

def audit_data_export(user, data_type, record_count=None, **kwargs):
    """Audit data exports"""
    description = f'Exported {data_type} data'
    if record_count:
        description += f' ({record_count} records)'
    
    return AuditLogger.log_user_action(
        user=user,
        action='DATA_EXPORT',
        description=description,
        category='data_access',
        severity='MEDIUM',
        **kwargs
    )