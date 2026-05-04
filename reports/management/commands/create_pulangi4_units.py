"""
Management command to create units for PULANGI4 plant
"""
from django.core.management.base import BaseCommand
from reports.models import Plant, Unit


class Command(BaseCommand):
    help = 'Create units for PULANGI4 plant'

    def handle(self, *args, **options):
        try:
            plant = Plant.objects.get(code='PULANGI4')
            self.stdout.write(f'Found plant: {plant.name} ({plant.code})')
            
            # PULANGI4 has 4 units, each 70 MW
            units_config = [
                {'unit_number': 1, 'capacity_mw': 70.00},
                {'unit_number': 2, 'capacity_mw': 70.00},
                {'unit_number': 3, 'capacity_mw': 70.00},
                {'unit_number': 4, 'capacity_mw': 70.00},
            ]
            
            created_count = 0
            updated_count = 0
            
            for config in units_config:
                unit, created = Unit.objects.get_or_create(
                    plant=plant,
                    unit_number=config['unit_number'],
                    defaults={
                        'capacity_mw': config['capacity_mw'],
                        'is_active': True
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Created Unit {unit.unit_number} - {unit.capacity_mw} MW'
                        )
                    )
                else:
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'Unit {unit.unit_number} already exists'
                        )
                    )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nSummary: {created_count} units created, {updated_count} already existed'
                )
            )
            
        except Plant.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('PULANGI4 plant not found in database!')
            )
