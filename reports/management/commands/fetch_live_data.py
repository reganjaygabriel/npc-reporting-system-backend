"""
Django management command to fetch live data from NPC
"""

from django.core.management.base import BaseCommand
from reports.services.npc_live_data_client import get_npc_client
import json


class Command(BaseCommand):
    help = 'Fetch live plant data from NPC systems'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test',
            action='store_true',
            help='Test connection to NPC API'
        )
        parser.add_argument(
            '--plants',
            type=str,
            help='Comma-separated list of plant codes (e.g., AGUS1,AGUS2)'
        )
        parser.add_argument(
            '--sync',
            action='store_true',
            help='Sync fetched data to local database'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output file path (JSON format)'
        )

    def handle(self, *args, **options):
        client = get_npc_client()
        
        # Test connection
        if options['test']:
            self.stdout.write("Testing connection to NPC live data source...")
            result = client.test_connection()
            
            self.stdout.write("\n" + "=" * 70)
            self.stdout.write("CONNECTION TEST RESULTS")
            self.stdout.write("=" * 70)
            
            if result['success']:
                self.stdout.write(self.style.SUCCESS(f"✓ {result['message']}"))
            else:
                self.stdout.write(self.style.ERROR(f"✗ {result['message']}"))
            
            self.stdout.write("\nConfiguration Status:")
            for key, value in result['config_status'].items():
                status = "✓" if value else "✗"
                color = self.style.SUCCESS if value else self.style.WARNING
                self.stdout.write(color(f"  {status} {key}: {value}"))
            
            return
        
        # Fetch plant status
        self.stdout.write("Fetching live plant data from NPC...")
        
        plant_codes = None
        if options['plants']:
            plant_codes = [p.strip() for p in options['plants'].split(',')]
            self.stdout.write(f"Fetching data for plants: {', '.join(plant_codes)}")
        
        result = client.fetch_plant_status(plant_codes)
        
        if not result['success']:
            self.stdout.write(self.style.ERROR(f"✗ Failed to fetch data: {result['error']}"))
            return
        
        self.stdout.write(self.style.SUCCESS(f"✓ Successfully fetched data for {len(result['plants'])} plant(s)"))
        
        # Display results
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("LIVE PLANT DATA")
        self.stdout.write("=" * 70)
        
        for plant in result['plants']:
            self.stdout.write(f"\nPlant: {plant.get('plant_name')} ({plant.get('plant_code')})")
            self.stdout.write(f"  Capacity: {plant.get('capacity_mw')} MW")
            self.stdout.write(f"  Current Generation: {plant.get('current_generation_mw')} MW")
            if plant.get('water_level'):
                self.stdout.write(f"  Water Level: {plant.get('water_level')}")
            self.stdout.write(f"  Status: {plant.get('status')}")
            self.stdout.write(f"  Timestamp: {plant.get('timestamp')}")
        
        # Sync to database
        if options['sync']:
            self.stdout.write("\nSyncing data to local database...")
            sync_result = client.sync_to_database(result['plants'])
            
            if sync_result['success']:
                self.stdout.write(self.style.SUCCESS(
                    f"✓ Synced {sync_result['synced_count']} plant(s)"
                ))
            
            if sync_result['failed_count'] > 0:
                self.stdout.write(self.style.WARNING(
                    f"⚠ Failed to sync {sync_result['failed_count']} plant(s)"
                ))
                for error in sync_result['errors']:
                    self.stdout.write(self.style.ERROR(f"  - {error}"))
        
        # Save to file
        if options['output']:
            try:
                with open(options['output'], 'w') as f:
                    json.dump(result, f, indent=2)
                self.stdout.write(self.style.SUCCESS(f"\n✓ Data saved to: {options['output']}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"\n✗ Failed to save file: {str(e)}"))
