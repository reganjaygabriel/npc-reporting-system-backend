# Generated migration to update report types to PSR only

from django.db import migrations


def update_report_types(apps, schema_editor):
    """Update all existing scheduled reports to PSR type"""
    ScheduledReport = apps.get_model('reports', 'ScheduledReport')
    
    # Update all existing reports to PSR type
    ScheduledReport.objects.all().update(report_type='PSR')


def reverse_update(apps, schema_editor):
    """Reverse migration - set to GENERATION_SUMMARY as default"""
    ScheduledReport = apps.get_model('reports', 'ScheduledReport')
    ScheduledReport.objects.filter(report_type='PSR').update(report_type='GENERATION_SUMMARY')


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0010_scheduled_reports'),
    ]

    operations = [
        migrations.RunPython(update_report_types, reverse_update),
    ]
