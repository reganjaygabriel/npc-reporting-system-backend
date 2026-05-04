import os
import django
import sys
from datetime import date, timedelta
import random

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'npc_reporting.settings_production')
django.setup()

from reports.models import Plant, Unit, GenerationReport, UploadedFile
from django.contrib.auth.models import User

def seed_data():
    # 1. Create Plants
    plants_data = [
        {'name': 'Agus 1 Hydro-Electric Power Plant', 'code': 'AGUS1', 'capacity': 80.0, 'location': 'Marawi City', 'units': 2},
        {'name': 'Agus 2 Hydro-Electric Power Plant', 'code': 'AGUS2', 'capacity': 180.0, 'location': 'Saguiran, Lanao del Sur', 'units': 3},
        {'name': 'Agus 4 Hydro-Electric Power Plant', 'code': 'AGUS4', 'capacity': 158.1, 'location': 'Baloi, Lanao del Norte', 'units': 3},
        {'name': 'Agus 5 Hydro-Electric Power Plant', 'code': 'AGUS5', 'capacity': 55.0, 'location': 'Maria Cristina, Iligan City', 'units': 2},
        {'name': 'Agus 6 Hydro-Electric Power Plant', 'code': 'AGUS6', 'capacity': 200.0, 'location': 'Maria Cristina, Iligan City', 'units': 4},
        {'name': 'Agus 7 Hydro-Electric Power Plant', 'code': 'AGUS7', 'capacity': 54.0, 'location': 'Maria Cristina, Iligan City', 'units': 2},
        {'name': 'Pulangi 4 Hydro-Electric Power Plant', 'code': 'PULANGI4', 'capacity': 255.0, 'location': 'Maramag, Bukidnon', 'units': 3},
    ]

    print("--- Seeding Plants and Units ---")
    for p_data in plants_data:
        plant, created = Plant.objects.get_or_create(
            code=p_data['code'],
            defaults={
                'name': p_data['name'],
                'capacity_mw': p_data['capacity'],
                'location': p_data['location']
            }
        )
        if created:
            print(f"Created Plant: {plant.code}")
        else:
            print(f"Plant exists: {plant.code}")

        # Create Units for this plant
        unit_capacity = float(p_data['capacity']) / p_data['units']
        for i in range(1, p_data['units'] + 1):
            unit, u_created = Unit.objects.get_or_create(
                plant=plant,
                unit_number=i,
                defaults={'capacity_mw': unit_capacity}
            )
            if u_created:
                print(f"  - Created Unit {i}")

    # 2. Create a dummy UploadedFile record for the sample data
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        print("Error: No admin user found. Create one first using createsuperuser.")
        return

    plant_agus1 = Plant.objects.get(code='AGUS1')
    dummy_file, _ = UploadedFile.objects.get_or_create(
        original_filename='sample_data_init.xlsx',
        plant=plant_agus1,
        defaults={
            'uploaded_by': admin_user,
            'file_size': 1024,
            'checksum': 'initial_seed_checksum',
            'status': 'COMPLETED',
            'records_imported': 14
        }
    )

    # 3. Create Sample Generation Records for the last 7 days
    print("\n--- Seeding Sample Generation Records (Last 7 Days) ---")
    today = date.today()
    for i in range(7):
        report_date = today - timedelta(days=i)
        for plant in Plant.objects.all():
            for unit in plant.units.all():
                # Random generation values
                # Generation = capacity * hours * random_factor
                op_hours = 24.0
                gen_kwh = float(unit.capacity_mw) * op_hours * random.uniform(0.7, 0.95) * 1000
                
                # Use update_or_create to avoid duplicates if re-run
                GenerationReport.objects.update_or_create(
                    plant=plant,
                    unit=unit,
                    report_date=report_date,
                    defaults={
                        'uploaded_file': dummy_file,
                        'generation_kwh': gen_kwh,
                        'operating_hours': op_hours,
                        'availability_hours': 24.0,
                        'forced_outage_hours': 0,
                        'scheduled_outage_hours': 0,
                        'remarks': 'Initial sample data'
                    }
                )
    
    print("Done seeding sample data!")

if __name__ == "__main__":
    seed_data()
