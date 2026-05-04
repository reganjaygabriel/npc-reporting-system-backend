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

try:
    from django.apps import apps
    from django.db import connection
    
    print(f"Connected to DB: {connection.settings_dict['NAME']}")
    
    # Just try to get count of users
    User = apps.get_model('auth', 'User')
    print(f"Number of users: {User.objects.count()}")
    
    Plant = apps.get_model('reports', 'Plant')
    print(f"Number of plants: {Plant.objects.count()}")
    
except Exception as e:
    print(f"Error reading models: {e}")
finally:
    # Restore original database settings
    settings.DATABASES = original_databases
