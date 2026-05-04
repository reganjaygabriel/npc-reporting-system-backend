"""
Authentication Views
Handles user login, logout, registration, and profile management
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from .serializers import (
    UserSerializer, 
    UserRegistrationSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
    PasswordResetRequestSerializer
)
from .utils import get_location_from_ip, get_client_ip
from .audit_utils import (
    audit_login, audit_logout, AuditLogger, audit_action, AuditContext
)
from .models import AuditLog


class AuthViewSet(viewsets.ViewSet):
    """Authentication endpoints"""
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        """Login user with session authentication"""
        username = request.data.get('username')
        password = request.data.get('password')
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Attempt authentication
        user = authenticate(username=username, password=password)
        
        if user and user.is_active:
            # Login user with session
            login(request, user)
            
            # Get user profile data
            from .serializers import UserProfileSerializer
            user_data = UserProfileSerializer(user).data
            
            # Comprehensive audit logging for successful login
            audit_login(
                user=user,
                success=True,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Additional detailed logging
            AuditLogger.log_user_action(
                user=user,
                action='LOGIN',
                description=f'Successful login from {ip_address}',
                category='authentication',
                severity='LOW',
                request=request
            )
            
            return Response({
                'user': user_data,
                'message': 'Login successful'
            }, status=status.HTTP_200_OK)
        else:
            # Failed login attempt
            audit_login(
                user=None,
                success=False,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            # Log failed attempt with more details
            AuditLogger.log_security_event(
                user=None,
                action='LOGIN_FAILED',
                description=f'Failed login attempt for username: {username} from {ip_address}',
                severity='MEDIUM',
                request=request
            )
            
            return Response({
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        """Register a new user"""
        serializer = UserRegistrationSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            
            # Log user registration
            AuditLogger.log_user_action(
                user=user,
                action='USER_REGISTER',
                description=f'New user registered: {user.username}',
                model_name='User',
                object_id=user.id,
                category='user_management',
                severity='MEDIUM',
                request=request
            )
            
            return Response({
                'user': UserSerializer(user).data,
                'message': 'Registration successful'
            }, status=status.HTTP_201_CREATED)
        else:
            # Log failed registration
            AuditLogger.log_user_action(
                user=None,
                action='USER_REGISTER',
                description=f'Failed user registration attempt',
                category='user_management',
                severity='LOW',
                success=False,
                error_message=str(serializer.errors),
                request=request
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """Logout user by ending session"""
        try:
            ip_address = get_client_ip(request)
            
            # Comprehensive audit logging for logout
            audit_logout(
                user=request.user,
                ip_address=ip_address
            )
            
            # Additional detailed logging
            AuditLogger.log_user_action(
                user=request.user,
                action='LOGOUT',
                description=f'User logged out from {ip_address}',
                category='authentication',
                severity='LOW',
                request=request
            )
            
            # Logout user
            logout(request)
            
            return Response({
                'message': 'Successfully logged out'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            # Log failed logout attempt
            AuditLogger.log_user_action(
                user=request.user,
                action='LOGOUT',
                description=f'Failed logout attempt: {str(e)}',
                category='authentication',
                severity='MEDIUM',
                success=False,
                error_message=str(e),
                request=request
            )
            
            return Response({
                'error': 'Logout failed'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def profile(self, request):
        """Get current user profile"""
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put'], permission_classes=[IsAuthenticated])
    def update_profile(self, request):
        """Update user profile"""
        serializer = UserProfileSerializer(
            request.user, 
            data=request.data, 
            partial=True
        )
        
        if serializer.is_valid():
            user = serializer.save()
            
            # Log profile update
            AuditLogger.log_user_action(
                user=request.user,
                action='USER_UPDATE',
                description=f'Updated user profile for {user.username}',
                model_name='User',
                object_id=user.id,
                category='user_management',
                severity='LOW',
                request=request
            )
            
            return Response(serializer.data)
        else:
            # Log failed profile update
            AuditLogger.log_user_action(
                user=request.user,
                action='USER_UPDATE',
                description=f'Failed to update profile: {str(serializer.errors)}',
                category='user_management',
                severity='LOW',
                success=False,
                error_message=str(serializer.errors),
                request=request
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        """Change user password"""
        serializer = ChangePasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            user = request.user
            
            # Check old password
            if not user.check_password(serializer.data.get('old_password')):
                AuditLogger.log_security_event(
                    user=user,
                    action='PASSWORD_CHANGE_FAILED',
                    description=f'Password change failed: Incorrect old password for {user.username}',
                    severity='MEDIUM',
                    request=request
                )
                return Response({
                    'old_password': ['Wrong password']
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Set new password
            user.set_password(serializer.data.get('new_password'))
            user.save()
            
            # Log successful password change
            AuditLogger.log_security_event(
                user=user,
                action='PASSWORD_CHANGE',
                description=f'Password changed successfully for {user.username}',
                severity='HIGH',
                request=request
            )
            
            return Response({
                'message': 'Password updated successfully'
            }, status=status.HTTP_200_OK)
        else:
            # Log validation failure
            AuditLogger.log_user_action(
                user=request.user,
                action='PASSWORD_CHANGE_FAILED',
                description=f'Password change failed: Validation errors',
                category='authentication',
                severity='LOW',
                success=False,
                error_message=str(serializer.errors),
                request=request
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def password_reset_request(self, request):
        """Submit a password reset request"""
        serializer = PasswordResetRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            username = serializer.validated_data.get('username')
            reason = serializer.validated_data.get('reason', '')
            
            # Verify username exists
            from django.contrib.auth.models import User
            if not User.objects.filter(username=username).exists():
                AuditLogger.log_security_event(
                    user=None,
                    action='PASSWORD_RESET_REQUEST',
                    description=f'Password reset request failed: Username {username} not found',
                    severity='MEDIUM',
                    request=request
                )
                return Response({
                    'error': 'Username not found'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Get IP address
            ip_address = get_client_ip(request)
            
            # Create password reset request
            from .models import PasswordResetRequest
            reset_request = PasswordResetRequest.objects.create(
                username=username,
                reason=reason,
                ip_address=ip_address
            )
            
            # Log password reset request
            AuditLogger.log_security_event(
                user=None,
                action='PASSWORD_RESET_REQUEST',
                description=f'Password reset request submitted for {username}. Reason: {reason}',
                severity='MEDIUM',
                request=request
            )
            
            # Send email notification to admins
            try:
                from .email_service import send_password_reset_notification
                send_password_reset_notification(reset_request)
            except Exception as e:
                # Log error but don't fail the request
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to send password reset notification email: {str(e)}")
            
            return Response({
                'message': 'Password reset request submitted successfully. An administrator will contact you shortly.',
                'request_id': reset_request.id
            }, status=status.HTTP_201_CREATED)
        else:
            # Log validation failure
            AuditLogger.log_user_action(
                user=None,
                action='PASSWORD_RESET_REQUEST',
                description=f'Password reset request failed: Validation errors',
                category='authentication',
                severity='LOW',
                success=False,
                error_message=str(serializer.errors),
                request=request
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def pending_reset_count(self, request):
        """Get count of pending password reset requests (Admin only)"""
        # Check if user is admin
        if not (request.user.is_staff or 
                (hasattr(request.user, 'profile') and request.user.profile.role == 'ADMIN')):
            return Response({
                'count': 0
            }, status=status.HTTP_200_OK)
        
        from .models import PasswordResetRequest
        pending_count = PasswordResetRequest.objects.filter(status='PENDING').count()
        
        return Response({
            'count': pending_count
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def reset_user_password(self, request):
        """Reset a user's password (Admin only)"""
        # Check if user is admin
        if not (request.user.is_staff or 
                (hasattr(request.user, 'profile') and request.user.profile.role == 'ADMIN')):
            return Response({
                'error': 'Permission denied. Admin access required.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        username = request.data.get('username')
        new_password = request.data.get('new_password')
        request_id = request.data.get('request_id')
        
        if not username:
            return Response({
                'error': 'Username is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(username=username)
            
            # Generate random password if not provided
            if not new_password:
                import secrets
                import string
                alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
                new_password = ''.join(secrets.choice(alphabet) for i in range(12))
            
            # Reset password
            user.set_password(new_password)
            user.save()
            
            # Update password reset request if provided
            if request_id:
                from .models import PasswordResetRequest
                try:
                    reset_request = PasswordResetRequest.objects.get(id=request_id)
                    reset_request.status = 'COMPLETED'
                    reset_request.processed_by = request.user
                    from django.utils import timezone
                    reset_request.processed_at = timezone.now()
                    reset_request.admin_notes = f'Password reset by {request.user.username}'
                    reset_request.save()
                except PasswordResetRequest.DoesNotExist:
                    pass
            
            # Create audit log
            from .models import AuditLog
            ip_address = get_client_ip(request)
            location = get_location_from_ip(ip_address)
            
            AuditLog.objects.create(
                user=request.user,
                action='PASSWORD_RESET',
                model_name='User',
                object_id=user.id,
                description=f'Admin {request.user.username} reset password for user {username}',
                ip_address=ip_address,
                location=location
            )
            
            # Try to send email with new password
            email_sent = False
            if user.email:
                try:
                    from django.core.mail import send_mail
                    from django.conf import settings
                    
                    send_mail(
                        subject='Your Password Has Been Reset - GPD System',
                        message=f'''Hello {username},

Your password has been reset by an administrator.

Your new temporary password is: {new_password}

Please log in and change your password immediately for security.

Login at: {settings.FRONTEND_URL}/login

If you did not request this password reset, please contact IT support immediately at gpd.support@npc.gov.ph

Best regards,
GPD System Administration''',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        fail_silently=False,
                    )
                    email_sent = True
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to send password reset email: {str(e)}")
            
            return Response({
                'message': 'Password reset successfully',
                'username': username,
                'new_password': new_password,
                'email_sent': email_sent,
                'user_email': user.email if user.email else None
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)


class UserViewSet(viewsets.ModelViewSet):
    """User management endpoints (admin only)"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter users based on permissions"""
        user = self.request.user
        
        # Only admins can see all users
        if user.is_staff or (hasattr(user, 'profile') and user.profile.role == 'ADMIN'):
            return User.objects.all().select_related('profile')
        else:
            # Regular users can only see themselves
            return User.objects.filter(id=user.id).select_related('profile')
    
    def get_permissions(self):
        """Only admins can create, update, or delete users"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            from .permissions import CanManageUsers
            return [CanManageUsers()]
        return super().get_permissions()



class PasswordResetRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for managing password reset requests (Admin only)"""
    from .models import PasswordResetRequest
    queryset = PasswordResetRequest.objects.all()
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset based on query parameters"""
        queryset = super().get_queryset()
        
        # Only admins can view password reset requests
        if not (self.request.user.is_staff or 
                (hasattr(self.request.user, 'profile') and 
                 self.request.user.profile.role == 'ADMIN')):
            return queryset.none()
        
        # Filter by status
        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(status=status)
        
        # Search by username
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(username__icontains=search)
        
        return queryset.order_by('-created_at')
    
    def update(self, request, *args, **kwargs):
        """Update password reset request status"""
        instance = self.get_object()
        
        # Auto-set processed_by and processed_at when status changes
        if 'status' in request.data and request.data['status'] != instance.status:
            if request.data['status'] in ['APPROVED', 'REJECTED', 'COMPLETED']:
                if not instance.processed_by:
                    instance.processed_by = request.user
                if not instance.processed_at:
                    from django.utils import timezone
                    instance.processed_at = timezone.now()
                instance.save()
        
        return super().update(request, *args, **kwargs)
