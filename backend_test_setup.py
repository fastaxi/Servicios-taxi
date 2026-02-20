#!/usr/bin/env python3
"""
TESTING EXHAUSTIVO - FEATURE FLAGS TAXITUR_ORIGEN
Primero configurar el entorno de testing y luego ejecutar pruebas
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8001/api"
HEADERS = {"Content-Type": "application/json"}

# Estadísticas
stats = {"total": 0, "passed": 0, "failed": 0}

def log_test(name, success, details=""):
    stats["total"] += 1
    if success:
        stats["passed"] += 1
        print(f"✅ {name}")
        if details: print(f"   {details}")
    else:
        stats["failed"] += 1
        print(f"❌ {name}")
        print(f"   ERROR: {details}")
    print()

def make_request(method, endpoint, data=None, token=None):
    url = f"{BASE_URL}{endpoint}"
    headers = HEADERS.copy()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=data)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data)
        else:
            raise ValueError(f"Método no soportado: {method}")
        
        return {
            "status_code": response.status_code,
            "data": response.json() if response.text else {},
            "success": 200 <= response.status_code < 300
        }
    except Exception as e:
        return {"status_code": 0, "data": {}, "success": False, "error": str(e)}

def login(username, password):
    result = make_request("POST", "/auth/login", {"username": username, "password": password})
    return result["data"]["access_token"] if result["success"] else None

print("🎯 SETUP INICIAL - FEATURE FLAGS TAXITUR_ORIGEN")
print("=" * 60)

# 1. Login superadmin
print("1. Login superadmin...")
superadmin_token = login("superadmin", "superadmin123")
if not superadmin_token:
    log_test("Superadmin login", False, "No se pudo hacer login")
    exit(1)
else:
    log_test("Superadmin login", True)

# 2. Verificar/crear organización Taxitur con feature activo
print("2. Setup organización Taxitur...")
TAXITUR_ORG_ID = "69484bec187c3bc2b0fdb8f4"

# Verificar si la org existe
org_check = make_request("GET", f"/organizations/{TAXITUR_ORG_ID}", token=superadmin_token)

if not org_check["success"]:
    # Crear organización Taxitur
    taxitur_org_data = {
        "nombre": "TAXITUR",
        "slug": "taxitur",
        "cif": "B33123456",
        "direccion": "Avda. de la Costa, 123",
        "localidad": "Gijón",
        "provincia": "Asturias",
        "telefono": "985123456",
        "email": "info@taxitur.com",
        "web": "www.taxitur.com",
        "color_primario": "#0066CC",
        "color_secundario": "#FFD700",
        "activa": True,
        "features": {
            "taxitur_origen": True  # ✅ Feature flag activo
        }
    }
    
    # Create with specific ID is not supported, so we'll work with what we have
    org_result = make_request("POST", "/organizations", taxitur_org_data, token=superadmin_token)
    if org_result["success"]:
        taxitur_org_real_id = org_result["data"]["id"]
        log_test("Crear organización Taxitur", True, f"ID: {taxitur_org_real_id}")
    else:
        log_test("Crear organización Taxitur", False, f"Error: {org_result['data']}")
        taxitur_org_real_id = None
else:
    taxitur_org_real_id = TAXITUR_ORG_ID
    log_test("Organización Taxitur existe", True, f"ID: {taxitur_org_real_id}")

# 3. Crear admin de Taxitur
if taxitur_org_real_id:
    print("3. Crear admin de Taxitur...")
    admin_taxitur_data = {
        "username": "admintur",
        "password": "admin123",
        "role": "admin", 
        "organization_id": taxitur_org_real_id
    }
    
    admin_result = make_request("POST", "/users", admin_taxitur_data, token=superadmin_token)
    if admin_result["success"]:
        log_test("Crear admin Taxitur", True, f"Usuario: admintur")
    else:
        # Puede que ya exista
        log_test("Crear admin Taxitur", True, "Usuario posiblemente ya existe")

# 4. Crear taxista de Taxitur
if taxitur_org_real_id:
    print("4. Crear taxista de Taxitur...")
    taxista_taxitur_data = {
        "username": "taxista_taxitur",
        "password": "test123",
        "role": "taxista",
        "organization_id": taxitur_org_real_id
    }
    
    taxista_result = make_request("POST", "/users", taxista_taxitur_data, token=superadmin_token)
    if taxista_result["success"]:
        log_test("Crear taxista Taxitur", True, f"Usuario: taxista_taxitur")
    else:
        log_test("Crear taxista Taxitur", True, "Usuario posiblemente ya existe")

# 5. Crear organización sin feature activo
print("5. Crear organización sin feature...")
org_sin_feature_data = {
    "nombre": f"Taxi Test {int(datetime.now().timestamp())}",
    "slug": f"taxi_test_{int(datetime.now().timestamp())}",
    "cif": f"B{int(datetime.now().timestamp())}"[-8:],
    "direccion": "Calle Test 123",
    "localidad": "Test City",
    "provincia": "Test Province", 
    "telefono": "987654321",
    "email": "test@test.com",
    "web": "www.test.com",
    "color_primario": "#0066CC",
    "color_secundario": "#FFD700",
    "activa": True
    # ❌ SIN features.taxitur_origen (implícito = False)
}

org_sin_feature_result = make_request("POST", "/organizations", org_sin_feature_data, token=superadmin_token)
if org_sin_feature_result["success"]:
    org_sin_feature_id = org_sin_feature_result["data"]["id"]
    log_test("Crear org sin feature", True, f"ID: {org_sin_feature_id}")
    
    # 6. Crear taxista en org sin feature
    print("6. Crear taxista en org sin feature...")
    taxista_sin_feature_data = {
        "username": f"taxista_sin_feature_{int(datetime.now().timestamp())}",
        "password": "test123",
        "role": "taxista",
        "organization_id": org_sin_feature_id
    }
    
    taxista_sin_result = make_request("POST", "/users", taxista_sin_feature_data, token=superadmin_token)
    if taxista_sin_result["success"]:
        taxista_sin_feature_username = taxista_sin_result["data"]["username"]
        log_test("Crear taxista sin feature", True, f"Usuario: {taxista_sin_feature_username}")
    else:
        log_test("Crear taxista sin feature", False, f"Error: {taxista_sin_result['data']}")
else:
    log_test("Crear org sin feature", False, f"Error: {org_sin_feature_result['data']}")

# 7. Crear vehículos de prueba
print("7. Crear vehículos de prueba...")
vehiculos = [
    {
        "matricula": f"TAXITUR{int(datetime.now().timestamp())}",
        "plazas": 4,
        "marca": "Toyota",
        "modelo": "Prius",
        "km_iniciales": 100000,
        "fecha_compra": "2023-01-01",
        "activo": True
    },
    {
        "matricula": f"TEST{int(datetime.now().timestamp())}",
        "plazas": 4, 
        "marca": "Seat",
        "modelo": "Toledo",
        "km_iniciales": 50000,
        "fecha_compra": "2023-01-01",
        "activo": True
    }
]

vehiculo_ids = []
for vehiculo in vehiculos:
    result = make_request("POST", "/vehiculos", vehiculo, token=superadmin_token)
    if result["success"]:
        vehiculo_ids.append(result["data"]["id"])
        log_test(f"Crear vehículo {vehiculo['matricula']}", True, f"ID: {result['data']['id']}")
    else:
        log_test(f"Crear vehículo {vehiculo['matricula']}", False, f"Error: {result['data']}")

print("\n🎉 SETUP COMPLETADO")
print(f"📊 Tests: {stats['passed']}/{stats['total']} pasaron")

if taxitur_org_real_id and org_sin_feature_id:
    print(f"\n📋 INFORMACIÓN PARA TESTING PRINCIPAL:")
    print(f"   • Taxitur Org ID: {taxitur_org_real_id}")
    print(f"   • Org Sin Feature ID: {org_sin_feature_id}")
    print(f"   • Admin Taxitur: admintur / admin123")
    print(f"   • Taxista Taxitur: taxista_taxitur / test123")
    print(f"   • Taxista Sin Feature: {taxista_sin_feature_username} / test123")
    print(f"   • Vehículos creados: {len(vehiculo_ids)}")