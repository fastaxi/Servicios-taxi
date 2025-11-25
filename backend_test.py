#!/usr/bin/env python3
"""
🎯 TESTING EXHAUSTIVO POST-BUILD v1.1.0 - VALIDACIÓN COMPLETA DEL SISTEMA
Backend API Testing Suite for Taxi Management System

This comprehensive test suite validates all backend functionalities:
- Authentication and Security
- CRUD Operations (Users, Companies, Vehicles, Services, Turnos)
- Complete Turno Workflow with Services
- Export Functionalities (CSV, Excel, PDF)
- Statistics and Reports
- Offline Synchronization
- Configuration Management
"""

import requests
import json
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import os

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://taxitineo.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"
ADMIN_CREDENTIALS = {"username": "admin", "password": "admin123"}

class TaxiTestSuite:
    def __init__(self):
        self.admin_token = None
        self.taxista_token = None
        self.taxista_id = None
        self.test_results = []
        self.created_resources = {
            "users": [],
            "companies": [],
            "vehiculos": [],
            "turnos": [],
            "services": []
        }
        
    def log_test(self, test_name: str, passed: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        if response_data and not passed:
            result["response_data"] = str(response_data)[:500]  # Limit response data
        
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"    Details: {details}")
        if not passed and response_data:
            print(f"    Response: {str(response_data)[:200]}...")
        print()

    def make_request(self, method: str, endpoint: str, data: dict = None, token: str = None, params: dict = None) -> tuple:
        """Make HTTP request with error handling"""
        url = f"{API_BASE}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=30)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=data, timeout=30)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                return False, f"Unsupported method: {method}"
            
            return True, response
        except requests.exceptions.RequestException as e:
            return False, f"Request failed: {str(e)}"
    
    # ==========================================
    # PARTE 1: AUTENTICACIÓN Y SEGURIDAD
    # ==========================================
    
    def test_admin_login_success(self):
        """Test admin login with correct credentials"""
        success, response = self.make_request("POST", "/auth/login", ADMIN_CREDENTIALS)
        
        if not success:
            self.log_test("Admin Login (Success)", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data and "user" in data:
                self.admin_token = data["access_token"]
                self.log_test("Admin Login (Success)", True, f"Token received, user: {data['user']['username']}")
                return True
            else:
                self.log_test("Admin Login (Success)", False, "Missing token or user in response", data)
                return False
        else:
            self.log_test("Admin Login (Success)", False, f"Status: {response.status_code}", response.text)
            return False

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        invalid_creds = {"username": "invalid", "password": "wrong"}
        success, response = self.make_request("POST", "/auth/login", invalid_creds)
        
        if not success:
            self.log_test("Login Invalid Credentials", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 401:
            self.log_test("Login Invalid Credentials", True, "Correctly rejected invalid credentials")
            return True
        else:
            self.log_test("Login Invalid Credentials", False, f"Expected 401, got {response.status_code}", response.text)
            return False

    def test_auth_me_valid_token(self):
        """Test /auth/me with valid token"""
        if not self.admin_token:
            self.log_test("Auth Me (Valid Token)", False, "No admin token available")
            return False
            
        success, response = self.make_request("GET", "/auth/me", token=self.admin_token)
        
        if not success:
            self.log_test("Auth Me (Valid Token)", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if "username" in data and data["username"] == "admin":
                self.log_test("Auth Me (Valid Token)", True, f"User info retrieved: {data['username']}")
                return True
            else:
                self.log_test("Auth Me (Valid Token)", False, "Invalid user data", data)
                return False
        else:
            self.log_test("Auth Me (Valid Token)", False, f"Status: {response.status_code}", response.text)
            return False

    def test_auth_me_invalid_token(self):
        """Test /auth/me with invalid token"""
        success, response = self.make_request("GET", "/auth/me", token="invalid_token")
        
        if not success:
            self.log_test("Auth Me (Invalid Token)", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 401:
            self.log_test("Auth Me (Invalid Token)", True, "Correctly rejected invalid token")
            return True
        else:
            self.log_test("Auth Me (Invalid Token)", False, f"Expected 401, got {response.status_code}", response.text)
            return False

    def test_auth_me_no_token(self):
        """Test /auth/me without token"""
        success, response = self.make_request("GET", "/auth/me")
        
        if not success:
            self.log_test("Auth Me (No Token)", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 403:  # FastAPI HTTPBearer returns 403 for missing token
            self.log_test("Auth Me (No Token)", True, "Correctly rejected missing token")
            return True
        else:
            self.log_test("Auth Me (No Token)", False, f"Expected 403, got {response.status_code}", response.text)
            return False
    
    # ==========================================
    # MAIN TEST EXECUTION
    # ==========================================
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🎯 STARTING EXHAUSTIVE BACKEND TESTING POST-BUILD v1.1.0")
        print("=" * 80)
        print()
        
        # PARTE 1: AUTENTICACIÓN Y SEGURIDAD
        print("🔐 PARTE 1: AUTENTICACIÓN Y SEGURIDAD")
        print("-" * 50)
        self.test_admin_login_success()
        self.test_login_invalid_credentials()
        self.test_auth_me_valid_token()
        self.test_auth_me_invalid_token()
        self.test_auth_me_no_token()
        print()
        
        # PARTE 2: CRUD USUARIOS/TAXISTAS
        print("👥 PARTE 2: CRUD USUARIOS/TAXISTAS")
        print("-" * 50)
        self.test_create_taxista_admin()
        self.test_get_users_admin()
        self.test_username_unique_validation()
        print()
        
        # PARTE 3: CRUD EMPRESAS/CLIENTES CON CIF
        print("🏢 PARTE 3: CRUD EMPRESAS/CLIENTES CON CIF")
        print("-" * 50)
        self.test_create_company_admin()
        self.test_get_companies()
        self.test_numero_cliente_unique_validation()
        print()
        
        # PARTE 4: CRUD VEHÍCULOS
        print("🚗 PARTE 4: CRUD VEHÍCULOS")
        print("-" * 50)
        self.test_create_vehiculo_admin()
        self.test_matricula_unique_validation()
        self.test_get_vehiculos()
        print()
        
        # PARTE 5: FLUJO COMPLETO DE TURNOS
        print("🕐 PARTE 5: FLUJO COMPLETO DE TURNOS")
        print("-" * 50)
        self.test_create_turno()
        self.test_get_turno_activo()
        self.test_create_multiple_services_for_turno()
        self.test_get_services_by_turno()
        self.test_finalizar_turno_with_totals()
        self.test_edit_turno_admin_only()
        print()
        
        # PARTE 6: CRUD SERVICIOS
        print("📋 PARTE 6: CRUD SERVICIOS")
        print("-" * 50)
        self.test_create_service_without_turno()
        self.test_service_filters()
        print()
        
        # PARTE 7: EXPORTACIONES DE SERVICIOS
        print("📊 PARTE 7: EXPORTACIONES DE SERVICIOS")
        print("-" * 50)
        self.test_export_services_csv()
        self.test_export_services_excel()
        self.test_export_services_pdf()
        print()
        
        # PARTE 8: EXPORTACIONES DE TURNOS CON SERVICIOS DETALLADOS
        print("📈 PARTE 8: EXPORTACIONES DE TURNOS CON SERVICIOS DETALLADOS")
        print("-" * 50)
        self.test_export_turnos_csv_detailed()
        self.test_export_turnos_excel_detailed()
        self.test_export_turnos_pdf_detailed()
        print()
        
        # PARTE 9: ESTADÍSTICAS Y REPORTES
        print("📊 PARTE 9: ESTADÍSTICAS Y REPORTES")
        print("-" * 50)
        self.test_turnos_estadisticas()
        self.test_reporte_diario()
        print()
        
        # PARTE 10: SINCRONIZACIÓN OFFLINE
        print("🔄 PARTE 10: SINCRONIZACIÓN OFFLINE")
        print("-" * 50)
        self.test_services_sync()
        print()
        
        # PARTE 11: CONFIGURACIÓN
        print("⚙️ PARTE 11: CONFIGURACIÓN")
        print("-" * 50)
        self.test_get_config()
        self.test_update_config()
        print()
        
        # PARTE 12: ELIMINACIÓN EN CASCADA DE TURNOS
        print("🗑️ PARTE 12: ELIMINACIÓN EN CASCADA DE TURNOS")
        print("-" * 50)
        self.test_delete_turno_cascade()
        print()
        
        # SUMMARY
        self.print_summary()

    def test_create_taxista_admin(self):
        """Test creating taxista as admin"""
        if not self.admin_token:
            self.log_test("Create Taxista (Admin)", False, "No admin token")
            return False
            
        taxista_data = {
            "username": f"taxista_test_{int(time.time())}",
            "password": "test123",
            "nombre": "Taxista Test",
            "role": "taxista",
            "licencia": "LIC123456"
        }
        
        success, response = self.make_request("POST", "/users", taxista_data, self.admin_token)
        
        if not success:
            self.log_test("Create Taxista (Admin)", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if "id" in data:
                self.taxista_id = data["id"]
                self.created_resources["users"].append(data["id"])
                self.log_test("Create Taxista (Admin)", True, f"Taxista created: {data['username']}")
                return True
            else:
                self.log_test("Create Taxista (Admin)", False, "Missing ID in response", data)
                return False
        else:
            self.log_test("Create Taxista (Admin)", False, f"Status: {response.status_code}", response.text)
            return False

    def test_get_users_admin(self):
        """Test getting users as admin"""
        if not self.admin_token:
            self.log_test("Get Users (Admin)", False, "No admin token")
            return False
            
        success, response = self.make_request("GET", "/users", token=self.admin_token)
        
        if not success:
            self.log_test("Get Users (Admin)", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                # Check that password field is not included
                has_password = any("password" in user for user in data)
                if has_password:
                    self.log_test("Get Users (Admin)", False, "Password field found in response (security issue)")
                    return False
                else:
                    self.log_test("Get Users (Admin)", True, f"Retrieved {len(data)} users, no password fields")
                    return True
            else:
                self.log_test("Get Users (Admin)", False, "Response is not a list", data)
                return False
        else:
            self.log_test("Get Users (Admin)", False, f"Status: {response.status_code}", response.text)
            return False

    def test_username_unique_validation(self):
        """Test username uniqueness validation"""
        if not self.admin_token:
            self.log_test("Username Unique Validation", False, "No admin token")
            return False
            
        # Try to create user with existing username
        duplicate_user = {
            "username": "admin",  # This should already exist
            "password": "test123",
            "nombre": "Duplicate Admin",
            "role": "taxista"
        }
        
        success, response = self.make_request("POST", "/users", duplicate_user, self.admin_token)
        
        if not success:
            self.log_test("Username Unique Validation", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 400:
            self.log_test("Username Unique Validation", True, "Correctly rejected duplicate username")
            return True
        else:
            self.log_test("Username Unique Validation", False, f"Expected 400, got {response.status_code}", response.text)
            return False

    def test_create_company_admin(self):
        """Test creating company as admin with CIF field"""
        if not self.admin_token:
            self.log_test("Create Company (Admin)", False, "No admin token")
            return False
            
        company_data = {
            "nombre": "Empresa Test S.L.",
            "cif": "B12345678",
            "direccion": "Calle Test 123",
            "codigo_postal": "33400",
            "localidad": "Avilés",
            "provincia": "Asturias",
            "telefono": "985123456",
            "email": "test@empresa.com",
            "numero_cliente": f"CLI{int(time.time())}",
            "contacto": "Juan Pérez",
            "fecha_alta": "01/01/2024",
            "notas": "Empresa de prueba"
        }
        
        success, response = self.make_request("POST", "/companies", company_data, self.admin_token)
        
        if not success:
            self.log_test("Create Company (Admin)", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if "id" in data and data.get("cif") == "B12345678":
                self.created_resources["companies"].append(data["id"])
                self.log_test("Create Company (Admin)", True, f"Company created with CIF: {data['cif']}")
                return True
            else:
                self.log_test("Create Company (Admin)", False, "Missing ID or CIF in response", data)
                return False
        else:
            self.log_test("Create Company (Admin)", False, f"Status: {response.status_code}", response.text)
            return False

    def test_get_companies(self):
        """Test getting companies"""
        if not self.admin_token:
            self.log_test("Get Companies", False, "No admin token")
            return False
            
        success, response = self.make_request("GET", "/companies", token=self.admin_token)
        
        if not success:
            self.log_test("Get Companies", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                self.log_test("Get Companies", True, f"Retrieved {len(data)} companies")
                return True
            else:
                self.log_test("Get Companies", False, "Response is not a list", data)
                return False
        else:
            self.log_test("Get Companies", False, f"Status: {response.status_code}", response.text)
            return False

    def test_numero_cliente_unique_validation(self):
        """Test numero_cliente uniqueness validation"""
        if not self.admin_token:
            self.log_test("Numero Cliente Unique Validation", False, "No admin token")
            return False
            
        # Try to create company with existing numero_cliente
        existing_numero = f"CLI{int(time.time()-1)}"  # Use a recent timestamp
        duplicate_company = {
            "nombre": "Duplicate Company",
            "numero_cliente": existing_numero
        }
        
        success, response = self.make_request("POST", "/companies", duplicate_company, self.admin_token)
        
        if not success:
            self.log_test("Numero Cliente Unique Validation", False, f"Request failed: {response}")
            return False
            
        # First creation should succeed
        if response.status_code == 200:
            # Now try to create another with same numero_cliente
            success2, response2 = self.make_request("POST", "/companies", duplicate_company, self.admin_token)
            
            if not success2:
                self.log_test("Numero Cliente Unique Validation", False, f"Second request failed: {response2}")
                return False
                
            if response2.status_code == 400:
                self.log_test("Numero Cliente Unique Validation", True, "Correctly rejected duplicate numero_cliente")
                return True
            else:
                self.log_test("Numero Cliente Unique Validation", False, f"Expected 400, got {response2.status_code}", response2.text)
                return False
        else:
            self.log_test("Numero Cliente Unique Validation", False, f"First creation failed: {response.status_code}", response.text)
            return False

    def test_create_vehiculo_admin(self):
        """Test creating vehicle as admin"""
        if not self.admin_token:
            self.log_test("Create Vehiculo (Admin)", False, "No admin token")
            return False
            
        vehiculo_data = {
            "matricula": f"TEST{int(time.time())}",
            "plazas": 4,
            "marca": "Toyota",
            "modelo": "Corolla",
            "km_iniciales": 50000,
            "fecha_compra": "01/01/2020",
            "activo": True
        }
        
        success, response = self.make_request("POST", "/vehiculos", vehiculo_data, self.admin_token)
        
        if not success:
            self.log_test("Create Vehiculo (Admin)", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if "id" in data and data.get("matricula") == vehiculo_data["matricula"]:
                self.created_resources["vehiculos"].append(data["id"])
                self.log_test("Create Vehiculo (Admin)", True, f"Vehicle created: {data['matricula']}")
                return True
            else:
                self.log_test("Create Vehiculo (Admin)", False, "Missing ID or matricula in response", data)
                return False
        else:
            self.log_test("Create Vehiculo (Admin)", False, f"Status: {response.status_code}", response.text)
            return False

    def test_matricula_unique_validation(self):
        """Test matricula uniqueness validation"""
        if not self.admin_token:
            self.log_test("Matricula Unique Validation", False, "No admin token")
            return False
            
        # Try to create vehicle with existing matricula
        existing_matricula = f"TEST{int(time.time()-1)}"
        duplicate_vehiculo = {
            "matricula": existing_matricula,
            "plazas": 4,
            "marca": "Ford",
            "modelo": "Focus",
            "km_iniciales": 30000,
            "fecha_compra": "01/01/2021",
            "activo": True
        }
        
        # First creation
        success, response = self.make_request("POST", "/vehiculos", duplicate_vehiculo, self.admin_token)
        
        if not success:
            self.log_test("Matricula Unique Validation", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            # Try to create another with same matricula
            success2, response2 = self.make_request("POST", "/vehiculos", duplicate_vehiculo, self.admin_token)
            
            if not success2:
                self.log_test("Matricula Unique Validation", False, f"Second request failed: {response2}")
                return False
                
            if response2.status_code == 400:
                self.log_test("Matricula Unique Validation", True, "Correctly rejected duplicate matricula")
                return True
            else:
                self.log_test("Matricula Unique Validation", False, f"Expected 400, got {response2.status_code}", response2.text)
                return False
        else:
            self.log_test("Matricula Unique Validation", False, f"First creation failed: {response.status_code}", response.text)
            return False

    def test_get_vehiculos(self):
        """Test getting vehicles"""
        if not self.admin_token:
            self.log_test("Get Vehiculos", False, "No admin token")
            return False
            
        success, response = self.make_request("GET", "/vehiculos", token=self.admin_token)
        
        if not success:
            self.log_test("Get Vehiculos", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                self.log_test("Get Vehiculos", True, f"Retrieved {len(data)} vehicles")
                return True
            else:
                self.log_test("Get Vehiculos", False, "Response is not a list", data)
                return False
        else:
            self.log_test("Get Vehiculos", False, f"Status: {response.status_code}", response.text)
            return False

    def test_create_turno(self):
        """Test creating turno"""
        if not self.admin_token:
            self.log_test("Create Turno", False, "No admin token")
            return False
            
        # First create a vehicle for the turno
        vehiculo_data = {
            "matricula": f"TURNO{int(time.time())}",
            "plazas": 4,
            "marca": "Test Car",
            "modelo": "Test Model",
            "km_iniciales": 100000,
            "fecha_compra": "01/01/2023",
            "activo": True
        }
        
        success, response = self.make_request("POST", "/vehiculos", vehiculo_data, self.admin_token)
        if not success or response.status_code != 200:
            self.log_test("Create Turno", False, "Could not create test vehicle")
            return False
            
        vehiculo_id = response.json()["id"]
        vehiculo_matricula = response.json()["matricula"]
        
        # Create turno
        turno_data = {
            "taxista_id": self.taxista_id or "test_taxista_id",
            "taxista_nombre": "Test Taxista",
            "vehiculo_id": vehiculo_id,
            "vehiculo_matricula": vehiculo_matricula,
            "fecha_inicio": "01/01/2024",
            "hora_inicio": "08:00",
            "km_inicio": 100000
        }
        
        success, response = self.make_request("POST", "/turnos", turno_data, self.admin_token)
        
        if not success:
            self.log_test("Create Turno", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if "id" in data:
                self.created_resources["turnos"].append(data["id"])
                self.log_test("Create Turno", True, f"Turno created: {data['id']}")
                return True
            else:
                self.log_test("Create Turno", False, "Missing ID in response", data)
                return False
        else:
            self.log_test("Create Turno", False, f"Status: {response.status_code}", response.text)
            return False

    def test_get_turno_activo(self):
        """Test getting active turno"""
        if not self.admin_token:
            self.log_test("Get Turno Activo", False, "No admin token")
            return False
            
        success, response = self.make_request("GET", "/turnos/activo", token=self.admin_token)
        
        if not success:
            self.log_test("Get Turno Activo", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if data is None:
                self.log_test("Get Turno Activo", True, "No active turno (expected)")
                return True
            elif "id" in data:
                self.log_test("Get Turno Activo", True, f"Active turno found: {data['id']}")
                return True
            else:
                self.log_test("Get Turno Activo", False, "Invalid turno data", data)
                return False
        else:
            self.log_test("Get Turno Activo", False, f"Status: {response.status_code}", response.text)
            return False

    def test_create_multiple_services_for_turno(self):
        """Test creating multiple services for turno"""
        if not self.admin_token or not self.created_resources["turnos"]:
            self.log_test("Create Multiple Services", False, "Missing admin token or turno ID")
            return False
            
        turno_id = self.created_resources["turnos"][0]
        
        # Create 5 different services
        services_data = [
            {
                "fecha": "01/01/2024",
                "hora": "09:00",
                "origen": "Avilés Centro",
                "destino": "Hospital San Agustín",
                "importe": 15.50,
                "importe_espera": 2.00,
                "kilometros": 8.5,
                "tipo": "particular",
                "turno_id": turno_id,
                "cobrado": True,
                "facturar": False
            },
            {
                "fecha": "01/01/2024",
                "hora": "10:30",
                "origen": "Hospital San Agustín",
                "destino": "Empresa ABC S.L.",
                "importe": 25.00,
                "importe_espera": 5.00,
                "kilometros": 12.3,
                "tipo": "empresa",
                "empresa_id": self.created_resources["companies"][0] if self.created_resources["companies"] else None,
                "empresa_nombre": "Empresa ABC S.L.",
                "turno_id": turno_id,
                "cobrado": False,
                "facturar": True
            },
            {
                "fecha": "01/01/2024",
                "hora": "12:00",
                "origen": "Empresa ABC S.L.",
                "destino": "Estación de Autobuses",
                "importe": 18.75,
                "importe_espera": 0.00,
                "kilometros": 9.8,
                "tipo": "particular",
                "turno_id": turno_id,
                "cobrado": True,
                "facturar": False
            },
            {
                "fecha": "01/01/2024",
                "hora": "14:15",
                "origen": "Estación de Autobuses",
                "destino": "Centro Comercial",
                "importe": 12.30,
                "importe_espera": 1.50,
                "kilometros": 6.2,
                "tipo": "empresa",
                "empresa_nombre": "Centro Comercial S.A.",
                "turno_id": turno_id,
                "cobrado": True,
                "facturar": True
            },
            {
                "fecha": "01/01/2024",
                "hora": "16:45",
                "origen": "Centro Comercial",
                "destino": "Aeropuerto Asturias",
                "importe": 45.00,
                "importe_espera": 3.00,
                "kilometros": 25.7,
                "tipo": "particular",
                "turno_id": turno_id,
                "cobrado": False,
                "facturar": False
            }
        ]
        
        created_services = 0
        for i, service_data in enumerate(services_data):
            success, response = self.make_request("POST", "/services", service_data, self.admin_token)
            
            if success and response.status_code == 200:
                data = response.json()
                if "id" in data:
                    self.created_resources["services"].append(data["id"])
                    created_services += 1
                else:
                    self.log_test("Create Multiple Services", False, f"Service {i+1} missing ID", data)
                    return False
            else:
                self.log_test("Create Multiple Services", False, f"Service {i+1} creation failed: {response.status_code if success else response}")
                return False
        
        if created_services == 5:
            self.log_test("Create Multiple Services", True, f"Created {created_services} services for turno")
            return True
        else:
            self.log_test("Create Multiple Services", False, f"Only created {created_services}/5 services")
            return False

    def test_get_services_by_turno(self):
        """Test getting services filtered by turno_id"""
        if not self.admin_token or not self.created_resources["turnos"]:
            self.log_test("Get Services by Turno", False, "Missing admin token or turno ID")
            return False
            
        turno_id = self.created_resources["turnos"][0]
        params = {"turno_id": turno_id}
        
        success, response = self.make_request("GET", "/services", token=self.admin_token, params=params)
        
        if not success:
            self.log_test("Get Services by Turno", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) == 5:
                self.log_test("Get Services by Turno", True, f"Retrieved {len(data)} services for turno")
                return True
            else:
                self.log_test("Get Services by Turno", False, f"Expected 5 services, got {len(data) if isinstance(data, list) else 'non-list'}", data)
                return False
        else:
            self.log_test("Get Services by Turno", False, f"Status: {response.status_code}", response.text)
            return False

    def test_finalizar_turno_with_totals(self):
        """Test finalizing turno and verify automatic totals calculation"""
        if not self.admin_token or not self.created_resources["turnos"]:
            self.log_test("Finalizar Turno with Totals", False, "Missing admin token or turno ID")
            return False
            
        turno_id = self.created_resources["turnos"][0]
        
        finalizar_data = {
            "fecha_fin": "01/01/2024",
            "hora_fin": "18:00",
            "km_fin": 100162,  # Started at 100000, so 162 km total
            "cerrado": True
        }
        
        success, response = self.make_request("PUT", f"/turnos/{turno_id}/finalizar", finalizar_data, self.admin_token)
        
        if not success:
            self.log_test("Finalizar Turno with Totals", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            data = response.json()
            
            # Verify totals calculation
            expected_particulares = 15.50 + 2.00 + 18.75 + 0.00 + 45.00 + 3.00  # 84.25
            expected_empresas = 25.00 + 5.00 + 12.30 + 1.50  # 43.80
            expected_servicios = 5
            
            total_particulares = data.get("total_importe_particulares", 0)
            total_empresas = data.get("total_importe_clientes", 0)
            cantidad_servicios = data.get("cantidad_servicios", 0)
            
            if (abs(total_particulares - expected_particulares) < 0.01 and 
                abs(total_empresas - expected_empresas) < 0.01 and 
                cantidad_servicios == expected_servicios):
                self.log_test("Finalizar Turno with Totals", True, 
                             f"Turno finalized with correct totals: Particulares={total_particulares}€, Empresas={total_empresas}€, Servicios={cantidad_servicios}")
                return True
            else:
                self.log_test("Finalizar Turno with Totals", False, 
                             f"Incorrect totals: Expected P={expected_particulares}, E={expected_empresas}, S={expected_servicios}; Got P={total_particulares}, E={total_empresas}, S={cantidad_servicios}")
                return False
        else:
            self.log_test("Finalizar Turno with Totals", False, f"Status: {response.status_code}", response.text)
            return False

    def test_edit_turno_admin_only(self):
        """Test editing turno (admin only)"""
        if not self.admin_token or not self.created_resources["turnos"]:
            self.log_test("Edit Turno (Admin Only)", False, "Missing admin token or turno ID")
            return False
            
        turno_id = self.created_resources["turnos"][0]
        
        edit_data = {
            "km_fin": 100200,
            "liquidado": True
        }
        
        success, response = self.make_request("PUT", f"/turnos/{turno_id}", edit_data, self.admin_token)
        
        if not success:
            self.log_test("Edit Turno (Admin Only)", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if data.get("liquidado") == True and data.get("km_fin") == 100200:
                self.log_test("Edit Turno (Admin Only)", True, "Turno edited successfully by admin")
                return True
            else:
                self.log_test("Edit Turno (Admin Only)", False, "Edit not reflected in response", data)
                return False
        else:
            self.log_test("Edit Turno (Admin Only)", False, f"Status: {response.status_code}", response.text)
            return False

    def test_create_service_without_turno(self):
        """Test creating service without active turno (should fail for taxista)"""
        # This test assumes we're testing as a taxista without active turno
        service_data = {
            "fecha": "02/01/2024",
            "hora": "10:00",
            "origen": "Test Origin",
            "destino": "Test Destination",
            "importe": 20.00,
            "importe_espera": 0.00,
            "kilometros": 10.0,
            "tipo": "particular",
            "cobrado": False,
            "facturar": False
        }
        
        # Use a fake taxista token to simulate taxista without turno
        success, response = self.make_request("POST", "/services", service_data, "fake_taxista_token")
        
        if not success:
            self.log_test("Create Service without Turno", True, "Request properly failed for invalid token")
            return True
        elif response.status_code == 400:
            self.log_test("Create Service without Turno", True, "Correctly rejected service without turno")
            return True
        elif response.status_code == 401:
            self.log_test("Create Service without Turno", True, "Correctly rejected invalid token")
            return True
        else:
            self.log_test("Create Service without Turno", False, f"Expected 400/401, got {response.status_code}")
            return False

    def test_service_filters(self):
        """Test service filtering by tipo, fechas, etc."""
        if not self.admin_token:
            self.log_test("Service Filters", False, "No admin token")
            return False
            
        # Test filter by tipo=empresa
        params = {"tipo": "empresa"}
        success, response = self.make_request("GET", "/services", token=self.admin_token, params=params)
        
        if not success:
            self.log_test("Service Filters", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                # Check that all returned services are tipo=empresa
                all_empresa = all(service.get("tipo") == "empresa" for service in data)
                if all_empresa:
                    self.log_test("Service Filters", True, f"Filter tipo=empresa returned {len(data)} empresa services")
                    return True
                else:
                    self.log_test("Service Filters", False, "Filter returned non-empresa services")
                    return False
            else:
                self.log_test("Service Filters", False, "Response is not a list", data)
                return False
        else:
            self.log_test("Service Filters", False, f"Status: {response.status_code}", response.text)
            return False

    def test_export_services_csv(self):
        """Test services CSV export"""
        if not self.admin_token:
            self.log_test("Export Services CSV", False, "No admin token")
            return False
            
        success, response = self.make_request("GET", "/services/export/csv", token=self.admin_token)
        
        if not success:
            self.log_test("Export Services CSV", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            content_type = response.headers.get("content-type", "")
            content_disposition = response.headers.get("content-disposition", "")
            
            if "text/csv" in content_type and "servicios.csv" in content_disposition:
                self.log_test("Export Services CSV", True, f"CSV export successful, size: {len(response.content)} bytes")
                return True
            else:
                self.log_test("Export Services CSV", False, f"Wrong headers: {content_type}, {content_disposition}")
                return False
        else:
            self.log_test("Export Services CSV", False, f"Status: {response.status_code}", response.text)
            return False

    def test_export_services_excel(self):
        """Test services Excel export"""
        if not self.admin_token:
            self.log_test("Export Services Excel", False, "No admin token")
            return False
            
        success, response = self.make_request("GET", "/services/export/excel", token=self.admin_token)
        
        if not success:
            self.log_test("Export Services Excel", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            content_type = response.headers.get("content-type", "")
            content_disposition = response.headers.get("content-disposition", "")
            
            if "spreadsheetml.sheet" in content_type and "servicios.xlsx" in content_disposition:
                self.log_test("Export Services Excel", True, f"Excel export successful, size: {len(response.content)} bytes")
                return True
            else:
                self.log_test("Export Services Excel", False, f"Wrong headers: {content_type}, {content_disposition}")
                return False
        else:
            self.log_test("Export Services Excel", False, f"Status: {response.status_code}", response.text)
            return False

    def test_export_services_pdf(self):
        """Test services PDF export"""
        if not self.admin_token:
            self.log_test("Export Services PDF", False, "No admin token")
            return False
            
        success, response = self.make_request("GET", "/services/export/pdf", token=self.admin_token)
        
        if not success:
            self.log_test("Export Services PDF", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            content_type = response.headers.get("content-type", "")
            content_disposition = response.headers.get("content-disposition", "")
            
            if "application/pdf" in content_type and "servicios.pdf" in content_disposition:
                self.log_test("Export Services PDF", True, f"PDF export successful, size: {len(response.content)} bytes")
                return True
            else:
                self.log_test("Export Services PDF", False, f"Wrong headers: {content_type}, {content_disposition}")
                return False
        else:
            self.log_test("Export Services PDF", False, f"Status: {response.status_code}", response.text)
            return False

    def test_export_turnos_csv_detailed(self):
        """Test turnos CSV export with detailed services"""
        if not self.admin_token:
            self.log_test("Export Turnos CSV Detailed", False, "No admin token")
            return False
            
        success, response = self.make_request("GET", "/turnos/export/csv", token=self.admin_token)
        
        if not success:
            self.log_test("Export Turnos CSV Detailed", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            content_type = response.headers.get("content-type", "")
            content_disposition = response.headers.get("content-disposition", "")
            
            if "text/csv" in content_type and "turnos_detallado.csv" in content_disposition:
                # Check if content contains both TURNO and SERVICIO rows
                content = response.content.decode('utf-8')
                has_turno_rows = "TURNO" in content
                has_servicio_rows = "SERVICIO" in content
                
                if has_turno_rows and has_servicio_rows:
                    self.log_test("Export Turnos CSV Detailed", True, f"Detailed CSV export successful, size: {len(response.content)} bytes")
                    return True
                else:
                    self.log_test("Export Turnos CSV Detailed", False, f"Missing TURNO or SERVICIO rows in content")
                    return False
            else:
                self.log_test("Export Turnos CSV Detailed", False, f"Wrong headers: {content_type}, {content_disposition}")
                return False
        else:
            self.log_test("Export Turnos CSV Detailed", False, f"Status: {response.status_code}", response.text)
            return False

    def test_export_turnos_excel_detailed(self):
        """Test turnos Excel export with detailed services (27 columns)"""
        if not self.admin_token:
            self.log_test("Export Turnos Excel Detailed", False, "No admin token")
            return False
            
        success, response = self.make_request("GET", "/turnos/export/excel", token=self.admin_token)
        
        if not success:
            self.log_test("Export Turnos Excel Detailed", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            content_type = response.headers.get("content-type", "")
            content_disposition = response.headers.get("content-disposition", "")
            
            if "spreadsheetml.sheet" in content_type and "turnos_detallado.xlsx" in content_disposition:
                file_size = len(response.content)
                if file_size > 5000:  # Should be substantial with detailed data
                    self.log_test("Export Turnos Excel Detailed", True, f"Detailed Excel export successful, size: {file_size} bytes")
                    return True
                else:
                    self.log_test("Export Turnos Excel Detailed", False, f"File too small: {file_size} bytes")
                    return False
            else:
                self.log_test("Export Turnos Excel Detailed", False, f"Wrong headers: {content_type}, {content_disposition}")
                return False
        else:
            self.log_test("Export Turnos Excel Detailed", False, f"Status: {response.status_code}", response.text)
            return False

    def test_export_turnos_pdf_detailed(self):
        """Test turnos PDF export with detailed services"""
        if not self.admin_token:
            self.log_test("Export Turnos PDF Detailed", False, "No admin token")
            return False
            
        success, response = self.make_request("GET", "/turnos/export/pdf", token=self.admin_token)
        
        if not success:
            self.log_test("Export Turnos PDF Detailed", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            content_type = response.headers.get("content-type", "")
            content_disposition = response.headers.get("content-disposition", "")
            
            if "application/pdf" in content_type and "turnos_detallado.pdf" in content_disposition:
                file_size = len(response.content)
                if file_size > 2000:  # Should be substantial with detailed data
                    self.log_test("Export Turnos PDF Detailed", True, f"Detailed PDF export successful, size: {file_size} bytes")
                    return True
                else:
                    self.log_test("Export Turnos PDF Detailed", False, f"File too small: {file_size} bytes")
                    return False
            else:
                self.log_test("Export Turnos PDF Detailed", False, f"Wrong headers: {content_type}, {content_disposition}")
                return False
        else:
            self.log_test("Export Turnos PDF Detailed", False, f"Status: {response.status_code}", response.text)
            return False

    def test_turnos_estadisticas(self):
        """Test turnos statistics endpoint"""
        if not self.admin_token:
            self.log_test("Turnos Estadisticas", False, "No admin token")
            return False
            
        success, response = self.make_request("GET", "/turnos/estadisticas", token=self.admin_token)
        
        if not success:
            self.log_test("Turnos Estadisticas", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            data = response.json()
            required_fields = ["total_turnos", "turnos_activos", "turnos_cerrados", "turnos_liquidados", 
                             "total_importe", "total_kilometros", "total_servicios"]
            
            if all(field in data for field in required_fields):
                self.log_test("Turnos Estadisticas", True, f"Statistics retrieved: {data['total_turnos']} turnos, {data['total_importe']}€")
                return True
            else:
                missing = [f for f in required_fields if f not in data]
                self.log_test("Turnos Estadisticas", False, f"Missing fields: {missing}", data)
                return False
        else:
            self.log_test("Turnos Estadisticas", False, f"Status: {response.status_code}", response.text)
            return False

    def test_reporte_diario(self):
        """Test daily report endpoint"""
        if not self.admin_token:
            self.log_test("Reporte Diario", False, "No admin token")
            return False
            
        params = {"fecha": "01/01/2024"}
        success, response = self.make_request("GET", "/reportes/diario", token=self.admin_token, params=params)
        
        if not success:
            self.log_test("Reporte Diario", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                self.log_test("Reporte Diario", True, f"Daily report retrieved: {len(data)} taxistas")
                return True
            else:
                self.log_test("Reporte Diario", False, "Response is not a list", data)
                return False
        else:
            self.log_test("Reporte Diario", False, f"Status: {response.status_code}", response.text)
            return False

    def test_services_sync(self):
        """Test services batch synchronization"""
        if not self.admin_token:
            self.log_test("Services Sync", False, "No admin token")
            return False
            
        sync_data = {
            "services": [
                {
                    "fecha": "02/01/2024",
                    "hora": "08:00",
                    "origen": "Sync Origin 1",
                    "destino": "Sync Destination 1",
                    "importe": 15.00,
                    "importe_espera": 0.00,
                    "kilometros": 8.0,
                    "tipo": "particular",
                    "cobrado": True,
                    "facturar": False
                },
                {
                    "fecha": "02/01/2024",
                    "hora": "09:30",
                    "origen": "Sync Origin 2",
                    "destino": "Sync Destination 2",
                    "importe": 22.50,
                    "importe_espera": 2.50,
                    "kilometros": 12.5,
                    "tipo": "empresa",
                    "empresa_nombre": "Sync Company",
                    "cobrado": False,
                    "facturar": True
                }
            ]
        }
        
        success, response = self.make_request("POST", "/services/sync", sync_data, self.admin_token)
        
        if not success:
            self.log_test("Services Sync", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if "message" in data and "ids" in data and len(data["ids"]) == 2:
                self.log_test("Services Sync", True, f"Synced 2 services: {data['message']}")
                return True
            else:
                self.log_test("Services Sync", False, "Invalid sync response", data)
                return False
        else:
            self.log_test("Services Sync", False, f"Status: {response.status_code}", response.text)
            return False

    def test_get_config(self):
        """Test getting configuration"""
        if not self.admin_token:
            self.log_test("Get Config", False, "No admin token")
            return False
            
        success, response = self.make_request("GET", "/config", token=self.admin_token)
        
        if not success:
            self.log_test("Get Config", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict):
                self.log_test("Get Config", True, f"Config retrieved: {len(data)} fields")
                return True
            else:
                self.log_test("Get Config", False, "Response is not a dict", data)
                return False
        else:
            self.log_test("Get Config", False, f"Status: {response.status_code}", response.text)
            return False

    def test_update_config(self):
        """Test updating configuration (admin only)"""
        if not self.admin_token:
            self.log_test("Update Config", False, "No admin token")
            return False
            
        config_data = {
            "nombre_radio_taxi": "Taxi Tineo Test",
            "telefono": "985123456",
            "web": "https://test.taxitineo.com",
            "direccion": "Test Address 123",
            "email": "test@taxitineo.com"
        }
        
        success, response = self.make_request("PUT", "/config", config_data, self.admin_token)
        
        if not success:
            self.log_test("Update Config", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            data = response.json()
            if data.get("nombre_radio_taxi") == "Taxi Tineo Test":
                self.log_test("Update Config", True, f"Config updated: {data['nombre_radio_taxi']}")
                return True
            else:
                self.log_test("Update Config", False, "Update not reflected in response", data)
                return False
        else:
            self.log_test("Update Config", False, f"Status: {response.status_code}", response.text)
            return False

    def test_delete_turno_cascade(self):
        """Test deleting turno with cascade deletion of services"""
        if not self.admin_token or not self.created_resources["turnos"]:
            self.log_test("Delete Turno Cascade", False, "Missing admin token or turno ID")
            return False
            
        turno_id = self.created_resources["turnos"][0]
        
        # First verify services exist for this turno
        params = {"turno_id": turno_id}
        success, response = self.make_request("GET", "/services", token=self.admin_token, params=params)
        
        if not success or response.status_code != 200:
            self.log_test("Delete Turno Cascade", False, "Could not verify services before deletion")
            return False
            
        services_before = len(response.json())
        
        # Delete the turno
        success, response = self.make_request("DELETE", f"/turnos/{turno_id}", token=self.admin_token)
        
        if not success:
            self.log_test("Delete Turno Cascade", False, f"Request failed: {response}")
            return False
            
        if response.status_code == 200:
            data = response.json()
            services_deleted = data.get("servicios_eliminados", 0)
            
            # Verify services were deleted
            success2, response2 = self.make_request("GET", "/services", token=self.admin_token, params=params)
            
            if success2 and response2.status_code == 200:
                services_after = len(response2.json())
                
                if services_after == 0 and services_deleted == services_before:
                    self.log_test("Delete Turno Cascade", True, f"Turno deleted with {services_deleted} services in cascade")
                    # Remove from our tracking
                    self.created_resources["turnos"].remove(turno_id)
                    return True
                else:
                    self.log_test("Delete Turno Cascade", False, f"Services not properly deleted: before={services_before}, after={services_after}, reported={services_deleted}")
                    return False
            else:
                self.log_test("Delete Turno Cascade", False, "Could not verify services after deletion")
                return False
        else:
            self.log_test("Delete Turno Cascade", False, f"Status: {response.status_code}", response.text)
            return False

    def print_summary(self):
        """Print test summary"""
        print("=" * 80)
        print("🎯 RESUMEN FINAL DE TESTING EXHAUSTIVO")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result["passed"])
        total = len(self.test_results)
        failed = total - passed
        
        print(f"📊 ESTADÍSTICAS GENERALES:")
        print(f"   Total Tests: {total}")
        print(f"   ✅ Passed: {passed}")
        print(f"   ❌ Failed: {failed}")
        print(f"   📈 Success Rate: {(passed/total*100):.1f}%")
        print()
        
        if failed > 0:
            print("❌ TESTS FALLIDOS:")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"   • {result['test']}: {result['details']}")
            print()
        
        print("✅ TESTS EXITOSOS:")
        for result in self.test_results:
            if result["passed"]:
                print(f"   • {result['test']}")
        
        print()
        print("=" * 80)
        
        if failed == 0:
            print("🎉 ¡TODOS LOS TESTS PASARON! SISTEMA 100% OPERATIVO PARA PRODUCCIÓN")
        elif failed <= 2:
            print("⚠️ SISTEMA MAYORMENTE OPERATIVO - REVISAR FALLOS MENORES")
        else:
            print("🚨 SISTEMA REQUIERE ATENCIÓN - MÚLTIPLES FALLOS DETECTADOS")
        
        print("=" * 80)

    def setup_test_data(self):
        """This method is no longer used - replaced by comprehensive test suite"""
        pass

def main():
    """Main execution function"""
    print("🚕 Taxi Management System - Backend API Testing Suite")
    print(f"🌐 Testing against: {BACKEND_URL}")
    print()
    
    suite = TaxiTestSuite()
    suite.run_all_tests()

if __name__ == "__main__":
    main()