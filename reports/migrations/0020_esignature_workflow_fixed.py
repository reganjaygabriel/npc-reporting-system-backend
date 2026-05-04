# Custom migration to fix SignatureAuditLog table conflict

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('reports', '0019_add_email_to_authorization_request'),
    ]

    operations = [
        # First, drop the existing signature_audit_logs table if it exists
        migrations.RunSQL(
            "DROP TABLE IF EXISTS signature_audit_logs;",
            reverse_sql="-- Cannot reverse dropping table"
        ),
        
        # Create Document model
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('document_type', models.CharField(choices=[('PSR', 'Plant Status Report'), ('DAILY', 'Daily Report'), ('MONTHLY', 'Monthly Report'), ('CUSTOM', 'Custom Document')], max_length=20)),
                ('file_path', models.FileField(blank=True, null=True, upload_to='documents/%Y/%m/')),
                ('content', models.TextField(blank=True, help_text='Document content if not file-based')),
                ('status', models.CharField(choices=[('DRAFT', 'Draft'), ('PENDING_SIGNATURE', 'Pending Signature'), ('SIGNED', 'Signed'), ('COMPLETED', 'Completed')], default='DRAFT', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_documents', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'documents',
                'ordering': ['-created_at'],
            },
        ),
        
        # Create SignatureRequest model
        migrations.CreateModel(
            name='SignatureRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('signer_name', models.CharField(max_length=100)),
                ('signer_email', models.EmailField(max_length=254)),
                ('signer_role', models.CharField(help_text="Role in document (e.g., 'Prepared by', 'Approved by')", max_length=100)),
                ('token', models.CharField(db_index=True, max_length=64, unique=True)),
                ('expires_at', models.DateTimeField()),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('SIGNED', 'Signed'), ('EXPIRED', 'Expired'), ('CANCELLED', 'Cancelled')], default='PENDING', max_length=20)),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('signed_at', models.DateTimeField(blank=True, null=True)),
                ('signature_x', models.IntegerField(blank=True, help_text='X coordinate for signature placement', null=True)),
                ('signature_y', models.IntegerField(blank=True, help_text='Y coordinate for signature placement', null=True)),
                ('signature_page', models.IntegerField(default=1, help_text='Page number for signature placement')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='signature_requests', to='reports.document')),
            ],
            options={
                'db_table': 'signature_requests',
                'ordering': ['-created_at'],
            },
        ),
        
        # Create DigitalSignature model
        migrations.CreateModel(
            name='DigitalSignature',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('signature_image', models.ImageField(upload_to='signatures/%Y/%m/')),
                ('signature_type', models.CharField(choices=[('DRAWN', 'Hand Drawn'), ('UPLOADED', 'Uploaded Image'), ('TYPED', 'Typed Text')], max_length=10)),
                ('signature_data', models.TextField(blank=True, help_text='Base64 signature data for drawn signatures')),
                ('verification_hash', models.CharField(blank=True, max_length=64)),
                ('signing_timestamp', models.DateTimeField(auto_now_add=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('width', models.IntegerField(default=400)),
                ('height', models.IntegerField(default=200)),
                ('signature_request', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='signature', to='reports.signaturerequest')),
            ],
            options={
                'db_table': 'digital_signatures',
                'ordering': ['-signing_timestamp'],
            },
        ),
        
        # Create new SignatureAuditLog model for e-signature workflow
        migrations.CreateModel(
            name='SignatureAuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('REQUEST_CREATED', 'Signature Request Created'), ('EMAIL_SENT', 'Signature Email Sent'), ('LINK_ACCESSED', 'Signature Link Accessed'), ('SIGNATURE_CREATED', 'Signature Created'), ('DOCUMENT_SIGNED', 'Document Signed'), ('REQUEST_EXPIRED', 'Request Expired'), ('REQUEST_CANCELLED', 'Request Cancelled')], max_length=20)),
                ('details', models.JSONField(blank=True, default=dict)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('signature_request', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='audit_logs', to='reports.signaturerequest')),
            ],
            options={
                'db_table': 'signature_audit_logs',
                'ordering': ['-timestamp'],
            },
        ),
        
        # Add indexes
        migrations.AddIndex(
            model_name='signaturerequest',
            index=models.Index(fields=['token'], name='signature_r_token_b8e5a5_idx'),
        ),
        migrations.AddIndex(
            model_name='signaturerequest',
            index=models.Index(fields=['status', 'expires_at'], name='signature_r_status_4a8b9c_idx'),
        ),
    ]