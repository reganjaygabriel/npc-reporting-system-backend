"""Custom permissions for signature operations"""
from rest_framework import permissions
from django.utils import timezone
from .models import SignatoryAuthorization, UserProfile


class IsAuthenticatedForSignature(permissions.BasePermission):
    """Require authentication for all signature operations"""
    
    message = "Authentication required for signature operations."
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class CanSignReports(permissions.BasePermission):
    """Permission to sign reports based on user role"""
    
    message = "You do not have permission to sign reports. Manager or Admin role required."
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Superusers always have permission
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        # Check user profile role
        try:
            profile = request.user.profile
            return profile.role in ['MANAGER', 'ADMIN']
        except UserProfile.DoesNotExist:
            return False


class CanSignAsSignatory(permissions.BasePermission):
    """Verify user is authorized to sign as specific signatory"""
    
    message = "You are not authorized to sign as this signatory."
    
    def has_permission(self, request, view):
        """Check if user has any signatory authorizations"""
        if not request.user.is_authenticated:
            return False
            
        # Superusers can sign as anyone
        if request.user.is_superuser:
            return True
            
        return True  # Basic check, detailed check in has_object_permission
    
    def has_object_permission(self, request, view, obj):
        """Check if user can sign as the specific signatory"""
        if not request.user.is_authenticated:
            return False
        
        # Superusers can sign as anyone
        if request.user.is_superuser:
            return True
        
        # Get signatory name from object or request data
        signatory_name = None
        if hasattr(obj, 'signatory_name'):
            signatory_name = obj.signatory_name
        elif request.data and 'signatory_name' in request.data:
            signatory_name = request.data['signatory_name']
        
        if not signatory_name:
            return False
        
        # Check if user has valid authorization
        try:
            auth = SignatoryAuthorization.objects.get(
                user=request.user,
                signatory_name=signatory_name,
                is_active=True
            )
            return auth.is_valid()
        except SignatoryAuthorization.DoesNotExist:
            return False


class IsSignatureOwner(permissions.BasePermission):
    """Only signature creator or admin can modify signature"""
    
    message = "You can only modify your own signatures."
    
    def has_object_permission(self, request, view, obj):
        # Read permissions allowed to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Superusers can modify any signature
        if request.user.is_superuser:
            return True
        
        # Check if user created this signature
        return obj.created_by == request.user


class CanManageSignatureAuthorizations(permissions.BasePermission):
    """Only admins can manage signatory authorizations"""
    
    message = "Only administrators can manage signatory authorizations."
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Superusers always have permission
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        # Check if user is admin
        try:
            profile = request.user.profile
            return profile.role == 'ADMIN'
        except UserProfile.DoesNotExist:
            return False


class CanManageUsers(permissions.BasePermission):
    """Only admins can manage users"""
    
    message = "Only administrators can manage users."
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Superusers always have permission
        if request.user.is_superuser or request.user.is_staff:
            return True
        
        # Check if user is admin
        try:
            profile = request.user.profile
            return profile.role == 'ADMIN'
        except UserProfile.DoesNotExist:
            return False


class RateLimitSignatures(permissions.BasePermission):
    """Rate limit signature operations"""
    
    message = "You have exceeded the maximum number of signatures allowed. Please try again later."
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Skip rate limiting for superusers
        if request.user.is_superuser:
            return True
        
        # Only rate limit creation/application actions
        if request.method not in ['POST', 'PUT', 'PATCH']:
            return True
        
        from .models import SignatureAuditLog, SignatureSecuritySettings
        from datetime import timedelta
        
        settings = SignatureSecuritySettings.get_settings()
        now = timezone.now()
        
        # Check hourly limit
        hour_ago = now - timedelta(hours=1)
        hourly_count = SignatureAuditLog.objects.filter(
            user=request.user,
            action__in=['CREATE', 'APPLY'],
            success=True,
            timestamp__gte=hour_ago
        ).count()
        
        if hourly_count >= settings.max_signatures_per_hour:
            return False
        
        # Check daily limit
        day_ago = now - timedelta(days=1)
        daily_count = SignatureAuditLog.objects.filter(
            user=request.user,
            action__in=['CREATE', 'APPLY'],
            success=True,
            timestamp__gte=day_ago
        ).count()
        
        if daily_count >= settings.max_signatures_per_day:
            return False
        
        return True
