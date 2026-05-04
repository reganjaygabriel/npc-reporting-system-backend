#!/usr/bin/env python
"""
Test script to verify user list shows all users including newly created ones
"""
import requests
import json

API_BASE = "http://localhost:8000/api"

def test_user_list():
    """Test user list and creation"""
    print("=" * 60)
    print("Testing User List")
    print("=" * 60)
    
    # 1. Get current user count
    print("\n1. Getting current user list...")
    response = requests.get(f"{API_BASE}/users/")
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        users = data.get('results', [])
        print(f"   Current users: {len(users)}")
        for user in users:
            print(f"   - {user['username']} ({user.get('email', 'no email')})")
        initial_count = len(users)
    else:
        print(f"   ERROR: {response.text}")
        return
    
    # 2. Create a new user
    print(f"\n2. Creating a new test user...")
    new_user = {
        "username": f"testuser_{len(users) + 1}",
        "password": "testpass123",
        "email": f"test{len(users) + 1}@example.com",
        "first_name": "Test",
        "last_name": f"User {len(users) + 1}",
        "is_active": True,
        "role": "VIEWER"
    }
    
    response = requests.post(f"{API_BASE}/users/", json=new_user)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 201:
        print(f"   ✅ User created: {new_user['username']}")
    else:
        print(f"   ❌ Failed: {response.text}")
        return
    
    # 3. Get updated user list
    print(f"\n3. Getting updated user list...")
    response = requests.get(f"{API_BASE}/users/")
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        users = data.get('results', [])
        print(f"   Updated users: {len(users)}")
        for user in users:
            print(f"   - {user['username']} ({user.get('email', 'no email')})")
        
        if len(users) > initial_count:
            print(f"\n   ✅ SUCCESS: New user appears in list!")
            print(f"   Initial count: {initial_count}, New count: {len(users)}")
        else:
            print(f"\n   ❌ FAILED: User count didn't increase!")
            print(f"   Initial count: {initial_count}, New count: {len(users)}")
    else:
        print(f"   ERROR: {response.text}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_user_list()
