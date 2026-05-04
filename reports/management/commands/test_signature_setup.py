"""
Django management command to test signature setup with a real token
"""

from django.core.management.base import BaseCommand
from reports.models import SignatoryAuthorization
import requests


class Command(BaseCommand):
    help = 'Test signature setup endpoint with a real token'

    def handle(self, *args, **options):
        # Get a recent authorization with a setup token
        auth_with_token = SignatoryAuthorization.objects.filter(
            setup_token__isnull=False,
            signature_created=False
        ).first()
        
        if not auth_with_token:
            self.stdout.write(
                self.style.ERROR('No authorization with setup token found')
            )
            return
        
        self.stdout.write(f'Found authorization: {auth_with_token.signatory_name}')
        self.stdout.write(f'Setup token: {auth_with_token.setup_token[:20]}...')
        self.stdout.write(f'Token expires: {auth_with_token.token_expires}')
        self.stdout.write(f'Token valid: {auth_with_token.is_setup_token_valid()}')
        
        # Test the endpoint without authentication
        setup_url = f"http://localhost:8000/api/signatory-authorizations/signature-setup/{auth_with_token.setup_token}/"
        
        self.stdout.write(f'\nTesting endpoint: {setup_url}')
        
        try:
            response = requests.get(setup_url)
            self.stdout.write(f'Status: {response.status_code}')
            self.stdout.write(f'Response: {response.text}')
            
            if response.status_code == 200:
                self.stdout.write(
                    self.style.SUCCESS('✅ SUCCESS! Signature setup endpoint works without authentication!')
                )
                
                # Test the frontend URL
                frontend_url = f"http://localhost:8081/signature-setup/{auth_with_token.setup_token}"
                self.stdout.write(f'\n🔗 Frontend URL to test: {frontend_url}')
                self.stdout.write('Copy this URL and paste it in your browser to test the signature setup page.')
                
            elif response.status_code == 401:
                self.stdout.write(
                    self.style.ERROR('❌ Endpoint still requires authentication')
                )
            elif response.status_code == 404:
                self.stdout.write(
                    self.style.WARNING('❌ Token not found or expired')
                )
            elif response.status_code == 500:
                self.stdout.write(
                    self.style.ERROR('❌ Internal server error in endpoint')
                )
            else:
                self.stdout.write(f'Unexpected status: {response.status_code}')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error testing endpoint: {e}')
            )