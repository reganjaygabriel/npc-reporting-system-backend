#!/usr/bin/env python
"""
Script to create units for all plants
Run this with: python create_units.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'npc_reporting.settings')
django.setup()

from reports.models import Plant, Unit

# Units configuration for each plant
units_config = {
    'AGUS1': {'units': 2, 'capacity_per_unit': 5.0},
    'AGUS2': {'units': 3, 'capacity_per_unit': 60.0},
    'AGUS4': {'units': 3, 'capacity_per_unit': 52.8},
    'AGUS5': {'units': 2, 'capacity_per_unit': 26.0},
    'AGUS6': {'units': 4, 'capacity_per_unit': 50.0},
    'AGUS7': {'units': 2, 'capacity_per_unit': 90.0},
    'PULANGI4': {'units': 3, 'capacity_per_unit': 85.0},
}

def create_units():
    """Create units for all plants"""
    created_count = 0
    
    for plant_code, config in units_config.items():
        try:
            plant = Plant.objects.get(code=plant_code)
            
            for unit_num in range(1, config['units'] + 1):
                unit, created = Unit.objects.get_or_create(
                    plant=plant,
                    unit_number=unit_num,
                    defaults={
                        'capacity_mw': config['capacity_per_unit'],
                        'is_active': True
                    }
                )
                
                if created:
                    created_count += 1
                    print(f"Created Unit {unit_num} for {plant.name}")
                else:
                    # Update capacity if needed
                    unit.capacity_mw = config['capacity_per_unit']
                    unit.is_active = True
                    unit.save()
                    print(f"Updated Unit {unit_num} for {plant.name}")
        
        except Plant.DoesNotExist:
            print(f"Warning: Plant {plant_code} not found. Run populate_plants.py first.")
    
    print(f"\nSummary:")
    print(f"Created: {created_count} units")
    print(f"Total active units: {Unit.objects.filter(is_active=True).count()}")

if __name__ == '__main__':
    create_units()
