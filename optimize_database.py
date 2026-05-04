#!/usr/bin/env python3
"""
Database optimization script for production deployment
Creates indexes for faster login and common queries
"""

import os
import django
from django.db import connection

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'npc_reporting.settings')
django.setup()

def create_performance_indexes():
    """Create indexes for better performance"""
    
    indexes = [
        # User authentication indexes (critical for login)
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_auth_user_username_active ON auth_user(username) WHERE is_active = true;",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_auth_user_email_active ON auth_user(email) WHERE is_active = true;",
        
        # Session indexes for faster session lookup
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_django_session_expire_date ON django_session(expire_date) WHERE expire_date > NOW();",
        
        # Common query indexes
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reports_plant_code ON reports_plant(code);",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reports_unit_plant ON reports_unit(plant_id);",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_generation_report_date ON reports_generationreport(report_date);",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_generation_plant_date ON reports_generationreport(plant_id, report_date);",
    ]
    
    with connection.cursor() as cursor:
        for index_sql in indexes:
            try:
                print(f"Creating index: {index_sql[:50]}...")
                cursor.execute(index_sql)
                print("✅ Success")
            except Exception as e:
                print(f"❌ Error: {e}")

def analyze_tables():
    """Update table statistics for better query planning"""
    
    tables = [
        'auth_user',
        'django_session', 
        'reports_plant',
        'reports_unit',
        'reports_generationreport'
    ]
    
    with connection.cursor() as cursor:
        for table in tables:
            try:
                cursor.execute(f"ANALYZE {table};")
                print(f"✅ Analyzed {table}")
            except Exception as e:
                print(f"❌ Error analyzing {table}: {e}")

if __name__ == "__main__":
    print("🚀 Starting database optimization...")
    create_performance_indexes()
    analyze_tables()
    print("✅ Database optimization complete!")