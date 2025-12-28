#!/usr/bin/env python3
"""
Debug test to understand specific error messages
"""

import requests
import json

BASE_URL = "https://taxiflow-18.preview.emergentagent.com/api"

def login(username, password):
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "username": username,
        "password": password
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Login failed for {username}: {response.status_code} - {response.text}")
        return None

def test_service_creation():
    # Login taxista_tineo
    token = login("taxista_tineo", "test123")
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test creating a service
    service_data = {
        "fecha": "15/12/2024",
        "hora": "15:00",
        "origen": "Tineo",
        "destino": "Grado",
        "importe": 18.50,
        "importe_espera": 0,
        "kilometros": 15.0,
        "tipo": "particular",
        "metodo_pago": "efectivo"
    }
    
    print("Testing service creation...")
    print(f"Data: {json.dumps(service_data, indent=2)}")
    
    response = requests.post(f"{BASE_URL}/services", json=service_data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code != 200 and response.status_code != 201:
        print("Service creation failed!")
    else:
        print("Service creation successful!")

if __name__ == "__main__":
    test_service_creation()