"""
Management command to verify all plants have their units configured
"""
from django.core.management.base import BaseCommand
from reports.models import Plant, Unit


class Command(BaseCommand):
    help = 'Verify all plants have their units configured'

    def handle(self, *args, **options):
        plants = Plant.objects.filter(is_active=True).order_by('code')
        
        self.stdout.write(self.style.SUCCESS('Plant Units Configuration:'))
        self.stdout.write('=' * 70)
        
        for plant in plants:
            units = Unit.objects.filter(plant=plant, is_active=True).order_by('unit_number')
            unit_numbers = [u.unit_number for u in units]
            
            self.stdout.write(f'\n{plant.code} - {plant.name}')
            self.stdout.write(f'  Total Capacity: {plant.capacity_mw} MW')
            self.stdout.write(f'  Units: {unit_numbers} ({len(units)} units)')
            
            for unit in units:
                self.stdout.write(f'    Unit {unit.unit_number}: {unit.capacity_mw} MW')
        
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('Verification complete!'))
