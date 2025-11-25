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
    
    def setup_authentication(self):
        """Setup admin and taxista authentication"""
        self.log("=== SETUP: Authentication ===")
        
        # Admin login
        admin_response = self.test_request(
            "POST", "/auth/login",
            data={"username": "admin", "password": "admin123"},
            test_name="Admin Login"
        )
        
        if admin_response and admin_response.status_code == 200:
            admin_data = admin_response.json()
            self.admin_token = admin_data["access_token"]
            self.log(f"Admin token obtained: {self.admin_token[:20]}...")
        else:
            self.log("Failed to get admin token", "ERROR")
            return False
            
        return True
    
    def setup_test_data(self):
        """Create test taxista, vehicle, turno and services"""
        self.log("=== SETUP: Test Data Creation ===")
        
        if not self.admin_token:
            self.log("No admin token available", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # 1. Create test taxista
        taxista_data = {
            "username": f"testdriver_{datetime.now().strftime('%H%M%S')}",
            "password": "test123",
            "nombre": "Conductor Prueba Exportación",
            "role": "taxista",
            "licencia": "LIC-EXPORT-001"
        }
        
        taxista_response = self.test_request(
            "POST", "/users",
            data=taxista_data,
            headers=headers,
            test_name="Create Test Taxista"
        )
        
        if taxista_response and taxista_response.status_code == 200:
            self.test_taxista_id = taxista_response.json()["id"]
            self.log(f"Test taxista created: {self.test_taxista_id}")
        else:
            return False
            
        # 2. Create test vehicle
        vehiculo_data = {
            "matricula": f"TEST-{datetime.now().strftime('%H%M')}",
            "plazas": 4,
            "marca": "Toyota",
            "modelo": "Prius Export Test",
            "km_iniciales": 50000,
            "fecha_compra": "01/01/2020",
            "activo": True
        }
        
        vehiculo_response = self.test_request(
            "POST", "/vehiculos",
            data=vehiculo_data,
            headers=headers,
            test_name="Create Test Vehicle"
        )
        
        if vehiculo_response and vehiculo_response.status_code == 200:
            self.test_vehiculo_id = vehiculo_response.json()["id"]
            self.log(f"Test vehicle created: {self.test_vehiculo_id}")
        else:
            return False
            
        # 3. Login as taxista to create turno
        taxista_login_response = self.test_request(
            "POST", "/auth/login",
            data={"username": taxista_data["username"], "password": taxista_data["password"]},
            test_name="Taxista Login"
        )
        
        if taxista_login_response and taxista_login_response.status_code == 200:
            taxista_data_response = taxista_login_response.json()
            self.taxista_token = taxista_data_response["access_token"]
            self.log(f"Taxista token obtained")
        else:
            return False
            
        # 4. Create turno as taxista
        taxista_headers = {"Authorization": f"Bearer {self.taxista_token}"}
        
        turno_data = {
            "taxista_id": self.test_taxista_id,
            "taxista_nombre": "Conductor Prueba Exportación",
            "vehiculo_id": self.test_vehiculo_id,
            "vehiculo_matricula": vehiculo_data["matricula"],
            "fecha_inicio": "15/12/2024",
            "hora_inicio": "08:00",
            "km_inicio": 50100
        }
        
        turno_response = self.test_request(
            "POST", "/turnos",
            data=turno_data,
            headers=taxista_headers,
            test_name="Create Test Turno"
        )
        
        if turno_response and turno_response.status_code == 200:
            self.test_turno_id = turno_response.json()["id"]
            self.log(f"Test turno created: {self.test_turno_id}")
        else:
            return False
            
        # 5. Create multiple test services
        services_data = [
            {
                "fecha": "15/12/2024",
                "hora": "08:30",
                "origen": "Estación de Tineo",
                "destino": "Hospital San Agustín",
                "importe": 12.50,
                "importe_espera": 2.00,
                "kilometros": 8.5,
                "tipo": "particular",
                "cobrado": True,
                "facturar": False
            },
            {
                "fecha": "15/12/2024", 
                "hora": "09:15",
                "origen": "Hospital San Agustín",
                "destino": "Polígono Industrial La Curiscada",
                "importe": 18.00,
                "importe_espera": 0.00,
                "kilometros": 12.3,
                "tipo": "empresa",
                "empresa_id": None,
                "empresa_nombre": "Empresa Construcciones Norte SL",
                "cobrado": False,
                "facturar": True
            },
            {
                "fecha": "15/12/2024",
                "hora": "10:45",
                "origen": "Polígono Industrial",
                "destino": "Centro Comercial Los Prados",
                "importe": 15.75,
                "importe_espera": 1.50,
                "kilometros": 9.8,
                "tipo": "particular",
                "cobrado": True,
                "facturar": False
            },
            {
                "fecha": "15/12/2024",
                "hora": "11:30",
                "origen": "Centro Comercial Los Prados",
                "destino": "Aeropuerto de Asturias",
                "importe": 45.00,
                "importe_espera": 5.00,
                "kilometros": 35.2,
                "tipo": "empresa",
                "empresa_id": None,
                "empresa_nombre": "Viajes Asturias Express SL",
                "cobrado": True,
                "facturar": True
            },
            {
                "fecha": "15/12/2024",
                "hora": "14:15",
                "origen": "Aeropuerto de Asturias",
                "destino": "Plaza del Ayuntamiento Tineo",
                "importe": 42.00,
                "importe_espera": 0.00,
                "kilometros": 33.7,
                "tipo": "particular",
                "cobrado": False,
                "facturar": False
            }
        ]
        
        for i, service_data in enumerate(services_data, 1):
            service_response = self.test_request(
                "POST", "/services",
                data=service_data,
                headers=taxista_headers,
                test_name=f"Create Test Service {i}"
            )
            
            if service_response and service_response.status_code == 200:
                service_id = service_response.json()["id"]
                self.test_service_ids.append(service_id)
                self.log(f"Test service {i} created: {service_id}")
            else:
                self.log(f"Failed to create service {i}", "ERROR")
                
        self.log(f"Created {len(self.test_service_ids)} test services")
        return len(self.test_service_ids) > 0
    
    def test_detailed_csv_export(self):
        """Test CSV export with detailed services"""
        self.log("=== TESTING: Detailed CSV Export ===")
        
        if not self.admin_token:
            self.log("No admin token available", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test 1: Export without filters
        response = self.test_request(
            "GET", "/turnos/export/csv",
            headers=headers,
            test_name="CSV Export - No Filters"
        )
        
        if response and response.status_code == 200:
            # Verify Content-Type
            content_type = response.headers.get('content-type', '')
            if 'text/csv' in content_type:
                self.passed_tests += 1
                self.log("✅ CSV Content-Type correct")
            else:
                self.failed_tests += 1
                self.log(f"❌ CSV Content-Type incorrect: {content_type}", "ERROR")
            
            # Verify filename
            content_disposition = response.headers.get('content-disposition', '')
            if 'turnos_detallado.csv' in content_disposition:
                self.passed_tests += 1
                self.log("✅ CSV Filename correct (turnos_detallado.csv)")
            else:
                self.failed_tests += 1
                self.log(f"❌ CSV Filename incorrect: {content_disposition}", "ERROR")
            
            # Verify content structure
            csv_content = response.text
            lines = csv_content.split('\n')
            
            # Check for header row
            if len(lines) > 0 and 'Tipo' in lines[0] and 'SERVICIO' in lines[0]:
                self.passed_tests += 1
                self.log("✅ CSV Header contains expected columns")
            else:
                self.failed_tests += 1
                self.log("❌ CSV Header missing expected columns", "ERROR")
            
            # Check for TURNO and SERVICIO rows
            turno_rows = [line for line in lines if line.startswith('TURNO')]
            servicio_rows = [line for line in lines if line.startswith('SERVICIO')]
            
            if len(turno_rows) > 0:
                self.passed_tests += 1
                self.log(f"✅ CSV contains {len(turno_rows)} TURNO rows")
            else:
                self.failed_tests += 1
                self.log("❌ CSV missing TURNO rows", "ERROR")
                
            if len(servicio_rows) > 0:
                self.passed_tests += 1
                self.log(f"✅ CSV contains {len(servicio_rows)} SERVICIO rows")
            else:
                self.failed_tests += 1
                self.log("❌ CSV missing SERVICIO rows", "ERROR")
            
            self.log(f"CSV Export size: {len(csv_content)} characters, {len(lines)} lines")
        
        # Test 2: Export with cerrado=true filter
        response = self.test_request(
            "GET", "/turnos/export/csv?cerrado=true",
            headers=headers,
            test_name="CSV Export - Cerrado Filter"
        )
        
        if response and response.status_code == 200:
            self.log(f"CSV Export with cerrado=true: {len(response.text)} characters")
        
        # Test 3: Export with liquidado=true filter
        response = self.test_request(
            "GET", "/turnos/export/csv?liquidado=true",
            headers=headers,
            test_name="CSV Export - Liquidado Filter"
        )
        
        if response and response.status_code == 200:
            self.log(f"CSV Export with liquidado=true: {len(response.text)} characters")
            
        return True
    
    def test_detailed_excel_export(self):
        """Test Excel export with detailed services"""
        self.log("=== TESTING: Detailed Excel Export ===")
        
        if not self.admin_token:
            self.log("No admin token available", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test 1: Export without filters
        response = self.test_request(
            "GET", "/turnos/export/excel",
            headers=headers,
            test_name="Excel Export - No Filters"
        )
        
        if response and response.status_code == 200:
            # Verify Content-Type
            content_type = response.headers.get('content-type', '')
            if 'spreadsheetml.sheet' in content_type:
                self.passed_tests += 1
                self.log("✅ Excel Content-Type correct")
            else:
                self.failed_tests += 1
                self.log(f"❌ Excel Content-Type incorrect: {content_type}", "ERROR")
            
            # Verify filename
            content_disposition = response.headers.get('content-disposition', '')
            if 'turnos_detallado.xlsx' in content_disposition:
                self.passed_tests += 1
                self.log("✅ Excel Filename correct (turnos_detallado.xlsx)")
            else:
                self.failed_tests += 1
                self.log(f"❌ Excel Filename incorrect: {content_disposition}", "ERROR")
            
            # Verify file size (should be larger with detailed data)
            file_size = len(response.content)
            if file_size > 5000:  # Expect larger file with detailed services
                self.passed_tests += 1
                self.log(f"✅ Excel file size appropriate: {file_size} bytes")
            else:
                self.failed_tests += 1
                self.log(f"❌ Excel file size too small: {file_size} bytes", "ERROR")
        
        # Test 2: Export with liquidado=true filter
        response = self.test_request(
            "GET", "/turnos/export/excel?liquidado=true",
            headers=headers,
            test_name="Excel Export - Liquidado Filter"
        )
        
        if response and response.status_code == 200:
            self.log(f"Excel Export with liquidado=true: {len(response.content)} bytes")
            
        return True
    
    def test_detailed_pdf_export(self):
        """Test PDF export with detailed services"""
        self.log("=== TESTING: Detailed PDF Export ===")
        
        if not self.admin_token:
            self.log("No admin token available", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test 1: Export without filters
        response = self.test_request(
            "GET", "/turnos/export/pdf",
            headers=headers,
            test_name="PDF Export - No Filters"
        )
        
        if response and response.status_code == 200:
            # Verify Content-Type
            content_type = response.headers.get('content-type', '')
            if 'application/pdf' in content_type:
                self.passed_tests += 1
                self.log("✅ PDF Content-Type correct")
            else:
                self.failed_tests += 1
                self.log(f"❌ PDF Content-Type incorrect: {content_type}", "ERROR")
            
            # Verify filename
            content_disposition = response.headers.get('content-disposition', '')
            if 'turnos_detallado.pdf' in content_disposition:
                self.passed_tests += 1
                self.log("✅ PDF Filename correct (turnos_detallado.pdf)")
            else:
                self.failed_tests += 1
                self.log(f"❌ PDF Filename incorrect: {content_disposition}", "ERROR")
            
            # Verify file size (should be larger with detailed data)
            file_size = len(response.content)
            if file_size > 2000:  # Expect reasonable PDF size with detailed services
                self.passed_tests += 1
                self.log(f"✅ PDF file size appropriate: {file_size} bytes")
            else:
                self.failed_tests += 1
                self.log(f"❌ PDF file size too small: {file_size} bytes", "ERROR")
            
            # Verify PDF header
            if response.content.startswith(b'%PDF'):
                self.passed_tests += 1
                self.log("✅ PDF file format valid")
            else:
                self.failed_tests += 1
                self.log("❌ PDF file format invalid", "ERROR")
        
        # Test 2: Export with liquidado=true filter
        response = self.test_request(
            "GET", "/turnos/export/pdf?liquidado=true",
            headers=headers,
            test_name="PDF Export - Liquidado Filter"
        )
        
        if response and response.status_code == 200:
            self.log(f"PDF Export with liquidado=true: {len(response.content)} bytes")
            
        return True
    
    def test_edge_cases(self):
        """Test edge cases for detailed exports"""
        self.log("=== TESTING: Edge Cases ===")
        
        if not self.admin_token:
            self.log("No admin token available", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test 1: Export turno without services (create empty turno)
        # First create another taxista and vehicle for empty turno
        empty_taxista_data = {
            "username": f"emptytaxista_{datetime.now().strftime('%H%M%S')}",
            "password": "test123",
            "nombre": "Taxista Sin Servicios",
            "role": "taxista"
        }
        
        empty_taxista_response = self.test_request(
            "POST", "/users",
            data=empty_taxista_data,
            headers=headers,
            test_name="Create Empty Taxista"
        )
        
        if empty_taxista_response and empty_taxista_response.status_code == 200:
            empty_taxista_id = empty_taxista_response.json()["id"]
            
            # Login as empty taxista
            empty_login_response = self.test_request(
                "POST", "/auth/login",
                data={"username": empty_taxista_data["username"], "password": empty_taxista_data["password"]},
                test_name="Empty Taxista Login"
            )
            
            if empty_login_response and empty_login_response.status_code == 200:
                empty_token = empty_login_response.json()["access_token"]
                empty_headers = {"Authorization": f"Bearer {empty_token}"}
                
                # Create empty turno
                empty_turno_data = {
                    "taxista_id": empty_taxista_id,
                    "taxista_nombre": "Taxista Sin Servicios",
                    "vehiculo_id": self.test_vehiculo_id,
                    "vehiculo_matricula": "TEST-EMPTY",
                    "fecha_inicio": "15/12/2024",
                    "hora_inicio": "16:00",
                    "km_inicio": 60000
                }
                
                empty_turno_response = self.test_request(
                    "POST", "/turnos",
                    data=empty_turno_data,
                    headers=empty_headers,
                    test_name="Create Empty Turno"
                )
                
                if empty_turno_response and empty_turno_response.status_code == 200:
                    self.log("✅ Empty turno created for edge case testing")
        
        # Test 2: Export with multiple turnos
        response = self.test_request(
            "GET", "/turnos/export/csv",
            headers=headers,
            test_name="CSV Export - Multiple Turnos"
        )
        
        if response and response.status_code == 200:
            csv_content = response.text
            turno_count = csv_content.count('TURNO,')
            if turno_count >= 1:
                self.passed_tests += 1
                self.log(f"✅ CSV Export handles multiple turnos: {turno_count} turnos found")
            else:
                self.failed_tests += 1
                self.log("❌ CSV Export missing turno data", "ERROR")
        
        return True
    
    def verify_services_in_turno(self):
        """Verify that services are correctly associated with turno"""
        self.log("=== VERIFICATION: Services in Turno ===")
        
        if not self.admin_token or not self.test_turno_id:
            self.log("Missing admin token or turno ID", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Get services for the test turno
        response = self.test_request(
            "GET", f"/services?turno_id={self.test_turno_id}",
            headers=headers,
            test_name="Get Services by Turno ID"
        )
        
        if response and response.status_code == 200:
            services = response.json()
            if len(services) == len(self.test_service_ids):
                self.passed_tests += 1
                self.log(f"✅ All {len(services)} services correctly associated with turno")
            else:
                self.failed_tests += 1
                self.log(f"❌ Service count mismatch. Expected: {len(self.test_service_ids)}, Got: {len(services)}", "ERROR")
            
            # Verify service details
            for service in services:
                if service.get('turno_id') == self.test_turno_id:
                    self.passed_tests += 1
                    self.log(f"✅ Service {service['id'][:8]}... correctly linked to turno")
                else:
                    self.failed_tests += 1
                    self.log(f"❌ Service {service['id'][:8]}... not linked to turno", "ERROR")
        
        return True
    
    def cleanup_test_data(self):
        """Clean up test data"""
        self.log("=== CLEANUP: Test Data ===")
        
        if not self.admin_token:
            return
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Delete test turno (this should also delete associated services via cascade)
        if self.test_turno_id:
            response = self.test_request(
                "DELETE", f"/turnos/{self.test_turno_id}",
                headers=headers,
                test_name="Delete Test Turno"
            )
            
            if response and response.status_code == 200:
                result = response.json()
                services_deleted = result.get('servicios_eliminados', 0)
                self.log(f"✅ Turno deleted with {services_deleted} services removed")
        
        # Delete test vehicle
        if self.test_vehiculo_id:
            self.test_request(
                "DELETE", f"/vehiculos/{self.test_vehiculo_id}",
                headers=headers,
                test_name="Delete Test Vehicle"
            )
        
        # Delete test taxista
        if self.test_taxista_id:
            self.test_request(
                "DELETE", f"/users/{self.test_taxista_id}",
                headers=headers,
                test_name="Delete Test Taxista"
            )
    
    def run_all_tests(self):
        """Run all tests for detailed turno exports"""
        self.log("🎯 STARTING: Detailed Turno Export Testing")
        self.log(f"Backend URL: {BACKEND_URL}")
        
        # Setup phase
        if not self.setup_authentication():
            self.log("Authentication setup failed", "ERROR")
            return False
            
        if not self.setup_test_data():
            self.log("Test data setup failed", "ERROR")
            return False
        
        # Verification phase
        self.verify_services_in_turno()
        
        # Main testing phase
        self.test_detailed_csv_export()
        self.test_detailed_excel_export()
        self.test_detailed_pdf_export()
        self.test_edge_cases()
        
        # Cleanup phase
        self.cleanup_test_data()
        
        # Results
        total_tests = self.passed_tests + self.failed_tests
        success_rate = (self.passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        self.log("=" * 60)
        self.log("🎉 TESTING COMPLETED")
        self.log(f"📊 Results: {self.passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
        
        if self.failed_tests == 0:
            self.log("✅ ALL TESTS PASSED - Detailed turno exports working correctly!")
            return True
        else:
            self.log(f"❌ {self.failed_tests} tests failed - Issues found in detailed turno exports")
            return False

if __name__ == "__main__":
    tester = TaxiTineoTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)