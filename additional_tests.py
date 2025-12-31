#!/usr/bin/env python3
"""
Additional Edge Case Testing for Taxi Tineo Management System
Testing configuration, edge cases, and specific validation scenarios
"""

import requests
import json
import sys
from datetime import datetime
import time

# Configuration
BASE_URL = "https://taxi-services-1.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {"username": "admin", "password": "admin123"}

class AdditionalTester:
    def __init__(self):
        self.admin_token = None
        self.taxista_token = None
        self.test_results = []
        
    def log_test(self, test_name, success, details=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "status": status,
            "success": success,
            "details": details
        })
        print(f"{status}: {test_name}")
        if details and not success:
            print(f"   Details: {details}")
    
    def authenticate(self):
        """Authenticate as admin"""
        try:
            response = requests.post(f"{BASE_URL}/auth/login", json=ADMIN_CREDENTIALS, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data['access_token']
                self.log_test("Admin Authentication", True, "Admin login successful")
                return True
            else:
                self.log_test("Admin Authentication", False, f"Login failed: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Admin Authentication", False, f"Exception: {str(e)}")
            return False
    
    def test_configuration_endpoints(self):
        """Test configuration get and update"""
        print("\n⚙️ TESTING CONFIGURATION ENDPOINTS")
        
        # Test get config (public endpoint)
        try:
            response = requests.get(f"{BASE_URL}/config", timeout=10)
            if response.status_code == 200:
                config = response.json()
                self.log_test("Get Configuration", True, f"Retrieved config: {config.get('nombre_radio_taxi')}")
            else:
                self.log_test("Get Configuration", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Get Configuration", False, f"Exception: {str(e)}")
        
        # Test update config (admin only)
        if self.admin_token:
            config_data = {
                "nombre_radio_taxi": "Taxi Tineo Test Updated",
                "telefono": "985 80 15 15",
                "web": "www.taxitineo.com",
                "direccion": "Tineo, Asturias - Test Updated",
                "email": "test@taxitineo.com"
            }
            
            try:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                response = requests.put(f"{BASE_URL}/config", json=config_data, headers=headers, timeout=10)
                if response.status_code == 200:
                    self.log_test("Update Configuration (Admin)", True, "Configuration updated successfully")
                    
                    # Verify the update
                    verify_response = requests.get(f"{BASE_URL}/config", timeout=10)
                    if verify_response.status_code == 200:
                        updated_config = verify_response.json()
                        if updated_config.get('nombre_radio_taxi') == config_data['nombre_radio_taxi']:
                            self.log_test("Verify Configuration Update", True, "Configuration changes persisted")
                        else:
                            self.log_test("Verify Configuration Update", False, "Configuration changes not persisted")
                else:
                    self.log_test("Update Configuration (Admin)", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test("Update Configuration (Admin)", False, f"Exception: {str(e)}")
    
    def test_edge_cases(self):
        """Test critical edge cases"""
        print("\n⚠️ TESTING CRITICAL EDGE CASES")
        
        if not self.admin_token:
            return
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test duplicate numero_cliente validation
        company_data = {
            "nombre": "Test Duplicate Cliente",
            "cif": "B99999999",
            "direccion": "Test Address",
            "localidad": "Tineo",
            "provincia": "Asturias",
            "numero_cliente": f"DUPLICATE_{int(time.time())}"
        }
        
        # Create first company
        try:
            response = requests.post(f"{BASE_URL}/companies", json=company_data, headers=headers, timeout=10)
            if response.status_code == 200:
                company_id = response.json()["id"]
                
                # Try to create duplicate
                duplicate_data = company_data.copy()
                duplicate_data["nombre"] = "Different Name"
                duplicate_data["cif"] = "B88888888"
                
                duplicate_response = requests.post(f"{BASE_URL}/companies", json=duplicate_data, headers=headers, timeout=10)
                if duplicate_response.status_code == 400:
                    self.log_test("Duplicate numero_cliente Validation", True, "Correctly rejected duplicate numero_cliente")
                else:
                    self.log_test("Duplicate numero_cliente Validation", False, f"Expected 400, got {duplicate_response.status_code}")
                
                # Cleanup
                requests.delete(f"{BASE_URL}/companies/{company_id}", headers=headers, timeout=10)
            else:
                self.log_test("Setup for Duplicate Test", False, f"Could not create test company: {response.status_code}")
        except Exception as e:
            self.log_test("Duplicate numero_cliente Validation", False, f"Exception: {str(e)}")
        
        # Test duplicate matricula validation
        vehiculo_data = {
            "matricula": f"EDGE-{int(time.time() % 10000)}",
            "plazas": 4,
            "marca": "Test",
            "modelo": "Edge",
            "km_iniciales": 0,
            "fecha_compra": "01/01/2024",
            "activo": True
        }
        
        try:
            response = requests.post(f"{BASE_URL}/vehiculos", json=vehiculo_data, headers=headers, timeout=10)
            if response.status_code == 200:
                vehiculo_id = response.json()["id"]
                
                # Try to create duplicate
                duplicate_vehiculo = vehiculo_data.copy()
                duplicate_vehiculo["marca"] = "Different"
                
                duplicate_response = requests.post(f"{BASE_URL}/vehiculos", json=duplicate_vehiculo, headers=headers, timeout=10)
                if duplicate_response.status_code == 400:
                    self.log_test("Duplicate Matricula Validation", True, "Correctly rejected duplicate matricula")
                else:
                    self.log_test("Duplicate Matricula Validation", False, f"Expected 400, got {duplicate_response.status_code}")
                
                # Cleanup
                requests.delete(f"{BASE_URL}/vehiculos/{vehiculo_id}", headers=headers, timeout=10)
            else:
                self.log_test("Setup for Matricula Test", False, f"Could not create test vehicle: {response.status_code}")
        except Exception as e:
            self.log_test("Duplicate Matricula Validation", False, f"Exception: {str(e)}")
    
    def test_service_without_turno_edge_case(self):
        """Test the specific edge case: creating service without active turno"""
        print("\n🚫 TESTING SERVICE WITHOUT TURNO EDGE CASE")
        
        # Create a test taxista
        if not self.admin_token:
            return
        
        admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Create test taxista
        taxista_data = {
            "username": f"edge_taxista_{int(time.time())}",
            "password": "edge123",
            "nombre": "Edge Case Taxista",
            "role": "taxista"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/users", json=taxista_data, headers=admin_headers, timeout=10)
            if response.status_code == 200:
                taxista_id = response.json()["id"]
                
                # Login as taxista
                login_response = requests.post(f"{BASE_URL}/auth/login", json={
                    "username": taxista_data["username"],
                    "password": taxista_data["password"]
                }, timeout=10)
                
                if login_response.status_code == 200:
                    taxista_token = login_response.json()["access_token"]
                    taxista_headers = {"Authorization": f"Bearer {taxista_token}"}
                    
                    # Try to create service without active turno
                    service_data = {
                        "fecha": "15/12/2024",
                        "hora": "10:00",
                        "origen": "Edge Test Origin",
                        "destino": "Edge Test Destination",
                        "importe": 15.00,
                        "importe_espera": 0,
                        "kilometros": 5.0,
                        "tipo": "particular"
                    }
                    
                    service_response = requests.post(f"{BASE_URL}/services", json=service_data, headers=taxista_headers, timeout=10)
                    if service_response.status_code == 400:
                        error_detail = service_response.json().get("detail", "")
                        if "turno" in error_detail.lower():
                            self.log_test("Service Without Active Turno", True, "Correctly rejected service creation without active turno")
                        else:
                            self.log_test("Service Without Active Turno", False, f"Wrong error message: {error_detail}")
                    else:
                        self.log_test("Service Without Active Turno", False, f"Expected 400, got {service_response.status_code}")
                
                # Cleanup
                requests.delete(f"{BASE_URL}/users/{taxista_id}", headers=admin_headers, timeout=10)
            else:
                self.log_test("Setup for Service Edge Case", False, f"Could not create test taxista: {response.status_code}")
        except Exception as e:
            self.log_test("Service Without Active Turno", False, f"Exception: {str(e)}")
    
    def test_turnos_statistics(self):
        """Test turnos statistics endpoint"""
        print("\n📊 TESTING TURNOS STATISTICS")
        
        if not self.admin_token:
            return
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            response = requests.get(f"{BASE_URL}/turnos/estadisticas", headers=headers, timeout=10)
            if response.status_code == 200:
                stats = response.json()
                required_fields = [
                    'total_turnos', 'turnos_activos', 'turnos_cerrados', 'turnos_liquidados',
                    'turnos_pendiente_liquidacion', 'total_importe', 'total_kilometros',
                    'total_servicios', 'promedio_importe_por_turno', 'promedio_servicios_por_turno'
                ]
                
                missing_fields = [field for field in required_fields if field not in stats]
                if not missing_fields:
                    self.log_test("Turnos Statistics", True, 
                                 f"Retrieved complete statistics - Total turnos: {stats.get('total_turnos')}, "
                                 f"Total importe: {stats.get('total_importe')}€")
                else:
                    self.log_test("Turnos Statistics", False, f"Missing fields: {missing_fields}")
            else:
                self.log_test("Turnos Statistics", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Turnos Statistics", False, f"Exception: {str(e)}")
    
    def test_daily_report(self):
        """Test daily report endpoint"""
        print("\n📅 TESTING DAILY REPORT")
        
        if not self.admin_token:
            return
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            # Test with today's date
            today = datetime.now().strftime("%d/%m/%Y")
            response = requests.get(f"{BASE_URL}/reportes/diario", params={"fecha": today}, headers=headers, timeout=10)
            if response.status_code == 200:
                report = response.json()
                self.log_test("Daily Report", True, f"Retrieved daily report for {today} - {len(report)} taxistas with activity")
            else:
                self.log_test("Daily Report", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Daily Report", False, f"Exception: {str(e)}")
    
    def test_export_with_complex_filters(self):
        """Test exports with complex filter combinations"""
        print("\n🔍 TESTING EXPORTS WITH COMPLEX FILTERS")
        
        if not self.admin_token:
            return
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test services export with date range
        try:
            params = {
                "fecha_inicio": "01/12/2024",
                "fecha_fin": "31/12/2024",
                "tipo": "particular"
            }
            response = requests.get(f"{BASE_URL}/services/export/csv", params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                self.log_test("Services Export with Complex Filters", True, f"Generated CSV with filters ({len(response.content)} bytes)")
            else:
                self.log_test("Services Export with Complex Filters", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Services Export with Complex Filters", False, f"Exception: {str(e)}")
        
        # Test turnos export with multiple filters
        try:
            params = {
                "cerrado": "true",
                "liquidado": "false"
            }
            response = requests.get(f"{BASE_URL}/turnos/export/excel", params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                self.log_test("Turnos Export with Complex Filters", True, f"Generated Excel with filters ({len(response.content)} bytes)")
            else:
                self.log_test("Turnos Export with Complex Filters", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Turnos Export with Complex Filters", False, f"Exception: {str(e)}")
    
    def run_additional_tests(self):
        """Run all additional tests"""
        print("🔍 ADDITIONAL EDGE CASE AND CONFIGURATION TESTING")
        print("=" * 60)
        
        if not self.authenticate():
            print("❌ Authentication failed - stopping tests")
            return
        
        self.test_configuration_endpoints()
        self.test_edge_cases()
        self.test_service_without_turno_edge_case()
        self.test_turnos_statistics()
        self.test_daily_report()
        self.test_export_with_complex_filters()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 ADDITIONAL TESTS SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        failed = len(self.test_results) - passed
        
        print(f"Total Additional Tests: {len(self.test_results)}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/len(self.test_results)*100):.1f}%")
        
        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")

if __name__ == "__main__":
    tester = AdditionalTester()
    tester.run_additional_tests()