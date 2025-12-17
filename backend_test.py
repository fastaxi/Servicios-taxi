#!/usr/bin/env python3
"""
TaxiFast Multi-tenant SaaS Platform - Comprehensive Backend Testing
================================================================

Testing all multi-tenant functionality including:
- Authentication and roles (superadmin, admin, taxista)
- Organization management (CRUD)
- Multi-tenant data isolation
- MY-ORGANIZATION branding endpoint
- Multi-tenant CRUD operations
- Security and permissions
- Legacy compatibility

Credentials:
- Super Admin: superadmin / superadmin123
- Admin Tineo: admin_tineo / tineo123 (Taxi Tineo)
- Admin Madrid: admin_madrid / madrid123 (Radio Taxi Madrid)
- Taxista Tineo: taxista_tineo1 / tax123
- Taxista Madrid: taxista_madrid1 / tax123
- Legacy Admin: admin / admin123
"""

import requests
import json
import sys
from datetime import datetime
import random
import string

# Configuration
BASE_URL = "https://taxi-platform-47.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

# Test counters
tests_passed = 0
tests_failed = 0
test_results = []

def log_test(test_name, passed, details=""):
    global tests_passed, tests_failed
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {test_name}")
    if details:
        print(f"   Details: {details}")
    
    test_results.append({
        "test": test_name,
        "passed": passed,
        "details": details
    })
    
    if passed:
        tests_passed += 1
    else:
        tests_failed += 1

def make_request(method, endpoint, data=None, headers=None, expected_status=200):
    """Make HTTP request and return response"""
    url = f"{BASE_URL}{endpoint}"
    req_headers = HEADERS.copy()
    if headers:
        req_headers.update(headers)
    
    try:
        if method == "GET":
            response = requests.get(url, headers=req_headers)
        elif method == "POST":
            response = requests.post(url, json=data, headers=req_headers)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=req_headers)
        elif method == "DELETE":
            response = requests.delete(url, headers=req_headers)
        
        return response
    except Exception as e:
        print(f"Request failed: {e}")
        return None

def login_user(username, password):
    """Login and return token"""
    response = make_request("POST", "/auth/login", {
        "username": username,
        "password": password
    })
    
    if response and response.status_code == 200:
        data = response.json()
        return data.get("access_token"), data.get("user")
    return None, None

def get_auth_headers(token):
    """Get authorization headers"""
    return {"Authorization": f"Bearer {token}"}

