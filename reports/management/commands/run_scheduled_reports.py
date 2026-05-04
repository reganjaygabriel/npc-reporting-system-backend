from django.core.management.base import BaseCommand
from django.utils import timezone
from reports.services.automated_reports import AutomatedReportService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run scheduled reports that are due'

    def add_arguments(self, parser):
        parser.add_argument(
            '--report-id',
            type=int,
            help='Run specific report by ID',
        )

    def handle(self, *args, **options):
        service = AutomatedReportService()
        
        if options['report_id']:
            # Run specific report
            from reports.models_scheduled import ScheduledReport
            try:
                report = ScheduledReport.objects.get(id=options['report_id'])
                self.stdout.write(f"Running report: {report.name}")
                
                success = service.execute_report(report)
                
                if success:
                    self.stdout.write(self.style.SUCCESS(f"Report executed successfully"))
                else:
                    self.stdout.write(self.style.ERROR(f"Report execution failed"))
                    
            except ScheduledReport.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Report with ID {options['report_id']} not found"))
        else:
            # Run all due reports
            due_reports = service.get_due_reports()
            
            if not due_reports.exists():
                self.stdout.write("No reports due to run")
                return
            
            self.stdout.write(f"Found {due_reports.count()} reports to run")
            
            for report in due_reports:
                self.stdout.write(f"Running: {report.name}")
                
                try:
                    success = service.execute_report(report)
                    
                    if success:
                        self.stdout.write(self.style.SUCCESS(f"  ✓ Completed"))
                    else:
                        self.stdout.write(self.style.ERROR(f"  ✗ Failed"))
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  ✗ Error: {str(e)}"))
                    logger.error(f"Report execution error: {str(e)}")
            
            self.stdout.write(self.style.SUCCESS(f"\nCompleted processing {due_reports.count()} reports"))
