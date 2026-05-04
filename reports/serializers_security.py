"""Serializers for signature security models"""
from rest_framework import serializers
from .models import (
    SignatoryAuthorization, SignatureAuditLog, 
    SignatureVerificationToken, SignatureSecuritySettings,
    SignatoryAuthorizationRequest
)


def trigger_email_workflow(auth_request):
    """Standalone function to trigger email workflow - called after request creation"""
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        from django.utils import timezone
        import secrets
        
        print(f"🔥 STANDALONE EMAIL WORKFLOW TRIGGERED for {auth_request.signatory_name}")
        
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
        print(f"🔥 Email sent successfully to {recipient_email}")
        
        # Write success to file for verification
        with open('email_workflow_success.txt', 'w', encoding='utf-8') as f:
            f.write(f"SUCCESS: Email workflow completed for {auth_request.signatory_name} at {timezone.now()}\n")
            f.write(f"Authorization ID: {authorization.id}\n")
            f.write(f"Setup Token: {setup_token}\n")
            f.write(f"Email: {recipient_email}\n")
        
        return True
        
    except Exception as e:
        print(f"🔥 STANDALONE EMAIL WORKFLOW FAILED: {e}")
        import traceback
        traceback.print_exc()
        
        # Write error to file for verification
        with open('email_workflow_error.txt', 'w', encoding='utf-8') as f:
            f.write(f"ERROR: Email workflow failed for {auth_request.signatory_name} at {timezone.now()}\n")
            f.write(f"Error: {str(e)}\n")
            f.write(f"Traceback: {traceback.format_exc()}\n")
        
        return False


