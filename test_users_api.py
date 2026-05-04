#!/usr/bin/env python
"""
Test the users API endpoint
"""
import requests

# Test GET /api/users/
print("Testing GET /api/users/")
response = requests.get('http://localhost:8000/api/users/')
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

# Test POST /api/users/ (create user)
print("\nTesting POST /api/users/ (create user)")
user_data = {
    'username': 'testuser123',
    'password': 'testpass123',
    'email': 'test@example.com',
    'first_name': 'Test',
    'last_name': 'User',
    'is_active': True
}
response = requests.post('http://localhost:8000/api/users/', json=user_data)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
