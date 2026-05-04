import os
import django
import sys

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'npc_reporting.settings_production')
django.setup()

from reports.models import Plant

def seed_plants():
    # Corrected data with capacity_mw and proper codes from models.py
    plants = [
        {'name': 'Agus 1 Hydro-Electric Power Plant', 'code': 'AGUS1', 'capacity': 80.0, 'location': 'Marawi City'},
        {'name': 'Agus 2 Hydro-Electric Power Plant', 'code': 'AGUS2', 'capacity': 180.0, 'location': 'Saguiran, Lanao del Sur'},
        {'name': 'Agus 4 Hydro-Electric Power Plant', 'code': 'AGUS4', 'capacity': 158.1, 'location': 'Baloi, Lanao del Norte'},
        {'name': 'Agus 5 Hydro-Electric Power Plant', 'code': 'AGUS5', 'capacity': 55.0, 'location': 'Maria Cristina, Iligan City'},
        {'name': 'Agus 6 Hydro-Electric Power Plant', 'code': 'AGUS6', 'capacity': 200.0, 'location': 'Maria Cristina, Iligan City'},
        {'name': 'Agus 7 Hydro-Electric Power Plant', 'code': 'AGUS7', 'capacity': 54.0, 'location': 'Maria Cristina, Iligan City'},
        {'name': 'Pulangi 4 Hydro-Electric Power Plant', 'code': 'PULANGI4', 'capacity': 255.0, 'location': 'Maramag, Bukidnon'},
    ]

    print("Seeding plants into database...")
    for plant_data in plants:
        plant, created = Plant.objects.get_or_create(
            code=plant_data['code'],
            defaults={
                'name': plant_data['name'],
                'capacity_mw': plant_data['capacity'],
                'location': plant_data['location']
            }
        )
        if created:
            print(f"Created plant: {plant.name} ({plant.code})")
        else:
            # Update existing plant if needed
            plant.capacity_mw = plant_data['capacity']
            plant.location = plant_data['location']
            plant.name = plant_data['name']
            plant.save()
            print(f"Updated plant: {plant.name} ({plant.code})")
    print("Done seeding plants!")

if __name__ == "__main__":
    seed_plants()
