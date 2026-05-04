"""
Update plant names to include "Power" in "Hydroelectric Power Plant"
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'npc_reporting.settings')
django.setup()

from reports.models import Plant

print("Updating plant names...")

# Update each plant
plants_to_update = [
    ('AGUS1', 'Agus 1 Hydroelectric Power Plant'),
    ('AGUS2', 'Agus 2 Hydroelectric Power Plant'),
    ('AGUS4', 'Agus 4 Hydroelectric Power Plant'),
    ('AGUS5', 'Agus 5 Hydroelectric Power Plant'),
    ('AGUS6', 'Agus 6 Hydroelectric Power Plant'),
    ('AGUS7', 'Agus 7 Hydroelectric Power Plant'),
]

for code, new_name in plants_to_update:
    try:
        plant = Plant.objects.get(code=code)
        old_name = plant.name
        plant.name = new_name
        plant.save()
        print(f"✓ Updated {code}: '{old_name}' → '{new_name}'")
    except Plant.DoesNotExist:
        print(f"✗ Plant {code} not found")

print("\n✓ All plant names updated successfully!")
print("\nCurrent plants in database:")
for plant in Plant.objects.all():
    print(f"  - {plant.code}: {plant.name}")
