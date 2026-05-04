"""
Django management command to fix signature setup for a specific token
"""

from django.core.management.base import BaseCommand
from reports.models import SignatoryAuthorization
from django.utils import timezone


class Command(BaseCommand):
    help = 'Fix signature setup for a specific token'

    def add_arguments(self, parser):
        parser.add_argument(
            '--token',
            type=str,
            help='Setup token to fix',
        )

    def handle(self, *args, **options):
        if not options['token']:
            self.stdout.write(
                self.style.ERROR('Please provide --token parameter')
            )
            return
        
        token = options['token']
        
        try:
            # Find the authorization with this token
            authorization = SignatoryAuthorization.objects.get(
                setup_token=token,
                is_active=True
            )
            
            self.stdout.write(f'Found authorization: {authorization.signatory_name}')
            self.stdout.write(f'User: {authorization.user.get_full_name() or authorization.user.username}')
            self.stdout.write(f'Token: {authorization.setup_token[:20]}...')
            self.stdout.write(f'Token expires: {authorization.token_expires}')
            
            # Check if token is expired
            if authorization.token_expires and timezone.now() > authorization.token_expires:
                self.stdout.write(
                    self.style.WARNING('Token is expired, extending validity...')
                )
                # Extend token validity by 24 hours
                authorization.token_expires = timezone.now() + timezone.timedelta(hours=24)
                authorization.save()
                self.stdout.write(
                    self.style.SUCCESS('Token validity extended by 24 hours')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('Token is still valid')
                )
            
            # Generate the frontend URL
            frontend_url = f"http://localhost:8081/signature-setup/{token}"
            self.stdout.write(f'\n🔗 Frontend URL: {frontend_url}')
            
            # Test the backend endpoint
            self.stdout.write('\nTesting backend endpoint...')
            
            # Simulate the endpoint logic
            try:
                # This should work now with the fallback logic
                is_valid = authorization.is_setup_token_valid()
                self.stdout.write(f'Token validation result: {is_valid}')
                
                if is_valid:
                    self.stdout.write(
                        self.style.SUCCESS('✅ Token validation successful!')
                    )
                    self.stdout.write(
                        self.style.SUCCESS('The signature setup link should now work.')
                    )
                    self.stdout.write(f'\n🎯 Try clicking this link: {frontend_url}')
                else:
                    self.stdout.write(
                        self.style.ERROR('❌ Token validation failed')
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error during validation: {e}')
                )
                
        except SignatoryAuthorization.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'No authorization found with token: {token[:20]}...')
            )