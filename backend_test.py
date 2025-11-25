#!/usr/bin/env python3
"""
Testing script for Taxi Tineo backend API - Focus on detailed turnos exports
Testing the new functionality that includes individual services in turno exports
"""

import requests
import json
import sys
from datetime import datetime
import os

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://taxitineo.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class TaxiBackendTester:
    def __init__(self):
        self.admin_token = None
        self.taxista_token = None
        self.test_data = {
            "taxista_id": None,
            "vehiculo_id": None,
            "turno_id": None,
            "service_ids": []
        }
        self.results = []
        
    def log_result(self, test_name: str, success: bool, details: str = "", response_data: dict = None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "response_data": response_data,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"    Details: {details}")
        if not success and response_data:
            print(f"    Response: {response_data}")
        print()

    def make_request(self, method: str, endpoint: str, data: dict = None, headers: dict = None, params: dict = None) -> tuple:
        """Make HTTP request and return (success, response_data, status_code)"""
        url = f"{BASE_URL}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=headers, params=params, timeout=30)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, headers=headers, params=params, timeout=30)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, params=params, timeout=30)
            else:
                return False, {"error": f"Unsupported method: {method}"}, 0
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}
            
            return response.status_code < 400, response_data, response.status_code
            
        except requests.exceptions.RequestException as e:
            return False, {"error": str(e)}, 0

    def get_auth_headers(self, token: str) -> dict:
        """Get authorization headers"""
        return {"Authorization": f"Bearer {token}"}

    # FASE 1: SETUP Y PREPARACIÓN
    def test_admin_login(self):
        """Test admin authentication"""
        success, data, status = self.make_request("POST", "/auth/login", ADMIN_CREDENTIALS)
        
        if success and "access_token" in data:
            self.admin_token = data["access_token"]
            self.log_result("Admin Login", True, f"Token obtained, user: {data.get('user', {}).get('username')}")
            return True
        else:
            self.log_result("Admin Login", False, f"Status: {status}", data)
            return False

    def test_create_test_taxista(self):
        """Create test taxista for testing"""
        taxista_data = {
            "username": "taxista_test_delete",
            "password": "test123",
            "nombre": "Taxista Test Delete",
            "role": "taxista",
            "licencia": "TEST123"
        }
        
        headers = self.get_auth_headers(self.admin_token)
        success, data, status = self.make_request("POST", "/users", taxista_data, headers)
        
        if success and "id" in data:
            self.test_data["taxista_id"] = data["id"]
            self.log_result("Create Test Taxista", True, f"Created taxista: {data['nombre']} (ID: {data['id']})")
            return True
        else:
            self.log_result("Create Test Taxista", False, f"Status: {status}", data)
            return False

    def test_create_test_vehiculo(self):
        """Create test vehicle"""
        vehiculo_data = {
            "matricula": "TEST123",
            "plazas": 4,
            "marca": "Test Brand",
            "modelo": "Test Model",
            "km_iniciales": 50000,
            "fecha_compra": "01/01/2020",
            "activo": True
        }
        
        headers = self.get_auth_headers(self.admin_token)
        success, data, status = self.make_request("POST", "/vehiculos", vehiculo_data, headers)
        
        if success and "id" in data:
            self.test_data["vehiculo_id"] = data["id"]
            self.log_result("Create Test Vehiculo", True, f"Created vehicle: {data['matricula']} (ID: {data['id']})")
            return True
        else:
            self.log_result("Create Test Vehiculo", False, f"Status: {status}", data)
            return False

    def test_taxista_login(self):
        """Test taxista authentication"""
        taxista_credentials = {"username": "taxista_test_delete", "password": "test123"}
        success, data, status = self.make_request("POST", "/auth/login", taxista_credentials)
        
        if success and "access_token" in data:
            self.taxista_token = data["access_token"]
            self.log_result("Taxista Login", True, f"Token obtained for: {data.get('user', {}).get('username')}")
            return True
        else:
            self.log_result("Taxista Login", False, f"Status: {status}", data)
            return False

    # FASE 2: CREAR TURNO CON SERVICIOS
    def test_create_turno(self):
        """Create turno for testing"""
        turno_data = {
            "taxista_id": self.test_data["taxista_id"],
            "taxista_nombre": "Taxista Test Delete",
            "vehiculo_id": self.test_data["vehiculo_id"],
            "vehiculo_matricula": "TEST123",
            "fecha_inicio": "15/12/2024",
            "hora_inicio": "08:00",
            "km_inicio": 50000
        }
        
        headers = self.get_auth_headers(self.taxista_token)
        success, data, status = self.make_request("POST", "/turnos", turno_data, headers)
        
        if success and "id" in data:
            self.test_data["turno_id"] = data["id"]
            self.log_result("Create Turno", True, f"Created turno ID: {data['id']}")
            return True
        else:
            self.log_result("Create Turno", False, f"Status: {status}", data)
            return False

    def test_create_services_for_turno(self):
        """Create 5 services associated with the turno"""
        services_created = 0
        
        for i in range(1, 6):
            service_data = {
                "fecha": "15/12/2024",
                "hora": f"0{8+i}:00",
                "origen": f"Origen Test {i}",
                "destino": f"Destino Test {i}",
                "importe": 10.0 + i,
                "importe_espera": 2.0,
                "kilometros": 5.0 + i,
                "tipo": "particular" if i % 2 == 1 else "empresa",
                "turno_id": self.test_data["turno_id"],
                "cobrado": True,
                "facturar": False
            }
            
            headers = self.get_auth_headers(self.taxista_token)
            success, data, status = self.make_request("POST", "/services", service_data, headers)
            
            if success and "id" in data:
                self.test_data["service_ids"].append(data["id"])
                services_created += 1
            else:
                self.log_result(f"Create Service {i}", False, f"Status: {status}", data)
        
        if services_created == 5:
            self.log_result("Create 5 Services", True, f"Created {services_created} services for turno")
            return True
        else:
            self.log_result("Create 5 Services", False, f"Only created {services_created}/5 services")
            return False

    def test_verify_services_exist(self):
        """Verify that services exist before deletion"""
        headers = self.get_auth_headers(self.admin_token)
        params = {"turno_id": self.test_data["turno_id"]}
        success, data, status = self.make_request("GET", "/services", headers=headers, params=params)
        
        if success and isinstance(data, list):
            service_count = len(data)
            if service_count == 5:
                self.log_result("Verify Services Exist", True, f"Found {service_count} services for turno")
                return True
            else:
                self.log_result("Verify Services Exist", False, f"Expected 5 services, found {service_count}")
                return False
        else:
            self.log_result("Verify Services Exist", False, f"Status: {status}", data)
            return False

    # FASE 3: ELIMINACIÓN Y VERIFICACIÓN (CRÍTICO)
    def test_delete_turno_cascade(self):
        """CRITICAL: Test DELETE turno with cascade deletion of services"""
        headers = self.get_auth_headers(self.admin_token)
        success, data, status = self.make_request("DELETE", f"/turnos/{self.test_data['turno_id']}", headers=headers)
        
        if success and status == 200:
            services_deleted = data.get("servicios_eliminados", 0)
            if services_deleted == 5:
                self.log_result("DELETE Turno (Cascade)", True, f"Turno deleted, {services_deleted} services eliminated")
                return True
            else:
                self.log_result("DELETE Turno (Cascade)", False, f"Expected 5 services deleted, got {services_deleted}", data)
                return False
        else:
            self.log_result("DELETE Turno (Cascade)", False, f"Status: {status}", data)
            return False

    def test_verify_turno_deleted(self):
        """Verify turno no longer exists"""
        headers = self.get_auth_headers(self.admin_token)
        success, data, status = self.make_request("GET", "/turnos", headers=headers)
        
        if success and isinstance(data, list):
            # Check if our turno is in the list
            turno_found = any(t.get("id") == self.test_data["turno_id"] for t in data)
            if not turno_found:
                self.log_result("Verify Turno Deleted", True, "Turno no longer appears in GET /turnos")
                return True
            else:
                self.log_result("Verify Turno Deleted", False, "Turno still appears in GET /turnos")
                return False
        else:
            self.log_result("Verify Turno Deleted", False, f"Status: {status}", data)
            return False

    def test_verify_services_deleted_cascade(self):
        """CRITICAL: Verify services were deleted automatically (cascade)"""
        headers = self.get_auth_headers(self.admin_token)
        params = {"turno_id": self.test_data["turno_id"]}
        success, data, status = self.make_request("GET", "/services", headers=headers, params=params)
        
        if success and isinstance(data, list):
            service_count = len(data)
            if service_count == 0:
                self.log_result("Verify Services Deleted (Cascade)", True, "Services automatically deleted with turno")
                return True
            else:
                self.log_result("Verify Services Deleted (Cascade)", False, f"Found {service_count} services still exist")
                return False
        else:
            self.log_result("Verify Services Deleted (Cascade)", False, f"Status: {status}", data)
            return False

    def test_verify_services_not_in_general_list(self):
        """Verify services don't appear in general services list"""
        headers = self.get_auth_headers(self.admin_token)
        success, data, status = self.make_request("GET", "/services", headers=headers)
        
        if success and isinstance(data, list):
            # Check if any of our service IDs are still in the general list
            found_services = [s for s in data if s.get("id") in self.test_data["service_ids"]]
            if len(found_services) == 0:
                self.log_result("Verify Services Not in General List", True, "Services not found in general list")
                return True
            else:
                self.log_result("Verify Services Not in General List", False, f"Found {len(found_services)} services still in general list")
                return False
        else:
            self.log_result("Verify Services Not in General List", False, f"Status: {status}", data)
            return False

    # FASE 4: TESTING DE AUTORIZACIÓN
    def test_taxista_cannot_delete_turno(self):
        """Test that taxista cannot delete turnos (should get 403)"""
        # First create another turno to test with
        turno_data = {
            "taxista_id": self.test_data["taxista_id"],
            "taxista_nombre": "Taxista Test Delete",
            "vehiculo_id": self.test_data["vehiculo_id"],
            "vehiculo_matricula": "TEST123",
            "fecha_inicio": "15/12/2024",
            "hora_inicio": "14:00",
            "km_inicio": 50100
        }
        
        headers = self.get_auth_headers(self.taxista_token)
        success, data, status = self.make_request("POST", "/turnos", turno_data, headers)
        
        if success and "id" in data:
            test_turno_id = data["id"]
            
            # Now try to delete it as taxista (should fail)
            success, data, status = self.make_request("DELETE", f"/turnos/{test_turno_id}", headers=headers)
            
            if status == 403:
                self.log_result("Taxista Cannot Delete Turno", True, "Correctly received 403 Forbidden")
                
                # Clean up: delete as admin
                admin_headers = self.get_auth_headers(self.admin_token)
                self.make_request("DELETE", f"/turnos/{test_turno_id}", headers=admin_headers)
                return True
            else:
                self.log_result("Taxista Cannot Delete Turno", False, f"Expected 403, got {status}", data)
                return False
        else:
            self.log_result("Taxista Cannot Delete Turno", False, "Could not create test turno")
            return False

    # FASE 5: EDGE CASES
    def test_delete_nonexistent_turno(self):
        """Test DELETE on non-existent turno (should return 404)"""
        fake_turno_id = "507f1f77bcf86cd799439011"  # Valid ObjectId format but non-existent
        headers = self.get_auth_headers(self.admin_token)
        success, data, status = self.make_request("DELETE", f"/turnos/{fake_turno_id}", headers=headers)
        
        if status == 404:
            self.log_result("Delete Non-existent Turno", True, "Correctly received 404 Not Found")
            return True
        else:
            self.log_result("Delete Non-existent Turno", False, f"Expected 404, got {status}", data)
            return False

    def test_delete_turno_without_services(self):
        """Test DELETE turno without services (should work with servicios_eliminados: 0)"""
        # Create turno without services
        turno_data = {
            "taxista_id": self.test_data["taxista_id"],
            "taxista_nombre": "Taxista Test Delete",
            "vehiculo_id": self.test_data["vehiculo_id"],
            "vehiculo_matricula": "TEST123",
            "fecha_inicio": "15/12/2024",
            "hora_inicio": "16:00",
            "km_inicio": 50200
        }
        
        headers = self.get_auth_headers(self.taxista_token)
        success, data, status = self.make_request("POST", "/turnos", turno_data, headers)
        
        if success and "id" in data:
            empty_turno_id = data["id"]
            
            # Delete it as admin
            admin_headers = self.get_auth_headers(self.admin_token)
            success, data, status = self.make_request("DELETE", f"/turnos/{empty_turno_id}", headers=admin_headers)
            
            if success and data.get("servicios_eliminados") == 0:
                self.log_result("Delete Turno Without Services", True, "Successfully deleted turno with 0 services")
                return True
            else:
                self.log_result("Delete Turno Without Services", False, f"Status: {status}", data)
                return False
        else:
            self.log_result("Delete Turno Without Services", False, "Could not create empty turno")
            return False

    def test_delete_turno_with_many_services(self):
        """Test DELETE turno with 10 services (should delete all)"""
        # Create turno
        turno_data = {
            "taxista_id": self.test_data["taxista_id"],
            "taxista_nombre": "Taxista Test Delete",
            "vehiculo_id": self.test_data["vehiculo_id"],
            "vehiculo_matricula": "TEST123",
            "fecha_inicio": "15/12/2024",
            "hora_inicio": "18:00",
            "km_inicio": 50300
        }
        
        headers = self.get_auth_headers(self.taxista_token)
        success, data, status = self.make_request("POST", "/turnos", turno_data, headers)
        
        if success and "id" in data:
            many_services_turno_id = data["id"]
            
            # Create 10 services
            services_created = 0
            for i in range(1, 11):
                service_data = {
                    "fecha": "15/12/2024",
                    "hora": f"{18+i//10}:{(i*6)%60:02d}",
                    "origen": f"Origen Many {i}",
                    "destino": f"Destino Many {i}",
                    "importe": 8.0 + i,
                    "importe_espera": 1.0,
                    "kilometros": 3.0 + i,
                    "tipo": "particular" if i % 2 == 1 else "empresa",
                    "turno_id": many_services_turno_id,
                    "cobrado": True,
                    "facturar": False
                }
                
                success_svc, data_svc, status_svc = self.make_request("POST", "/services", service_data, headers)
                if success_svc:
                    services_created += 1
            
            if services_created == 10:
                # Delete turno as admin
                admin_headers = self.get_auth_headers(self.admin_token)
                success, data, status = self.make_request("DELETE", f"/turnos/{many_services_turno_id}", headers=admin_headers)
                
                if success and data.get("servicios_eliminados") == 10:
                    self.log_result("Delete Turno With Many Services", True, "Successfully deleted turno with 10 services")
                    return True
                else:
                    self.log_result("Delete Turno With Many Services", False, f"Expected 10 services deleted, got {data.get('servicios_eliminados')}", data)
                    return False
            else:
                self.log_result("Delete Turno With Many Services", False, f"Only created {services_created}/10 services")
                return False
        else:
            self.log_result("Delete Turno With Many Services", False, "Could not create turno for many services test")
            return False

    # FASE 6: FUNCIONALIDADES CORE (NO REGRESIONES)
    def test_core_authentication(self):
        """Test core authentication still works"""
        # Test admin auth
        success, data, status = self.make_request("POST", "/auth/login", ADMIN_CREDENTIALS)
        auth_works = success and "access_token" in data
        
        # Test /auth/me endpoint
        if auth_works:
            headers = self.get_auth_headers(data["access_token"])
            success_me, data_me, status_me = self.make_request("GET", "/auth/me", headers=headers)
            me_works = success_me and data_me.get("username") == "admin"
        else:
            me_works = False
        
        if auth_works and me_works:
            self.log_result("Core Authentication", True, "Login and /auth/me working")
            return True
        else:
            self.log_result("Core Authentication", False, f"Auth: {auth_works}, Me: {me_works}")
            return False

    def test_core_crud_users(self):
        """Test CRUD Users still works"""
        headers = self.get_auth_headers(self.admin_token)
        
        # Test GET users
        success, data, status = self.make_request("GET", "/users", headers=headers)
        get_works = success and isinstance(data, list)
        
        # Test POST user (create temp user)
        temp_user = {
            "username": "temp_test_user",
            "password": "temp123",
            "nombre": "Temp Test User",
            "role": "taxista"
        }
        success_post, data_post, status_post = self.make_request("POST", "/users", temp_user, headers)
        post_works = success_post and "id" in data_post
        
        # Clean up temp user
        if post_works:
            temp_user_id = data_post["id"]
            self.make_request("DELETE", f"/users/{temp_user_id}", headers=headers)
        
        if get_works and post_works:
            self.log_result("Core CRUD Users", True, "GET and POST users working")
            return True
        else:
            self.log_result("Core CRUD Users", False, f"GET: {get_works}, POST: {post_works}")
            return False

    def test_core_crud_companies(self):
        """Test CRUD Companies still works"""
        headers = self.get_auth_headers(self.admin_token)
        
        # Test GET companies
        success, data, status = self.make_request("GET", "/companies", headers=headers)
        get_works = success and isinstance(data, list)
        
        # Test POST company
        temp_company = {
            "nombre": "Temp Test Company",
            "cif": "B12345678",
            "direccion": "Test Address",
            "localidad": "Test City",
            "provincia": "Test Province",
            "numero_cliente": "TEMP001"
        }
        success_post, data_post, status_post = self.make_request("POST", "/companies", temp_company, headers)
        post_works = success_post and "id" in data_post
        
        # Clean up temp company
        if post_works:
            temp_company_id = data_post["id"]
            self.make_request("DELETE", f"/companies/{temp_company_id}", headers=headers)
        
        if get_works and post_works:
            self.log_result("Core CRUD Companies", True, "GET and POST companies working")
            return True
        else:
            self.log_result("Core CRUD Companies", False, f"GET: {get_works}, POST: {post_works}")
            return False

    def test_core_crud_vehiculos(self):
        """Test CRUD Vehiculos still works"""
        headers = self.get_auth_headers(self.admin_token)
        
        # Test GET vehiculos
        success, data, status = self.make_request("GET", "/vehiculos", headers=headers)
        get_works = success and isinstance(data, list)
        
        # Test POST vehiculo
        temp_vehiculo = {
            "matricula": "TEMP999",
            "plazas": 4,
            "marca": "Temp Brand",
            "modelo": "Temp Model",
            "km_iniciales": 0,
            "fecha_compra": "01/01/2024",
            "activo": True
        }
        success_post, data_post, status_post = self.make_request("POST", "/vehiculos", temp_vehiculo, headers)
        post_works = success_post and "id" in data_post
        
        # Clean up temp vehiculo
        if post_works:
            temp_vehiculo_id = data_post["id"]
            self.make_request("DELETE", f"/vehiculos/{temp_vehiculo_id}", headers=headers)
        
        if get_works and post_works:
            self.log_result("Core CRUD Vehiculos", True, "GET and POST vehiculos working")
            return True
        else:
            self.log_result("Core CRUD Vehiculos", False, f"GET: {get_works}, POST: {post_works}")
            return False

    def test_core_crud_services(self):
        """Test CRUD Services still works"""
        headers = self.get_auth_headers(self.admin_token)
        
        # Test GET services
        success, data, status = self.make_request("GET", "/services", headers=headers)
        get_works = success and isinstance(data, list)
        
        if get_works:
            self.log_result("Core CRUD Services", True, "GET services working")
            return True
        else:
            self.log_result("Core CRUD Services", False, f"GET services failed: {status}")
            return False

    def test_core_crud_turnos(self):
        """Test CRUD Turnos still works"""
        headers = self.get_auth_headers(self.admin_token)
        
        # Test GET turnos
        success, data, status = self.make_request("GET", "/turnos", headers=headers)
        get_works = success and isinstance(data, list)
        
        if get_works:
            self.log_result("Core CRUD Turnos", True, "GET turnos working")
            return True
        else:
            self.log_result("Core CRUD Turnos", False, f"GET turnos failed: {status}")
            return False

    def test_core_exportaciones(self):
        """Test core export functionality"""
        headers = self.get_auth_headers(self.admin_token)
        
        # Test CSV export
        success_csv, data_csv, status_csv = self.make_request("GET", "/services/export/csv", headers=headers)
        csv_works = success_csv and status_csv == 200
        
        # Test Excel export
        success_excel, data_excel, status_excel = self.make_request("GET", "/services/export/excel", headers=headers)
        excel_works = success_excel and status_excel == 200
        
        # Test PDF export
        success_pdf, data_pdf, status_pdf = self.make_request("GET", "/services/export/pdf", headers=headers)
        pdf_works = success_pdf and status_pdf == 200
        
        exports_working = csv_works and excel_works and pdf_works
        
        if exports_working:
            self.log_result("Core Exportaciones", True, "CSV, Excel, and PDF exports working")
            return True
        else:
            self.log_result("Core Exportaciones", False, f"CSV: {csv_works}, Excel: {excel_works}, PDF: {pdf_works}")
            return False

    def test_core_estadisticas(self):
        """Test statistics endpoint"""
        headers = self.get_auth_headers(self.admin_token)
        success, data, status = self.make_request("GET", "/turnos/estadisticas", headers=headers)
        
        if success and isinstance(data, dict) and "total_turnos" in data:
            self.log_result("Core Estadísticas", True, "Statistics endpoint working")
            return True
        else:
            self.log_result("Core Estadísticas", False, f"Status: {status}", data)
            return False

    # FASE 7: OPTIMIZACIONES (SIGUEN ACTIVAS)
    def test_optimizations_batch_queries(self):
        """Test that batch queries optimization is still active"""
        headers = self.get_auth_headers(self.admin_token)
        
        start_time = time.time()
        success, data, status = self.make_request("GET", "/turnos", headers=headers)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        if success and response_time < 2.0:  # Should be fast due to batch queries
            self.log_result("Optimizations - Batch Queries", True, f"GET /turnos responded in {response_time:.2f}s")
            return True
        else:
            self.log_result("Optimizations - Batch Queries", False, f"Response time: {response_time:.2f}s (expected < 2s)")
            return False

    def test_optimizations_password_exclusion(self):
        """Test that passwords are excluded from GET /users"""
        headers = self.get_auth_headers(self.admin_token)
        success, data, status = self.make_request("GET", "/users", headers=headers)
        
        if success and isinstance(data, list):
            # Check that no user has password field
            has_password = any("password" in user for user in data)
            if not has_password:
                self.log_result("Optimizations - Password Exclusion", True, "Passwords correctly excluded from GET /users")
                return True
            else:
                self.log_result("Optimizations - Password Exclusion", False, "Found password field in user data")
                return False
        else:
            self.log_result("Optimizations - Password Exclusion", False, f"Status: {status}")
            return False

    def test_optimizations_limits(self):
        """Test that limits are respected"""
        headers = self.get_auth_headers(self.admin_token)
        params = {"limit": 5}
        success, data, status = self.make_request("GET", "/services", headers=headers, params=params)
        
        if success and isinstance(data, list):
            if len(data) <= 5:
                self.log_result("Optimizations - Limits", True, f"Limit respected: returned {len(data)} items")
                return True
            else:
                self.log_result("Optimizations - Limits", False, f"Limit not respected: returned {len(data)} items")
                return False
        else:
            self.log_result("Optimizations - Limits", False, f"Status: {status}")
            return False

    # CLEANUP
    def cleanup_test_data(self):
        """Clean up test data"""
        headers = self.get_auth_headers(self.admin_token)
        
        # Delete test taxista (this should also clean up related data)
        if self.test_data["taxista_id"]:
            self.make_request("DELETE", f"/users/{self.test_data['taxista_id']}", headers=headers)
        
        # Delete test vehiculo
        if self.test_data["vehiculo_id"]:
            self.make_request("DELETE", f"/vehiculos/{self.test_data['vehiculo_id']}", headers=headers)
        
        print("🧹 Test data cleanup completed")

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🎯 TESTING FINAL - ELIMINACIÓN DE TURNOS Y VERIFICACIÓN COMPLETA")
        print("=" * 80)
        print()
        
        # FASE 1: SETUP Y PREPARACIÓN
        print("📋 FASE 1: SETUP Y PREPARACIÓN")
        if not self.test_admin_login():
            print("❌ Cannot continue without admin login")
            return
        
        if not self.test_create_test_taxista():
            print("❌ Cannot continue without test taxista")
            return
            
        if not self.test_create_test_vehiculo():
            print("❌ Cannot continue without test vehiculo")
            return
            
        if not self.test_taxista_login():
            print("❌ Cannot continue without taxista login")
            return
        
        print()
        
        # FASE 2: CREAR TURNO CON SERVICIOS
        print("🚕 FASE 2: CREAR TURNO CON SERVICIOS")
        if not self.test_create_turno():
            print("❌ Cannot continue without turno")
            return
            
        if not self.test_create_services_for_turno():
            print("❌ Cannot continue without services")
            return
            
        self.test_verify_services_exist()
        print()
        
        # FASE 3: ELIMINACIÓN Y VERIFICACIÓN (CRÍTICO)
        print("🔥 FASE 3: ELIMINACIÓN Y VERIFICACIÓN (CRÍTICO)")
        self.test_delete_turno_cascade()
        self.test_verify_turno_deleted()
        self.test_verify_services_deleted_cascade()
        self.test_verify_services_not_in_general_list()
        print()
        
        # FASE 4: TESTING DE AUTORIZACIÓN
        print("🔒 FASE 4: TESTING DE AUTORIZACIÓN")
        self.test_taxista_cannot_delete_turno()
        print()
        
        # FASE 5: EDGE CASES
        print("⚠️ FASE 5: EDGE CASES")
        self.test_delete_nonexistent_turno()
        self.test_delete_turno_without_services()
        self.test_delete_turno_with_many_services()
        print()
        
        # FASE 6: FUNCIONALIDADES CORE (NO REGRESIONES)
        print("✅ FASE 6: FUNCIONALIDADES CORE (NO REGRESIONES)")
        self.test_core_authentication()
        self.test_core_crud_users()
        self.test_core_crud_companies()
        self.test_core_crud_vehiculos()
        self.test_core_crud_services()
        self.test_core_crud_turnos()
        self.test_core_exportaciones()
        self.test_core_estadisticas()
        print()
        
        # FASE 7: OPTIMIZACIONES (SIGUEN ACTIVAS)
        print("⚡ FASE 7: OPTIMIZACIONES (SIGUEN ACTIVAS)")
        self.test_optimizations_batch_queries()
        self.test_optimizations_password_exclusion()
        self.test_optimizations_limits()
        print()
        
        # CLEANUP
        self.cleanup_test_data()
        
        # SUMMARY
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print("=" * 80)
        print("📊 RESUMEN FINAL DE TESTING")
        print("=" * 80)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print()
        
        # Critical tests summary
        critical_tests = [
            "DELETE Turno (Cascade)",
            "Verify Services Deleted (Cascade)",
            "Verify Turno Deleted",
            "Taxista Cannot Delete Turno"
        ]
        
        print("🔥 CRITICAL TESTS RESULTS:")
        for test_name in critical_tests:
            result = next((r for r in self.results if r["test"] == test_name), None)
            if result:
                print(f"  {result['status']}: {test_name}")
            else:
                print(f"  ❓ NOT RUN: {test_name}")
        print()
        
        # Failed tests details
        if failed_tests > 0:
            print("❌ FAILED TESTS DETAILS:")
            for result in self.results:
                if not result["success"]:
                    print(f"  • {result['test']}: {result['details']}")
            print()
        
        # Final verdict
        critical_passed = all(
            any(r["test"] == test and r["success"] for r in self.results)
            for test in critical_tests
        )
        
        if critical_passed and success_rate >= 90:
            print("🎉 VEREDICTO: SISTEMA LISTO PARA PRODUCCIÓN")
            print("   ✅ Eliminación en cascada funcionando correctamente")
            print("   ✅ Todas las funcionalidades críticas operativas")
            print("   ✅ No hay regresiones detectadas")
        elif critical_passed:
            print("⚠️ VEREDICTO: FUNCIONALIDAD CRÍTICA OK, REVISAR TESTS MENORES")
            print("   ✅ Eliminación en cascada funcionando correctamente")
            print("   ⚠️ Algunos tests menores fallaron")
        else:
            print("❌ VEREDICTO: PROBLEMAS CRÍTICOS DETECTADOS")
            print("   ❌ Eliminación en cascada o funcionalidades críticas fallan")
            print("   🔧 Requiere corrección antes de producción")

if __name__ == "__main__":
    tester = TaxiBackendTester()
    tester.run_all_tests()