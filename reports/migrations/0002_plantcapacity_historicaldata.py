# Generated migration for PlantCapacity and HistoricalData models

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlantCapacity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('installed_capacity', models.DecimalField(decimal_places=2, max_digits=10)),
                ('dependable_capacity', models.DecimalField(decimal_places=2, max_digits=10)),
                ('effective_date', models.DateField()),
                ('remarks', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('plant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='capacity_records', to='reports.plant')),
            ],
            options={
                'db_table': 'plant_capacity',
                'ordering': ['-effective_date', 'plant'],
                'indexes': [
                    models.Index(fields=['plant', 'effective_date'], name='plant_capac_plant_i_idx'),
                ],
                'unique_together': {('plant', 'effective_date')},
            },
        ),
        migrations.CreateModel(
            name='HistoricalData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('generation_mwh', models.DecimalField(decimal_places=2, default=0, max_digits=15)),
                ('availability_percent', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('status', models.CharField(default='Operating', max_length=50)),
                ('remarks', models.TextField(blank=True)),
                ('sheet_name', models.CharField(blank=True, max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('plant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='historical_data', to='reports.plant')),
            ],
            options={
                'db_table': 'historical_data',
                'ordering': ['-date', 'plant'],
                'indexes': [
                    models.Index(fields=['plant', 'date'], name='historical_plant_i_idx'),
                    models.Index(fields=['date'], name='historical_date_idx'),
                ],
                'unique_together': {('plant', 'date')},
            },
        ),
    ]
