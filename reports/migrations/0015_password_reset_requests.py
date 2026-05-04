# Generated migration for PasswordResetRequest model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('reports', '0014_merge_20260226_1334'),
    ]

    operations = [
        migrations.CreateModel(
            name='PasswordResetRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(help_text='Username requesting password reset', max_length=150)),
                ('reason', models.TextField(blank=True, help_text='Optional reason for password reset request')),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected'), ('COMPLETED', 'Completed')], default='PENDING', max_length=20)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('processed_at', models.DateTimeField(blank=True, null=True)),
                ('admin_notes', models.TextField(blank=True, help_text='Internal notes from admin')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('processed_by', models.ForeignKey(blank=True, help_text='Admin who processed this request', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='processed_reset_requests', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'password_reset_requests',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='passwordresetrequest',
            index=models.Index(fields=['username', 'status'], name='password_re_usernam_8a9c5f_idx'),
        ),
        migrations.AddIndex(
            model_name='passwordresetrequest',
            index=models.Index(fields=['status', 'created_at'], name='password_re_status_2f4e8a_idx'),
        ),
        migrations.AddIndex(
            model_name='passwordresetrequest',
            index=models.Index(fields=['created_at'], name='password_re_created_1b7d3c_idx'),
        ),
    ]
