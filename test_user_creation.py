#!/usr/bin/env python
"""
Test script to verify user creation API works
"""
import requests
import json

API_BASE = "http://localhost:8000/api"

def test_user_creation():
    """Test creating a user via API"""
    print("=" * 60)
    print("Testing User Creation API")
    print("=" * 60)
    
    # Test data
    user_data = {
        "username": "testuser123",
        "password": "testpass123",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "is_active": True,
        "role": "VIEWER"
    }
    
    print(f"\n1. Creating user: {user_data['username']}")
    print(f"   POST {API_BASE}/users/")
    
    try:
        response = requests.post(
            f"{API_BASE}/users/",
            json=user_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\n   Status Code: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 201:
            print("\n   ✅ SUCCESS: User created!")
        else:
            print(f"\n   ❌ FAILED: {response.status_code}")
            
    except Exception as e:
        print(f"\n   ❌ ERROR: {str(e)}")
    
    # Test listing users
    print(f"\n2. Listing all users")
    print(f"   GET {API_BASE}/users/")
    
    try:
        response = requests.get(f"{API_BASE}/users/")
        print(f"\n   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            users = data.get('results', [])
            print(f"   Total users: {len(users)}")
            for user in users:
                print(f"   - {user['username']} ({user.get('email', 'no email')})")
            print("\n   ✅ SUCCESS: Users listed!")
        else:
            print(f"\n   ❌ FAILED: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"\n   ❌ ERROR: {str(e)}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_user_creation()
