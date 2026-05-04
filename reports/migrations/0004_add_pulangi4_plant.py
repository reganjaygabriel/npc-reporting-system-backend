# Generated migration for adding Pulangi 4 plant

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0003_rename_historical_plant_i_idx_historical__plant_i_823568_idx_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='plant',
            name='code',
            field=models.CharField(
                choices=[
                    ('AGUS1', 'Agus 1'),
                    ('AGUS2', 'Agus 2'),
                    ('AGUS4', 'Agus 4'),
                    ('AGUS5', 'Agus 5'),
                    ('AGUS6', 'Agus 6'),
                    ('AGUS7', 'Agus 7'),
                    ('PULANGI4', 'Pulangi 4'),
                ],
                max_length=10,
                unique=True
            ),
        ),
    ]
