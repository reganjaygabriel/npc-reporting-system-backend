import os
import django
import random
from datetime import date

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'npc_reporting.settings')
django.setup()

from reports.models import Plant, Unit, GenerationReport, UploadedFile

def generate_sample_data():
    today = date.today()
    plant_codes = ['AGUS1', 'AGUS2', 'AGUS4', 'AGUS5', 'AGUS6', 'AGUS7', 'PULANGI4']
    
    plants = Plant.objects.filter(code__in=plant_codes, is_active=True)
    if not plants.exists():
        print("No active plants found matching the codes.")
        return
        
    created_count = 0
    updated_count = 0
    
    for plant in plants:
        # Create a dummy uploaded file per plant to satisfy constraints
        dummy_file, _ = UploadedFile.objects.get_or_create(
            file=f'uploads/dummy_sample_{plant.code}_for_today.xlsx',
            defaults={
                'status': 'COMPLETED', 
                'file_size': 1024, 
                'original_filename': f'dummy_sample_{plant.code}_for_today.xlsx',
                'plant': plant
            }
        )
        
        units = Unit.objects.filter(plant=plant)
        for unit in units:
            unit.is_active = True
            unit.save()
            
            # Generate some plausible dummy data
            operating_hours = round(random.uniform(12.0, 24.0), 2)
            availability_hours = round(random.uniform(operating_hours, 24.0), 2)
            forced_outage_hours = round(24.0 - availability_hours, 2)
            scheduled_outage_hours = 0.0
            
            # Max possible generation based on unit capacity (if available) or generic
            capacity_kw = float(unit.capacity_mw) * 1000 if hasattr(unit, 'capacity_mw') and unit.capacity_mw else 50000.0
            generation_kwh = round(random.uniform(0.3, 0.9) * capacity_kw * operating_hours, 2)
            
            # Create or update the report for today
            report, created = GenerationReport.objects.update_or_create(
                plant=plant,
                unit=unit,
                report_date=today,
                defaults={
                    'uploaded_file': dummy_file,
                    'generation_kwh': generation_kwh,
                    'operating_hours': operating_hours,
                    'availability_hours': availability_hours,
                    'forced_outage_hours': forced_outage_hours,
                    'scheduled_outage_hours': scheduled_outage_hours,
                    'remarks': 'Sample data generated for testing'
                }
            )
            
            if created:
                created_count += 1
            else:
                updated_count += 1

    print(f"Sample data generation complete for {today}.")
    print(f"Created: {created_count} records.")
    print(f"Updated: {updated_count} records.")

if __name__ == '__main__':
    generate_sample_data()
