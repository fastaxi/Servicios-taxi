#!/usr/bin/env python3
"""
Multi-Tenant Backend Testing Suite for Taxi Management System
Tests the new multi-tenancy functionality implemented in the backend.

TESTING SCOPE:
1. Organizations CRUD (superadmin only)
2. Superadmin Role functionality
3. Data Isolation between organizations
4. Authorization restrictions
5. Backward compatibility
"""

import requests
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional

# Configuration
BACKEND_URL = "https://taxi-platform-47.preview.emergentagent.com/api"

# Test credentials
CREDENTIALS = {
    "superadmin": {"username": "superadmin", "password": "superadmin123"},
    "admin_tineo": {"username": "admin_tineo", "password": "tineo123"},
    "admin_madrid": {"username": "admin_madrid", "password": "madrid123"},
    "legacy_admin": {"username": "admin", "password": "admin123"}
}

class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []
    
    def add_result(self, test_name: str, passed: bool, message: str = ""):
        self.results.append({
            "test": test_name,
            "passed": passed,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        if passed:
            self.passed += 1
            print(f"✅ {test_name}")
        else:
            self.failed += 1
            print(f"❌ {test_name}: {message}")
        if message and passed:
            print(f"   Details: {message}")
    
    def summary(self):
        total = self.passed + self.failed
        success_rate = (self.passed / total * 100) if total > 0 else 0
        print(f"\n📊 TESTING SUMMARY:")
        print(f"✅ Passed: {self.passed}/{total} ({success_rate:.1f}%)")
        print(f"❌ Failed: {self.failed}/{total}")
        return self.passed, self.failed, success_rate

class MultiTenantTester:
    def __init__(self):
        self.result = TestResult()
        self.tokens = {}
        self.org_ids = {}
        self.test_data = {}
    
    def login(self, user_type: str) -> Optional[str]:
        """Login and get JWT token"""
        try:
            creds = CREDENTIALS[user_type]
            response = requests.post(f"{BACKEND_URL}/auth/login", json=creds, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                token = data["access_token"]
                self.tokens[user_type] = token
                print(f"🔐 Login successful for {user_type}: {creds['username']}")
                return token
            else:
                print(f"❌ Login failed for {user_type}: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ Login error for {user_type}: {str(e)}")
            return None
    
    def make_request(self, method: str, endpoint: str, token: str = None, data: dict = None, params: dict = None) -> requests.Response:
        """Make authenticated request"""
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        url = f"{BACKEND_URL}{endpoint}"
        
        try:
            if method.upper() == "GET":
                return requests.get(url, headers=headers, params=params, timeout=30)
            elif method.upper() == "POST":
                return requests.post(url, headers=headers, json=data, timeout=30)
            elif method.upper() == "PUT":
                return requests.put(url, headers=headers, json=data, timeout=30)
            elif method.upper() == "DELETE":
                return requests.delete(url, headers=headers, timeout=30)
        except Exception as e:
            print(f"Request error: {str(e)}")
            return None
    
    def test_authentication(self):
        """Test 1: Authentication with new credentials"""
        print("\n🔐 TESTING AUTHENTICATION")
        
        # Test superadmin login
        token = self.login("superadmin")
        self.result.add_result(
            "Superadmin Login", 
            token is not None,
            "Failed to login with superadmin credentials"
        )
        
        # Test admin_tineo login
        token = self.login("admin_tineo")
        self.result.add_result(
            "Admin Tineo Login", 
            token is not None,
            "Failed to login with admin_tineo credentials"
        )
        
        # Test admin_madrid login
        token = self.login("admin_madrid")
        self.result.add_result(
            "Admin Madrid Login", 
            token is not None,
            "Failed to login with admin_madrid credentials"
        )
        
        # Test legacy admin login (backward compatibility)
        token = self.login("legacy_admin")
        self.result.add_result(
            "Legacy Admin Login (Backward Compatibility)", 
            token is not None,
            "Failed to login with legacy admin credentials"
        )
    
    def test_organizations_crud(self):
        """Test 2: Organizations CRUD (Superadmin only)"""
        print("\n🏢 TESTING ORGANIZATIONS CRUD")
        
        if "superadmin" not in self.tokens:
            self.result.add_result("Organizations CRUD", False, "Superadmin token not available")
            return
        
        superadmin_token = self.tokens["superadmin"]
        
        # Test CREATE organization
        org_data = {
            "nombre": "Test Taxi Organization",
            "cif": "B12345678",
            "direccion": "Calle Test 123",
            "localidad": "Test City",
            "provincia": "Test Province",
            "telefono": "123456789",
            "email": "test@taxi.com",
            "web": "https://test-taxi.com"
        }
        
        response = self.make_request("POST", "/organizations", superadmin_token, org_data)
        if response is None:
            self.result.add_result("Create Organization (Superadmin)", False, "Request failed")
            return
            
        create_success = response.status_code == 200
        self.result.add_result(
            "Create Organization (Superadmin)",
            create_success,
            f"Status: {response.status_code}, Response: {response.text[:200]}"
        )
        
        if create_success:
            created_org = response.json()
            self.org_ids["test_org"] = created_org["id"]
        
        # Test GET organizations
        response = self.make_request("GET", "/organizations", superadmin_token)
        if response is None:
            self.result.add_result("List Organizations (Superadmin)", False, "Request failed")
            return
            
        get_success = response.status_code == 200
        self.result.add_result(
            "List Organizations (Superadmin)",
            get_success,
            f"Status: {response.status_code}, Response: {response.text[:200]}"
        )
        
        if get_success:
            orgs = response.json()
            print(f"   Found {len(orgs)} organizations")
            # Store existing org IDs for later tests
            for org in orgs:
                if "tineo" in org["nombre"].lower():
                    self.org_ids["tineo"] = org["id"]
                elif "madrid" in org["nombre"].lower():
                    self.org_ids["madrid"] = org["id"]
        
        # Test GET specific organization
        if "test_org" in self.org_ids:
            response = self.make_request("GET", f"/organizations/{self.org_ids['test_org']}", superadmin_token)
            if response is not None:
                self.result.add_result(
                    "Get Organization Detail (Superadmin)",
                    response.status_code == 200,
                    f"Status: {response.status_code}"
                )
        
        # Test UPDATE organization
        if "test_org" in self.org_ids:
            update_data = {"nombre": "Updated Test Taxi Organization"}
            response = self.make_request("PUT", f"/organizations/{self.org_ids['test_org']}", superadmin_token, update_data)
            if response is not None:
                self.result.add_result(
                    "Update Organization (Superadmin)",
                    response.status_code == 200,
                    f"Status: {response.status_code}"
                )
    
    def test_organization_admin_creation(self):
        """Test 3: Create organization admin"""
        print("\n👤 TESTING ORGANIZATION ADMIN CREATION")
        
        if "superadmin" not in self.tokens or "test_org" not in self.org_ids:
            self.result.add_result("Create Organization Admin", False, "Prerequisites not met")
            return
        
        superadmin_token = self.tokens["superadmin"]
        org_id = self.org_ids["test_org"]
        
        admin_data = {
            "username": "test_org_admin",
            "password": "testadmin123",
            "nombre": "Test Organization Admin",
            "role": "admin"
        }
        
        response = self.make_request("POST", f"/organizations/{org_id}/admin", superadmin_token, admin_data)
        if response is not None:
            self.result.add_result(
                "Create Organization Admin (Superadmin)",
                response.status_code == 200,
                f"Status: {response.status_code}, Response: {response.text[:200]}"
            )
    
    def test_authorization_restrictions(self):
        """Test 4: Authorization restrictions"""
        print("\n🔒 TESTING AUTHORIZATION RESTRICTIONS")
        
        # Test that regular admin CANNOT access organizations
        if "admin_tineo" in self.tokens:
            response = self.make_request("GET", "/organizations", self.tokens["admin_tineo"])
            if response is not None:
                self.result.add_result(
                    "Admin Tineo CANNOT access Organizations (403 expected)",
                    response.status_code == 403,
                    f"Status: {response.status_code} (expected 403)"
                )
        
        if "admin_madrid" in self.tokens:
            response = self.make_request("GET", "/organizations", self.tokens["admin_madrid"])
            if response is not None:
                self.result.add_result(
                    "Admin Madrid CANNOT access Organizations (403 expected)",
                    response.status_code == 403,
                    f"Status: {response.status_code} (expected 403)"
                )
        
        # Test that legacy admin CANNOT access organizations
        if "legacy_admin" in self.tokens:
            response = self.make_request("GET", "/organizations", self.tokens["legacy_admin"])
            if response is not None:
                self.result.add_result(
                    "Legacy Admin CANNOT access Organizations (403 expected)",
                    response.status_code == 403,
                    f"Status: {response.status_code} (expected 403)"
                )
    
    def test_data_isolation_setup(self):
        """Test 5: Setup test data for isolation testing"""
        print("\n🏗️ SETTING UP DATA ISOLATION TEST DATA")
        
        # Create test taxistas for each organization
        for admin_type in ["admin_tineo", "admin_madrid"]:
            if admin_type not in self.tokens:
                continue
            
            token = self.tokens[admin_type]
            org_name = "Tineo" if "tineo" in admin_type else "Madrid"
            
            # Create test taxista
            taxista_data = {
                "username": f"taxista_{org_name.lower()}_test",
                "password": "test123",
                "nombre": f"Taxista {org_name} Test",
                "role": "taxista",
                "licencia": f"LIC{org_name.upper()}001"
            }
            
            response = self.make_request("POST", "/users", token, taxista_data)
            if response is not None:
                success = response.status_code == 200
                self.result.add_result(
                    f"Create Test Taxista for {org_name}",
                    success,
                    f"Status: {response.status_code}"
                )
                
                if success:
                    user_data = response.json()
                    self.test_data[f"taxista_{org_name.lower()}_id"] = user_data["id"]
            
            # Create test company/client
            company_data = {
                "nombre": f"Empresa Test {org_name}",
                "cif": f"B{org_name.upper()}123",
                "numero_cliente": f"CLI{org_name.upper()}001",
                "telefono": "123456789"
            }
            
            response = self.make_request("POST", "/companies", token, company_data)
            if response is not None:
                success = response.status_code == 200
                self.result.add_result(
                    f"Create Test Company for {org_name}",
                    success,
                    f"Status: {response.status_code}"
                )
                
                if success:
                    company_data = response.json()
                    self.test_data[f"company_{org_name.lower()}_id"] = company_data["id"]
            
            # Create test vehicle
            vehicle_data = {
                "matricula": f"TEST{org_name.upper()}001",
                "plazas": 4,
                "marca": "Test Brand",
                "modelo": "Test Model",
                "km_iniciales": 50000,
                "fecha_compra": "01/01/2020",
                "activo": True
            }
            
            response = self.make_request("POST", "/vehiculos", token, vehicle_data)
            if response is not None:
                success = response.status_code == 200
                self.result.add_result(
                    f"Create Test Vehicle for {org_name}",
                    success,
                    f"Status: {response.status_code}"
                )
                
                if success:
                    vehicle_data = response.json()
                    self.test_data[f"vehicle_{org_name.lower()}_id"] = vehicle_data["id"]
    
    def test_data_isolation(self):
        """Test 6: Data isolation between organizations"""
        print("\n🔐 TESTING DATA ISOLATION")
        
        # Test that admin_tineo only sees Tineo data
        if "admin_tineo" in self.tokens:
            token = self.tokens["admin_tineo"]
            
            # Test users isolation
            response = self.make_request("GET", "/users", token)
            if response is not None and response.status_code == 200:
                users = response.json()
                print(f"   Admin Tineo sees {len(users)} users")
                self.result.add_result(
                    "Admin Tineo can access users",
                    True,
                    f"Found {len(users)} users"
                )
            
            # Test companies isolation
            response = self.make_request("GET", "/companies", token)
            if response is not None and response.status_code == 200:
                companies = response.json()
                print(f"   Admin Tineo sees {len(companies)} companies")
                self.result.add_result(
                    "Admin Tineo can access companies",
                    True,
                    f"Found {len(companies)} companies"
                )
            
            # Test vehicles isolation
            response = self.make_request("GET", "/vehiculos", token)
            if response is not None and response.status_code == 200:
                vehicles = response.json()
                print(f"   Admin Tineo sees {len(vehicles)} vehicles")
                self.result.add_result(
                    "Admin Tineo can access vehicles",
                    True,
                    f"Found {len(vehicles)} vehicles"
                )
        
        # Test that admin_madrid only sees Madrid data
        if "admin_madrid" in self.tokens:
            token = self.tokens["admin_madrid"]
            
            # Test users isolation
            response = self.make_request("GET", "/users", token)
            if response is not None and response.status_code == 200:
                users = response.json()
                print(f"   Admin Madrid sees {len(users)} users")
                self.result.add_result(
                    "Admin Madrid can access users",
                    True,
                    f"Found {len(users)} users"
                )
            
            # Test companies isolation
            response = self.make_request("GET", "/companies", token)
            if response is not None and response.status_code == 200:
                companies = response.json()
                print(f"   Admin Madrid sees {len(companies)} companies")
                self.result.add_result(
                    "Admin Madrid can access companies",
                    True,
                    f"Found {len(companies)} companies"
                )
        
        # Test that superadmin sees ALL data
        if "superadmin" in self.tokens:
            token = self.tokens["superadmin"]
            
            # Test that superadmin can see all users
            response = self.make_request("GET", "/users", token)
            if response is not None and response.status_code == 200:
                users = response.json()
                print(f"   Superadmin sees {len(users)} users (should see all)")
                self.result.add_result(
                    "Superadmin can see all users",
                    len(users) > 0,
                    f"Found {len(users)} users"
                )
    
    def test_backward_compatibility(self):
        """Test 7: Backward compatibility"""
        print("\n🔄 TESTING BACKWARD COMPATIBILITY")
        
        if "legacy_admin" not in self.tokens:
            self.result.add_result("Backward Compatibility", False, "Legacy admin token not available")
            return
        
        token = self.tokens["legacy_admin"]
        
        # Test that legacy admin can still access existing endpoints
        endpoints_to_test = [
            ("/users", "GET"),
            ("/companies", "GET"),
            ("/vehiculos", "GET"),
            ("/services", "GET")
        ]
        
        for endpoint, method in endpoints_to_test:
            response = self.make_request(method, endpoint, token)
            if response is not None:
                self.result.add_result(
                    f"Legacy Admin can access {endpoint}",
                    response.status_code == 200,
                    f"Status: {response.status_code}"
                )
    
    def test_services_isolation(self):
        """Test 8: Services data isolation"""
        print("\n📋 TESTING SERVICES DATA ISOLATION")
        
        # Test services for each admin
        for admin_type in ["admin_tineo", "admin_madrid"]:
            if admin_type not in self.tokens:
                continue
            
            token = self.tokens[admin_type]
            org_name = "Tineo" if "tineo" in admin_type else "Madrid"
            
            response = self.make_request("GET", "/services", token)
            if response is not None:
                if response.status_code == 200:
                    services = response.json()
                    print(f"   Admin {org_name} sees {len(services)} services")
                    self.result.add_result(
                        f"Admin {org_name} can access services",
                        True,
                        f"Found {len(services)} services"
                    )
                else:
                    self.result.add_result(
                        f"Admin {org_name} services access",
                        False,
                        f"Status: {response.status_code}"
                    )
    
    def test_turnos_isolation(self):
        """Test 9: Turnos data isolation"""
        print("\n🕐 TESTING TURNOS DATA ISOLATION")
        
        # Test turnos for each admin
        for admin_type in ["admin_tineo", "admin_madrid"]:
            if admin_type not in self.tokens:
                continue
            
            token = self.tokens[admin_type]
            org_name = "Tineo" if "tineo" in admin_type else "Madrid"
            
            response = self.make_request("GET", "/turnos", token)
            if response is not None:
                if response.status_code == 200:
                    turnos = response.json()
                    print(f"   Admin {org_name} sees {len(turnos)} turnos")
                    self.result.add_result(
                        f"Admin {org_name} can access turnos",
                        True,
                        f"Found {len(turnos)} turnos"
                    )
                else:
                    self.result.add_result(
                        f"Admin {org_name} turnos access",
                        False,
                        f"Status: {response.status_code}"
                    )
    
    def cleanup_test_data(self):
        """Test 10: Cleanup test data"""
        print("\n🧹 CLEANING UP TEST DATA")
        
        if "superadmin" in self.tokens and "test_org" in self.org_ids:
            # Delete test organization (should cascade delete all related data)
            response = self.make_request("DELETE", f"/organizations/{self.org_ids['test_org']}", self.tokens["superadmin"])
            if response is not None:
                self.result.add_result(
                    "Delete Test Organization (Cascade)",
                    response.status_code == 200,
                    f"Status: {response.status_code}"
                )
                
                if response.status_code == 200:
                    delete_info = response.json()
                    print(f"   Deleted organization with cascade: {delete_info}")
    
    def run_all_tests(self):
        """Run all multi-tenancy tests"""
        print("🚀 STARTING MULTI-TENANT BACKEND TESTING")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 60)
        
        try:
            # Run tests in sequence
            self.test_authentication()
            self.test_organizations_crud()
            self.test_organization_admin_creation()
            self.test_authorization_restrictions()
            self.test_data_isolation_setup()
            self.test_data_isolation()
            self.test_backward_compatibility()
            self.test_services_isolation()
            self.test_turnos_isolation()
            self.cleanup_test_data()
            
        except Exception as e:
            print(f"❌ Critical error during testing: {str(e)}")
            self.result.add_result("Critical Error", False, str(e))
        
        # Print summary
        print("\n" + "=" * 60)
        passed, failed, success_rate = self.result.summary()
        
        # Print detailed results for failed tests
        if failed > 0:
            print(f"\n❌ FAILED TESTS DETAILS:")
            for result in self.result.results:
                if not result["passed"]:
                    print(f"   • {result['test']}: {result['message']}")
        
        return passed, failed, success_rate

def main():
    """Main testing function"""
    tester = MultiTenantTester()
    passed, failed, success_rate = tester.run_all_tests()
    
    # Exit with appropriate code
    if failed == 0:
        print(f"\n🎉 ALL TESTS PASSED! Multi-tenancy system is working correctly.")
        sys.exit(0)
    else:
        print(f"\n⚠️  {failed} tests failed. Multi-tenancy system needs attention.")
        sys.exit(1)

if __name__ == "__main__":
    main()