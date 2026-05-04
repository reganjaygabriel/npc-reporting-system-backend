# Generated migration for adding email field to SignatoryAuthorizationRequest

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0018_signatory_authorization_requests'),
    ]

    operations = [
        migrations.AddField(
            model_name='signatoryauthorizationrequest',
            name='email',
            field=models.EmailField(default='', help_text='Email address for notifications', max_length=254),
            preserve_default=False,
        ),
    ]
