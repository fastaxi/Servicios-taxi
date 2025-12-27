#!/usr/bin/env python3
"""
Debug test to check specific failing endpoints
"""

import requests
import json
import os

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://secureobserve.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def test_invalid_login():
    """Test invalid login"""
    try:
        response = requests.post(f"{API_BASE}/auth/login", json={
            'username': 'invalid',
            'password': 'invalid'
        }, timeout=10)
        print(f"Invalid login test: Status {response.status_code}, Response: {response.text}")
        return response.status_code == 401
    except Exception as e:
        print(f"Invalid login test failed with exception: {e}")
        return False

def test_admin_login():
    """Test admin login and get token"""
    try:
        response = requests.post(f"{API_BASE}/auth/login", json={
            'username': 'admin',
            'password': 'admin123'
        }, timeout=10)
        if response.status_code == 200:
            data = response.json()
            token = data['access_token']
            print(f"Admin login successful, token: {token[:20]}...")
            return token
        else:
            print(f"Admin login failed: Status {response.status_code}, Response: {response.text}")
            return None
    except Exception as e:
        print(f"Admin login failed with exception: {e}")
        return None

def test_get_users(token):
    """Test GET users endpoint"""
    try:
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.get(f"{API_BASE}/users", headers=headers, timeout=10)
        print(f"GET users test: Status {response.status_code}")
        if response.status_code == 200:
            users = response.json()
            print(f"Found {len(users)} users")
            # Check if any user has password field
            has_passwords = any('password' in user for user in users)
            print(f"Users have password field: {has_passwords}")
        else:
            print(f"GET users failed: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"GET users failed with exception: {e}")
        return False

def test_duplicate_company(token):
    """Test duplicate company creation"""
    try:
        headers = {'Authorization': f'Bearer {token}'}
        
        # Create first company
        company_data = {
            'nombre': 'Test Company',
            'cif': 'B12345678',
            'direccion': 'Test Address',
            'localidad': 'Tineo',
            'provincia': 'Asturias',
            'numero_cliente': 'TEST123'
        }
        
        response1 = requests.post(f"{API_BASE}/companies", json=company_data, headers=headers, timeout=10)
        print(f"First company creation: Status {response1.status_code}")
        
        if response1.status_code == 200:
            company_id = response1.json()['id']
            
            # Try to create duplicate
            response2 = requests.post(f"{API_BASE}/companies", json=company_data, headers=headers, timeout=10)
            print(f"Duplicate company creation: Status {response2.status_code}, Response: {response2.text}")
            
            # Cleanup
            requests.delete(f"{API_BASE}/companies/{company_id}", headers=headers, timeout=10)
            
            return response2.status_code == 400
        else:
            print(f"First company creation failed: {response1.text}")
            return False
            
    except Exception as e:
        print(f"Duplicate company test failed with exception: {e}")
        return False

def main():
    print("🔍 DEBUG TESTING SPECIFIC FAILING ENDPOINTS")
    print("=" * 50)
    
    # Test invalid login
    print("\n1. Testing invalid login...")
    invalid_login_ok = test_invalid_login()
    print(f"Result: {'✅ PASS' if invalid_login_ok else '❌ FAIL'}")
    
    # Test admin login
    print("\n2. Testing admin login...")
    admin_token = test_admin_login()
    
    if admin_token:
        # Test GET users
        print("\n3. Testing GET users...")
        get_users_ok = test_get_users(admin_token)
        print(f"Result: {'✅ PASS' if get_users_ok else '❌ FAIL'}")
        
        # Test duplicate company
        print("\n4. Testing duplicate company...")
        duplicate_company_ok = test_duplicate_company(admin_token)
        print(f"Result: {'✅ PASS' if duplicate_company_ok else '❌ FAIL'}")
    else:
        print("❌ Cannot proceed without admin token")

if __name__ == "__main__":
    main()