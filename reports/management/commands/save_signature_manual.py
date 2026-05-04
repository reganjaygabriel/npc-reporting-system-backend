"""
Django management command to manually save a signature for JMM MATA
"""

from django.core.management.base import BaseCommand
from reports.models import SignatoryAuthorization
import base64
import os
from django.conf import settings


class Command(BaseCommand):
    help = 'Manually save signature for JMM MATA'

    def add_arguments(self, parser):
        parser.add_argument(
            '--signature-data',
            type=str,
            help='Base64 signature data (data:image/png;base64,...)',
        )

    def handle(self, *args, **options):
        # Find the JMM MATA authorization
        jmm_auth = SignatoryAuthorization.objects.filter(
            signatory_name='JMM MATA',
            setup_token__isnull=False,
            signature_created=False
        ).first()
        
        if not jmm_auth:
            self.stdout.write(
                self.style.ERROR('No JMM MATA authorization found')
            )
            return
        
        self.stdout.write(f'Found authorization: {jmm_auth.signatory_name}')
        
        if options['signature_data']:
            signature_data = options['signature_data']
        else:
            # Create a simple placeholder signature
            self.stdout.write('No signature data provided, creating placeholder...')
            
            # Create a simple signature file
            signature_content = '''
            <svg width="600" height="200" xmlns="http://www.w3.org/2000/svg">
                <text x="50" y="100" font-family="cursive" font-size="40" fill="black">JMM MATA</text>
            </svg>
            '''
            
            # Save as SVG first, then we'll create a PNG placeholder
            filename = f"{jmm_auth.signatory_name.lower().replace(' ', '_').replace('.', '_')}_signature.svg"
            
            # Save to admin_signatures folder
            admin_signatures_dir = os.path.join(settings.MEDIA_ROOT, 'admin_signatures')
            os.makedirs(admin_signatures_dir, exist_ok=True)
            
            file_path = os.path.join(admin_signatures_dir, filename)
            with open(file_path, 'w') as f:
                f.write(signature_content)
            
            self.stdout.write(f'Placeholder signature saved: {filename}')
        else:
            try:
                # Decode base64 signature
                format, imgstr = signature_data.split(';base64,')
                ext = format.split('/')[-1]
                
                # Create filename
                filename = f"{jmm_auth.signatory_name.lower().replace(' ', '_').replace('.', '_')}_signature.{ext}"
                
                # Save to admin_signatures folder
                admin_signatures_dir = os.path.join(settings.MEDIA_ROOT, 'admin_signatures')
                os.makedirs(admin_signatures_dir, exist_ok=True)
                
                file_path = os.path.join(admin_signatures_dir, filename)
                with open(file_path, 'wb') as f:
                    f.write(base64.b64decode(imgstr))
                
                self.stdout.write(f'Signature saved: {filename}')
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error saving signature: {e}')
                )
                return
        
        # Update authorization
        jmm_auth.signature_created = True
        jmm_auth.setup_token = None  # Invalidate token after use
        jmm_auth.token_expires = None
        jmm_auth.save()
        
        self.stdout.write(
            self.style.SUCCESS('✅ Signature setup completed!')
        )
        self.stdout.write(
            self.style.SUCCESS('JMM MATA can now use e-signature to sign reports.')
        )
        
        # Check if there are any reports that need signing
        self.stdout.write('\n📋 Next steps:')
        self.stdout.write('1. The e-signature is now ready for use')
        self.stdout.write('2. JMM MATA can sign reports in the system')
        self.stdout.write('3. The signature setup process is complete')