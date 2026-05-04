"""
Django management command to generate Daily Plant Status Report
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from reports.services.daily_status_exporter import generate_daily_status_report
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Generate Daily Plant Status Report in Excel format'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Report date (YYYY-MM-DD format, defaults to today)'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output file path (auto-generated if not specified)'
        )

    def handle(self, *args, **options):
        # Parse date
        if options['date']:
            try:
                report_date = datetime.strptime(options['date'], '%Y-%m-%d').date()
            except ValueError:
                self.stdout.write(self.style.ERROR('Invalid date format. Use YYYY-MM-DD'))
                return
        else:
            report_date = timezone.now().date()
        
        self.stdout.write(f"Generating Daily Plant Status Report for {report_date}...")
        
        try:
            # Generate report
            output_path = generate_daily_status_report(
                report_date=report_date,
                output_filename=options['output']
            )
            
            self.stdout.write(self.style.SUCCESS(f'\n✓ Report generated successfully!'))
            self.stdout.write(self.style.SUCCESS(f'✓ Saved to: {output_path}'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Failed to generate report: {str(e)}'))
            import traceback
            traceback.print_exc()
