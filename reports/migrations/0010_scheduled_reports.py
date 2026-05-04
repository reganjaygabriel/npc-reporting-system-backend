from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('reports', '0009_rename_audit_logs_user_ts_idx_audit_logs_user_id_88267f_idx_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScheduledReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('report_type', models.CharField(choices=[('GENERATION_SUMMARY', 'Generation Summary'), ('CAPACITY_FACTOR', 'Capacity Factor Analysis'), ('AVAILABILITY', 'Availability Report'), ('WATER_NOMINATION', 'Water Nomination Report'), ('PERFORMANCE_METRICS', 'Performance Metrics'), ('COMPARATIVE_ANALYSIS', 'Comparative Analysis')], max_length=50)),
                ('frequency', models.CharField(choices=[('DAILY', 'Daily'), ('WEEKLY', 'Weekly'), ('MONTHLY', 'Monthly'), ('QUARTERLY', 'Quarterly')], max_length=20)),
                ('format', models.CharField(choices=[('PDF', 'PDF'), ('EXCEL', 'Excel'), ('BOTH', 'Both PDF and Excel')], default='PDF', max_length=10)),
                ('status', models.CharField(choices=[('ACTIVE', 'Active'), ('PAUSED', 'Paused'), ('INACTIVE', 'Inactive')], default='ACTIVE', max_length=20)),
                ('date_range_days', models.IntegerField(default=30, help_text='Number of days to include in report')),
                ('schedule_time', models.TimeField(help_text='Time to generate report (24-hour format)')),
                ('schedule_day', models.IntegerField(blank=True, help_text='Day of week (0=Monday) or month (1-31)', null=True)),
                ('additional_emails', models.TextField(blank=True, help_text='Additional email addresses (one per line)')),
                ('last_run', models.DateTimeField(blank=True, null=True)),
                ('next_run', models.DateTimeField(blank=True, null=True)),
                ('run_count', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_scheduled_reports', to=settings.AUTH_USER_MODEL)),
                ('plants', models.ManyToManyField(blank=True, help_text='Leave empty for all plants', to='reports.plant')),
                ('recipients', models.ManyToManyField(help_text='Users to receive report', related_name='scheduled_reports', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'scheduled_reports',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ReportExecution',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('RUNNING', 'Running'), ('COMPLETED', 'Completed'), ('FAILED', 'Failed')], default='PENDING', max_length=20)),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('duration_seconds', models.IntegerField(blank=True, null=True)),
                ('file_path', models.CharField(blank=True, max_length=500)),
                ('file_size', models.IntegerField(blank=True, null=True)),
                ('records_processed', models.IntegerField(default=0)),
                ('error_message', models.TextField(blank=True)),
                ('recipients_sent', models.IntegerField(default=0)),
                ('recipients_failed', models.IntegerField(default=0)),
                ('scheduled_report', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='executions', to='reports.scheduledreport')),
            ],
            options={
                'db_table': 'report_executions',
                'ordering': ['-started_at'],
            },
        ),
        migrations.AddIndex(
            model_name='scheduledreport',
            index=models.Index(fields=['status', 'next_run'], name='scheduled_r_status_idx'),
        ),
        migrations.AddIndex(
            model_name='scheduledreport',
            index=models.Index(fields=['frequency'], name='scheduled_r_frequen_idx'),
        ),
        migrations.AddIndex(
            model_name='reportexecution',
            index=models.Index(fields=['scheduled_report', 'started_at'], name='report_exec_schedul_idx'),
        ),
        migrations.AddIndex(
            model_name='reportexecution',
            index=models.Index(fields=['status'], name='report_exec_status_idx'),
        ),
    ]
