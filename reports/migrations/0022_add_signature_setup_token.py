# Generated migration for signature setup token fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0021_add_cancelled_status_to_authorization_requests'),
    ]

    operations = [
        migrations.AddField(
            model_name='signatoryauthorization',
            name='setup_token',
            field=models.CharField(blank=True, help_text='Secure token for signature setup', max_length=64, null=True),
        ),
        migrations.AddField(
            model_name='signatoryauthorization',
            name='token_expires',
            field=models.DateTimeField(blank=True, help_text='When setup token expires', null=True),
        ),
        migrations.AddField(
            model_name='signatoryauthorization',
            name='signature_created',
            field=models.BooleanField(default=False, help_text='Whether user has created their signature'),
        ),
        migrations.AddIndex(
            model_name='signatoryauthorization',
            index=models.Index(fields=['setup_token'], name='reports_sig_setup_token_idx'),
        ),
    ]