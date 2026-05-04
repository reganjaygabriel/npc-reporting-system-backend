# Fix audit log session_key field to be nullable

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0024_merge_20260318_1513'),
    ]

    operations = [
        # Make session_key nullable to fix NOT NULL constraint errors
        migrations.AlterField(
            model_name='auditlog',
            name='session_key',
            field=models.CharField(blank=True, null=True, help_text='Session identifier', max_length=40),
        ),
    ]