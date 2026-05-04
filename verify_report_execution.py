"""
Verify ReportExecution model and database schema
"""
import os
import django
import sys

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'npc_reporting.settings')
django.setup()

from reports.models_scheduled import ReportExecution
from django.db import connection

print("=" * 60)
print("REPORT EXECUTION MODEL VERIFICATION")
print("=" * 60)

# Check model fields
print("\n1. Model Fields (from Python code):")
print("-" * 60)
for field in ReportExecution._meta.get_fields():
    print(f"  - {field.name}: {field.__class__.__name__}")

# Check database schema
print("\n2. Database Schema (actual table):")
print("-" * 60)
with connection.cursor() as cursor:
    cursor.execute("PRAGMA table_info(report_executions)")
    columns = cursor.fetchall()
    for col in columns:
        print(f"  - {col[1]}: {col[2]}")

# Check for problematic fields
print("\n3. Checking for problematic fields:")
print("-" * 60)
model_fields = [f.name for f in ReportExecution._meta.get_fields()]
if 'approved' in model_fields:
    print("  ❌ ERROR: 'approved' field found in model (should not exist)")
else:
    print("  ✅ OK: 'approved' field not in model")

if 'report_type' in model_fields:
    print("  ❌ ERROR: 'report_type' field found in model (should not exist)")
else:
    print("  ✅ OK: 'report_type' field not in model")

# Check database columns
with connection.cursor() as cursor:
    cursor.execute("PRAGMA table_info(report_executions)")
    db_columns = [col[1] for col in cursor.fetchall()]
    
if 'approved' in db_columns:
    print("  ❌ ERROR: 'approved' column found in database (should not exist)")
else:
    print("  ✅ OK: 'approved' column not in database")

if 'report_type' in db_columns:
    print("  ❌ ERROR: 'report_type' column found in database (should not exist)")
else:
    print("  ✅ OK: 'report_type' column not in database")

print("\n4. Expected Fields:")
print("-" * 60)
expected = [
    'id', 'scheduled_report', 'status', 'started_at', 'completed_at',
    'duration_seconds', 'file_path', 'file_size', 'records_processed',
    'error_message', 'recipients_sent', 'recipients_failed'
]
for field in expected:
    if field in model_fields:
        print(f"  ✅ {field}")
    else:
        print(f"  ❌ {field} (MISSING)")

print("\n" + "=" * 60)
print("DIAGNOSIS:")
print("=" * 60)

if 'approved' in model_fields or 'report_type' in model_fields:
    print("❌ PROBLEM: Python cache has old model definition")
    print("\nSOLUTION:")
    print("1. Run FIX_RUN_NOW_ERROR.bat to clear cache")
    print("2. Restart backend server")
else:
    print("✅ Model definition looks correct!")
    print("\nIf you still get errors, check:")
    print("1. Backend server logs for actual error")
    print("2. Make sure backend was restarted after clearing cache")

print("=" * 60)
