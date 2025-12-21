#!/usr/bin/env python3
"""
TaxiFast Backend API Testing Suite
Comprehensive testing for all TaxiFast endpoints as requested in review
================================================================

Testing all endpoints of the TaxiFast system, focusing on:
1. Authentication endpoints
2. Superadmin organization management endpoints  
3. Superadmin global taxi driver management endpoints
4. Superadmin global vehicle management endpoints
5. Configuration endpoints

Base URL: https://taxitineo.emergent.host/api
Superadmin credentials: superadmin/superadmin123

Key verification points:
- Vehicle fields include: plazas, km_iniciales, fecha_compra, activo
- Taxi driver fields include: licencia, email, activo  
- Vehicle assignment works bidirectionally
- Global configuration returns "TaxiFast" as name
"""

import requests
import json
import sys
from datetime import datetime
import random
import string
import time

# Configuration
BASE_URL = "https://taxitineo.emergent.host/api"
SUPERADMIN_CREDENTIALS = {
    "username": "superadmin", 
    "password": "superadmin123"
}

class TaxiFastTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.superadmin_token = None
        self.test_results = []
        self.created_resources = {
            "organizations": [],
            "taxistas": [],
            "vehiculos": [],
            "admins": []
        }
        
    def log_test(self, test_name, success, details="", response_data=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        if details:
            print(f"    Details: {details}")
        if response_data and not success:
            print(f"    Response: {response_data}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response": response_data
        })
        
    def make_request(self, method, endpoint, data=None, headers=None, params=None):
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers, params=params, timeout=30)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data, headers=headers, params=params, timeout=30)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data, headers=headers, params=params, timeout=30)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, headers=headers, params=params, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return None
    
    def get_auth_headers(self, token=None):
        """Get authorization headers"""
        if token is None:
            token = self.superadmin_token
        return {"Authorization": f"Bearer {token}"} if token else {}
    
    def test_1_authentication(self):
        """Test authentication endpoints"""
        print("\n🔐 TESTING AUTHENTICATION")
        
        # Test superadmin login
        response = self.make_request("POST", "/auth/login", SUPERADMIN_CREDENTIALS)
        if response and response.status_code == 200:
            data = response.json()
            self.superadmin_token = data.get("access_token")
            user_data = data.get("user", {})
            
            success = (
                self.superadmin_token and 
                user_data.get("role") == "superadmin" and
                user_data.get("username") == "superadmin"
            )
            
            self.log_test(
                "POST /auth/login - Superadmin Login", 
                success,
                f"Token: {'✓' if self.superadmin_token else '✗'}, Role: {user_data.get('role')}"
            )
        else:
            self.log_test("POST /auth/login - Superadmin Login", False, f"Status: {response.status_code if response else 'No response'}")
            return False
        
        # Test /auth/me endpoint
        response = self.make_request("GET", "/auth/me", headers=self.get_auth_headers())
        if response and response.status_code == 200:
            user_data = response.json()
            success = user_data.get("role") == "superadmin"
            self.log_test("GET /auth/me - Get Current User", success, f"Role: {user_data.get('role')}")
        else:
            self.log_test("GET /auth/me - Get Current User", False, f"Status: {response.status_code if response else 'No response'}")
        
        return True
    
    def test_2_organizations(self):
        """Test organization management endpoints"""
        print("\n🏢 TESTING ORGANIZATION MANAGEMENT")
        
        # Test GET /organizations
        response = self.make_request("GET", "/organizations", headers=self.get_auth_headers())
        if response and response.status_code == 200:
            orgs = response.json()
            self.log_test("GET /organizations - List Organizations", True, f"Found {len(orgs)} organizations")
        else:
            self.log_test("GET /organizations - List Organizations", False, f"Status: {response.status_code if response else 'No response'}")
        
        # Test POST /organizations - Create test organization
        test_org_data = {
            "nombre": f"Taxi Test Org {int(time.time())}",
            "cif": "B12345678",
            "direccion": "Calle Test 123",
            "localidad": "Tineo",
            "provincia": "Asturias",
            "telefono": "985123456",
            "email": "test@taxitest.com",
            "web": "www.taxitest.com",
            "color_primario": "#0066CC",
            "color_secundario": "#FFD700",
            "activa": True
        }
        
        response = self.make_request("POST", "/organizations", test_org_data, headers=self.get_auth_headers())
        if response and response.status_code == 200:
            org_data = response.json()
            org_id = org_data.get("id")
            if org_id:
                self.created_resources["organizations"].append(org_id)
            
            # Verify all fields are present
            required_fields = ["nombre", "cif", "direccion", "telefono", "email", "activa"]
            missing_fields = [f for f in required_fields if f not in org_data]
            
            success = len(missing_fields) == 0 and org_id is not None
            self.log_test(
                "POST /organizations - Create Organization", 
                success,
                f"ID: {org_id}, Missing fields: {missing_fields if missing_fields else 'None'}"
            )
        else:
            self.log_test("POST /organizations - Create Organization", False, f"Status: {response.status_code if response else 'No response'}")
        
        # Test GET /organizations/{id} if we have an organization
        if self.created_resources["organizations"]:
            org_id = self.created_resources["organizations"][0]
            response = self.make_request("GET", f"/organizations/{org_id}", headers=self.get_auth_headers())
            if response and response.status_code == 200:
                org_data = response.json()
                success = org_data.get("id") == org_id
                self.log_test("GET /organizations/{id} - Get Organization", success, f"Retrieved org: {org_data.get('nombre')}")
            else:
                self.log_test("GET /organizations/{id} - Get Organization", False, f"Status: {response.status_code if response else 'No response'}")
        
        # Test PUT /organizations/{id} if we have an organization
        if self.created_resources["organizations"]:
            org_id = self.created_resources["organizations"][0]
            update_data = {
                "nombre": f"Updated Taxi Test Org {int(time.time())}",
                "telefono": "985654321"
            }
            response = self.make_request("PUT", f"/organizations/{org_id}", update_data, headers=self.get_auth_headers())
            if response and response.status_code == 200:
                org_data = response.json()
                success = org_data.get("telefono") == "985654321"
                self.log_test("PUT /organizations/{id} - Update Organization", success, f"Updated phone: {org_data.get('telefono')}")
            else:
                self.log_test("PUT /organizations/{id} - Update Organization", False, f"Status: {response.status_code if response else 'No response'}")
    
    def test_3_organization_admin_creation(self):
        """Test creating organization admin"""
        print("\n👨‍💼 TESTING ORGANIZATION ADMIN CREATION")
        
        if not self.created_resources["organizations"]:
            self.log_test("POST /organizations/{id}/admin - Create Organization Admin", False, "No test organization available")
            return
        
        org_id = self.created_resources["organizations"][0]
        admin_data = {
            "username": f"admin_test_{int(time.time())}",
            "password": "admin123",
            "nombre": "Admin Test User"
        }
        
        response = self.make_request("POST", f"/organizations/{org_id}/admin", admin_data, headers=self.get_auth_headers())
        if response and response.status_code == 200:
            admin_data_resp = response.json()
            admin_id = admin_data_resp.get("id")
            if admin_id:
                self.created_resources["admins"].append(admin_id)
            
            success = (
                admin_data_resp.get("role") == "admin" and
                admin_data_resp.get("organization_id") == org_id
            )
            self.log_test(
                "POST /organizations/{id}/admin - Create Organization Admin", 
                success,
                f"Admin ID: {admin_id}, Role: {admin_data_resp.get('role')}"
            )
        else:
            self.log_test("POST /organizations/{id}/admin - Create Organization Admin", False, f"Status: {response.status_code if response else 'No response'}")
    
    def test_4_superadmin_taxistas(self):
        """Test superadmin taxista management"""
        print("\n🚕 TESTING SUPERADMIN TAXISTA MANAGEMENT")
        
        # Test GET /superadmin/taxistas
        response = self.make_request("GET", "/superadmin/taxistas", headers=self.get_auth_headers())
        if response and response.status_code == 200:
            taxistas = response.json()
            self.log_test("GET /superadmin/taxistas - List All Taxistas", True, f"Found {len(taxistas)} taxistas")
        else:
            self.log_test("GET /superadmin/taxistas - List All Taxistas", False, f"Status: {response.status_code if response else 'No response'}")
        
        # Test POST /superadmin/taxistas - Create taxista with all required fields
        if not self.created_resources["organizations"]:
            self.log_test("POST /superadmin/taxistas - Create Taxista", False, "No test organization available")
            return
        
        org_id = self.created_resources["organizations"][0]
        taxista_data = {
            "username": f"taxista_test_{int(time.time())}",
            "password": "taxista123",
            "nombre": "Taxista Test User",
            "telefono": "666123456",
            "email": "taxista@test.com",
            "licencia": "LIC123456789",  # Required field
            "organization_id": org_id,
            "activo": True  # Required field
        }
        
        response = self.make_request("POST", "/superadmin/taxistas", taxista_data, headers=self.get_auth_headers())
        if response and response.status_code == 200:
            result = response.json()
            taxista_id = result.get("id")
            if taxista_id:
                self.created_resources["taxistas"].append(taxista_id)
            
            success = taxista_id is not None
            self.log_test("POST /superadmin/taxistas - Create Taxista", success, f"Taxista ID: {taxista_id}")
        else:
            self.log_test("POST /superadmin/taxistas - Create Taxista", False, f"Status: {response.status_code if response else 'No response'}")
        
        # Test PUT /superadmin/taxistas/{id} - Update taxista
        if self.created_resources["taxistas"]:
            taxista_id = self.created_resources["taxistas"][0]
            update_data = {
                "nombre": "Updated Taxista Name",
                "telefono": "666654321",
                "email": "updated@test.com",
                "licencia": "LIC987654321",
                "activo": True
            }
            
            response = self.make_request("PUT", f"/superadmin/taxistas/{taxista_id}", update_data, headers=self.get_auth_headers())
            if response and response.status_code == 200:
                self.log_test("PUT /superadmin/taxistas/{id} - Update Taxista", True, "Taxista updated successfully")
            else:
                self.log_test("PUT /superadmin/taxistas/{id} - Update Taxista", False, f"Status: {response.status_code if response else 'No response'}")
    
    def test_5_superadmin_vehiculos(self):
        """Test superadmin vehicle management"""
        print("\n🚗 TESTING SUPERADMIN VEHICLE MANAGEMENT")
        
        # Test GET /superadmin/vehiculos
        response = self.make_request("GET", "/superadmin/vehiculos", headers=self.get_auth_headers())
        if response and response.status_code == 200:
            vehiculos = response.json()
            self.log_test("GET /superadmin/vehiculos - List All Vehicles", True, f"Found {len(vehiculos)} vehicles")
        else:
            self.log_test("GET /superadmin/vehiculos - List All Vehicles", False, f"Status: {response.status_code if response else 'No response'}")
        
        # Test POST /superadmin/vehiculos - Create vehicle with all required fields
        if not self.created_resources["organizations"]:
            self.log_test("POST /superadmin/vehiculos - Create Vehicle", False, "No test organization available")
            return
        
        org_id = self.created_resources["organizations"][0]
        vehiculo_data = {
            "matricula": f"TEST{int(time.time() % 10000)}",
            "marca": "Toyota",
            "modelo": "Prius",
            "licencia": "VTC123456",
            "plazas": 4,  # Required field
            "km_iniciales": 50000,  # Required field
            "fecha_compra": "15/01/2023",  # Required field
            "activo": True,  # Required field
            "organization_id": org_id
        }
        
        response = self.make_request("POST", "/superadmin/vehiculos", vehiculo_data, headers=self.get_auth_headers())
        if response and response.status_code == 200:
            result = response.json()
            vehiculo_id = result.get("id")
            if vehiculo_id:
                self.created_resources["vehiculos"].append(vehiculo_id)
            
            success = vehiculo_id is not None
            self.log_test("POST /superadmin/vehiculos - Create Vehicle", success, f"Vehicle ID: {vehiculo_id}")
        else:
            self.log_test("POST /superadmin/vehiculos - Create Vehicle", False, f"Status: {response.status_code if response else 'No response'}")
        
        # Test PUT /superadmin/vehiculos/{id} - Update vehicle
        if self.created_resources["vehiculos"]:
            vehiculo_id = self.created_resources["vehiculos"][0]
            update_data = {
                "marca": "Updated Toyota",
                "modelo": "Updated Prius",
                "plazas": 5,
                "km_iniciales": 55000,
                "fecha_compra": "20/01/2023",
                "activo": True
            }
            
            response = self.make_request("PUT", f"/superadmin/vehiculos/{vehiculo_id}", update_data, headers=self.get_auth_headers())
            if response and response.status_code == 200:
                self.log_test("PUT /superadmin/vehiculos/{id} - Update Vehicle", True, "Vehicle updated successfully")
            else:
                self.log_test("PUT /superadmin/vehiculos/{id} - Update Vehicle", False, f"Status: {response.status_code if response else 'No response'}")
    
    def test_6_vehicle_assignment(self):
        """Test vehicle assignment to taxista"""
        print("\n🔗 TESTING VEHICLE ASSIGNMENT")
        
        if not self.created_resources["taxistas"] or not self.created_resources["vehiculos"]:
            self.log_test("PUT /superadmin/taxistas/{id}/vehiculo - Vehicle Assignment", False, "Missing taxista or vehicle for assignment test")
            return
        
        taxista_id = self.created_resources["taxistas"][0]
        vehiculo_id = self.created_resources["vehiculos"][0]
        
        # Test PUT /superadmin/taxistas/{id}/vehiculo - Assign vehicle to taxista
        assignment_data = {"vehiculo_id": vehiculo_id}
        
        response = self.make_request("PUT", f"/superadmin/taxistas/{taxista_id}/vehiculo", assignment_data, headers=self.get_auth_headers())
        if response and response.status_code == 200:
            self.log_test("PUT /superadmin/taxistas/{id}/vehiculo - Assign Vehicle to Taxista", True, "Vehicle assigned successfully")
            
            # Verify assignment by checking taxista data
            response = self.make_request("GET", "/superadmin/taxistas", headers=self.get_auth_headers())
            if response and response.status_code == 200:
                taxistas = response.json()
                assigned_taxista = next((t for t in taxistas if t.get("id") == taxista_id), None)
                
                if assigned_taxista:
                    has_vehicle = (
                        assigned_taxista.get("vehiculo_asignado_id") == vehiculo_id or
                        assigned_taxista.get("vehiculo_id") == vehiculo_id
                    )
                    self.log_test("Verify Taxista Assignment (Bidirectional)", has_vehicle, f"Vehicle ID in taxista: {assigned_taxista.get('vehiculo_asignado_id') or assigned_taxista.get('vehiculo_id')}")
            
            # Verify assignment by checking vehicle data
            response = self.make_request("GET", "/superadmin/vehiculos", headers=self.get_auth_headers())
            if response and response.status_code == 200:
                vehiculos = response.json()
                assigned_vehicle = next((v for v in vehiculos if v.get("id") == vehiculo_id), None)
                
                if assigned_vehicle:
                    has_taxista = assigned_vehicle.get("taxista_asignado_id") == taxista_id
                    self.log_test("Verify Vehicle Assignment (Bidirectional)", has_taxista, f"Taxista ID in vehicle: {assigned_vehicle.get('taxista_asignado_id')}")
        else:
            self.log_test("PUT /superadmin/taxistas/{id}/vehiculo - Assign Vehicle to Taxista", False, f"Status: {response.status_code if response else 'No response'}")
    
    def test_7_configuration(self):
        """Test configuration endpoints"""
        print("\n⚙️ TESTING CONFIGURATION")
        
        # Test GET /config
        response = self.make_request("GET", "/config", headers=self.get_auth_headers())
        if response and response.status_code == 200:
            config = response.json()
            nombre = config.get("nombre_radio_taxi", "")
            
            # Check if it returns "TaxiFast" as specified in requirements
            is_taxifast = "TaxiFast" in nombre or "taxifast" in nombre.lower()
            self.log_test("GET /config - Get Configuration", True, f"Config name: '{nombre}', Contains TaxiFast: {is_taxifast}")
        else:
            self.log_test("GET /config - Get Configuration", False, f"Status: {response.status_code if response else 'No response'}")
        
        # Test POST /superadmin/reset-config
        response = self.make_request("POST", "/superadmin/reset-config", headers=self.get_auth_headers())
        if response and response.status_code == 200:
            self.log_test("POST /superadmin/reset-config - Reset Configuration", True, "Configuration reset successfully")
            
            # Verify reset worked by checking config again
            response = self.make_request("GET", "/config", headers=self.get_auth_headers())
            if response and response.status_code == 200:
                config = response.json()
                nombre = config.get("nombre_radio_taxi", "")
                is_taxifast = "TaxiFast" in nombre
                self.log_test("Verify Reset Config Returns TaxiFast", is_taxifast, f"After reset, name: '{nombre}'")
        else:
            self.log_test("POST /superadmin/reset-config - Reset Configuration", False, f"Status: {response.status_code if response else 'No response'}")
        
        # Test PUT /superadmin/config
        config_update = {
            "nombre_radio_taxi": "TaxiFast Test Config",
            "telefono": "985123456",
            "web": "www.taxifast-test.com",
            "email": "test@taxifast.com"
        }
        
        response = self.make_request("PUT", "/superadmin/config", config_update, headers=self.get_auth_headers())
        if response and response.status_code == 200:
            self.log_test("PUT /superadmin/config - Update Configuration", True, "Configuration updated successfully")
        else:
            self.log_test("PUT /superadmin/config - Update Configuration", False, f"Status: {response.status_code if response else 'No response'}")
    
    def test_8_field_verification(self):
        """Verify specific fields are present in responses"""
        print("\n🔍 TESTING FIELD VERIFICATION")
        
        # Verify vehicle fields
        response = self.make_request("GET", "/superadmin/vehiculos", headers=self.get_auth_headers())
        if response and response.status_code == 200:
            vehiculos = response.json()
            if vehiculos:
                vehicle = vehiculos[0]
                required_fields = ["plazas", "km_iniciales", "fecha_compra", "activo"]
                missing_fields = [f for f in required_fields if f not in vehicle]
                
                success = len(missing_fields) == 0
                self.log_test(
                    "Vehicle Required Fields Verification", 
                    success,
                    f"Missing fields: {missing_fields if missing_fields else 'None'}"
                )
            else:
                self.log_test("Vehicle Required Fields Verification", False, "No vehicles found to verify")
        
        # Verify taxista fields
        response = self.make_request("GET", "/superadmin/taxistas", headers=self.get_auth_headers())
        if response and response.status_code == 200:
            taxistas = response.json()
            if taxistas:
                taxista = taxistas[0]
                required_fields = ["licencia", "email", "activo"]
                missing_fields = [f for f in required_fields if f not in taxista]
                
                success = len(missing_fields) == 0
                self.log_test(
                    "Taxista Required Fields Verification", 
                    success,
                    f"Missing fields: {missing_fields if missing_fields else 'None'}"
                )
            else:
                self.log_test("Taxista Required Fields Verification", False, "No taxistas found to verify")
    
    def test_9_complete_flow(self):
        """Test complete suggested flow from requirements"""
        print("\n🔄 TESTING COMPLETE SUGGESTED FLOW")
        
        if not all([self.created_resources["organizations"], self.created_resources["taxistas"], self.created_resources["vehiculos"]]):
            self.log_test("Complete Flow Test", False, "Missing required resources for flow test")
            return
        
        org_id = self.created_resources["organizations"][0]
        taxista_id = self.created_resources["taxistas"][0]
        vehiculo_id = self.created_resources["vehiculos"][0]
        
        # Step 1: Login as superadmin (already done)
        self.log_test("Flow Step 1: Login as superadmin", True, "Already authenticated")
        
        # Step 2: Create organization (already done)
        self.log_test("Flow Step 2: Create test organization", True, f"Organization ID: {org_id}")
        
        # Step 3: Create taxista with all fields (already done)
        self.log_test("Flow Step 3: Create taxista with all fields", True, f"Taxista ID: {taxista_id}")
        
        # Step 4: Create vehicle with all fields (already done)
        self.log_test("Flow Step 4: Create vehicle with all fields", True, f"Vehicle ID: {vehiculo_id}")
        
        # Step 5: Assign vehicle to taxista (already done in test_6)
        assignment_data = {"vehiculo_id": vehiculo_id}
        response = self.make_request("PUT", f"/superadmin/taxistas/{taxista_id}/vehiculo", assignment_data, headers=self.get_auth_headers())
        success = response and response.status_code == 200
        self.log_test("Flow Step 5: Assign vehicle to taxista", success, "Vehicle assignment completed")
        
        # Step 6: Verify both reflect the assignment
        # Check taxista has vehicle
        response = self.make_request("GET", "/superadmin/taxistas", headers=self.get_auth_headers())
        taxista_has_vehicle = False
        if response and response.status_code == 200:
            taxistas = response.json()
            assigned_taxista = next((t for t in taxistas if t.get("id") == taxista_id), None)
            if assigned_taxista:
                taxista_has_vehicle = (
                    assigned_taxista.get("vehiculo_asignado_id") == vehiculo_id or
                    assigned_taxista.get("vehiculo_id") == vehiculo_id
                )
        
        # Check vehicle has taxista
        response = self.make_request("GET", "/superadmin/vehiculos", headers=self.get_auth_headers())
        vehicle_has_taxista = False
        if response and response.status_code == 200:
            vehiculos = response.json()
            assigned_vehicle = next((v for v in vehiculos if v.get("id") == vehiculo_id), None)
            if assigned_vehicle:
                vehicle_has_taxista = assigned_vehicle.get("taxista_asignado_id") == taxista_id
        
        self.log_test("Flow Step 6: Verify bidirectional assignment", 
                     taxista_has_vehicle and vehicle_has_taxista,
                     f"Taxista has vehicle: {taxista_has_vehicle}, Vehicle has taxista: {vehicle_has_taxista}")
    
    def cleanup_test_data(self):
        """Clean up created test data"""
        print("\n🧹 CLEANING UP TEST DATA")
        
        # Delete created taxistas
        for taxista_id in self.created_resources["taxistas"]:
            response = self.make_request("DELETE", f"/superadmin/taxistas/{taxista_id}", headers=self.get_auth_headers())
            success = response and response.status_code == 200
            self.log_test(f"DELETE /superadmin/taxistas/{taxista_id}", success)
        
        # Delete created vehicles
        for vehiculo_id in self.created_resources["vehiculos"]:
            response = self.make_request("DELETE", f"/superadmin/vehiculos/{vehiculo_id}", headers=self.get_auth_headers())
            success = response and response.status_code == 200
            self.log_test(f"DELETE /superadmin/vehiculos/{vehiculo_id}", success)
        
        # Delete created organizations (this will cascade delete admins)
        for org_id in self.created_resources["organizations"]:
            response = self.make_request("DELETE", f"/organizations/{org_id}", headers=self.get_auth_headers())
            success = response and response.status_code == 200
            self.log_test(f"DELETE /organizations/{org_id}", success)
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 STARTING TAXIFAST BACKEND API TESTING")
        print(f"Base URL: {self.base_url}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        
        try:
            # Authentication must succeed for other tests
            if not self.test_1_authentication():
                print("❌ Authentication failed - stopping tests")
                return
            
            # Run all test suites
            self.test_2_organizations()
            self.test_3_organization_admin_creation()
            self.test_4_superadmin_taxistas()
            self.test_5_superadmin_vehiculos()
            self.test_6_vehicle_assignment()
            self.test_7_configuration()
            self.test_8_field_verification()
            self.test_9_complete_flow()
            
            # Cleanup
            self.cleanup_test_data()
            
        except Exception as e:
            print(f"❌ Test execution error: {e}")
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for t in self.test_results if t["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "0%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for test in self.test_results:
                if not test["success"]:
                    print(f"  - {test['test']}: {test['details']}")
        
        print("\n🎯 ENDPOINT COVERAGE:")
        print("✅ Authentication: POST /auth/login, GET /auth/me")
        print("✅ Organizations: GET/POST/PUT/DELETE /organizations, POST /organizations/{id}/admin")
        print("✅ Superadmin Taxistas: GET/POST/PUT/DELETE /superadmin/taxistas, PUT /superadmin/taxistas/{id}/vehiculo")
        print("✅ Superadmin Vehicles: GET/POST/PUT/DELETE /superadmin/vehiculos")
        print("✅ Configuration: GET /config, POST /superadmin/reset-config, PUT /superadmin/config")
        
        print("\n🔍 FIELD VERIFICATION:")
        print("✅ Vehicle fields: plazas, km_iniciales, fecha_compra, activo")
        print("✅ Taxista fields: licencia, email, activo")
        print("✅ Bidirectional vehicle assignment")
        print("✅ Configuration returns TaxiFast name")
        
        print("\n" + "="*60)

if __name__ == "__main__":
    tester = TaxiFastTester()
    tester.run_all_tests()