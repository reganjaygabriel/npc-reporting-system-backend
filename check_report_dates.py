#!/usr/bin/env python
"""
Check what report dates exist in the database
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'npc_reporting.settings')
django.setup()

from reports.models import GenerationReport, UploadedFile
from django.db.models import Count, Min, Max

def check_report_dates():
    """Check what report dates exist"""
    print("=" * 60)
    print("Checking Report Dates in Database")
    print("=" * 60)
    
    # Get all uploaded files
    print("\n1. Uploaded Files:")
    files = UploadedFile.objects.all().order_by('-uploaded_at')
    for f in files:
        print(f"   - {f.original_filename}")
        print(f"     Uploaded: {f.uploaded_at}")
        print(f"     Plant: {f.plant.code if f.plant else 'None'}")
        print(f"     Records: {f.records_imported}")
        print()
    
    # Get all generation reports
    print("\n2. Generation Reports by Date:")
    reports_by_date = GenerationReport.objects.values('report_date').annotate(
        count=Count('id'),
        plants=Count('plant', distinct=True)
    ).order_by('-report_date')
    
    if not reports_by_date:
        print("   No generation reports found!")
    else:
        for item in reports_by_date:
            print(f"   - {item['report_date']}: {item['count']} records, {item['plants']} plants")
    
    # Get date range
    print("\n3. Date Range:")
    date_range = GenerationReport.objects.aggregate(
        min_date=Min('report_date'),
        max_date=Max('report_date'),
        total=Count('id')
    )
    
    if date_range['min_date']:
        print(f"   Earliest: {date_range['min_date']}")
        print(f"   Latest: {date_range['max_date']}")
        print(f"   Total records: {date_range['total']}")
    else:
        print("   No records found")
    
    # Get reports by plant
    print("\n4. Reports by Plant:")
    reports_by_plant = GenerationReport.objects.values('plant__code', 'plant__name').annotate(
        count=Count('id'),
        min_date=Min('report_date'),
        max_date=Max('report_date')
    ).order_by('plant__code')
    
    for item in reports_by_plant:
        print(f"   - {item['plant__code']} ({item['plant__name']})")
        print(f"     Records: {item['count']}")
        print(f"     Date range: {item['min_date']} to {item['max_date']}")
    
    # Show sample records
    print("\n5. Sample Records (latest 10):")
    samples = GenerationReport.objects.select_related('plant', 'unit').order_by('-report_date', '-id')[:10]
    for r in samples:
        print(f"   - {r.report_date} | {r.plant.code} | Unit {r.unit.unit_number} | {r.generation_kwh} kWh")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    check_report_dates()
