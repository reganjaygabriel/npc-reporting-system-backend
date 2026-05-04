# Generated migration for signatory authorization requests

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('reports', '0017_signature_security_models'),
    ]

    operations = [
        # SignatoryAuthorizationRequest model
        migrations.CreateModel(
            name='SignatoryAuthorizationRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('signatory_name', models.CharField(help_text='Name of signatory requested', max_length=100)),
                ('role', models.CharField(help_text='Role (Prepared by, Approved by, etc.)', max_length=100)),
                ('justification', models.TextField(help_text="User's justification for the request")),
                ('status', models.CharField(choices=[('PENDING', 'Pending Review'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')], default='PENDING', max_length=20)),
                ('admin_notes', models.TextField(blank=True, help_text='Admin notes on the decision')),
                ('requires_2fa', models.BooleanField(default=True, help_text='Require 2FA for this authorization')),
                ('expiry_date', models.DateTimeField(blank=True, help_text='When authorization expires', null=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_authorization_requests', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='authorization_requests', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'signatory_authorization_requests',
                'ordering': ['-created_at'],
            },
        ),
        
        # Add indexes
        migrations.AddIndex(
            model_name='signatoryauthorizationrequest',
            index=models.Index(fields=['user', 'status'], name='auth_req_user_status_idx'),
        ),
        migrations.AddIndex(
            model_name='signatoryauthorizationrequest',
            index=models.Index(fields=['status', 'created_at'], name='auth_req_status_created_idx'),
        ),
        migrations.AddIndex(
            model_name='signatoryauthorizationrequest',
            index=models.Index(fields=['signatory_name'], name='auth_req_signatory_idx'),
        ),
    ]