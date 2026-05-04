"""
Django management command to get a working signature setup link
"""

from django.core.management.base import BaseCommand
from reports.models import SignatoryAuthorization
from django.conf import settings


class Command(BaseCommand):
    help = 'Get a working signature setup link for JMM MATA'

    def handle(self, *args, **options):
        # Find the JMM MATA authorization
        jmm_auth = SignatoryAuthorization.objects.filter(
            signatory_name='JMM MATA',
            setup_token__isnull=False,
            signature_created=False
        ).first()
        
        if not jmm_auth:
            self.stdout.write(
                self.style.ERROR('No JMM MATA authorization with setup token found')
            )
            return
        
        self.stdout.write(f'Found authorization: {jmm_auth.signatory_name}')
        self.stdout.write(f'Setup token: {jmm_auth.setup_token[:20]}...')
        self.stdout.write(f'Token expires: {jmm_auth.token_expires}')
        
        # Check if token is valid
        try:
            is_valid = jmm_auth.is_setup_token_valid()
            self.stdout.write(f'Token valid: {is_valid}')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error checking token validity: {e}')
            )
            return
        
        if not is_valid:
            self.stdout.write(
                self.style.ERROR('Token has expired. Creating a new one...')
            )
            
            # Generate a new token
            import secrets
            from django.utils import timezone
            
            jmm_auth.setup_token = secrets.token_urlsafe(32)
            jmm_auth.token_expires = timezone.now() + timezone.timedelta(hours=24)
            jmm_auth.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'New token generated: {jmm_auth.setup_token[:20]}...')
            )
        
        # Generate the working URL
        frontend_url = f"http://localhost:8081/signature-setup/{jmm_auth.setup_token}"
        
        self.stdout.write(
            self.style.SUCCESS(f'\n🔗 WORKING SIGNATURE SETUP URL:')
        )
        self.stdout.write(
            self.style.SUCCESS(f'{frontend_url}')
        )
        
        self.stdout.write(f'\n📋 Instructions:')
        self.stdout.write(f'1. Copy the URL above')
        self.stdout.write(f'2. Paste it in your browser')
        self.stdout.write(f'3. The signature setup page should load')
        self.stdout.write(f'4. Draw your signature and save it')
        
        self.stdout.write(f'\n⚠️  Note: This URL bypasses the email link and should work immediately.')
        self.stdout.write(f'The Django server restart is still needed to fix the email links permanently.')