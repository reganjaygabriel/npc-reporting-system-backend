"""
Django management command to get current plant status from database
This provides an alternative to web scraping when real-time web data is not available
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from reports.models import GenerationReport, Plant
import json
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Get current plant status from database (alternative to web scraping)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=1,
            help='Number of days to look back for latest data (default: 1)'
        )
        parser.add_argument(
            '--format',
            type=str,
            default='json',
            choices=['json', 'text', 'csv'],
            help='Output format (default: json)'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output file path (optional, prints to console if not specified)'
        )

    def handle(self, *args, **options):
        days = options['days']
        output_format = options['format']
        output_file = options['output']
        
        # Get date range
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        self.stdout.write(f"Fetching plant status from {start_date} to {end_date}...")
        
        # Get all plants
        plants = Plant.objects.all().order_by('name')
        
        if not plants.exists():
            self.stdout.write(self.style.ERROR('No plants found in database'))
            return
        
        # Collect plant status data
        plants_data = []
        
        for plant in plants:
            # Get latest reports for this plant (all units)
            latest_reports = GenerationReport.objects.filter(
                plant=plant,
                report_date__gte=start_date,
                report_date__lte=end_date
            ).order_by('-report_date', '-created_at')
            
            if latest_reports.exists():
                # Get the most recent date
                latest_date = latest_reports.first().report_date
                
                # Get all reports for that date
                day_reports = latest_reports.filter(report_date=latest_date)
                
                # Aggregate generation for all units
                total_generation = sum(float(r.generation_kwh) for r in day_reports) / 1000  # Convert to MWh
                
                # Get remarks from first report
                remarks = day_reports.first().remarks or 'Normal operation'
                
                # Determine status based on generation
                generation_status = 'OPERATIONAL' if total_generation > 0 else 'OFFLINE'
                
                plant_info = {
                    'plant_name': plant.name,
                    'plant_code': plant.code,
                    'capacity_mw': float(plant.capacity_mw),
                    'date': latest_date.isoformat(),
                    'generation_mwh': round(total_generation, 2),
                    'water_level': None,  # Not available in GenerationReport
                    'generation_status': generation_status,
                    'units_count': day_reports.count(),
                    'remarks': remarks,
                    'timestamp': day_reports.first().created_at.isoformat()
                }
            else:
                # No recent data
                plant_info = {
                    'plant_name': plant.name,
                    'plant_code': plant.code,
                    'capacity_mw': float(plant.capacity_mw),
                    'date': None,
                    'generation_mwh': None,
                    'water_level': None,
                    'generation_status': 'NO DATA',
                    'units_count': 0,
                    'remarks': f'No data available for the last {days} day(s)',
                    'timestamp': timezone.now().isoformat()
                }
            
            plants_data.append(plant_info)
        
        # Create result object
        result = {
            'success': True,
            'source': 'database',
            'timestamp': timezone.now().isoformat(),
            'date_range': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'plants_count': len(plants_data),
            'plants': plants_data
        }
        
        # Format output
        if output_format == 'json':
            output = json.dumps(result, indent=2, ensure_ascii=False)
        elif output_format == 'text':
            output = self._format_text(result)
        elif output_format == 'csv':
            output = self._format_csv(plants_data)
        
        # Write output
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(output)
                self.stdout.write(self.style.SUCCESS(f'✓ Output saved to: {output_file}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'✗ Failed to save output: {str(e)}'))
        else:
            self.stdout.write(output)
        
        # Summary
        operational_count = sum(1 for p in plants_data if p['generation_status'] == 'OPERATIONAL')
        self.stdout.write(self.style.SUCCESS(f'\n✓ Found {len(plants_data)} plants'))
        self.stdout.write(self.style.SUCCESS(f'✓ {operational_count} operational, {len(plants_data) - operational_count} offline/no data'))

    def _format_text(self, result):
        """Format output as human-readable text"""
        lines = []
        lines.append("=" * 70)
        lines.append("PLANT STATUS REPORT")
        lines.append("=" * 70)
        lines.append(f"Source: {result['source']}")
        lines.append(f"Timestamp: {result['timestamp']}")
        lines.append(f"Date Range: {result['date_range']['start']} to {result['date_range']['end']}")
        lines.append(f"Total Plants: {result['plants_count']}")
        lines.append("=" * 70)
        lines.append("")
        
        for plant in result['plants']:
            lines.append(f"Plant: {plant['plant_name']} ({plant['plant_code']})")
            lines.append(f"  Capacity: {plant['capacity_mw']} MW")
            lines.append(f"  Status: {plant['generation_status']}")
            if plant['generation_mwh'] is not None:
                lines.append(f"  Generation: {plant['generation_mwh']} MWh")
                lines.append(f"  Units Reporting: {plant['units_count']}")
            lines.append(f"  Remarks: {plant['remarks']}")
            lines.append(f"  Last Updated: {plant['timestamp']}")
            lines.append("")
        
        return "\n".join(lines)

    def _format_csv(self, plants_data):
        """Format output as CSV"""
        lines = []
        lines.append("Plant Name,Plant Code,Capacity (MW),Date,Generation (MWh),Units Count,Status,Remarks,Timestamp")
        
        for plant in plants_data:
            lines.append(
                f'"{plant["plant_name"]}",'
                f'"{plant["plant_code"]}",'
                f'{plant["capacity_mw"]},'
                f'"{plant["date"] or ""}",'
                f'{plant["generation_mwh"] or ""},'
                f'{plant["units_count"]},'
                f'"{plant["generation_status"]}",'
                f'"{plant["remarks"]}",'
                f'"{plant["timestamp"]}"'
            )
        
        return "\n".join(lines)
