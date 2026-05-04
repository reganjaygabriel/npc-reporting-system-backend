"""
Django management command to import historical data from Excel files

Usage:
    python manage.py import_historical_data --capacity path/to/capacity.xlsx --historical path/to/historical.xlsx
"""

from django.core.management.base import BaseCommand, CommandError
from reports.services.historical_data_importer import HistoricalDataImporter
import os


class Command(BaseCommand):
    help = 'Import historical data from Excel files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--capacity',
            type=str,
            help='Path to plant capacity Excel file (0PLANT DEPCAP.xlsx)',
        )
        parser.add_argument(
            '--historical',
            type=str,
            help='Path to historical data Excel file (1DATA APAO.xlsx)',
        )

    def handle(self, *args, **options):
        capacity_file = options.get('capacity')
        historical_file = options.get('historical')

        if not capacity_file and not historical_file:
            raise CommandError('At least one file must be specified (--capacity or --historical)')

        # Validate files exist
        if capacity_file and not os.path.exists(capacity_file):
            raise CommandError(f'Capacity file not found: {capacity_file}')
        
        if historical_file and not os.path.exists(historical_file):
            raise CommandError(f'Historical file not found: {historical_file}')

        importer = HistoricalDataImporter()
        
        self.stdout.write(self.style.WARNING('Starting import...'))
        
        results = {}
        
        # Import capacity data
        if capacity_file:
            self.stdout.write(f'Importing plant capacity from: {capacity_file}')
            results['capacity'] = importer.import_plant_capacity(capacity_file)
            
            if results['capacity']['success']:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Imported {results['capacity']['imported']} capacity records"
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"✗ Failed to import capacity: {results['capacity'].get('error')}"
                    )
                )
            
            if results['capacity'].get('errors'):
                self.stdout.write(self.style.WARNING('Errors:'))
                for error in results['capacity']['errors']:
                    self.stdout.write(f"  - {error}")
        
        # Import historical data
        if historical_file:
            self.stdout.write(f'Importing historical data from: {historical_file}')
            results['historical'] = importer.import_historical_data(historical_file)
            
            if results['historical']['success']:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Imported {results['historical']['imported']} historical records"
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"✗ Failed to import historical data: {results['historical'].get('error')}"
                    )
                )
            
            if results['historical'].get('errors'):
                self.stdout.write(self.style.WARNING('Errors:'))
                for error in results['historical']['errors'][:10]:  # Show first 10
                    self.stdout.write(f"  - {error}")
                if len(results['historical']['errors']) > 10:
                    self.stdout.write(f"  ... and {len(results['historical']['errors']) - 10} more")
            
            if results['historical'].get('warnings'):
                self.stdout.write(self.style.WARNING('Warnings:'))
                for warning in results['historical']['warnings'][:10]:  # Show first 10
                    self.stdout.write(f"  - {warning}")
                if len(results['historical']['warnings']) > 10:
                    self.stdout.write(f"  ... and {len(results['historical']['warnings']) - 10} more")
        
        # Summary
        total_imported = sum(r.get('imported', 0) for r in results.values())
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Import complete! Total records imported: {total_imported}'
            )
        )
