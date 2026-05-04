"""
Django management command to fix the email workflow for existing requests
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from reports.models import SignatoryAuthorizationRequest, SignatoryAuthorization
import secrets


class Command(BaseCommand):
    help = 'Fix email workflow by sending signature setup links for pending requests'

    def add_arguments(self, parser):
        parser.add_argument(
            '--request-id',
            type=int,
            help='Process specific request ID',
        )
        parser.add_argument(
            '--all-pending',
            action='store_true',
            help='Process all pending requests',
        )

    def handle(self, *args, **options):
        if options['request_id']:
            try:
                auth_request = SignatoryAuthorizationRequest.objects.get(id=options['request_id'])
                self.process_request(auth_request)
            except SignatoryAuthorizationRequest.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Request with ID {options["request_id"]} not found')
                )
        elif options['all_pending']:
            pending_requests = SignatoryAuthorizationRequest.objects.filter(status='PENDING')
            self.stdout.write(f'Found {pending_requests.count()} pending requests')
            
            for auth_request in pending_requests:
                self.process_request(auth_request)
        else:
            self.stdout.write(
                self.style.ERROR('Please specify --request-id or --all-pending')
            )

    def process_request(self, auth_request):
        """Process a single authorization request"""
        self.stdout.write(f'Processing request ID {auth_request.id}: {auth_request.signatory_name}')
        
        try:
            # Check if authorization already exists
            existing_auth = SignatoryAuthorization.objects.filter(
                user=auth_request.user,
                signatory_name=auth_request.signatory_name,
                is_active=True
            ).first()
            
            if existing_auth:
                self.stdout.write(
                    self.style.WARNING(f'Authorization already exists for {auth_request.signatory_name}')
                )
                return
            
            # Generate secure token for signature setup
            setup_token = secrets.token_urlsafe(32)
            
            # Create authorization (auto-approve)
            authorization = SignatoryAuthorization.objects.create(
                user=auth_request.user,
                signatory_name=auth_request.signatory_name,
                authorized_by=auth_request.user,  # Self-authorized
                is_active=True,
                requires_2fa=True,
                notes='Auto-approved via management command',
                setup_token=setup_token,
                token_expires=timezone.now() + timezone.timedelta(hours=24),
                signature_created=False
            )
            
            # Update request status
            auth_request.status = 'APPROVED'
            auth_request.reviewed_by = auth_request.user
            auth_request.reviewed_at = timezone.now()
            auth_request.admin_notes = 'Auto-approved via management command'
            auth_request.save()
            
            # Send email with signature setup link
            self.send_signature_setup_email(auth_request, authorization)
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Processed {auth_request.signatory_name} - Email sent!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error processing {auth_request.signatory_name}: {e}')
            )

    def send_signature_setup_email(self, auth_request, authorization):
        """Send email with signature setup link"""
        recipient_email = auth_request.email or auth_request.user.email
        if not recipient_email:
            self.stdout.write(
                self.style.WARNING(f'No email address for {auth_request.signatory_name}')
            )
            return
        
        # Extract last name for greeting
        signatory_parts = auth_request.signatory_name.split()
        if len(signatory_parts) > 1:
            last_name = signatory_parts[-1]
            if last_name.upper() in ['JR.', 'JR', 'SR.', 'SR', 'III', 'II']:
                last_name = signatory_parts[-2] if len(signatory_parts) > 2 else signatory_parts[0]
            greeting = f"Dear {last_name},"
        else:
            greeting = f"Dear {auth_request.signatory_name},"
        
        setup_url = f"{getattr(settings, 'SITE_URL', 'http://localhost:8081')}/signature-setup/{authorization.setup_token}"
        
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
        
        send_mail(
            subject,
            message,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@npc-reporting.com'),
            [recipient_email],
            fail_silently=False,
        )
        
        self.stdout.write(f'📧 Email sent to {recipient_email}')