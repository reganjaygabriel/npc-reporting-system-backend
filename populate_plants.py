#!/usr/bin/env python
"""
Script to populate the database with the required plants
Run this with: python manage.py shell < populate_plants.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'npc_reporting.settings')
django.setup()

from reports.models import Plant

# Plant data
plants_data = [
    {'code': 'AGUS1', 'name': 'Agus 1 Hydroelectric Power Plant', 'capacity_mw': 10.0, 'location': 'Lanao del Sur'},
    {'code': 'AGUS2', 'name': 'Agus 2 Hydroelectric Power Plant', 'capacity_mw': 180.0, 'location': 'Lanao del Sur'},
    {'code': 'AGUS4', 'name': 'Agus 4 Hydroelectric Power Plant', 'capacity_mw': 158.4, 'location': 'Lanao del Sur'},
    {'code': 'AGUS5', 'name': 'Agus 5 Hydroelectric Power Plant', 'capacity_mw': 52.0, 'location': 'Lanao del Sur'},
    {'code': 'AGUS6', 'name': 'Agus 6 Hydroelectric Power Plant', 'capacity_mw': 200.0, 'location': 'Lanao del Sur'},
    {'code': 'AGUS7', 'name': 'Agus 7 Hydroelectric Power Plant', 'capacity_mw': 180.0, 'location': 'Lanao del Sur'},
    {'code': 'PULANGI4', 'name': 'Pulangi 4 Hydroelectric Power Plant', 'capacity_mw': 255.0, 'location': 'Bukidnon'},
]

def populate_plants():
    """Create plants if they don't exist"""
    created_count = 0
    updated_count = 0
    
    for plant_data in plants_data:
        plant, created = Plant.objects.get_or_create(
            code=plant_data['code'],
            defaults=plant_data
        )
        
        if created:
            created_count += 1
            print(f"Created plant: {plant.name} ({plant.code})")
        else:
            # Update existing plant data
            for key, value in plant_data.items():
                setattr(plant, key, value)
            plant.is_active = True  # Ensure it's active
            plant.save()
            updated_count += 1
            print(f"Updated plant: {plant.name} ({plant.code})")
    
    print(f"\nSummary:")
    print(f"Created: {created_count} plants")
    print(f"Updated: {updated_count} plants")
    print(f"Total active plants: {Plant.objects.filter(is_active=True).count()}")

if __name__ == '__main__':
    populate_plants()