#!/usr/bin/env python3
"""
Test de Integridad Referencial y Seguridad Multi-tenant para TaxiFast

Pruebas:
1. Admin A no puede crear taxista con vehiculo_id de Org B
2. Admin A no puede filtrar turnos con taxista_id de Org B (400)
3. Admin A no puede filtrar servicios con empresa_id de Org B (400)
4. IDs inválidos no causan 500

Ejecución:
    BASE_URL="https://taxitineo.emergent.host/api" python3 integrity_reference_test.py

Variables de entorno opcionales:
    SUPERADMIN_USER=superadmin
    SUPERADMIN_PASS=superadmin123
"""

import os
import sys
import requests
import json
from typing import Optional, Tuple

# Configuración
BASE_URL = os.environ.get("BASE_URL", "https://taxitineo.emergent.host/api")
SUPERADMIN_USER = os.environ.get("SUPERADMIN_USER", "superadmin")
SUPERADMIN_PASS = os.environ.get("SUPERADMIN_PASS", "superadmin123")

# Colores para output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def log_pass(msg: str):
    print(f"{GREEN}✓ PASS:{RESET} {msg}")

def log_fail(msg: str):
    print(f"{RED}✗ FAIL:{RESET} {msg}")

def log_info(msg: str):
    print(f"{YELLOW}ℹ INFO:{RESET} {msg}")

def login(username: str, password: str) -> Optional[str]:
    """Obtener token de autenticación"""
    try:
        resp = requests.post(
            f"{BASE_URL}/auth/login",
            json={"username": username, "password": password},
            timeout=10
        )
        if resp.status_code == 200:
            return resp.json().get("access_token")
        return None
    except Exception as e:
        log_fail(f"Error en login: {e}")
        return None

def api_call(method: str, endpoint: str, token: str, data: dict = None) -> Tuple[int, dict]:
    """Hacer llamada API y retornar (status_code, response_json)"""
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            resp = requests.post(url, headers=headers, json=data, timeout=10)
        elif method == "PUT":
            resp = requests.put(url, headers=headers, json=data, timeout=10)
        elif method == "DELETE":
            resp = requests.delete(url, headers=headers, timeout=10)
        else:
            return (0, {"error": "Método no soportado"})
        
        try:
            return (resp.status_code, resp.json())
        except:
            return (resp.status_code, {"raw": resp.text})
    except Exception as e:
        return (0, {"error": str(e)})

def cleanup(token: str, org_ids: list, user_ids: list, vehiculo_ids: list, company_ids: list):
    """Limpiar datos de prueba"""
    log_info("Limpiando datos de prueba...")
    
    for uid in user_ids:
        api_call("DELETE", f"/superadmin/taxistas/{uid}", token)
    
    for vid in vehiculo_ids:
        api_call("DELETE", f"/superadmin/vehiculos/{vid}", token)
    
    for cid in company_ids:
        api_call("DELETE", f"/companies/{cid}", token)
    
    for oid in org_ids:
        api_call("DELETE", f"/organizations/{oid}", token)

