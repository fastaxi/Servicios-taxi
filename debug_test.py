#!/usr/bin/env python3
"""
Debug specific failing tests
"""

import requests
import json

BASE_URL = "https://flagged-services.preview.emergentagent.com/api"

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

def debug_combustible():
    print("=== DEBUGGING COMBUSTIBLE ===")
    token = login("taxista_tineo", "test123")
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    turno_id = "6951247a58935fb953225445"
    
    # Check if turno exists and is active
    response = requests.get(f"{BASE_URL}/turnos/activo", headers=headers)
    print(f"Active turno check: {response.status_code} - {response.text}")
    
    # Try combustible update
    combustible_data = {
        "repostado": True,
        "litros": 45.0,
        "vehiculo_id": "6951247958935fb953225441",  # TEST-TINEO
        "km_vehiculo": 100050
    }
    
    response = requests.put(f"{BASE_URL}/turnos/{turno_id}/combustible", json=combustible_data, headers=headers)
    print(f"Combustible update: {response.status_code} - {response.text}")

def debug_turno_creation():
    print("\n=== DEBUGGING TURNO CREATION ===")
    token = login("taxista_tineo", "test123")
    if not token:
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    turno_data = {
        "taxista_id": "test_taxista_id",
        "taxista_nombre": "Test Taxista",
        "vehiculo_id": "6951247958935fb953225441",
        "vehiculo_matricula": "TEST-TINEO",
        "fecha_inicio": "15/12/2024",
        "hora_inicio": "99:99",  # Hora inválida, debería usar hora del servidor
        "km_inicio": 100200
    }
    
    print(f"Turno data: {json.dumps(turno_data, indent=2)}")
    
    response = requests.post(f"{BASE_URL}/turnos", json=turno_data, headers=headers)
    print(f"Turno creation: {response.status_code} - {response.text}")

if __name__ == "__main__":
    debug_combustible()
    debug_turno_creation()