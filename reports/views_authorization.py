"""Views for user-friendly signatory authorization requests"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from .models import SignatoryAuthorization, SignatoryAuthorizationRequest, AuditLog
from .serializers_security import SignatoryAuthorizationSerializer
from .permissions import CanManageSignatureAuthorizations
from .audit_utils import audit_action


class SignatoryAuthorizationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing signatory authorizations with user-friendly requests"""
    queryset = SignatoryAuthorization.objects.all()
    serializer_class = SignatoryAuthorizationSerializer
    permission_classes = [IsAuthenticated]
    
    def dispatch(self, request, *args, **kwargs):
        """Override dispatch to log all requests"""
        with open('debug_log.txt', 'a', encoding='utf-8') as f:
            f.write(f"DISPATCH METHOD CALLED! Time: {timezone.now()}\n")
            f.write(f"Request method: {request.method}\n")
            f.write(f"Request path: {request.path}\n")
            f.write(f"Args: {args}\n")
            f.write(f"Kwargs: {kwargs}\n")
            f.write("=" * 50 + "\n")
        
        print("DISPATCH METHOD CALLED!")
        print(f"Request method: {request.method}")
        print(f"Request path: {request.path}")
        print(f"Args: {args}")
        print(f"Kwargs: {kwargs}")
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        """Filter based on user permissions"""
        if self.request.user.is_superuser:
            return self.queryset
        
        # Regular users can only see their own authorizations
        return self.queryset.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Override create method - this should not be called for authorization requests"""
        # This method should only be called for creating actual SignatoryAuthorization objects
        # Authorization requests should go through the request_authorization action
        return Response(
            {'error': 'Use /request/ endpoint for authorization requests'},
            status=status.HTTP_400_BAD_REQUEST
        )

    
    @action(detail=False, methods=['get'], url_path='my-authorizations')
    def my_authorizations(self, request):
        """Get current user's authorizations"""
        # TEST: Add a simple debug message to see if code changes are picked up
        print("MY_AUTHORIZATIONS METHOD CALLED - CODE CHANGES ARE WORKING!")
        
        authorizations = SignatoryAuthorization.objects.filter(
            user=request.user
        ).order_by('-authorization_date')
        
        serializer = self.get_serializer(authorizations, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='my-requests')
    def my_requests(self, request):
        """Get current user's authorization requests"""
        from .serializers_security import SignatoryAuthorizationRequestSerializer
        
        requests = SignatoryAuthorizationRequest.objects.filter(
            user=request.user
        ).order_by('-created_at')
        
        serializer = SignatoryAuthorizationRequestSerializer(requests, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], url_path='request')
    @audit_action('AUTH_REQUEST_CREATE', 'Authorization request submission', category='authorization', severity='MEDIUM')
    def request_authorization(self, request):
        """Submit a new authorization request"""
        # IMMEDIATE file write to confirm method is called
        try:
            with open('method_called.txt', 'w', encoding='utf-8') as f:
                f.write(f"METHOD CALLED AT {timezone.now()}\n")
                f.write(f"User: {request.user}\n")
                f.write(f"Data: {request.data}\n")
        except:
            pass
        
        # Write to debug file
        with open('debug_log.txt', 'a', encoding='utf-8') as f:
            f.write(f"🔥 REQUEST_AUTHORIZATION METHOD CALLED! Time: {timezone.now()}\n")
            f.write(f"Request data: {request.data}\n")
            f.write("=" * 50 + "\n")
        
        print("🔥 REQUEST_AUTHORIZATION METHOD CALLED!")
        print(f"Request data: {request.data}")
        
        from .serializers_security import SignatoryAuthorizationRequestSerializer
        
        data = request.data.copy()
        signatory_name = data.get('signatory_name')
        role = data.get('role')
        
        # Check if user already has this authorization
        existing_auth = SignatoryAuthorization.objects.filter(
            user=request.user,
            signatory_name=signatory_name,
            is_active=True
        ).first()
        
        if existing_auth and existing_auth.is_valid():
            AuditLogger.log_user_action(
                user=request.user,
                action='AUTH_REQUEST_CREATE',
                description=f'Authorization request rejected: User already has active authorization for {signatory_name}',
                category='authorization',
                severity='LOW',
                success=False,
                error_message='Already authorized',
                request=request
            )
            return Response(
                {'error': 'You already have active authorization for this signatory'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = SignatoryAuthorizationRequestSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            print("🔥 Serializer is valid, creating auth request...")
            with open('debug_log.txt', 'a', encoding='utf-8') as f:
                f.write("🔥 Serializer is valid, creating auth request...\n")
            
            auth_request = serializer.save(user=request.user)
            print(f"🔥 Auth request created: ID={auth_request.id}, Status={auth_request.status}")
            with open('debug_log.txt', 'a', encoding='utf-8') as f:
                f.write(f"🔥 Auth request created: ID={auth_request.id}, Status={auth_request.status}\n")
            
            # Log authorization request creation
            audit_authorization_request(
                user=request.user,
                signatory_name=signatory_name,
                role=role,
                request=request
            )
            
            AuditLogger.log_user_action(
                user=request.user,
                action='AUTH_REQUEST_CREATE',
                description=f'Created authorization request for {signatory_name} as {role}',
                model_name='SignatoryAuthorizationRequest',
                object_id=auth_request.id,
                category='authorization',
                severity='MEDIUM',
                request=request
            )
            
            # Send notification to admins
            try:
                print("🔥 Sending admin notification...")
                with open('debug_log.txt', 'a', encoding='utf-8') as f:
                    f.write("🔥 Sending admin notification...\n")
                self._notify_admins_of_request(auth_request)
                print("🔥 Admin notification sent successfully")
                with open('debug_log.txt', 'a', encoding='utf-8') as f:
                    f.write("🔥 Admin notification sent successfully\n")
            except Exception as e:
                print(f"🔥 Failed to send admin notification: {e}")
                with open('debug_log.txt', 'a', encoding='utf-8') as f:
                    f.write(f"🔥 Failed to send admin notification: {e}\n")
                import traceback
                traceback.print_exc()
            
            # Send confirmation email to user with auto-approval and signature setup link
            try:
                print("🔥 Sending confirmation email with auto-approval...")
                with open('debug_log.txt', 'a', encoding='utf-8') as f:
                    f.write("🔥 Sending confirmation email with auto-approval...\n")
                self._send_confirmation_email(auth_request)
                print("🔥 Confirmation email sent successfully")
                with open('debug_log.txt', 'a', encoding='utf-8') as f:
                    f.write("🔥 Confirmation email sent successfully\n")
            except Exception as e:
                print(f"🔥 Failed to send confirmation email: {e}")
                with open('debug_log.txt', 'a', encoding='utf-8') as f:
                    f.write(f"🔥 Failed to send confirmation email: {e}\n")
                import traceback
                traceback.print_exc()
            
            # Refresh the auth_request to get updated status
            auth_request.refresh_from_db()
            print(f"🔥 Final auth request status: {auth_request.status}")
            with open('debug_log.txt', 'a', encoding='utf-8') as f:
                f.write(f"🔥 Final auth request status: {auth_request.status}\n")
                f.write("=" * 50 + "\n")
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            print(f"🔥 Serializer errors: {serializer.errors}")
            with open('debug_log.txt', 'a', encoding='utf-8') as f:
                f.write(f"🔥 Serializer errors: {serializer.errors}\n")
            
            # Log validation failure
            AuditLogger.log_user_action(
                user=request.user,
                action='AUTH_REQUEST_CREATE',
                description=f'Authorization request failed for {signatory_name}: Validation errors',
                category='authorization',
                severity='LOW',
                success=False,
                error_message=str(serializer.errors),
                request=request
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='pending-requests', 
            permission_classes=[IsAuthenticated, CanManageSignatureAuthorizations])
    def pending_requests(self, request):
        """Get all pending authorization requests (admin only)"""
        from .serializers_security import SignatoryAuthorizationRequestSerializer
        
        requests = SignatoryAuthorizationRequest.objects.filter(
            status='PENDING'
        ).order_by('-created_at')
        
        serializer = SignatoryAuthorizationRequestSerializer(requests, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], url_path='approve-request/(?P<request_id>[^/.]+)',
            permission_classes=[IsAuthenticated, CanManageSignatureAuthorizations])
    def approve_request(self, request, request_id=None):
        """Approve an authorization request (admin only)"""
        try:
            auth_request = SignatoryAuthorizationRequest.objects.get(
                id=request_id,
                status='PENDING'
            )
        except SignatoryAuthorizationRequest.DoesNotExist:
            AuditLogger.log_user_action(
                user=request.user,
                action='AUTH_REQUEST_APPROVE',
                description=f'Failed to approve authorization request: Request {request_id} not found or already processed',
                category='authorization',
                severity='LOW',
                success=False,
                error_message='Request not found',
                request=request
            )
            return Response(
                {'error': 'Request not found or already processed'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        admin_notes = request.data.get('admin_notes', '')
        requires_2fa = request.data.get('requires_2fa', True)
        expiry_date = request.data.get('expiry_date')
        
        # Set expiry date if provided
        if expiry_date:
            from datetime import datetime
            auth_request.expiry_date = datetime.fromisoformat(expiry_date.replace('Z', '+00:00'))
        
        auth_request.requires_2fa = requires_2fa
        
        # Approve the request
        authorization = auth_request.approve(request.user, admin_notes)
        
        # Log authorization approval
        AuditLogger.log_user_action(
            user=request.user,
            action='AUTH_REQUEST_APPROVE',
            description=f'Approved authorization request for {auth_request.signatory_name} by {auth_request.user.username}',
            model_name='SignatoryAuthorizationRequest',
            object_id=auth_request.id,
            category='authorization',
            severity='HIGH',
            request=request
        )
        
        # Send notification to user
        self._notify_user_of_approval(auth_request, authorization)
        
        # Return the created authorization
        serializer = self.get_serializer(authorization)
        return Response({
            'message': 'Request approved successfully',
            'authorization': serializer.data
        })
    
    @action(detail=False, methods=['post'], url_path='reject-request/(?P<request_id>[^/.]+)',
            permission_classes=[IsAuthenticated, CanManageSignatureAuthorizations])
    def reject_request(self, request, request_id=None):
        """Reject an authorization request (admin only)"""
        try:
            auth_request = SignatoryAuthorizationRequest.objects.get(
                id=request_id,
                status='PENDING'
            )
        except SignatoryAuthorizationRequest.DoesNotExist:
            AuditLogger.log_user_action(
                user=request.user,
                action='AUTH_REQUEST_REJECT',
                description=f'Failed to reject authorization request: Request {request_id} not found or already processed',
                category='authorization',
                severity='LOW',
                success=False,
                error_message='Request not found',
                request=request
            )
            return Response(
                {'error': 'Request not found or already processed'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        admin_notes = request.data.get('admin_notes', 'Request rejected by administrator')
        
        # Reject the request
        auth_request.reject(request.user, admin_notes)
        
        # Log authorization rejection
        AuditLogger.log_user_action(
            user=request.user,
            action='AUTH_REQUEST_REJECT',
            description=f'Rejected authorization request for {auth_request.signatory_name} by {auth_request.user.username}. Reason: {admin_notes}',
            model_name='SignatoryAuthorizationRequest',
            object_id=auth_request.id,
            category='authorization',
            severity='MEDIUM',
            request=request
        )
        
        # Send notification to user
        self._notify_user_of_rejection(auth_request)
        
        return Response({'message': 'Request rejected successfully'})
    
    @action(detail=False, methods=['post'], url_path='cancel-request/(?P<request_id>[^/.]+)')
    def cancel_request(self, request, request_id=None):
        """Cancel an authorization request (user can cancel their own requests)"""
        try:
            auth_request = SignatoryAuthorizationRequest.objects.get(
                id=request_id,
                status='PENDING'
            )
        except SignatoryAuthorizationRequest.DoesNotExist:
            AuditLogger.log_user_action(
                user=request.user,
                action='AUTH_REQUEST_CANCEL',
                description=f'Failed to cancel authorization request: Request {request_id} not found or already processed',
                category='authorization',
                severity='LOW',
                success=False,
                error_message='Request not found',
                request=request
            )
            return Response(
                {'error': 'Request not found or already processed'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user can cancel this request
        if auth_request.user != request.user and not request.user.is_staff:
            AuditLogger.log_user_action(
                user=request.user,
                action='AUTH_REQUEST_CANCEL',
                description=f'Unauthorized attempt to cancel authorization request {request_id} for {auth_request.signatory_name}',
                category='authorization',
                severity='MEDIUM',
                success=False,
                error_message='Permission denied',
                request=request
            )
            return Response(
                {'error': 'You can only cancel your own requests'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update request status to cancelled
        auth_request.status = 'CANCELLED'
        auth_request.reviewed_by = request.user
        auth_request.reviewed_at = timezone.now()
        auth_request.admin_notes = 'Request cancelled by user'
        auth_request.save()
        
        # Log authorization cancellation
        AuditLogger.log_user_action(
            user=request.user,
            action='AUTH_REQUEST_CANCEL',
            description=f'Cancelled authorization request for {auth_request.signatory_name}',
            model_name='SignatoryAuthorizationRequest',
            object_id=auth_request.id,
            category='authorization',
            severity='LOW',
            request=request
        )
        
        return Response({'message': 'Request cancelled successfully'})
    
    @action(detail=True, methods=['delete'], url_path='delete-authorization')
    def delete_authorization(self, request, pk=None):
        """Delete an authorization (for testing purposes)"""
        try:
            authorization = SignatoryAuthorization.objects.get(
                id=pk,
                user=request.user
            )
        except SignatoryAuthorization.DoesNotExist:
            AuditLogger.log_user_action(
                user=request.user,
                action='AUTH_DELETE',
                description=f'Failed to delete authorization: Authorization {pk} not found or permission denied',
                category='authorization',
                severity='LOW',
                success=False,
                error_message='Authorization not found',
                request=request
            )
            return Response(
                {'error': 'Authorization not found or you do not have permission to delete it'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Store signatory name for response and logging
        signatory_name = authorization.signatory_name
        
        # Delete the authorization
        authorization.delete()
        
        # Log authorization deletion
        AuditLogger.log_user_action(
            user=request.user,
            action='AUTH_DELETE',
            description=f'Deleted authorization for {signatory_name}',
            model_name='SignatoryAuthorization',
            object_id=pk,
            category='authorization',
            severity='HIGH',
            request=request
        )
        
        return Response({
            'message': f'Authorization for {signatory_name} deleted successfully'
        })
    
    @action(detail=False, methods=['delete'], url_path='delete-authorization/(?P<auth_id>[^/.]+)')
    def delete_authorization_by_id(self, request, auth_id=None):
        """Delete an authorization by ID (alternative endpoint)"""
        try:
            authorization = SignatoryAuthorization.objects.get(
                id=auth_id,
                user=request.user
            )
        except SignatoryAuthorization.DoesNotExist:
            return Response(
                {'error': 'Authorization not found or you do not have permission to delete it'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Store signatory name for response
        signatory_name = authorization.signatory_name
        
        # Delete the authorization
        authorization.delete()
        
        return Response({
            'message': f'Authorization for {signatory_name} deleted successfully'
        })
    
    @action(detail=False, methods=['get'], url_path='signature-setup/(?P<token>[^/.]+)', permission_classes=[])
    def signature_setup(self, request, token=None):
        """Handle signature setup via secure token - NO AUTHENTICATION REQUIRED"""
        try:
            authorization = SignatoryAuthorization.objects.get(
                setup_token=token,
                is_active=True
            )
            
            if not authorization.is_setup_token_valid():
                return Response(
                    {'error': 'Setup link has expired. Please contact your administrator.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Return authorization details for signature setup
            return Response({
                'signatory_name': authorization.signatory_name,
                'user_name': authorization.user.get_full_name() or authorization.user.username,
                'requires_2fa': authorization.requires_2fa,
                'token': token
            })
            
        except SignatoryAuthorization.DoesNotExist:
            return Response(
                {'error': 'Invalid setup link. Please contact your administrator.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            # Log the actual error for debugging
            print(f"❌ Signature setup error: {e}")
            import traceback
            traceback.print_exc()
            return Response(
                {'error': 'An error occurred while setting up your signature. Please contact your administrator.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], url_path='save-signature/(?P<token>[^/.]+)', permission_classes=[])
    def save_signature(self, request, token=None):
        """Save signature via secure token - NO AUTHENTICATION REQUIRED"""
        try:
            authorization = SignatoryAuthorization.objects.get(
                setup_token=token,
                is_active=True
            )
            
            if not authorization.is_setup_token_valid():
                AuditLogger.log_security_event(
                    user=None,
                    action='SIGNATURE_SETUP_FAILED',
                    description=f'Signature setup failed: Expired token for {authorization.signatory_name}',
                    severity='MEDIUM',
                    request=request
                )
                return Response(
                    {'error': 'Setup link has expired. Please contact your administrator.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            signature_data = request.data.get('signature')
            if not signature_data:
                AuditLogger.log_security_event(
                    user=authorization.user,
                    action='SIGNATURE_SETUP_FAILED',
                    description=f'Signature setup failed: No signature data provided for {authorization.signatory_name}',
                    severity='LOW',
                    request=request
                )
                return Response(
                    {'error': 'Signature data is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Save signature to admin_signatures folder
            import base64
            import os
            from django.conf import settings
            
            # Decode base64 signature
            format, imgstr = signature_data.split(';base64,')
            ext = format.split('/')[-1]
            
            # Create filename
            filename = f"{authorization.signatory_name.lower().replace(' ', '_').replace('.', '_')}_signature.{ext}"
            
            # Save to admin_signatures folder
            admin_signatures_dir = os.path.join(settings.MEDIA_ROOT, 'admin_signatures')
            os.makedirs(admin_signatures_dir, exist_ok=True)
            
            file_path = os.path.join(admin_signatures_dir, filename)
            with open(file_path, 'wb') as f:
                f.write(base64.b64decode(imgstr))
            
            # Update authorization
            authorization.signature_created = True
            authorization.setup_token = None  # Invalidate token after use
            authorization.token_expires = None
            authorization.save()
            
            # Log successful signature setup
            AuditLogger.log_user_action(
                user=authorization.user,
                action='SIGNATURE_SETUP_COMPLETE',
                description=f'Successfully set up e-signature for {authorization.signatory_name}',
                model_name='SignatoryAuthorization',
                object_id=authorization.id,
                category='e_signature',
                severity='HIGH',
                request=request
            )
            
            return Response({
                'message': 'Signature saved successfully! You can now use your e-signature to sign reports.',
                'signature_file': filename
            })
            
        except SignatoryAuthorization.DoesNotExist:
            AuditLogger.log_security_event(
                user=None,
                action='SIGNATURE_SETUP_FAILED',
                description=f'Signature setup failed: Invalid token {token[:8]}...',
                severity='HIGH',
                request=request
            )
            return Response(
                {'error': 'Invalid setup link. Please contact your administrator.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            # Log the actual error for debugging
            print(f"❌ Save signature error: {e}")
            import traceback
            traceback.print_exc()
            
            AuditLogger.log_user_action(
                user=authorization.user if 'authorization' in locals() else None,
                action='SIGNATURE_SETUP_FAILED',
                description=f'Signature setup failed: {str(e)}',
                category='e_signature',
                severity='HIGH',
                success=False,
                error_message=str(e),
                request=request
            )
            
            return Response(
                {'error': f'Failed to save signature: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _notify_admins_of_request(self, auth_request):
        """Send email notification to admins about new request"""
        try:
            from django.contrib.auth.models import User
            
            # Get all admin users
            admin_users = User.objects.filter(
                is_staff=True,
                is_active=True,
                email__isnull=False
            ).exclude(email='')
            
            admin_emails = [user.email for user in admin_users]
            
            if not admin_emails:
                print("Warning: No admin emails found for notification")
                return
            
            subject = f'New E-Signature Authorization Request - {auth_request.signatory_name}'
            message = f"""
Dear Data Manager/System Administrator,

A new e-signature authorization request has been submitted and requires your review:

Requestor Information:
- Name: {auth_request.user.get_full_name() or auth_request.user.username}
- Email: {auth_request.email}
- Requested Signatory Name: {auth_request.signatory_name}
- Role: {auth_request.role}

Justification for E-Signature Access:
{auth_request.justification}

Action Required:
Please review and approve/reject this e-signature authorization request in the admin panel:
{settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8000'}/admin/reports/signatoryauthorizationrequest/

Best regards,
NPC Reporting System
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@npc-reporting.com',
                admin_emails,
                fail_silently=True,
            )
            print(f"Admin notification sent to {len(admin_emails)} administrators")
        except Exception as e:
            print(f"Failed to send admin notification: {e}")
    
    def _send_confirmation_email(self, auth_request):
        """Send confirmation email to user that request was received"""
        try:
            print("🔥 Starting _send_confirmation_email method...")
            
            # Check if authorization already exists
            existing_auth = SignatoryAuthorization.objects.filter(
                user=auth_request.user,
                signatory_name=auth_request.signatory_name,
                is_active=True
            ).first()
            
            if existing_auth:
                print(f"🔥 Authorization already exists for {auth_request.signatory_name}")
                return
            
            recipient_email = auth_request.email or auth_request.user.email
            if not recipient_email:
                print("🔥 No recipient email found")
                return
            
            print(f"🔥 Recipient email: {recipient_email}")
            
            # Generate secure token for immediate signature setup
            import secrets
            setup_token = secrets.token_urlsafe(32)
            print(f"🔥 Generated setup token: {setup_token[:20]}...")
            
            # Create authorization immediately (auto-approve) - SAME AS MANAGEMENT COMMAND
            authorization = SignatoryAuthorization.objects.create(
                user=auth_request.user,
                signatory_name=auth_request.signatory_name,
                authorized_by=auth_request.user,  # Self-authorized
                is_active=True,
                requires_2fa=True,
                notes='Auto-approved via email link',
                setup_token=setup_token,
                token_expires=timezone.now() + timezone.timedelta(hours=24),
                signature_created=False
            )
            print(f"🔥 Authorization created: ID={authorization.id}")
            
            # Update request status to approved - SAME AS MANAGEMENT COMMAND
            auth_request.status = 'APPROVED'
            auth_request.reviewed_by = auth_request.user
            auth_request.reviewed_at = timezone.now()
            auth_request.admin_notes = 'Auto-approved via email signature setup'
            auth_request.save()
            print(f"🔥 Request status updated to: {auth_request.status}")
            
            # Extract last name from signatory name for professional greeting
            signatory_parts = auth_request.signatory_name.split()
            if len(signatory_parts) > 1:
                # Get the last part before any suffix (JR., SR., etc.)
                last_name = signatory_parts[-1]
                if last_name.upper() in ['JR.', 'JR', 'SR.', 'SR', 'III', 'II']:
                    last_name = signatory_parts[-2] if len(signatory_parts) > 2 else signatory_parts[0]
                greeting = f"Dear {last_name},"
            else:
                greeting = f"Dear {auth_request.signatory_name},"
            
            setup_url = f"{getattr(settings, 'SITE_URL', 'http://localhost:8081')}/signature-setup/{setup_token}"
            print(f"🔥 Setup URL: {setup_url}")
            
            subject = f'E-Signature Required - {auth_request.signatory_name}'
            message = f"""
{greeting}

The NPC Reporting System requires your e-signature for the following:

Signatory Name: {auth_request.signatory_name}
Role: {auth_request.role}

Reason for E-Signature Request:
{auth_request.justification}

🖊️ CREATE YOUR E-SIGNATURE NOW:
Click this secure link to create your digital signature:
{setup_url}

This link is valid for 24 hours and can only be used once for security.

After clicking the link, you will:
1. Be taken to a secure signature drawing pad
2. Draw your signature using your mouse or touch screen
3. Click "Save Signature" to submit it to the system
4. Your e-signature will be immediately available for signing reports

Best regards,
NPC Reporting System
            """
            
            print("🔥 Sending email...")
            send_mail(
                subject,
                message,
                getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@npc-reporting.com'),
                [recipient_email],
                fail_silently=False,  # Don't fail silently so we can see errors
            )
            print(f"🔥 Confirmation email sent to {recipient_email}")
            
        except Exception as e:
            print(f"🔥 Failed to send confirmation email: {e}")
            import traceback
            traceback.print_exc()
    
    def _notify_user_of_approval(self, auth_request, authorization):
        """Send email notification to user about approval"""
        try:
            # Use email from request, fallback to user.email
            recipient_email = auth_request.email or auth_request.user.email
            if not recipient_email:
                return
            
            # Generate secure token for signature setup
            import secrets
            setup_token = secrets.token_urlsafe(32)
            
            # Store token in authorization for verification
            authorization.setup_token = setup_token
            authorization.token_expires = timezone.now() + timezone.timedelta(hours=24)
            authorization.save()
            
            # Extract last name for greeting
            signatory_parts = auth_request.signatory_name.split()
            if len(signatory_parts) > 1:
                last_name = signatory_parts[-1]
                if last_name.upper() in ['JR.', 'JR', 'SR.', 'SR', 'III', 'II']:
                    last_name = signatory_parts[-2] if len(signatory_parts) > 2 else signatory_parts[0]
                greeting = f"Dear {last_name},"
            else:
                greeting = f"Dear {auth_request.signatory_name},"
            
            setup_url = f"{settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'http://localhost:8081'}/signature-setup/{setup_token}"
            
            subject = f'E-Signature Authorization APPROVED - {auth_request.signatory_name}'
            message = f"""
{greeting}

Great news! Your e-signature authorization has been APPROVED!

E-Signature Authorization Details:
- Signatory Name: {auth_request.signatory_name}
- Role: {auth_request.role}
- 2FA Security Required: {'Yes' if authorization.requires_2fa else 'No'}
- Authorization Expires: {authorization.expiry_date.strftime('%B %d, %Y') if authorization.expiry_date else 'Never'}

Your Original Justification:
{auth_request.justification}

🖊️ SET UP YOUR E-SIGNATURE NOW:
Click this secure link to create your digital signature:
{setup_url}

This link is valid for 24 hours and can only be used once for security.

After clicking the link, you will:
1. Be taken to a secure signature drawing pad
2. Draw your signature using your mouse or touch screen
3. Click "Save Signature" to submit it to the system
4. Your e-signature will be immediately available for signing reports

Data Manager/System Administrator Notes: {auth_request.admin_notes}

Your e-signature is now ready for use in the NPC Reporting System!

Best regards,
NPC Reporting System
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@npc-reporting.com',
                [recipient_email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Failed to send user approval notification: {e}")
    
    def _notify_user_of_rejection(self, auth_request):
        """Send email notification to user about rejection"""
        try:
            # Use email from request, fallback to user.email
            recipient_email = auth_request.email or auth_request.user.email
            if not recipient_email:
                return
            
            subject = f'E-Signature Authorization Request - Additional Information Required'
            message = f"""
Hello {auth_request.user.get_full_name() or auth_request.user.username},

Your e-signature authorization request requires additional information or has been declined by the Data Manager/System Administrator.

E-Signature Request Details:
- Requested Signatory Name: {auth_request.signatory_name}
- Role: {auth_request.role}

Your Original Justification:
{auth_request.justification}

Data Manager/System Administrator Notes: {auth_request.admin_notes}

Next Steps:
- Review the administrator's notes above
- If you need to resubmit your e-signature request with additional information, you can do so through the system
- Contact the Data Manager or System Administrator if you need clarification

If you believe this decision is an error or need further clarification about your e-signature request, please contact the Data Manager or System Administrator directly.

Best regards,
NPC Reporting System
            """
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@npc-reporting.com',
                [recipient_email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Failed to send user rejection notification: {e}")