#!/usr/bin/env python
"""
Test script to verify login API works
"""
import requests
import json

API_BASE = "http://localhost:8000/api"

def test_login():
    """Test login via API"""
    print("=" * 60)
    print("Testing Login API")
    print("=" * 60)
    
    # Test data - using the admin superuser
    credentials = {
        "username": "admin",
        "password": "admin123"  # Password reset to admin123
    }
    
    print(f"\n1. Attempting login with username: {credentials['username']}")
    print(f"   POST {API_BASE}/auth/login/")
    
    try:
        response = requests.post(
            f"{API_BASE}/auth/login/",
            json=credentials,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\n   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
            print("\n   ✅ SUCCESS: Login successful!")
            print(f"   User: {data.get('user', {}).get('username')}")
            print(f"   Session ID: {data.get('session_id')}")
        else:
            print(f"   Response: {response.text}")
            print(f"\n   ❌ FAILED: {response.status_code}")
            
    except Exception as e:
        print(f"\n   ❌ ERROR: {str(e)}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_login()