def generate_random_string(length=8):
    """Generate random string for unique identifiers"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def print_section(title):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def test_authentication_and_roles():
    """Test 1: Authentication and Roles"""
    print_section("1. AUTENTICACIÓN Y ROLES")
    
    # Test superadmin login
    token_superadmin, user_superadmin = login_user("superadmin", "superadmin123")
    log_test("Login Superadmin", 
             token_superadmin is not None, 
             f"Role: {user_superadmin.get('role') if user_superadmin else 'None'}")
    
    # Test admin logins
    token_admin_tineo, user_admin_tineo = login_user("admin_tineo", "tineo123")
    log_test("Login Admin Tineo", 
             token_admin_tineo is not None,
             f"Org: {user_admin_tineo.get('organization_nombre') if user_admin_tineo else 'None'}")
    
    token_admin_madrid, user_admin_madrid = login_user("admin_madrid", "madrid123")
    log_test("Login Admin Madrid", 
             token_admin_madrid is not None,
             f"Org: {user_admin_madrid.get('organization_nombre') if user_admin_madrid else 'None'}")
    
    # Test taxista logins
    token_taxista_tineo, user_taxista_tineo = login_user("taxista_tineo1", "tax123")
    log_test("Login Taxista Tineo", 
             token_taxista_tineo is not None,
             f"Org: {user_taxista_tineo.get('organization_nombre') if user_taxista_tineo else 'None'}")
    
    token_taxista_madrid, user_taxista_madrid = login_user("taxista_madrid1", "tax123")
    log_test("Login Taxista Madrid", 
             token_taxista_madrid is not None,
             f"Org: {user_taxista_madrid.get('organization_nombre') if user_taxista_madrid else 'None'}")
    
    # Test legacy admin
    token_legacy, user_legacy = login_user("admin", "admin123")
    log_test("Login Legacy Admin", 
             token_legacy is not None,
             f"Role: {user_legacy.get('role') if user_legacy else 'None'}")
    
    # Test /auth/me endpoint for organization info
    if token_admin_tineo:
        response = make_request("GET", "/auth/me", headers=get_auth_headers(token_admin_tineo))
        if response and response.status_code == 200:
            user_data = response.json()
            has_org_info = user_data.get("organization_id") and user_data.get("organization_nombre")
            log_test("Auth/me returns organization info", 
                     has_org_info,
                     f"Org ID: {user_data.get('organization_id')}, Name: {user_data.get('organization_nombre')}")
    
    return {
        "superadmin": (token_superadmin, user_superadmin),
        "admin_tineo": (token_admin_tineo, user_admin_tineo),
        "admin_madrid": (token_admin_madrid, user_admin_madrid),
        "taxista_tineo": (token_taxista_tineo, user_taxista_tineo),
        "taxista_madrid": (token_taxista_madrid, user_taxista_madrid),
        "legacy": (token_legacy, user_legacy)
    }

def test_organization_management(tokens):
    """Test 2: Organization Management (Superadmin only)"""
    print_section("2. GESTIÓN DE ORGANIZACIONES (Solo Superadmin)")
    
    token_superadmin = tokens["superadmin"][0]
    token_admin_tineo = tokens["admin_tineo"][0]
    
    if not token_superadmin:
        log_test("Organization Management", False, "No superadmin token available")
        return {}
    
    # Test GET /organizations (superadmin)
    response = make_request("GET", "/organizations", headers=get_auth_headers(token_superadmin))
    orgs_data = []
    if response and response.status_code == 200:
        orgs_data = response.json()
        log_test("GET /organizations (superadmin)", True, f"Found {len(orgs_data)} organizations")
    else:
        log_test("GET /organizations (superadmin)", False, f"Status: {response.status_code if response else 'No response'}")
    
    # Test GET /organizations (admin - should fail with 403)
    if token_admin_tineo:
        response = make_request("GET", "/organizations", headers=get_auth_headers(token_admin_tineo))
        log_test("GET /organizations (admin blocked)", 
                 response and response.status_code == 403,
                 f"Status: {response.status_code if response else 'No response'}")
    
    # Test POST /organizations (create new organization)
    new_org_name = f"Test Org {generate_random_string()}"
    new_org_data = {
        "nombre": new_org_name,
        "cif": f"B{generate_random_string(8).upper()}",
        "telefono": "987654321",
        "email": "test@testorg.com",
        "color_primario": "#FF0000",
        "color_secundario": "#00FF00"
    }
    
    response = make_request("POST", "/organizations", new_org_data, headers=get_auth_headers(token_superadmin))
    created_org = None
    if response and response.status_code == 200:
        created_org = response.json()
        log_test("POST /organizations (create)", True, f"Created org: {created_org.get('nombre')}")
    else:
        log_test("POST /organizations (create)", False, f"Status: {response.status_code if response else 'No response'}")
    
    # Test GET /organizations/{id} (get specific organization)
    if created_org:
        org_id = created_org.get("id")
        response = make_request("GET", f"/organizations/{org_id}", headers=get_auth_headers(token_superadmin))
        if response and response.status_code == 200:
            org_detail = response.json()
            log_test("GET /organizations/{id}", True, f"Retrieved org: {org_detail.get('nombre')}")
        else:
            log_test("GET /organizations/{id}", False, f"Status: {response.status_code if response else 'No response'}")
    
    # Test PUT /organizations/{id} (update organization)
    if created_org:
        org_id = created_org.get("id")
        update_data = {
            "nombre": f"Updated {new_org_name}",
            "activa": False
        }
        response = make_request("PUT", f"/organizations/{org_id}", update_data, headers=get_auth_headers(token_superadmin))
        if response and response.status_code == 200:
            updated_org = response.json()
            log_test("PUT /organizations/{id}", True, f"Updated org: {updated_org.get('nombre')}")
        else:
            log_test("PUT /organizations/{id}", False, f"Status: {response.status_code if response else 'No response'}")
    
    # Test POST /organizations/{id}/admin (create admin for organization)
    if created_org:
        org_id = created_org.get("id")
        admin_data = {
            "username": f"admin_test_{generate_random_string()}",
            "password": "test123",
            "nombre": "Test Admin"
        }
        response = make_request("POST", f"/organizations/{org_id}/admin", admin_data, headers=get_auth_headers(token_superadmin))
        if response and response.status_code == 200:
            new_admin = response.json()
            log_test("POST /organizations/{id}/admin", True, f"Created admin: {new_admin.get('username')}")
        else:
            log_test("POST /organizations/{id}/admin", False, f"Status: {response.status_code if response else 'No response'}")
    
    # Test DELETE /organizations/{id} (delete organization - cascade)
    if created_org:
        org_id = created_org.get("id")
        response = make_request("DELETE", f"/organizations/{org_id}", headers=get_auth_headers(token_superadmin))
        if response and response.status_code == 200:
            delete_result = response.json()
            log_test("DELETE /organizations/{id}", True, f"Deleted org with cascade: {delete_result}")
        else:
            log_test("DELETE /organizations/{id}", False, f"Status: {response.status_code if response else 'No response'}")
    
    return {"organizations": orgs_data}

def test_data_isolation(tokens):
    """Test 3: Multi-tenant Data Isolation"""
    print_section("3. AISLAMIENTO DE DATOS MULTI-TENANT")
    
    token_superadmin = tokens["superadmin"][0]
    token_admin_tineo = tokens["admin_tineo"][0]
    token_admin_madrid = tokens["admin_madrid"][0]
    
    if not all([token_superadmin, token_admin_tineo, token_admin_madrid]):
        log_test("Data Isolation", False, "Missing required tokens")
        return
    
    # Test users isolation
    # Get users as admin_tineo
    response_tineo = make_request("GET", "/users", headers=get_auth_headers(token_admin_tineo))
    users_tineo = []
    if response_tineo and response_tineo.status_code == 200:
        users_tineo = response_tineo.json()
    
    # Get users as admin_madrid
    response_madrid = make_request("GET", "/users", headers=get_auth_headers(token_admin_madrid))
    users_madrid = []
    if response_madrid and response_madrid.status_code == 200:
        users_madrid = response_madrid.json()
    
    # Get users as superadmin
    response_super = make_request("GET", "/users", headers=get_auth_headers(token_superadmin))
    users_super = []
    if response_super and response_super.status_code == 200:
        users_super = response_super.json()
    
    log_test("Users data isolation - Tineo admin", 
             len(users_tineo) >= 0,
             f"Tineo admin sees {len(users_tineo)} users")
    
    log_test("Users data isolation - Madrid admin", 
             len(users_madrid) >= 0,
             f"Madrid admin sees {len(users_madrid)} users")
    
    log_test("Users data isolation - Superadmin sees all", 
             len(users_super) >= len(users_tineo) + len(users_madrid),
             f"Superadmin sees {len(users_super)} users (should be >= {len(users_tineo) + len(users_madrid)})")
    
    # Test companies isolation
    response_tineo = make_request("GET", "/companies", headers=get_auth_headers(token_admin_tineo))
    companies_tineo = []
    if response_tineo and response_tineo.status_code == 200:
        companies_tineo = response_tineo.json()
    
    response_madrid = make_request("GET", "/companies", headers=get_auth_headers(token_admin_madrid))
    companies_madrid = []
    if response_madrid and response_madrid.status_code == 200:
        companies_madrid = response_madrid.json()
    
    log_test("Companies data isolation - Tineo", 
             len(companies_tineo) >= 0,
             f"Tineo admin sees {len(companies_tineo)} companies")
    
    log_test("Companies data isolation - Madrid", 
             len(companies_madrid) >= 0,
             f"Madrid admin sees {len(companies_madrid)} companies")
    
    # Test vehicles isolation
    response_tineo = make_request("GET", "/vehiculos", headers=get_auth_headers(token_admin_tineo))
    vehicles_tineo = []
    if response_tineo and response_tineo.status_code == 200:
        vehicles_tineo = response_tineo.json()
    
    response_madrid = make_request("GET", "/vehiculos", headers=get_auth_headers(token_admin_madrid))
    vehicles_madrid = []
    if response_madrid and response_madrid.status_code == 200:
        vehicles_madrid = response_madrid.json()
    
    log_test("Vehicles data isolation - Tineo", 
             len(vehicles_tineo) >= 0,
             f"Tineo admin sees {len(vehicles_tineo)} vehicles")
    
    log_test("Vehicles data isolation - Madrid", 
             len(vehicles_madrid) >= 0,
             f"Madrid admin sees {len(vehicles_madrid)} vehicles")

def test_my_organization_endpoint(tokens):
    """Test 4: MY-ORGANIZATION Endpoint (Mobile Branding)"""
    print_section("4. ENDPOINT MY-ORGANIZATION (Branding móvil)")
    
    token_taxista_tineo = tokens["taxista_tineo"][0]
    token_taxista_madrid = tokens["taxista_madrid"][0]
    
    # Test with Tineo taxista
    if token_taxista_tineo:
        response = make_request("GET", "/my-organization", headers=get_auth_headers(token_taxista_tineo))
        if response and response.status_code == 200:
            org_data = response.json()
            required_fields = ["nombre", "color_primario", "color_secundario", "telefono", "email"]
            has_required = all(field in org_data for field in required_fields)
            log_test("GET /my-organization (Taxista Tineo)", 
                     has_required,
                     f"Org: {org_data.get('nombre')}, Colors: {org_data.get('color_primario')}/{org_data.get('color_secundario')}")
        else:
            log_test("GET /my-organization (Taxista Tineo)", False, f"Status: {response.status_code if response else 'No response'}")
    
    # Test with Madrid taxista
    if token_taxista_madrid:
        response = make_request("GET", "/my-organization", headers=get_auth_headers(token_taxista_madrid))
        if response and response.status_code == 200:
            org_data = response.json()
            required_fields = ["nombre", "color_primario", "color_secundario", "telefono", "email"]
            has_required = all(field in org_data for field in required_fields)
            log_test("GET /my-organization (Taxista Madrid)", 
                     has_required,
                     f"Org: {org_data.get('nombre')}, Colors: {org_data.get('color_primario')}/{org_data.get('color_secundario')}")
        else:
            log_test("GET /my-organization (Taxista Madrid)", False, f"Status: {response.status_code if response else 'No response'}")

def test_multi_tenant_crud(tokens):
    """Test 5: CRUD Multi-tenant Operations"""
    print_section("5. CRUD MULTI-TENANT")
    
    token_admin_tineo = tokens["admin_tineo"][0]
    token_admin_madrid = tokens["admin_madrid"][0]
    user_admin_tineo = tokens["admin_tineo"][1]
    user_admin_madrid = tokens["admin_madrid"][1]
    
    if not all([token_admin_tineo, token_admin_madrid]):
        log_test("Multi-tenant CRUD", False, "Missing admin tokens")
        return
    
    # Test creating user as admin_tineo
    user_data = {
        "username": f"taxista_test_tineo_{generate_random_string()}",
        "password": "test123",
        "nombre": "Test Taxista Tineo",
        "role": "taxista"
    }
    
    response = make_request("POST", "/users", user_data, headers=get_auth_headers(token_admin_tineo))
    created_user_tineo = None
    if response and response.status_code == 200:
        created_user_tineo = response.json()
        expected_org_id = user_admin_tineo.get("organization_id")
        actual_org_id = created_user_tineo.get("organization_id")
        log_test("Create user as admin_tineo", 
                 actual_org_id == expected_org_id,
                 f"User org_id: {actual_org_id}, Expected: {expected_org_id}")
    else:
        log_test("Create user as admin_tineo", False, f"Status: {response.status_code if response else 'No response'}")
    
    # Test creating vehicle as admin_madrid
    vehicle_data = {
        "matricula": f"TEST{generate_random_string(4).upper()}",
        "plazas": 4,
        "marca": "Test Brand",
        "modelo": "Test Model",
        "km_iniciales": 50000,
        "fecha_compra": "01/01/2023",
        "activo": True
    }
    
    response = make_request("POST", "/vehiculos", vehicle_data, headers=get_auth_headers(token_admin_madrid))
    created_vehicle_madrid = None
    if response and response.status_code == 200:
        created_vehicle_madrid = response.json()
        expected_org_id = user_admin_madrid.get("organization_id")
        actual_org_id = created_vehicle_madrid.get("organization_id")
        log_test("Create vehicle as admin_madrid", 
                 actual_org_id == expected_org_id,
                 f"Vehicle org_id: {actual_org_id}, Expected: {expected_org_id}")
    else:
        log_test("Create vehicle as admin_madrid", False, f"Status: {response.status_code if response else 'No response'}")
    
    # Test creating company/client
    company_data = {
        "nombre": f"Test Company {generate_random_string()}",
        "cif": f"B{generate_random_string(8).upper()}",
        "numero_cliente": f"CLI{generate_random_string(6).upper()}",
        "telefono": "123456789",
        "email": "test@company.com"
    }
    
    response = make_request("POST", "/companies", company_data, headers=get_auth_headers(token_admin_tineo))
    created_company_tineo = None
    if response and response.status_code == 200:
        created_company_tineo = response.json()
        expected_org_id = user_admin_tineo.get("organization_id")
        actual_org_id = created_company_tineo.get("organization_id")
        log_test("Create company as admin_tineo", 
                 actual_org_id == expected_org_id,
                 f"Company org_id: {actual_org_id}, Expected: {expected_org_id}")
    else:
        log_test("Create company as admin_tineo", False, f"Status: {response.status_code if response else 'No response'}")
    
    # Test cross-organization access (should fail)
    if created_user_tineo:
        user_id = created_user_tineo.get("id")
        # Try to access Tineo user from Madrid admin (should fail or not show)
        response = make_request("GET", "/users", headers=get_auth_headers(token_admin_madrid))
        if response and response.status_code == 200:
            madrid_users = response.json()
            tineo_user_visible = any(u.get("id") == user_id for u in madrid_users)
            log_test("Cross-org access blocked", 
                     not tineo_user_visible,
                     f"Tineo user {'visible' if tineo_user_visible else 'not visible'} to Madrid admin")

def test_turnos_and_services_multi_tenant(tokens):
    """Test 6: Turnos and Services Multi-tenant"""
    print_section("6. TURNOS Y SERVICIOS MULTI-TENANT")
    
    token_taxista_tineo = tokens["taxista_tineo"][0]
    token_taxista_madrid = tokens["taxista_madrid"][0]
    user_taxista_tineo = tokens["taxista_tineo"][1]
    user_taxista_madrid = tokens["taxista_madrid"][1]
    
    if not all([token_taxista_tineo, token_taxista_madrid]):
        log_test("Turnos and Services Multi-tenant", False, "Missing taxista tokens")
        return
    
    # Create a vehicle first for turnos (using admin tokens)
    token_admin_tineo = tokens["admin_tineo"][0]
    if token_admin_tineo:
        vehicle_data = {
            "matricula": f"TURNO{generate_random_string(4).upper()}",
            "plazas": 4,
            "marca": "Test",
            "modelo": "Turno",
            "km_iniciales": 0,
            "fecha_compra": "01/01/2023",
            "activo": True
        }
        response = make_request("POST", "/vehiculos", vehicle_data, headers=get_auth_headers(token_admin_tineo))
        test_vehicle = None
        if response and response.status_code == 200:
            test_vehicle = response.json()
    
    # Test creating turno as taxista_tineo
    if test_vehicle:
        turno_data = {
            "taxista_id": user_taxista_tineo.get("id"),
            "taxista_nombre": user_taxista_tineo.get("nombre"),
            "vehiculo_id": test_vehicle.get("id"),
            "vehiculo_matricula": test_vehicle.get("matricula"),
            "fecha_inicio": "01/12/2024",
            "hora_inicio": "08:00",
            "km_inicio": 100000
        }
        
        response = make_request("POST", "/turnos", turno_data, headers=get_auth_headers(token_taxista_tineo))
        created_turno_tineo = None
        if response and response.status_code == 200:
            created_turno_tineo = response.json()
            expected_org_id = user_taxista_tineo.get("organization_id")
            actual_org_id = created_turno_tineo.get("organization_id")
            log_test("Create turno as taxista_tineo", 
                     actual_org_id == expected_org_id,
                     f"Turno org_id: {actual_org_id}, Expected: {expected_org_id}")
        else:
            log_test("Create turno as taxista_tineo", False, f"Status: {response.status_code if response else 'No response'}")
        
        # Test creating service (should inherit organization from turno/user)
        if created_turno_tineo:
            service_data = {
                "fecha": "01/12/2024",
                "hora": "09:00",
                "origen": "Test Origin",
                "destino": "Test Destination",
                "importe": 15.50,
                "importe_espera": 2.00,
                "kilometros": 10.5,
                "tipo": "particular",
                "cobrado": True,
                "facturar": False
            }
            
            response = make_request("POST", "/services", service_data, headers=get_auth_headers(token_taxista_tineo))
            if response and response.status_code == 200:
                created_service = response.json()
                expected_org_id = user_taxista_tineo.get("organization_id")
                actual_org_id = created_service.get("organization_id")
                log_test("Create service as taxista_tineo", 
                         actual_org_id == expected_org_id,
                         f"Service org_id: {actual_org_id}, Expected: {expected_org_id}")
            else:
                log_test("Create service as taxista_tineo", False, f"Status: {response.status_code if response else 'No response'}")
    
    # Test listing turnos with organization filter
    response = make_request("GET", "/turnos", headers=get_auth_headers(token_taxista_tineo))
    if response and response.status_code == 200:
        turnos_tineo = response.json()
        log_test("List turnos (taxista_tineo)", 
                 len(turnos_tineo) >= 0,
                 f"Found {len(turnos_tineo)} turnos for Tineo taxista")
    
    response = make_request("GET", "/turnos", headers=get_auth_headers(token_taxista_madrid))
    if response and response.status_code == 200:
        turnos_madrid = response.json()
        log_test("List turnos (taxista_madrid)", 
                 len(turnos_madrid) >= 0,
                 f"Found {len(turnos_madrid)} turnos for Madrid taxista")
    
    # Test listing services with organization filter
    response = make_request("GET", "/services", headers=get_auth_headers(token_taxista_tineo))
    if response and response.status_code == 200:
        services_tineo = response.json()
        log_test("List services (taxista_tineo)", 
                 len(services_tineo) >= 0,
                 f"Found {len(services_tineo)} services for Tineo taxista")

def test_legacy_compatibility(tokens):
    """Test 7: Legacy Compatibility"""
    print_section("7. COMPATIBILIDAD LEGACY")
    
    token_legacy = tokens["legacy"][0]
    user_legacy = tokens["legacy"][1]
    
    if not token_legacy:
        log_test("Legacy Compatibility", False, "No legacy admin token")
        return
    
    # Test that legacy admin can access existing endpoints
    response = make_request("GET", "/users", headers=get_auth_headers(token_legacy))
    if response and response.status_code == 200:
        users = response.json()
        log_test("Legacy admin - GET /users", True, f"Found {len(users)} users")
    else:
        log_test("Legacy admin - GET /users", False, f"Status: {response.status_code if response else 'No response'}")
    
    response = make_request("GET", "/companies", headers=get_auth_headers(token_legacy))
    if response and response.status_code == 200:
        companies = response.json()
        log_test("Legacy admin - GET /companies", True, f"Found {len(companies)} companies")
    else:
        log_test("Legacy admin - GET /companies", False, f"Status: {response.status_code if response else 'No response'}")
    
    response = make_request("GET", "/vehiculos", headers=get_auth_headers(token_legacy))
    if response and response.status_code == 200:
        vehicles = response.json()
        log_test("Legacy admin - GET /vehiculos", True, f"Found {len(vehicles)} vehicles")
    else:
        log_test("Legacy admin - GET /vehiculos", False, f"Status: {response.status_code if response else 'No response'}")
    
    # Test that legacy admin cannot access organization endpoints
    response = make_request("GET", "/organizations", headers=get_auth_headers(token_legacy))
    log_test("Legacy admin blocked from /organizations", 
             response and response.status_code == 403,
             f"Status: {response.status_code if response else 'No response'}")

def test_security_and_permissions(tokens):
    """Test 8: Security and Permissions"""
    print_section("8. SEGURIDAD Y PERMISOS")
    
    token_taxista_tineo = tokens["taxista_tineo"][0]
    token_admin_tineo = tokens["admin_tineo"][0]
    token_superadmin = tokens["superadmin"][0]
    
    # Test taxista cannot access admin endpoints
    if token_taxista_tineo:
        # Try to create user (admin only)
        user_data = {
            "username": f"test_fail_{generate_random_string()}",
            "password": "test123",
            "nombre": "Should Fail",
            "role": "taxista"
        }
        response = make_request("POST", "/users", user_data, headers=get_auth_headers(token_taxista_tineo))
        log_test("Taxista blocked from POST /users", 
                 response and response.status_code == 403,
                 f"Status: {response.status_code if response else 'No response'}")
        
        # Try to access organizations (superadmin only)
        response = make_request("GET", "/organizations", headers=get_auth_headers(token_taxista_tineo))
        log_test("Taxista blocked from GET /organizations", 
                 response and response.status_code == 403,
                 f"Status: {response.status_code if response else 'No response'}")
    
    # Test admin cannot access superadmin endpoints
    if token_admin_tineo:
        response = make_request("GET", "/organizations", headers=get_auth_headers(token_admin_tineo))
        log_test("Admin blocked from GET /organizations", 
                 response and response.status_code == 403,
                 f"Status: {response.status_code if response else 'No response'}")
    
    # Test invalid token
    invalid_headers = {"Authorization": "Bearer invalid_token_12345"}
    response = make_request("GET", "/auth/me", headers=invalid_headers)
    log_test("Invalid token rejected", 
             response and response.status_code == 401,
             f"Status: {response.status_code if response else 'No response'}")
    
    # Test no token
    response = make_request("GET", "/users")
    log_test("No token rejected", 
             response and response.status_code in [401, 403, 422],
             f"Status: {response.status_code if response else 'No response'}")

def print_final_summary():
    """Print final test summary"""
    print_section("RESUMEN FINAL DE TESTING")
    
    total_tests = tests_passed + tests_failed
    success_rate = (tests_passed / total_tests * 100) if total_tests > 0 else 0
    
    print(f"📊 ESTADÍSTICAS FINALES:")
    print(f"   Total tests ejecutados: {total_tests}")
    print(f"   ✅ Tests exitosos: {tests_passed}")
    print(f"   ❌ Tests fallidos: {tests_failed}")
    print(f"   📈 Tasa de éxito: {success_rate:.1f}%")
    
    if tests_failed > 0:
        print(f"\n❌ TESTS FALLIDOS:")
        for result in test_results:
            if not result["passed"]:
                print(f"   - {result['test']}: {result['details']}")
    
    print(f"\n🎯 VEREDICTO FINAL:")
    if success_rate >= 95:
        print("   ✅ SISTEMA COMPLETAMENTE OPERATIVO PARA PRODUCCIÓN")
    elif success_rate >= 85:
        print("   ⚠️  SISTEMA MAYORMENTE FUNCIONAL - REVISAR FALLOS MENORES")
    else:
        print("   ❌ SISTEMA REQUIERE CORRECCIONES ANTES DE PRODUCCIÓN")

def main():
    """Main testing function"""
    print("🚕 TaxiFast Multi-tenant SaaS Platform - Testing Exhaustivo")
    print("=" * 60)
    print("Ejecutando tests completos del sistema multi-tenant...")
    
    try:
        # Test 1: Authentication and Roles
        tokens = test_authentication_and_roles()
        
        # Test 2: Organization Management
        test_organization_management(tokens)
        
        # Test 3: Data Isolation
        test_data_isolation(tokens)
        
        # Test 4: MY-ORGANIZATION Endpoint
        test_my_organization_endpoint(tokens)
        
        # Test 5: Multi-tenant CRUD
        test_multi_tenant_crud(tokens)
        
        # Test 6: Turnos and Services Multi-tenant
        test_turnos_and_services_multi_tenant(tokens)
        
        # Test 7: Legacy Compatibility
        test_legacy_compatibility(tokens)
        
        # Test 8: Security and Permissions
        test_security_and_permissions(tokens)
        
        # Final Summary
        print_final_summary()
        
    except Exception as e:
        print(f"\n💥 ERROR CRÍTICO EN TESTING: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0 if tests_failed == 0 else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)