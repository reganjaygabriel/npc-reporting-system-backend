# Generated migration for archive functionality

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0010_scheduled_reports'),
    ]

    operations = [
        migrations.AddField(
            model_name='uploadedfile',
            name='is_archived',
            field=models.BooleanField(default=False, help_text='Whether this file is archived'),
        ),
        migrations.AddField(
            model_name='uploadedfile',
            name='archived_at',
            field=models.DateTimeField(null=True, blank=True, help_text='When the file was archived'),
        ),
        migrations.AddField(
            model_name='uploadedfile',
            name='archived_by',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=models.SET_NULL,
                related_name='archived_files',
                to='auth.user',
                help_text='User who archived the file'
            ),
        ),
        migrations.AddIndex(
            model_name='uploadedfile',
            index=models.Index(fields=['is_archived'], name='uploaded_fi_is_arch_idx'),
        ),
    ]
