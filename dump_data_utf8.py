import os
import sys
import json
from django.core.management import call_command
from django.conf import settings
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'npc_reporting.settings')
django.setup()

# Temporarily switch to the correct SQLite database (the one with data)
original_databases = settings.DATABASES
settings.DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': r'C:\Users\eladiong\Desktop\OJT Intern_v2\npc-reporting-system\backend\db.sqlite3',
    }
}

output_file = 'data_full.json'

try:
    with open(output_file, 'w', encoding='utf-8') as f:
        call_command('dumpdata', stdout=f, indent=2, exclude=['auth.permission', 'contenttypes', 'sessions', 'admin.logentry'])
    print(f"Successfully dumped FULL data to {output_file}")
except Exception as e:
    print(f"Error dumping data: {e}")
finally:
    # Restore original database settings
    settings.DATABASES = original_databases
