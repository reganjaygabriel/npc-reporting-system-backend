#!/usr/bin/env python
"""
Test script to verify user update (role change) works
"""
import requests
import json

API_BASE = "http://localhost:8000/api"

def test_user_update():
    """Test updating a user's role"""
    print("=" * 60)
    print("Testing User Update (Role Change)")
    print("=" * 60)
    
    # 1. Get user list
    print("\n1. Getting user list...")
    response = requests.get(f"{API_BASE}/users/")
    
    if response.status_code != 200:
        print(f"   ERROR: {response.text}")
        return
    
    users = response.json().get('results', [])
    if not users:
        print("   No users found!")
        return
    
    # Find a test user (not admin)
    test_user = None
    for user in users:
        if user['username'] not in ['admin', 'admin123']:
            test_user = user
            break
    
    if not test_user:
        print("   No test user found, creating one...")
        create_response = requests.post(f"{API_BASE}/users/", json={
            "username": "roletest",
            "password": "test123",
            "email": "roletest@example.com",
            "is_active": True,
            "role": "VIEWER"
        })
        if create_response.status_code == 201:
            test_user = create_response.json()
            test_user['id'] = test_user['id']
            test_user['profile'] = {'role': 'VIEWER'}
            print(f"   Created test user: {test_user['username']}")
        else:
            print(f"   Failed to create test user: {create_response.text}")
            return
    
    print(f"   Using test user: {test_user['username']} (ID: {test_user['id']})")
    print(f"   Current role: {test_user.get('profile', {}).get('role', 'VIEWER')}")
    
    # 2. Update user role
    new_role = 'MANAGER' if test_user.get('profile', {}).get('role') != 'MANAGER' else 'OPERATOR'
    print(f"\n2. Updating user role to: {new_role}")
    
    update_data = {
        "username": test_user['username'],
        "email": test_user.get('email', ''),
        "first_name": test_user.get('first_name', ''),
        "last_name": test_user.get('last_name', ''),
        "is_active": test_user.get('is_active', True),
        "role": new_role
    }
    
    response = requests.put(
        f"{API_BASE}/users/{test_user['id']}/",
        json=update_data
    )
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        print(f"\n   ✅ SUCCESS: User role updated to {new_role}!")
    else:
        print(f"   ❌ FAILED: {response.text}")
        return
    
    # 3. Verify the update
    print(f"\n3. Verifying the update...")
    response = requests.get(f"{API_BASE}/users/")
    
    if response.status_code == 200:
        users = response.json().get('results', [])
        updated_user = next((u for u in users if u['id'] == test_user['id']), None)
        
        if updated_user:
            current_role = updated_user.get('profile', {}).get('role', 'VIEWER')
            print(f"   Updated role: {current_role}")
            
            if current_role == new_role:
                print(f"\n   ✅ VERIFICATION SUCCESS: Role changed to {new_role}!")
            else:
                print(f"\n   ❌ VERIFICATION FAILED: Role is still {current_role}")
        else:
            print(f"   ❌ User not found in list")
    else:
        print(f"   ERROR: {response.text}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_user_update()
