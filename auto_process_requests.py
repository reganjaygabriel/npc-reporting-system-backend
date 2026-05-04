#!/usr/bin/env python3
"""
Auto-process pending authorization requests
This script monitors for new PENDING requests and automatically processes them
"""
import os
import sys
import django
import time
from datetime import datetime, timedelta

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'npc_reporting.settings')
django.setup()

from reports.models import SignatoryAuthorizationRequest, SignatoryAuthorization
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import secrets


def process_pending_requests():
    """Process all pending requests that are less than 1 minute old"""
    try:
        # Get pending requests created in the last minute
        one_minute_ago = timezone.now() - timedelta(minutes=1)
        pending_requests = SignatoryAuthorizationRequest.objects.filter(
            status='PENDING',
            created_at__gte=one_minute_ago
        )
        
        if not pending_requests.exists():
            return
        
        print(f"Found {pending_requests.count()} recent pending requests to process")
        
        for auth_request in pending_requests:
            try:
                # Check if authorization already exists
                existing_auth = SignatoryAuthorization.objects.filter(
                    user=auth_request.user,
                    signatory_name=auth_request.signatory_name,
                    is_active=True
                ).first()
                
                if existing_auth:
                    print(f"Authorization already exists for {auth_request.signatory_name}")
                    continue
                
                print(f"Processing: {auth_request.signatory_name}")
                
                # Generate secure token for signature setup
                setup_token = secrets.token_urlsafe(32)
                
                # Create authorization (auto-approve)
                authorization = SignatoryAuthorization.objects.create(
                    user=auth_request.user,
                    signatory_name=auth_request.signatory_name,
                    authorized_by=auth_request.user,  # Self-authorized
                    is_active=True,
                    requires_2fa=True,
                    notes='Auto-approved via auto-processor',
                    setup_token=setup_token,
                    token_expires=timezone.now() + timezone.timedelta(hours=24),
                    signature_created=False
                )
                
                # Update request status
                auth_request.status = 'APPROVED'
                auth_request.reviewed_by = auth_request.user
                auth_request.reviewed_at = timezone.now()
                auth_request.admin_notes = 'Auto-approved via auto-processor'
                auth_request.save()
                
                # Send email with signature setup link
                send_signature_setup_email(auth_request, authorization)
                
                print(f"✅ Processed {auth_request.signatory_name} - Email sent!")
                
            except Exception as e:
                print(f"❌ Error processing {auth_request.signatory_name}: {e}")
                
    except Exception as e:
        print(f"❌ Error in process_pending_requests: {e}")


def send_signature_setup_email(auth_request, authorization):
    """Send email with signature setup link"""
    recipient_email = auth_request.email or auth_request.user.email
    if not recipient_email:
        print(f"No email address for {auth_request.signatory_name}")
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
    
    print(f"📧 Email sent to {recipient_email}")


if __name__ == "__main__":
    print("Auto-processor started. Monitoring for pending requests...")
    
    while True:
        try:
            process_pending_requests()
            time.sleep(10)  # Check every 10 seconds
        except KeyboardInterrupt:
            print("\nAuto-processor stopped.")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            time.sleep(10)  # Wait before retrying