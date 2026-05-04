#!/usr/bin/env python
"""
Test script to verify uploaded files API
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'npc_reporting.settings')
django.setup()

from reports.models import UploadedFile
from reports.serializers import UploadedFileSerializer

def test_uploaded_files():
    """Test uploaded files retrieval"""
    print("=" * 60)
    print("TESTING UPLOADED FILES API")
    print("=" * 60)
    
    # Get all uploaded files
    files = UploadedFile.objects.filter(is_archived=False).select_related('plant', 'uploaded_by').order_by('-uploaded_at')
    
    print(f"\nTotal uploaded files (not archived): {files.count()}")
    print(f"Total uploaded files (all): {UploadedFile.objects.count()}")
    
    print("\n" + "-" * 60)
    print("RECENT UPLOADS:")
    print("-" * 60)
    
    for file in files[:10]:
        print(f"\nID: {file.id}")
        print(f"Filename: {file.original_filename}")
        print(f"Plant: {file.plant.name if file.plant else 'None'}")
        print(f"Plant Code: {file.plant.code if file.plant else 'None'}")
        print(f"Status: {file.status}")
        print(f"Records Imported: {file.records_imported}")
        print(f"Uploaded At: {file.uploaded_at}")
        print(f"Uploaded By: {file.uploaded_by.username if file.uploaded_by else 'Anonymous'}")
        print(f"Is Archived: {file.is_archived}")
    
    print("\n" + "=" * 60)
    print("SERIALIZED DATA (API Response):")
    print("=" * 60)
    
    serializer = UploadedFileSerializer(files, many=True)
    import json
    print(json.dumps(serializer.data[:3], indent=2))

if __name__ == '__main__':
    test_uploaded_files()
