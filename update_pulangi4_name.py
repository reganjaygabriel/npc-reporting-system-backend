"""
Update Pulangi 4 plant name to include "Power" word
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'npc_reporting.settings')
django.setup()

from reports.models import Plant

print("=" * 60)
print("Updating Pulangi 4 Plant Name")
print("=" * 60)
print()

try:
    # Get Pulangi 4 plant
    plant = Plant.objects.get(code='PULANGI4')
    
    print(f"Current name: {plant.name}")
    
    # Update the name
    plant.name = 'Pulangi 4 Hydroelectric Power Plant'
    plant.save()
    
    print(f"Updated name: {plant.name}")
    print()
    print("✓ Successfully updated Pulangi 4 plant name!")
    print()
    
except Plant.DoesNotExist:
    print("✗ Error: Pulangi 4 plant not found in database")
    print("  Please run add_pulangi4.py first to add the plant")
    print()
    
except Exception as e:
    print()
    print("✗ Error updating Pulangi 4:")
    print(f"  {str(e)}")
    print()
    import traceback
    traceback.print_exc()
