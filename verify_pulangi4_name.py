"""
Verify Pulangi 4 plant name
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'npc_reporting.settings')
django.setup()

from reports.models import Plant

print("=" * 60)
print("Verifying Pulangi 4 Plant Name")
print("=" * 60)
print()

try:
    plant = Plant.objects.get(code='PULANGI4')
    print(f"✓ Plant Code: {plant.code}")
    print(f"✓ Plant Name: {plant.name}")
    print(f"✓ Capacity: {plant.capacity_mw} MW")
    print(f"✓ Location: {plant.location}")
    print()
    
    if plant.name == 'Pulangi 4 Hydroelectric Power Plant':
        print("✓ SUCCESS! Plant name is correct!")
    else:
        print("✗ WARNING: Plant name is not updated yet")
        print(f"  Expected: Pulangi 4 Hydroelectric Power Plant")
        print(f"  Current: {plant.name}")
    
except Plant.DoesNotExist:
    print("✗ Error: Pulangi 4 plant not found in database")
    
except Exception as e:
    print(f"✗ Error: {str(e)}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)