def main():
    print("\n" + "="*60)
    print("TEST DE INTEGRIDAD REFERENCIAL - TaxiFast Multi-tenant")
    print("="*60 + "\n")
    
    # Datos para cleanup
    created_orgs = []
    created_users = []
    created_vehiculos = []
    created_companies = []
    
    tests_passed = 0
    tests_failed = 0
    
    # 1. Login como superadmin
    log_info(f"Conectando a {BASE_URL}...")
    superadmin_token = login(SUPERADMIN_USER, SUPERADMIN_PASS)
    if not superadmin_token:
        log_fail("No se pudo autenticar como superadmin")
        sys.exit(1)
    log_pass("Autenticado como superadmin")
    
    try:
        # 2. Crear dos organizaciones de prueba
        log_info("Creando organizaciones de prueba...")
        
        status, org_a = api_call("POST", "/organizations", superadmin_token, {
            "nombre": "Test Org A",
            "slug": "test-org-a-integrity",
            "activa": True
        })
        if status != 200:
            log_fail(f"No se pudo crear Org A: {org_a}")
            sys.exit(1)
        org_a_id = org_a.get("id")
        created_orgs.append(org_a_id)
        log_pass(f"Org A creada: {org_a_id}")
        
        status, org_b = api_call("POST", "/organizations", superadmin_token, {
            "nombre": "Test Org B",
            "slug": "test-org-b-integrity",
            "activa": True
        })
        if status != 200:
            log_fail(f"No se pudo crear Org B: {org_b}")
            cleanup(superadmin_token, created_orgs, created_users, created_vehiculos, created_companies)
            sys.exit(1)
        org_b_id = org_b.get("id")
        created_orgs.append(org_b_id)
        log_pass(f"Org B creada: {org_b_id}")
        
        # 3. Crear admins para cada org
        log_info("Creando admins de prueba...")
        
        status, admin_a = api_call("POST", f"/organizations/{org_a_id}/admin", superadmin_token, {
            "username": "test_admin_a_integrity",
            "password": "test123",
            "nombre": "Admin A Test"
        })
        if status != 200:
            log_fail(f"No se pudo crear Admin A: {admin_a}")
            cleanup(superadmin_token, created_orgs, created_users, created_vehiculos, created_companies)
            sys.exit(1)
        admin_a_id = admin_a.get("id")
        created_users.append(admin_a_id)
        log_pass(f"Admin A creado: {admin_a_id}")
        
        status, admin_b = api_call("POST", f"/organizations/{org_b_id}/admin", superadmin_token, {
            "username": "test_admin_b_integrity",
            "password": "test123",
            "nombre": "Admin B Test"
        })
        if status != 200:
            log_fail(f"No se pudo crear Admin B: {admin_b}")
            cleanup(superadmin_token, created_orgs, created_users, created_vehiculos, created_companies)
            sys.exit(1)
        admin_b_id = admin_b.get("id")
        created_users.append(admin_b_id)
        log_pass(f"Admin B creado: {admin_b_id}")
        
        # 4. Login como Admin A
        admin_a_token = login("test_admin_a_integrity", "test123")
        if not admin_a_token:
            log_fail("No se pudo autenticar como Admin A")
            cleanup(superadmin_token, created_orgs, created_users, created_vehiculos, created_companies)
            sys.exit(1)
        log_pass("Autenticado como Admin A")
        
        # 5. Crear vehículo en Org B (como superadmin)
        log_info("Creando vehículo en Org B...")
        status, vehiculo_b = api_call("POST", "/superadmin/vehiculos", superadmin_token, {
            "matricula": "TEST-ORG-B",
            "marca": "Test",
            "modelo": "Vehiculo B",
            "organization_id": org_b_id
        })
        if status != 200:
            log_fail(f"No se pudo crear vehículo en Org B: {vehiculo_b}")
            cleanup(superadmin_token, created_orgs, created_users, created_vehiculos, created_companies)
            sys.exit(1)
        vehiculo_b_id = vehiculo_b.get("id")
        created_vehiculos.append(vehiculo_b_id)
        log_pass(f"Vehículo en Org B creado: {vehiculo_b_id}")
        
        # 6. Crear taxista en Org B (como superadmin)
        log_info("Creando taxista en Org B...")
        status, taxista_b = api_call("POST", "/superadmin/taxistas", superadmin_token, {
            "username": "test_taxista_b_integrity",
            "password": "test123",
            "nombre": "Taxista B Test",
            "organization_id": org_b_id
        })
        if status != 200:
            log_fail(f"No se pudo crear taxista en Org B: {taxista_b}")
            cleanup(superadmin_token, created_orgs, created_users, created_vehiculos, created_companies)
            sys.exit(1)
        taxista_b_id = taxista_b.get("id")
        created_users.append(taxista_b_id)
        log_pass(f"Taxista en Org B creado: {taxista_b_id}")
        
        # 7. Crear empresa en Org B (como superadmin, necesitamos endpoint directo)
        log_info("Creando empresa en Org B...")
        # Usamos el token de admin B para crear empresa
        admin_b_token = login("test_admin_b_integrity", "test123")
        status, empresa_b = api_call("POST", "/companies", admin_b_token, {
            "nombre": "Empresa Test Org B",
            "cif": "B12345678",
            "email": "test@orgb.com"
        })
        if status == 200:
            empresa_b_id = empresa_b.get("id")
            created_companies.append(empresa_b_id)
            log_pass(f"Empresa en Org B creada: {empresa_b_id}")
        else:
            log_info(f"No se pudo crear empresa (puede ser normal): {empresa_b}")
            empresa_b_id = None
        
        print("\n" + "-"*60)
        print("EJECUTANDO TESTS DE SEGURIDAD")
        print("-"*60 + "\n")
        
        # ========================================
        # TEST 1: Admin A no puede crear taxista con vehiculo_id de Org B
        # ========================================
        log_info("TEST 1: Admin A intenta crear taxista con vehículo de Org B...")
        status, resp = api_call("POST", "/users", admin_a_token, {
            "username": "test_cross_tenant_user",
            "password": "test123",
            "nombre": "Cross Tenant Test",
            "role": "taxista",
            "vehiculo_id": vehiculo_b_id
        })
        
        if status == 400:
            # Cualquier 400 es correcto - el sistema rechazó la operación
            log_pass(f"TEST 1: Admin A rechazado al usar vehículo de Org B (400: {resp.get('detail', 'sin detalle')})")
            tests_passed += 1
        elif status == 200:
            log_fail("TEST 1: Admin A pudo crear taxista con vehículo de otra org!")
            # Limpiar el usuario creado
            if resp.get("id"):
                created_users.append(resp.get("id"))
            tests_failed += 1
        else:
            log_fail(f"TEST 1: Respuesta inesperada: {status} - {resp}")
            tests_failed += 1
        
        # ========================================
        # TEST 2: Admin A no puede filtrar turnos con taxista_id de Org B
        # ========================================
        log_info("TEST 2: Admin A intenta filtrar turnos por taxista de Org B...")
        status, resp = api_call("GET", f"/turnos?taxista_id={taxista_b_id}", admin_a_token)
        
        if status == 400:
            log_pass("TEST 2: Admin A rechazado al filtrar por taxista de Org B (400)")
            tests_passed += 1
        elif status == 200 and len(resp) == 0:
            log_fail("TEST 2: Se devolvió vacío en vez de 400 (comportamiento antiguo)")
            tests_failed += 1
        else:
            log_fail(f"TEST 2: Respuesta inesperada: {status} - {resp}")
            tests_failed += 1
        
        # ========================================
        # TEST 3: Admin A no puede filtrar servicios con empresa_id de Org B
        # ========================================
        if empresa_b_id:
            log_info("TEST 3: Admin A intenta filtrar servicios por empresa de Org B...")
            status, resp = api_call("GET", f"/services?empresa_id={empresa_b_id}", admin_a_token)
            
            if status == 400:
                log_pass("TEST 3: Admin A rechazado al filtrar por empresa de Org B (400)")
                tests_passed += 1
            elif status == 200 and len(resp) == 0:
                log_fail("TEST 3: Se devolvió vacío en vez de 400 (comportamiento antiguo)")
                tests_failed += 1
            else:
                log_fail(f"TEST 3: Respuesta inesperada: {status} - {resp}")
                tests_failed += 1
        else:
            log_info("TEST 3: Saltado (no se pudo crear empresa en Org B)")
        
        # ========================================
        # TEST 4: IDs inválidos no causan 500
        # ========================================
        log_info("TEST 4: IDs inválidos no causan 500...")
        
        # 4a. taxista_id inválido
        status, resp = api_call("GET", "/turnos?taxista_id=invalid_id", admin_a_token)
        if status == 400:
            log_pass("TEST 4a: taxista_id inválido retorna 400 (no 500)")
            tests_passed += 1
        elif status == 500:
            log_fail("TEST 4a: taxista_id inválido causa 500!")
            tests_failed += 1
        else:
            log_info(f"TEST 4a: Respuesta: {status}")
            tests_passed += 1  # Cualquier cosa que no sea 500 es aceptable
        
        # 4b. empresa_id inválido
        status, resp = api_call("GET", "/services?empresa_id=invalid_id", admin_a_token)
        if status == 400:
            log_pass("TEST 4b: empresa_id inválido retorna 400 (no 500)")
            tests_passed += 1
        elif status == 500:
            log_fail("TEST 4b: empresa_id inválido causa 500!")
            tests_failed += 1
        else:
            log_info(f"TEST 4b: Respuesta: {status}")
            tests_passed += 1
        
        # 4c. turno_id inválido
        status, resp = api_call("GET", "/services?turno_id=invalid_id", admin_a_token)
        if status == 400:
            log_pass("TEST 4c: turno_id inválido retorna 400 (no 500)")
            tests_passed += 1
        elif status == 500:
            log_fail("TEST 4c: turno_id inválido causa 500!")
            tests_failed += 1
        else:
            log_info(f"TEST 4c: Respuesta: {status}")
            tests_passed += 1
        
        # ========================================
        # TEST 5: Admin no puede crear otro admin
        # ========================================
        log_info("TEST 5: Admin A intenta crear otro admin...")
        status, resp = api_call("POST", "/users", admin_a_token, {
            "username": "test_admin_from_admin",
            "password": "test123",
            "nombre": "Admin Creado Por Admin",
            "role": "admin"
        })
        
        if status == 403:
            log_pass("TEST 5: Admin A no puede crear admin (403)")
            tests_passed += 1
        elif status == 200:
            log_fail("TEST 5: Admin A pudo crear otro admin!")
            if resp.get("id"):
                created_users.append(resp.get("id"))
            tests_failed += 1
        else:
            log_fail(f"TEST 5: Respuesta inesperada: {status} - {resp}")
            tests_failed += 1
        
        # ========================================
        # RESUMEN
        # ========================================
        print("\n" + "="*60)
        print("RESUMEN DE TESTS")
        print("="*60)
        print(f"{GREEN}Pasados: {tests_passed}{RESET}")
        print(f"{RED}Fallados: {tests_failed}{RESET}")
        print("="*60 + "\n")
        
    finally:
        # Cleanup
        cleanup(superadmin_token, created_orgs, created_users, created_vehiculos, created_companies)
        log_info("Limpieza completada")
    
    # Exit code
    sys.exit(0 if tests_failed == 0 else 1)

if __name__ == "__main__":
    main()
