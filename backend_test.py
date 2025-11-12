#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Taxi Tineo Management System
Tests all CRUD operations, authentication, authorization, filters, and exports
"""

import requests
import json
import sys
from datetime import datetime, timedelta
import io

# Configuration
BASE_URL = "https://taxiflow-admin.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {"username": "admin", "password": "admin123"}
TAXISTA_CREDENTIALS = {"username": "taxista1", "password": "taxista123"}

class TaxiTineoAPITester:
    def __init__(self):
        self.admin_token = None
        self.taxista_token = None
        self.test_results = []
        self.created_resources = {
            'users': [],
            'companies': [],
            'services': []
        }
        
    def log_result(self, test_name, success, message, details=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            'test': test_name,
            'status': status,
            'message': message,
            'details': details or {}
        }
        self.test_results.append(result)
        print(f"{status}: {test_name} - {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def authenticate_admin(self):
        """Authenticate as admin and get token"""
        try:
            response = requests.post(f"{BASE_URL}/auth/login", json=ADMIN_CREDENTIALS)
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data['access_token']
                self.log_result("Admin Authentication", True, "Admin login successful")
                return True
            else:
                self.log_result("Admin Authentication", False, f"Login failed: {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("Admin Authentication", False, f"Exception: {str(e)}")
            return False
    
    def authenticate_taxista(self):
        """Authenticate as taxista and get token"""
        try:
            response = requests.post(f"{BASE_URL}/auth/login", json=TAXISTA_CREDENTIALS)
            if response.status_code == 200:
                data = response.json()
                self.taxista_token = data['access_token']
                self.log_result("Taxista Authentication", True, "Taxista login successful")
                return True
            else:
                self.log_result("Taxista Authentication", False, f"Login failed: {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("Taxista Authentication", False, f"Exception: {str(e)}")
            return False
    
    def test_auth_endpoints(self):
        """Test authentication endpoints"""
        print("\n=== TESTING AUTHENTICATION ===")
        
        # Test invalid credentials
        try:
            response = requests.post(f"{BASE_URL}/auth/login", json={"username": "invalid", "password": "invalid"})
            if response.status_code == 401:
                self.log_result("Invalid Login", True, "Correctly rejected invalid credentials")
            else:
                self.log_result("Invalid Login", False, f"Expected 401, got {response.status_code}")
        except Exception as e:
            self.log_result("Invalid Login", False, f"Exception: {str(e)}")
        
        # Test /auth/me with admin token
        if self.admin_token:
            try:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('role') == 'admin':
                        self.log_result("Admin /auth/me", True, "Admin profile retrieved correctly")
                    else:
                        self.log_result("Admin /auth/me", False, f"Wrong role: {data.get('role')}")
                else:
                    self.log_result("Admin /auth/me", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_result("Admin /auth/me", False, f"Exception: {str(e)}")
        
        # Test /auth/me with taxista token
        if self.taxista_token:
            try:
                headers = {"Authorization": f"Bearer {self.taxista_token}"}
                response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('role') == 'taxista':
                        self.log_result("Taxista /auth/me", True, "Taxista profile retrieved correctly")
                    else:
                        self.log_result("Taxista /auth/me", False, f"Wrong role: {data.get('role')}")
                else:
                    self.log_result("Taxista /auth/me", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_result("Taxista /auth/me", False, f"Exception: {str(e)}")
    
    def test_user_crud(self):
        """Test user CRUD operations"""
        print("\n=== TESTING USER CRUD ===")
        
        if not self.admin_token:
            self.log_result("User CRUD Setup", False, "No admin token available")
            return
        
        admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test create user (admin only)
        test_user = {
            "username": f"test_taxista_{datetime.now().strftime('%H%M%S')}",
            "password": "test123",
            "nombre": "Taxista de Prueba",
            "role": "taxista"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/users", json=test_user, headers=admin_headers)
            if response.status_code == 200:
                data = response.json()
                user_id = data['id']
                self.created_resources['users'].append(user_id)
                self.log_result("Create User (Admin)", True, f"User created with ID: {user_id}")
            else:
                self.log_result("Create User (Admin)", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_result("Create User (Admin)", False, f"Exception: {str(e)}")
        
        # Test create user with taxista token (should fail)
        if self.taxista_token:
            taxista_headers = {"Authorization": f"Bearer {self.taxista_token}"}
            try:
                response = requests.post(f"{BASE_URL}/users", json=test_user, headers=taxista_headers)
                if response.status_code == 403:
                    self.log_result("Create User (Taxista - Should Fail)", True, "Correctly denied access to taxista")
                else:
                    self.log_result("Create User (Taxista - Should Fail)", False, f"Expected 403, got {response.status_code}")
            except Exception as e:
                self.log_result("Create User (Taxista - Should Fail)", False, f"Exception: {str(e)}")
        
        # Test list users (admin only)
        try:
            response = requests.get(f"{BASE_URL}/users", headers=admin_headers)
            if response.status_code == 200:
                data = response.json()
                self.log_result("List Users (Admin)", True, f"Retrieved {len(data)} users")
            else:
                self.log_result("List Users (Admin)", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("List Users (Admin)", False, f"Exception: {str(e)}")
        
        # Test list users with taxista token (should fail)
        if self.taxista_token:
            taxista_headers = {"Authorization": f"Bearer {self.taxista_token}"}
            try:
                response = requests.get(f"{BASE_URL}/users", headers=taxista_headers)
                if response.status_code == 403:
                    self.log_result("List Users (Taxista - Should Fail)", True, "Correctly denied access to taxista")
                else:
                    self.log_result("List Users (Taxista - Should Fail)", False, f"Expected 403, got {response.status_code}")
            except Exception as e:
                self.log_result("List Users (Taxista - Should Fail)", False, f"Exception: {str(e)}")
    
    def test_company_crud(self):
        """Test company CRUD operations"""
        print("\n=== TESTING COMPANY CRUD ===")
        
        if not self.admin_token:
            self.log_result("Company CRUD Setup", False, "No admin token available")
            return
        
        admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test create company (admin only)
        test_company = {
            "nombre": f"Empresa Test {datetime.now().strftime('%H%M%S')}",
            "cif": "B12345678",
            "direccion": "Calle Test 123",
            "localidad": "Tineo",
            "provincia": "Asturias"
        }
        
        company_id = None
        try:
            response = requests.post(f"{BASE_URL}/companies", json=test_company, headers=admin_headers)
            if response.status_code == 200:
                data = response.json()
                company_id = data['id']
                self.created_resources['companies'].append(company_id)
                self.log_result("Create Company (Admin)", True, f"Company created with ID: {company_id}")
            else:
                self.log_result("Create Company (Admin)", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_result("Create Company (Admin)", False, f"Exception: {str(e)}")
        
        # Test create company with taxista token (should fail)
        if self.taxista_token:
            taxista_headers = {"Authorization": f"Bearer {self.taxista_token}"}
            try:
                response = requests.post(f"{BASE_URL}/companies", json=test_company, headers=taxista_headers)
                if response.status_code == 403:
                    self.log_result("Create Company (Taxista - Should Fail)", True, "Correctly denied access to taxista")
                else:
                    self.log_result("Create Company (Taxista - Should Fail)", False, f"Expected 403, got {response.status_code}")
            except Exception as e:
                self.log_result("Create Company (Taxista - Should Fail)", False, f"Exception: {str(e)}")
        
        # Test list companies (both admin and taxista should work)
        try:
            response = requests.get(f"{BASE_URL}/companies", headers=admin_headers)
            if response.status_code == 200:
                data = response.json()
                self.log_result("List Companies (Admin)", True, f"Retrieved {len(data)} companies")
            else:
                self.log_result("List Companies (Admin)", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("List Companies (Admin)", False, f"Exception: {str(e)}")
        
        if self.taxista_token:
            taxista_headers = {"Authorization": f"Bearer {self.taxista_token}"}
            try:
                response = requests.get(f"{BASE_URL}/companies", headers=taxista_headers)
                if response.status_code == 200:
                    data = response.json()
                    self.log_result("List Companies (Taxista)", True, f"Retrieved {len(data)} companies")
                else:
                    self.log_result("List Companies (Taxista)", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_result("List Companies (Taxista)", False, f"Exception: {str(e)}")
        
        # Test update company (admin only)
        if company_id:
            updated_company = test_company.copy()
            updated_company["nombre"] = f"Empresa Updated {datetime.now().strftime('%H%M%S')}"
            
            try:
                response = requests.put(f"{BASE_URL}/companies/{company_id}", json=updated_company, headers=admin_headers)
                if response.status_code == 200:
                    self.log_result("Update Company (Admin)", True, "Company updated successfully")
                else:
                    self.log_result("Update Company (Admin)", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_result("Update Company (Admin)", False, f"Exception: {str(e)}")
    
    def test_service_crud(self):
        """Test service CRUD operations"""
        print("\n=== TESTING SERVICE CRUD ===")
        
        # Test create service as taxista
        test_service = {
            "fecha": "20/12/2024",
            "hora": "14:30",
            "origen": "Tineo Centro",
            "destino": "Hospital de Cangas",
            "importe": 25.50,
            "importe_espera": 5.0,
            "kilometros": 18.2,
            "tipo": "particular"
        }
        
        service_id = None
        if self.taxista_token:
            taxista_headers = {"Authorization": f"Bearer {self.taxista_token}"}
            try:
                response = requests.post(f"{BASE_URL}/services", json=test_service, headers=taxista_headers)
                if response.status_code == 200:
                    data = response.json()
                    service_id = data['id']
                    self.created_resources['services'].append(service_id)
                    self.log_result("Create Service (Taxista)", True, f"Service created with ID: {service_id}")
                else:
                    self.log_result("Create Service (Taxista)", False, f"Status: {response.status_code}, Response: {response.text}")
            except Exception as e:
                self.log_result("Create Service (Taxista)", False, f"Exception: {str(e)}")
        
        # Test create service as admin
        if self.admin_token:
            admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
            try:
                response = requests.post(f"{BASE_URL}/services", json=test_service, headers=admin_headers)
                if response.status_code == 200:
                    data = response.json()
                    admin_service_id = data['id']
                    self.created_resources['services'].append(admin_service_id)
                    self.log_result("Create Service (Admin)", True, f"Service created with ID: {admin_service_id}")
                else:
                    self.log_result("Create Service (Admin)", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_result("Create Service (Admin)", False, f"Exception: {str(e)}")
        
        # Test list services as taxista (should only see own services)
        if self.taxista_token:
            taxista_headers = {"Authorization": f"Bearer {self.taxista_token}"}
            try:
                response = requests.get(f"{BASE_URL}/services", headers=taxista_headers)
                if response.status_code == 200:
                    data = response.json()
                    self.log_result("List Services (Taxista)", True, f"Retrieved {len(data)} services (own only)")
                else:
                    self.log_result("List Services (Taxista)", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_result("List Services (Taxista)", False, f"Exception: {str(e)}")
        
        # Test list services as admin (should see all services)
        if self.admin_token:
            admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
            try:
                response = requests.get(f"{BASE_URL}/services", headers=admin_headers)
                if response.status_code == 200:
                    data = response.json()
                    self.log_result("List Services (Admin)", True, f"Retrieved {len(data)} services (all)")
                else:
                    self.log_result("List Services (Admin)", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_result("List Services (Admin)", False, f"Exception: {str(e)}")
        
        # Test update service
        if service_id and self.taxista_token:
            updated_service = test_service.copy()
            updated_service["importe"] = 30.00
            
            taxista_headers = {"Authorization": f"Bearer {self.taxista_token}"}
            try:
                response = requests.put(f"{BASE_URL}/services/{service_id}", json=updated_service, headers=taxista_headers)
                if response.status_code == 200:
                    self.log_result("Update Service (Owner)", True, "Service updated successfully")
                else:
                    self.log_result("Update Service (Owner)", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_result("Update Service (Owner)", False, f"Exception: {str(e)}")
    
    def test_service_filters(self):
        """Test service filtering"""
        print("\n=== TESTING SERVICE FILTERS ===")
        
        if not self.admin_token:
            self.log_result("Service Filters Setup", False, "No admin token available")
            return
        
        admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test filter by tipo
        try:
            response = requests.get(f"{BASE_URL}/services?tipo=particular", headers=admin_headers)
            if response.status_code == 200:
                data = response.json()
                self.log_result("Filter by Tipo", True, f"Retrieved {len(data)} particular services")
            else:
                self.log_result("Filter by Tipo", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Filter by Tipo", False, f"Exception: {str(e)}")
        
        # Test filter by date range
        try:
            response = requests.get(f"{BASE_URL}/services?fecha_inicio=2025-01-01&fecha_fin=2025-01-31", headers=admin_headers)
            if response.status_code == 200:
                data = response.json()
                self.log_result("Filter by Date Range", True, f"Retrieved {len(data)} services in date range")
            else:
                self.log_result("Filter by Date Range", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Filter by Date Range", False, f"Exception: {str(e)}")
    
    def test_batch_sync(self):
        """Test batch synchronization"""
        print("\n=== TESTING BATCH SYNC ===")
        
        if not self.taxista_token:
            self.log_result("Batch Sync Setup", False, "No taxista token available")
            return
        
        taxista_headers = {"Authorization": f"Bearer {self.taxista_token}"}
        
        # Test sync multiple services
        sync_data = {
            "services": [
                {
                    "fecha": "21/12/2024",
                    "hora": "09:00",
                    "origen": "Tineo",
                    "destino": "Oviedo",
                    "importe": 45.50,
                    "importe_espera": 0.0,
                    "kilometros": 35.0,
                    "tipo": "empresa",
                    "empresa_id": "68f9bf6639ddad8a39451da0",
                    "empresa_nombre": "Hospital Universitario Central de Asturias"
                },
                {
                    "fecha": "21/12/2024",
                    "hora": "11:30",
                    "origen": "Oviedo",
                    "destino": "Tineo",
                    "importe": 45.50,
                    "importe_espera": 10.0,
                    "kilometros": 35.0,
                    "tipo": "particular"
                }
            ]
        }
        
        try:
            response = requests.post(f"{BASE_URL}/services/sync", json=sync_data, headers=taxista_headers)
            if response.status_code == 200:
                data = response.json()
                self.log_result("Batch Sync", True, f"Synced {len(sync_data['services'])} services")
            else:
                self.log_result("Batch Sync", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_result("Batch Sync", False, f"Exception: {str(e)}")
    
    def test_export_endpoint(self, endpoint, expected_content_type, test_name, params=None):
        """Test a single export endpoint with comprehensive validation"""
        if not self.admin_token:
            self.log_result(test_name, False, "No admin token available")
            return False
        
        admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            url = f"{BASE_URL}{endpoint}"
            response = requests.get(url, params=params, headers=admin_headers, timeout=30)
            
            # Check status code
            if response.status_code != 200:
                self.log_result(test_name, False, f"Status: {response.status_code}, Response: {response.text[:200]}")
                return False
            
            # Check content type
            content_type = response.headers.get('content-type', '')
            if expected_content_type not in content_type:
                self.log_result(test_name, False, f"Wrong content-type. Expected: {expected_content_type}, Got: {content_type}")
                return False
            
            # Check file size
            file_size = len(response.content)
            if file_size == 0:
                self.log_result(test_name, False, "File is empty (0 bytes)")
                return False
            
            # Check Content-Disposition header
            content_disposition = response.headers.get('content-disposition', '')
            if 'attachment' not in content_disposition:
                self.log_result(test_name, False, f"Missing or invalid Content-Disposition header: {content_disposition}")
                return False
            
            # Additional checks based on file type
            details = f"Content-Type: {content_type}, Size: {file_size} bytes"
            
            if 'text/csv' in content_type:
                # Check if CSV contains readable text
                try:
                    content_text = response.content.decode('utf-8')
                    if len(content_text.strip()) == 0:
                        self.log_result(test_name, False, "CSV file contains no readable text")
                        return False
                    # Check for CSV headers
                    lines = content_text.strip().split('\n')
                    if len(lines) < 1:
                        self.log_result(test_name, False, "CSV file has no header row")
                        return False
                    details += f", Lines: {len(lines)}"
                except UnicodeDecodeError:
                    self.log_result(test_name, False, "CSV file contains invalid UTF-8 content")
                    return False
            
            self.log_result(test_name, True, details)
            return True
            
        except Exception as e:
            self.log_result(test_name, False, f"Exception: {str(e)}")
            return False

    def test_export_endpoints(self):
        """Test ALL export endpoints as requested - Services and Turnos"""
        print("\n=== TESTING ALL EXPORT ENDPOINTS (COMPREHENSIVE) ===")
        
        if not self.admin_token:
            self.log_result("Export Setup", False, "No admin token available")
            return
        
        # Create test data first to ensure exports have content
        self.create_export_test_data()
        
        print("\n📊 TESTING SERVICES EXPORT ENDPOINTS:")
        print("-" * 50)
        
        # SERVICES EXPORT TEST CASES (as specified in request)
        services_tests = [
            ("/services/export/csv", None, "Services CSV - No filters", "text/csv"),
            ("/services/export/csv", {"tipo": "empresa"}, "Services CSV - Filter tipo=empresa", "text/csv"),
            ("/services/export/csv", {"tipo": "particular"}, "Services CSV - Filter tipo=particular", "text/csv"),
            ("/services/export/excel", None, "Services Excel - No filters", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            ("/services/export/excel", {"tipo": "empresa"}, "Services Excel - Filter tipo=empresa", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            ("/services/export/pdf", None, "Services PDF - No filters", "application/pdf"),
            ("/services/export/pdf", {"tipo": "particular"}, "Services PDF - Filter tipo=particular", "application/pdf"),
        ]
        
        services_results = []
        for endpoint, params, test_name, content_type in services_tests:
            success = self.test_export_endpoint(endpoint, content_type, test_name, params)
            services_results.append(success)
        
        print("\n🚕 TESTING TURNOS EXPORT ENDPOINTS:")
        print("-" * 50)
        
        # TURNOS EXPORT TEST CASES (as specified in request)
        turnos_tests = [
            ("/turnos/export/csv", None, "Turnos CSV - No filters", "text/csv"),
            ("/turnos/export/csv", {"cerrado": "false"}, "Turnos CSV - Filter cerrado=false", "text/csv"),
            ("/turnos/export/csv", {"cerrado": "true"}, "Turnos CSV - Filter cerrado=true", "text/csv"),
            ("/turnos/export/csv", {"liquidado": "true"}, "Turnos CSV - Filter liquidado=true", "text/csv"),
            ("/turnos/export/excel", None, "Turnos Excel - No filters", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            ("/turnos/export/excel", {"cerrado": "true"}, "Turnos Excel - Filter cerrado=true", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
            ("/turnos/export/pdf", None, "Turnos PDF - No filters", "application/pdf"),
            ("/turnos/export/pdf", {"liquidado": "true"}, "Turnos PDF - Filter liquidado=true", "application/pdf"),
        ]
        
        turnos_results = []
        for endpoint, params, test_name, content_type in turnos_tests:
            success = self.test_export_endpoint(endpoint, content_type, test_name, params)
            turnos_results.append(success)
        
        # Test export access with taxista token (should fail)
        print("\n🔒 TESTING EXPORT ACCESS CONTROL:")
        print("-" * 50)
        if self.taxista_token:
            taxista_headers = {"Authorization": f"Bearer {self.taxista_token}"}
            try:
                response = requests.get(f"{BASE_URL}/services/export/csv", headers=taxista_headers)
                if response.status_code == 403:
                    self.log_result("Export Access Control (Services)", True, "Correctly denied export access to taxista")
                else:
                    self.log_result("Export Access Control (Services)", False, f"Expected 403, got {response.status_code}")
            except Exception as e:
                self.log_result("Export Access Control (Services)", False, f"Exception: {str(e)}")
            
            try:
                response = requests.get(f"{BASE_URL}/turnos/export/csv", headers=taxista_headers)
                if response.status_code == 403:
                    self.log_result("Export Access Control (Turnos)", True, "Correctly denied export access to taxista")
                else:
                    self.log_result("Export Access Control (Turnos)", False, f"Expected 403, got {response.status_code}")
            except Exception as e:
                self.log_result("Export Access Control (Turnos)", False, f"Exception: {str(e)}")
        
        # Summary of export tests
        total_services = len(services_tests)
        passed_services = sum(services_results)
        total_turnos = len(turnos_tests)
        passed_turnos = sum(turnos_results)
        
        print(f"\n📈 EXPORT TESTS SUMMARY:")
        print(f"Services Exports: {passed_services}/{total_services} passed")
        print(f"Turnos Exports: {passed_turnos}/{total_turnos} passed")
        print(f"Total Export Tests: {passed_services + passed_turnos}/{total_services + total_turnos} passed")

    def create_export_test_data(self):
        """Create comprehensive test data for export testing"""
        print("\n📝 Creating test data for export testing...")
        
        if not self.admin_token:
            return False
        
        admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            # Create test company
            company_data = {
                "nombre": "Empresa Export Test",
                "cif": "B87654321",
                "direccion": "Calle Export 456",
                "localidad": "Tineo",
                "provincia": "Asturias",
                "telefono": "985654321"
            }
            
            company_response = requests.post(f"{BASE_URL}/companies", json=company_data, headers=admin_headers, timeout=10)
            company_id = None
            if company_response.status_code == 200:
                company_id = company_response.json()["id"]
                self.created_resources.setdefault('companies', []).append(company_id)
                print(f"✅ Test company created for exports: {company_id}")
            
            # Create test taxista for exports
            taxista_data = {
                "username": f"export_taxista_{datetime.now().strftime('%H%M%S')}",
                "password": "export123",
                "nombre": "Taxista Export Test",
                "role": "taxista",
                "licencia": "EXPORT123"
            }
            
            taxista_response = requests.post(f"{BASE_URL}/users", json=taxista_data, headers=admin_headers, timeout=10)
            taxista_id = None
            if taxista_response.status_code == 200:
                taxista_id = taxista_response.json()["id"]
                self.created_resources.setdefault('users', []).append(taxista_id)
                print(f"✅ Test taxista created for exports: {taxista_id}")
            
            # Create test vehicle
            vehiculo_data = {
                "matricula": f"EXP-{datetime.now().strftime('%H%M')}",
                "plazas": 4,
                "marca": "Seat",
                "modelo": "Leon",
                "km_iniciales": 75000,
                "fecha_compra": "01/06/2019",
                "activo": True
            }
            
            vehiculo_response = requests.post(f"{BASE_URL}/vehiculos", json=vehiculo_data, headers=admin_headers, timeout=10)
            vehiculo_id = None
            if vehiculo_response.status_code == 200:
                vehiculo_id = vehiculo_response.json()["id"]
                self.created_resources.setdefault('vehiculos', []).append(vehiculo_id)
                print(f"✅ Test vehicle created for exports: {vehiculo_id}")
            
            # Create multiple test services with different types
            test_services = [
                {
                    "fecha": "15/12/2024",
                    "hora": "08:30",
                    "origen": "Tineo Plaza",
                    "destino": "Hospital San Agustín",
                    "importe": 18.50,
                    "importe_espera": 3.00,
                    "kilometros": 8.5,
                    "tipo": "empresa",
                    "empresa_id": company_id,
                    "empresa_nombre": "Empresa Export Test"
                },
                {
                    "fecha": "15/12/2024",
                    "hora": "10:15",
                    "origen": "Estación Autobuses",
                    "destino": "Centro Comercial",
                    "importe": 12.00,
                    "importe_espera": 0.00,
                    "kilometros": 4.2,
                    "tipo": "particular"
                },
                {
                    "fecha": "15/12/2024",
                    "hora": "14:45",
                    "origen": "Residencia Ancianos",
                    "destino": "Centro Salud",
                    "importe": 15.75,
                    "importe_espera": 2.50,
                    "kilometros": 6.8,
                    "tipo": "empresa",
                    "empresa_id": company_id,
                    "empresa_nombre": "Empresa Export Test"
                },
                {
                    "fecha": "16/12/2024",
                    "hora": "09:00",
                    "origen": "Domicilio Particular",
                    "destino": "Aeropuerto Asturias",
                    "importe": 85.00,
                    "importe_espera": 5.00,
                    "kilometros": 65.0,
                    "tipo": "particular"
                }
            ]
            
            services_created = 0
            for service_data in test_services:
                service_response = requests.post(f"{BASE_URL}/services", json=service_data, headers=admin_headers, timeout=10)
                if service_response.status_code == 200:
                    service_id = service_response.json()["id"]
                    self.created_resources.setdefault('services', []).append(service_id)
                    services_created += 1
            
            print(f"✅ Created {services_created} test services for exports")
            
            # Create test turnos if we have taxista and vehicle
            if taxista_id and vehiculo_id:
                # Login as the test taxista to create turnos
                taxista_login = requests.post(f"{BASE_URL}/auth/login", json={
                    "username": taxista_data["username"],
                    "password": taxista_data["password"]
                }, timeout=10)
                
                if taxista_login.status_code == 200:
                    test_taxista_token = taxista_login.json()["access_token"]
                    test_taxista_headers = {"Authorization": f"Bearer {test_taxista_token}"}
                    
                    # Create and finalize a turno
                    turno_data = {
                        "taxista_id": taxista_id,
                        "taxista_nombre": "Taxista Export Test",
                        "vehiculo_id": vehiculo_id,
                        "vehiculo_matricula": vehiculo_data["matricula"],
                        "fecha_inicio": "15/12/2024",
                        "hora_inicio": "07:30",
                        "km_inicio": 75100
                    }
                    
                    turno_response = requests.post(f"{BASE_URL}/turnos", json=turno_data, headers=test_taxista_headers, timeout=10)
                    if turno_response.status_code == 200:
                        turno_id = turno_response.json()["id"]
                        self.created_resources.setdefault('turnos', []).append(turno_id)
                        print(f"✅ Test turno created for exports: {turno_id}")
                        
                        # Finalize the turno
                        finalize_data = {
                            "fecha_fin": "15/12/2024",
                            "hora_fin": "18:00",
                            "km_fin": 75200,
                            "cerrado": True
                        }
                        
                        finalize_response = requests.put(f"{BASE_URL}/turnos/{turno_id}/finalizar", json=finalize_data, headers=test_taxista_headers, timeout=10)
                        if finalize_response.status_code == 200:
                            print(f"✅ Test turno finalized for exports")
                            
                            # Mark as liquidated (admin only)
                            liquidate_data = {"liquidado": True}
                            liquidate_response = requests.put(f"{BASE_URL}/turnos/{turno_id}", json=liquidate_data, headers=admin_headers, timeout=10)
                            if liquidate_response.status_code == 200:
                                print(f"✅ Test turno marked as liquidated")
            
            print("✅ Export test data creation completed\n")
            return True
            
        except Exception as e:
            print(f"⚠️ Error creating export test data: {str(e)}")
            return False

    def test_vehiculos_crud(self):
        """Test vehículos CRUD operations"""
        print("\n=== TESTING VEHÍCULOS CRUD ===")
        
        if not self.admin_token:
            self.log_result("Vehículos CRUD Setup", False, "No admin token available")
            return
        
        admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test create vehículo (admin only)
        test_vehiculo = {
            "matricula": f"AS-{datetime.now().strftime('%H%M')}-BC",
            "plazas": 4,
            "marca": "Toyota",
            "modelo": "Prius",
            "km_iniciales": 50000,
            "fecha_compra": "15/01/2020",
            "activo": True
        }
        
        vehiculo_id = None
        try:
            response = requests.post(f"{BASE_URL}/vehiculos", json=test_vehiculo, headers=admin_headers)
            if response.status_code == 200:
                data = response.json()
                vehiculo_id = data['id']
                self.created_resources.setdefault('vehiculos', []).append(vehiculo_id)
                self.log_result("Create Vehículo (Admin)", True, f"Vehículo created with ID: {vehiculo_id}, Matrícula: {data['matricula']}")
            else:
                self.log_result("Create Vehículo (Admin)", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_result("Create Vehículo (Admin)", False, f"Exception: {str(e)}")
        
        # Test unique matricula validation
        try:
            response = requests.post(f"{BASE_URL}/vehiculos", json=test_vehiculo, headers=admin_headers)
            if response.status_code == 400:
                self.log_result("Unique Matrícula Validation", True, "Correctly rejected duplicate matricula")
            else:
                self.log_result("Unique Matrícula Validation", False, f"Should have failed with 400, got: {response.status_code}")
        except Exception as e:
            self.log_result("Unique Matrícula Validation", False, f"Exception: {str(e)}")
        
        # Test list vehículos (both admin and taxista should work)
        try:
            response = requests.get(f"{BASE_URL}/vehiculos", headers=admin_headers)
            if response.status_code == 200:
                data = response.json()
                self.log_result("List Vehículos (Admin)", True, f"Retrieved {len(data)} vehículos")
            else:
                self.log_result("List Vehículos (Admin)", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("List Vehículos (Admin)", False, f"Exception: {str(e)}")
        
        if self.taxista_token:
            taxista_headers = {"Authorization": f"Bearer {self.taxista_token}"}
            try:
                response = requests.get(f"{BASE_URL}/vehiculos", headers=taxista_headers)
                if response.status_code == 200:
                    data = response.json()
                    self.log_result("List Vehículos (Taxista)", True, f"Retrieved {len(data)} vehículos")
                else:
                    self.log_result("List Vehículos (Taxista)", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_result("List Vehículos (Taxista)", False, f"Exception: {str(e)}")
        
        # Test update vehículo (admin only)
        if vehiculo_id:
            updated_vehiculo = test_vehiculo.copy()
            updated_vehiculo["km_iniciales"] = 55000
            
            try:
                response = requests.put(f"{BASE_URL}/vehiculos/{vehiculo_id}", json=updated_vehiculo, headers=admin_headers)
                if response.status_code == 200:
                    self.log_result("Update Vehículo (Admin)", True, "Vehículo updated successfully")
                else:
                    self.log_result("Update Vehículo (Admin)", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_result("Update Vehículo (Admin)", False, f"Exception: {str(e)}")
        
        return vehiculo_id

    def test_turnos_crud(self):
        """Test turnos CRUD operations and workflow"""
        print("\n=== TESTING TURNOS CRUD & WORKFLOW ===")
        
        if not self.taxista_token:
            self.log_result("Turnos CRUD Setup", False, "No taxista token available")
            return
        
        # First create a vehículo to use
        vehiculo_id = self.test_vehiculos_crud()
        if not vehiculo_id:
            self.log_result("Turnos Setup", False, "Could not create vehículo for turno testing")
            return
        
        taxista_headers = {"Authorization": f"Bearer {self.taxista_token}"}
        
        # Test create turno
        test_turno = {
            "taxista_id": "test_taxista_id",  # Will be overridden by backend
            "taxista_nombre": "Taxista Test",
            "vehiculo_id": vehiculo_id,
            "vehiculo_matricula": f"AS-{datetime.now().strftime('%H%M')}-BC",
            "fecha_inicio": "20/12/2024",
            "hora_inicio": "08:00",
            "km_inicio": 52000
        }
        
        turno_id = None
        try:
            response = requests.post(f"{BASE_URL}/turnos", json=test_turno, headers=taxista_headers)
            if response.status_code == 200:
                data = response.json()
                turno_id = data['id']
                self.created_resources.setdefault('turnos', []).append(turno_id)
                self.log_result("Create Turno", True, f"Turno created with ID: {turno_id}")
            else:
                self.log_result("Create Turno", False, f"Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_result("Create Turno", False, f"Exception: {str(e)}")
        
        # Test get active turno
        try:
            response = requests.get(f"{BASE_URL}/turnos/activo", headers=taxista_headers)
            if response.status_code == 200:
                data = response.json()
                if data and data.get('id') == turno_id:
                    self.log_result("Get Turno Activo", True, f"Active turno retrieved: {data['id']}")
                else:
                    self.log_result("Get Turno Activo", False, f"Expected turno {turno_id}, got: {data}")
            else:
                self.log_result("Get Turno Activo", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("Get Turno Activo", False, f"Exception: {str(e)}")
        
        # Test duplicate turno prevention
        try:
            response = requests.post(f"{BASE_URL}/turnos", json=test_turno, headers=taxista_headers)
            if response.status_code == 400:
                self.log_result("Duplicate Turno Prevention", True, "Correctly prevented duplicate active turno")
            else:
                self.log_result("Duplicate Turno Prevention", False, f"Should have failed with 400, got: {response.status_code}")
        except Exception as e:
            self.log_result("Duplicate Turno Prevention", False, f"Exception: {str(e)}")
        
        # Create services that should auto-assign to active turno
        services_created = self.create_services_for_turno(turno_id)
        
        # Test services filter by turno_id
        if services_created:
            try:
                response = requests.get(f"{BASE_URL}/services?turno_id={turno_id}", headers=taxista_headers)
                if response.status_code == 200:
                    data = response.json()
                    if len(data) >= 2:  # Should have at least the services we created
                        all_correct_turno = all(service.get("turno_id") == turno_id for service in data)
                        if all_correct_turno:
                            self.log_result("Filter Services by Turno", True, f"Found {len(data)} services correctly assigned to turno")
                        else:
                            self.log_result("Filter Services by Turno", False, "Some services have incorrect turno_id")
                    else:
                        self.log_result("Filter Services by Turno", False, f"Expected at least 2 services, got {len(data)}")
                else:
                    self.log_result("Filter Services by Turno", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_result("Filter Services by Turno", False, f"Exception: {str(e)}")
        
        # Test finalize turno
        if turno_id:
            finalize_data = {
                "fecha_fin": "20/12/2024",
                "hora_fin": "16:30",
                "km_fin": 52150,
                "cerrado": True
            }
            
            try:
                response = requests.put(f"{BASE_URL}/turnos/{turno_id}/finalizar", json=finalize_data, headers=taxista_headers)
                if response.status_code == 200:
                    data = response.json()
                    
                    # Verify totals calculation
                    has_totals = (
                        'total_importe_particulares' in data and
                        'total_importe_clientes' in data and
                        'total_kilometros' in data and
                        'cantidad_servicios' in data
                    )
                    
                    if has_totals and data.get('cerrado'):
                        self.log_result("Finalize Turno", True, f"Turno finalized with totals: Particulares={data.get('total_importe_particulares')}€, Empresas={data.get('total_importe_clientes')}€, KM={data.get('total_kilometros')}, Servicios={data.get('cantidad_servicios')}")
                    else:
                        self.log_result("Finalize Turno", False, f"Missing totals or not marked as closed: {data}")
                else:
                    self.log_result("Finalize Turno", False, f"Status: {response.status_code}, Response: {response.text}")
            except Exception as e:
                self.log_result("Finalize Turno", False, f"Exception: {str(e)}")
        
        # Test list turnos (should include our closed turno)
        try:
            response = requests.get(f"{BASE_URL}/turnos", headers=taxista_headers)
            if response.status_code == 200:
                data = response.json()
                our_turno = next((t for t in data if t.get('id') == turno_id), None)
                if our_turno and our_turno.get('cerrado'):
                    self.log_result("List Turnos", True, f"Retrieved {len(data)} turnos, including our closed turno")
                else:
                    self.log_result("List Turnos", False, "Our turno not found in list or not marked as closed")
            else:
                self.log_result("List Turnos", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_result("List Turnos", False, f"Exception: {str(e)}")

    def create_services_for_turno(self, turno_id):
        """Create test services that should be assigned to the active turno"""
        if not self.taxista_token:
            return False
        
        taxista_headers = {"Authorization": f"Bearer {self.taxista_token}"}
        
        services_data = [
            {
                "fecha": "20/12/2024",
                "hora": "09:30",
                "origen": "Tineo Centro",
                "destino": "Hospital de Cangas",
                "importe": 25.50,
                "importe_espera": 5.00,
                "kilometros": 15.2,
                "tipo": "particular"
            },
            {
                "fecha": "20/12/2024",
                "hora": "11:15",
                "origen": "Hospital de Cangas",
                "destino": "Oviedo HUCA",
                "importe": 45.00,
                "importe_espera": 0.00,
                "kilometros": 32.5,
                "tipo": "empresa",
                "empresa_nombre": "Hospital Universitario Central de Asturias"
            }
        ]
        
        success_count = 0
        for i, service_data in enumerate(services_data):
            try:
                response = requests.post(f"{BASE_URL}/services", json=service_data, headers=taxista_headers)
                if response.status_code == 200:
                    data = response.json()
                    self.created_resources['services'].append(data['id'])
                    success_count += 1
                    
                    # Verify turno assignment
                    if data.get('turno_id') == turno_id:
                        self.log_result(f"Service {i+1} Turno Assignment", True, f"Service correctly assigned to turno {turno_id}")
                    else:
                        self.log_result(f"Service {i+1} Turno Assignment", False, f"Expected turno {turno_id}, got {data.get('turno_id')}")
                else:
                    self.log_result(f"Create Service {i+1} for Turno", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_result(f"Create Service {i+1} for Turno", False, f"Exception: {str(e)}")
        
        if success_count == len(services_data):
            self.log_result("Create Services for Turno", True, f"Created {success_count} services for turno testing")
            return True
        else:
            self.log_result("Create Services for Turno", False, f"Only {success_count}/{len(services_data)} services created")
            return False
    
    def cleanup_resources(self):
        """Clean up created test resources"""
        print("\n=== CLEANING UP TEST RESOURCES ===")
        
        if not self.admin_token:
            return
        
        admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Delete test users
        for user_id in self.created_resources.get('users', []):
            try:
                response = requests.delete(f"{BASE_URL}/users/{user_id}", headers=admin_headers)
                if response.status_code == 200:
                    print(f"✅ Deleted test user: {user_id}")
                else:
                    print(f"❌ Failed to delete user {user_id}: {response.status_code}")
            except Exception as e:
                print(f"❌ Exception deleting user {user_id}: {str(e)}")
        
        # Delete test companies
        for company_id in self.created_resources.get('companies', []):
            try:
                response = requests.delete(f"{BASE_URL}/companies/{company_id}", headers=admin_headers)
                if response.status_code == 200:
                    print(f"✅ Deleted test company: {company_id}")
                else:
                    print(f"❌ Failed to delete company {company_id}: {response.status_code}")
            except Exception as e:
                print(f"❌ Exception deleting company {company_id}: {str(e)}")
        
        # Delete test services
        for service_id in self.created_resources.get('services', []):
            try:
                response = requests.delete(f"{BASE_URL}/services/{service_id}", headers=admin_headers)
                if response.status_code == 200:
                    print(f"✅ Deleted test service: {service_id}")
                else:
                    print(f"❌ Failed to delete service {service_id}: {response.status_code}")
            except Exception as e:
                print(f"❌ Exception deleting service {service_id}: {str(e)}")
        
        # Delete test vehículos
        for vehiculo_id in self.created_resources.get('vehiculos', []):
            try:
                response = requests.delete(f"{BASE_URL}/vehiculos/{vehiculo_id}", headers=admin_headers)
                if response.status_code == 200:
                    print(f"✅ Deleted test vehículo: {vehiculo_id}")
                else:
                    print(f"❌ Failed to delete vehículo {vehiculo_id}: {response.status_code}")
            except Exception as e:
                print(f"❌ Exception deleting vehículo {vehiculo_id}: {str(e)}")
        
        # Note: Turnos are not deleted as they are historical records
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚕 Starting Taxi Tineo Backend API Tests")
        print(f"🌐 Base URL: {BASE_URL}")
        print("=" * 60)
        
        # Authentication
        admin_auth_success = self.authenticate_admin()
        taxista_auth_success = self.authenticate_taxista()
        
        if not admin_auth_success and not taxista_auth_success:
            print("❌ CRITICAL: No authentication successful. Cannot proceed with tests.")
            return False
        
        # Run all test suites
        self.test_auth_endpoints()
        self.test_user_crud()
        self.test_company_crud()
        self.test_service_crud()
        self.test_service_filters()
        self.test_batch_sync()
        self.test_export_endpoints()
        
        # NEW: Test Turnos and Vehículos functionality
        self.test_turnos_crud()
        
        # Cleanup
        self.cleanup_resources()
        
        # Summary
        self.print_summary()
        
        return True
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if "✅ PASS" in result['status'])
        failed = sum(1 for result in self.test_results if "❌ FAIL" in result['status'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        
        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if "❌ FAIL" in result['status']:
                    print(f"  - {result['test']}: {result['message']}")
        
        print("\n" + "=" * 60)

def main():
    """Main function"""
    tester = TaxiTineoAPITester()
    success = tester.run_all_tests()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()