# Generated migration for monthly targets

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('reports', '0026_rename_reports_auditlog_ip_timestamp_idx_audit_logs_ip_addr_932507_idx_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='MonthlyTarget',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('month', models.IntegerField(help_text='Month (1-12)')),
                ('year', models.IntegerField(help_text='Year')),
                ('target_percentage', models.DecimalField(decimal_places=2, help_text='Target capacity factor percentage', max_digits=5)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_monthly_targets', to=settings.AUTH_USER_MODEL)),
                ('plant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='monthly_targets', to='reports.plant')),
            ],
            options={
                'db_table': 'monthly_targets',
                'ordering': ['-year', '-month', 'plant'],
                'indexes': [
                    models.Index(fields=['plant', 'year', 'month'], name='monthly_targets_plant_year_month_idx'),
                    models.Index(fields=['year', 'month'], name='monthly_targets_year_month_idx'),
                ],
            },
        ),
        migrations.AddConstraint(
            model_name='monthlytarget',
            constraint=models.UniqueConstraint(fields=('plant', 'year', 'month'), name='unique_plant_year_month_target'),
        ),
    ]