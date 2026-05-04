# Generated migration for signature security models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('reports', '0016_add_esignature_models'),
    ]

    operations = [
        # Add verification_hash field to ESignature
        migrations.AddField(
            model_name='esignature',
            name='verification_hash',
            field=models.CharField(blank=True, max_length=64, help_text='HMAC hash for signature verification'),
        ),
        
        # SignatoryAuthorization model
        migrations.CreateModel(
            name='SignatoryAuthorization',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('signatory_name', models.CharField(help_text='Name of signatory this user can sign as', max_length=100)),
                ('authorization_date', models.DateTimeField(auto_now_add=True)),
                ('expiry_date', models.DateTimeField(blank=True, help_text='When this authorization expires', null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('requires_2fa', models.BooleanField(default=True, help_text='Require 2FA for this signatory')),
                ('notes', models.TextField(blank=True)),
                ('authorized_by', models.ForeignKey(help_text='Admin who granted this authorization', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='granted_authorizations', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='signatory_authorizations', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'signatory_authorizations',
                'ordering': ['-authorization_date'],
            },
        ),
        
        # SignatureAuditLog model
        migrations.CreateModel(
            name='SignatureAuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('CREATE', 'Create Signature'), ('UPDATE', 'Update Signature'), ('DELETE', 'Delete Signature'), ('APPLY', 'Apply to Report'), ('VERIFY', 'Verify Signature'), ('VIEW', 'View Signature'), ('2FA_REQUEST', '2FA Requested'), ('2FA_SUCCESS', '2FA Success'), ('2FA_FAILURE', '2FA Failed')], max_length=20)),
                ('ip_address', models.GenericIPAddressField()),
                ('user_agent', models.TextField(blank=True)),
                ('device_fingerprint', models.CharField(blank=True, max_length=255)),
                ('geolocation', models.JSONField(blank=True, help_text='Approximate location data', null=True)),
                ('success', models.BooleanField(default=True)),
                ('failure_reason', models.TextField(blank=True)),
                ('additional_data', models.JSONField(blank=True, help_text='Additional context data', null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('report_signature', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='reports.reportsignature')),
                ('signature', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='reports.esignature')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'signature_audit_logs',
                'ordering': ['-timestamp'],
            },
        ),
        
        # SignatureVerificationToken model
        migrations.CreateModel(
            name='SignatureVerificationToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(help_text='6-digit OTP code', max_length=6)),
                ('secret', models.CharField(help_text='Secret for token generation', max_length=64)),
                ('signature_intent', models.JSONField(help_text='What the user is trying to sign')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField(help_text='When this token expires')),
                ('is_used', models.BooleanField(default=False)),
                ('verified_at', models.DateTimeField(blank=True, null=True)),
                ('attempts', models.IntegerField(default=0, help_text='Number of verification attempts')),
                ('max_attempts', models.IntegerField(default=3)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='signature_tokens', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'signature_verification_tokens',
                'ordering': ['-created_at'],
            },
        ),
        
        # SignatureSecuritySettings model
        migrations.CreateModel(
            name='SignatureSecuritySettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('require_2fa_for_all', models.BooleanField(default=False, help_text='Require 2FA for all signatures')),
                ('otp_validity_minutes', models.IntegerField(default=5, help_text='OTP validity in minutes')),
                ('max_otp_attempts', models.IntegerField(default=3, help_text='Maximum OTP verification attempts')),
                ('max_signatures_per_hour', models.IntegerField(default=10, help_text='Max signatures per user per hour')),
                ('max_signatures_per_day', models.IntegerField(default=50, help_text='Max signatures per user per day')),
                ('audit_retention_days', models.IntegerField(default=2555, help_text='Audit log retention (7 years default)')),
                ('log_geolocation', models.BooleanField(default=False, help_text='Log approximate geolocation')),
                ('enable_encryption', models.BooleanField(default=True, help_text='Encrypt signature data at rest')),
                ('enable_verification_hash', models.BooleanField(default=True, help_text='Generate verification hashes')),
                ('require_device_fingerprint', models.BooleanField(default=True, help_text='Require device fingerprinting')),
                ('notify_on_signature', models.BooleanField(default=True, help_text='Email notification on signature')),
                ('notify_on_suspicious', models.BooleanField(default=True, help_text='Alert on suspicious activity')),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'signature_security_settings',
                'verbose_name': 'Signature Security Settings',
                'verbose_name_plural': 'Signature Security Settings',
            },
        ),
        
        # Add indexes
        migrations.AddIndex(
            model_name='signatoryauthorization',
            index=models.Index(fields=['user', 'is_active'], name='signatory_user_active_idx'),
        ),
        migrations.AddIndex(
            model_name='signatoryauthorization',
            index=models.Index(fields=['signatory_name', 'is_active'], name='signatory_name_active_idx'),
        ),
        migrations.AddIndex(
            model_name='signatureauditlog',
            index=models.Index(fields=['user', 'timestamp'], name='sig_audit_user_time_idx'),
        ),
        migrations.AddIndex(
            model_name='signatureauditlog',
            index=models.Index(fields=['signature', 'timestamp'], name='sig_audit_sig_time_idx'),
        ),
        migrations.AddIndex(
            model_name='signatureauditlog',
            index=models.Index(fields=['action', 'timestamp'], name='sig_audit_action_time_idx'),
        ),
        migrations.AddIndex(
            model_name='signatureauditlog',
            index=models.Index(fields=['ip_address'], name='sig_audit_ip_idx'),
        ),
        migrations.AddIndex(
            model_name='signatureauditlog',
            index=models.Index(fields=['success', 'timestamp'], name='sig_audit_success_time_idx'),
        ),
        migrations.AddIndex(
            model_name='signatureverificationtoken',
            index=models.Index(fields=['user', 'is_used'], name='sig_token_user_used_idx'),
        ),
        migrations.AddIndex(
            model_name='signatureverificationtoken',
            index=models.Index(fields=['token', 'is_used'], name='sig_token_token_used_idx'),
        ),
        migrations.AddIndex(
            model_name='signatureverificationtoken',
            index=models.Index(fields=['expires_at'], name='sig_token_expires_idx'),
        ),
        
        # Add unique constraint
        migrations.AddConstraint(
            model_name='signatoryauthorization',
            constraint=models.UniqueConstraint(fields=['user', 'signatory_name'], name='unique_user_signatory'),
        ),
    ]
