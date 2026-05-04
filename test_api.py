#!/usr/bin/env python
"""
Test script to check the generate report API endpoint
"""

import os
import sys
import django
import requests
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'npc_reporting.settings')
django.setup()

def test_generate_report():
    """Test the generate report API endpoint"""
    url = 'http://localhost:8000/api/generation-reports/generate-report/'
    
    # Test data
    data = {
        'plant_codes': ['AGUS1', 'AGUS2', 'AGUS4', 'AGUS5', 'AGUS6', 'AGUS7', 'PULANGI4'],
        'start_date': '2026-03-11',
        'end_date': '2026-03-11',
        'report_type': 'psr'
    }
    
    print(f"Testing API endpoint: {url}")
    print(f"Request data: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, json=data, headers={'Content-Type': 'application/json'})
        
        print(f"\nResponse status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("SUCCESS: Report generated successfully")
            print(f"Content-Type: {response.headers.get('Content-Type')}")
            print(f"Content-Length: {len(response.content)} bytes")
        else:
            print("ERROR: Request failed")
            try:
                error_data = response.json()
                print(f"Error data: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Error text: {response.text}")
                
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to the server. Make sure Django is running on localhost:8000")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == '__main__':
    test_generate_report()