class SignatoryAuthorizationSerializer(serializers.ModelSerializer):
    """Serializer for signatory authorizations"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    authorized_by_username = serializers.CharField(source='authorized_by.username', read_only=True)
    is_valid = serializers.SerializerMethodField()
    signature_url = serializers.SerializerMethodField()
    has_signature = serializers.SerializerMethodField()
    
    class Meta:
        model = SignatoryAuthorization
        fields = [
            'id', 'user', 'user_username', 'signatory_name',
            'authorized_by', 'authorized_by_username', 'authorization_date',
            'expiry_date', 'is_active', 'requires_2fa', 'notes', 'is_valid',
            'signature_url', 'has_signature', 'signature_created'
        ]
        read_only_fields = ['id', 'authorization_date', 'user_username', 'authorized_by_username']
    
    def get_is_valid(self, obj):
        """Check if authorization is currently valid"""
        return obj.is_valid()
    
    def get_signature_url(self, obj):
        """Get the signature image URL if it exists"""
        if not obj.signature_created:
            return None
            
        import os
        import glob
        from django.conf import settings
        
        # Generate expected filename based on signatory name
        base_filename = obj.signatory_name.lower().replace(' ', '_').replace('.', '_')
        
        # Try multiple filename patterns
        patterns = [
            f"{base_filename}_signature.png",
            f"{base_filename}_signature.jpg",
            f"{base_filename}_signature.jpeg",
        ]
        
        admin_signatures_dir = os.path.join(settings.MEDIA_ROOT, 'admin_signatures')
        
        # First try exact matches
        for pattern in patterns:
            file_path = os.path.join(admin_signatures_dir, pattern)
            if os.path.exists(file_path):
                # Return absolute URL for frontend - use backend URL for media files
                backend_url = 'http://localhost:8000'  # Django backend serves media files
                return f"{backend_url}{settings.MEDIA_URL}admin_signatures/{pattern}"
        
        # If no exact match, try glob pattern to find similar files
        glob_pattern = os.path.join(admin_signatures_dir, f"{base_filename}*signature*")
        matching_files = glob.glob(glob_pattern)
        
        if matching_files:
            # Use the first matching file
            filename = os.path.basename(matching_files[0])
            backend_url = 'http://localhost:8000'  # Django backend serves media files
            return f"{backend_url}{settings.MEDIA_URL}admin_signatures/{filename}"
        
        return None
    
    def get_has_signature(self, obj):
        """Check if signature file exists"""
        return obj.signature_created and self.get_signature_url(obj) is not None


class SignatureAuditLogSerializer(serializers.ModelSerializer):
    """Serializer for signature audit logs"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = SignatureAuditLog
        fields = [
            'id', 'user', 'user_username', 'action', 'action_display',
            'signature', 'report_signature', 'ip_address', 'user_agent',
            'device_fingerprint', 'geolocation', 'success', 'failure_reason',
            'additional_data', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp', 'user_username', 'action_display']


class SignatureVerificationTokenSerializer(serializers.ModelSerializer):
    """Serializer for 2FA verification tokens"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    is_valid = serializers.SerializerMethodField()
    
    class Meta:
        model = SignatureVerificationToken
        fields = [
            'id', 'user', 'user_username', 'token', 'signature_intent',
            'created_at', 'expires_at', 'is_used', 'verified_at',
            'attempts', 'max_attempts', 'ip_address', 'is_valid'
        ]
        read_only_fields = ['id', 'created_at', 'user_username', 'is_valid']
        extra_kwargs = {
            'secret': {'write_only': True},
            'token': {'write_only': True}
        }
    
    def get_is_valid(self, obj):
        """Check if token is still valid"""
        return obj.is_valid()


class SignatureSecuritySettingsSerializer(serializers.ModelSerializer):
    """Serializer for signature security settings"""
    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True)
    
    class Meta:
        model = SignatureSecuritySettings
        fields = [
            'id', 'require_2fa_for_all', 'otp_validity_minutes', 'max_otp_attempts',
            'max_signatures_per_hour', 'max_signatures_per_day',
            'audit_retention_days', 'log_geolocation',
            'enable_encryption', 'enable_verification_hash', 'require_device_fingerprint',
            'notify_on_signature', 'notify_on_suspicious',
            'updated_at', 'updated_by', 'updated_by_username'
        ]
        read_only_fields = ['id', 'updated_at', 'updated_by_username']


class Request2FASerializer(serializers.Serializer):
    """Serializer for requesting 2FA code"""
    signatory_name = serializers.CharField(max_length=100)
    signature_intent = serializers.JSONField()


class Verify2FASerializer(serializers.Serializer):
    """Serializer for verifying 2FA code"""
    token_id = serializers.IntegerField()
    otp_code = serializers.CharField(max_length=6)
    device_fingerprint = serializers.CharField(required=False, allow_blank=True)


class SignatoryAuthorizationRequestSerializer(serializers.ModelSerializer):
    """Serializer for user-friendly authorization requests"""
    user_username = serializers.CharField(source='user.username', read_only=True)
    user_full_name = serializers.CharField(source='user.get_full_name', read_only=True)
    reviewed_by_username = serializers.CharField(source='reviewed_by.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = SignatoryAuthorizationRequest
        fields = [
            'id', 'user', 'user_username', 'user_full_name', 'email',
            'signatory_name', 'role', 'justification', 'status', 'status_display',
            'reviewed_by', 'reviewed_by_username', 'reviewed_at', 'admin_notes',
            'requires_2fa', 'expiry_date', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'user_username', 'user_full_name',
            'status', 'status_display', 'reviewed_by', 'reviewed_by_username', 
            'reviewed_at', 'admin_notes', 'created_at', 'updated_at'
        ]
    
    def create(self, validated_data):
        # User is passed from the view, don't override it
        auth_request = super().create(validated_data)
        
        print(f"🔥 SERIALIZER CREATE CALLED for {auth_request.signatory_name}")
        
        # Call the standalone email workflow function
        try:
            success = trigger_email_workflow(auth_request)
            if success:
                print(f"✅ Email workflow completed successfully for {auth_request.signatory_name}")
            else:
                print(f"❌ Email workflow failed for {auth_request.signatory_name}")
        except Exception as e:
            print(f"❌ Error calling email workflow: {e}")
        
        return auth_request

