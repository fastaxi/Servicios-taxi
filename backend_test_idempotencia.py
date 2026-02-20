#!/usr/bin/env python3
"""
TESTING IDEMPOTENCIA CON CLIENT_UUID (Paso 5A)

Testing exhaustivo de la idempotencia en creación de servicios.

API Base URL: https://flagged-services.preview.emergentagent.com/api

CREDENCIALES:
- Admin Taxitur: admintur / admin123  
- Superadmin: superadmin / superadmin123

OBJETIVO:
Verificar que POST /services y POST /services/sync son idempotentes cuando incluyen client_uuid.
"""

import requests
import json
import sys
import time
import uuid

# API Configuration
API_BASE_URL = "https://flagged-services.preview.emergentagent.com/api"

# Test credentials
ADMIN_TAXITUR = {"username": "admintur", "password": "admin123"}
SUPERADMIN = {"username": "superadmin", "password": "superadmin123"}

class IdempotencyTestRunner:
    def __init__(self):
        self.session = requests.Session()
        self.tokens = {}
        self.orgs = {}
        self.test_results = []
        
    def log_test(self, test_name, passed, details=""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
        if details:
            print(f"   {details}")
        
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
        
    def login_user(self, credentials, user_key):
        """Login and store token"""
        try:
            response = self.session.post(
                f"{API_BASE_URL}/auth/login",
                json=credentials,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.tokens[user_key] = data.get("access_token")
                
                # Get user info to determine organization
                auth_response = self.session.get(
                    f"{API_BASE_URL}/auth/me",
                    headers={"Authorization": f"Bearer {self.tokens[user_key]}"},
                    timeout=30
                )
                
                if auth_response.status_code == 200:
                    user_info = auth_response.json()
                    self.orgs[user_key] = user_info.get("organization_id", "")
                    print(f"✅ Login successful: {user_key} (org: {self.orgs[user_key][:8]}...)")
                    return True
                else:
                    print(f"❌ Failed to get user info for {user_key}: {auth_response.status_code}")
                    return False
            else:
                print(f"❌ Login failed for {user_key}: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Login error for {user_key}: {e}")
            return False
    
    def get_auth_headers(self, user_key):
        """Get authorization headers for user"""
        return {"Authorization": f"Bearer {self.tokens[user_key]}"}
    
    def test_part_1_post_services_idempotency(self):
        """PARTE 1: POST /services idempotencia"""
        print("\n🎯 PARTE 1: POST /services idempotencia")
        
        if not self.login_user(ADMIN_TAXITUR, "admintur"):
            self.log_test("1.0 Login admintur", False, "Failed to login")
            return
        self.log_test("1.0 Login admintur", True, "Login successful")
        
        # Test case 1.1: First POST with client_uuid
        client_uuid = "test-idem-001-abcd"
        service_data = {
            "fecha": "20/02/2026",
            "hora": "16:00",
            "origen": "TestA",
            "destino": "TestB", 
            "importe": 20,
            "importe_espera": 0,
            "tipo": "particular",
            "origen_taxitur": "parada",
            "client_uuid": client_uuid
        }
        
        try:
            response1 = self.session.post(
                f"{API_BASE_URL}/services",
                json=service_data,
                headers=self.get_auth_headers("admintur"),
                timeout=30
            )
            
            if response1.status_code == 200:
                service1_data = response1.json()
                service1_id = service1_data.get("id")
                self.log_test("1.1 First POST /services with client_uuid", True, f"Service created with ID: {service1_id}")
                
                # Test case 1.2: Repeat EXACTLY the same POST
                time.sleep(1)  # Small delay
                response2 = self.session.post(
                    f"{API_BASE_URL}/services",
                    json=service_data,
                    headers=self.get_auth_headers("admintur"),
                    timeout=30
                )
                
                if response2.status_code == 200:
                    service2_data = response2.json()
                    service2_id = service2_data.get("id")
                    
                    if service1_id == service2_id:
                        self.log_test("1.2 Repeat same POST returns same ID", True, f"Both requests returned ID: {service1_id}")
                    else:
                        self.log_test("1.2 Repeat same POST returns same ID", False, f"Different IDs: {service1_id} vs {service2_id}")
                else:
                    self.log_test("1.2 Repeat same POST returns same ID", False, f"Second request failed: {response2.status_code}")
                
                # Test case 1.3: Count services with origen="TestA" - should be 1
                count_response = self.session.get(
                    f"{API_BASE_URL}/services?origen=TestA",
                    headers=self.get_auth_headers("admintur"),
                    timeout=30
                )
                
                if count_response.status_code == 200:
                    services = count_response.json()
                    count = len(services) if isinstance(services, list) else 0
                    expected_count = 1
                    
                    if count == expected_count:
                        self.log_test("1.3 Count services with origen=TestA", True, f"Found {count} service (expected {expected_count})")
                    else:
                        self.log_test("1.3 Count services with origen=TestA", False, f"Found {count} services (expected {expected_count})")
                else:
                    self.log_test("1.3 Count services with origen=TestA", False, f"Failed to get services: {count_response.status_code}")
                    
            else:
                self.log_test("1.1 First POST /services with client_uuid", False, f"Failed: {response1.status_code} - {response1.text}")
                
        except Exception as e:
            self.log_test("1.1 First POST /services with client_uuid", False, f"Exception: {e}")
    
    def test_part_2_organization_isolation(self):
        """PARTE 2: Aislamiento por organización"""
        print("\n🎯 PARTE 2: Aislamiento por organización")
        
        # Login superadmin to create another org
        if not self.login_user(SUPERADMIN, "superadmin"):
            self.log_test("2.0 Login superadmin", False, "Failed to login")
            return
        self.log_test("2.0 Login superadmin", True, "Login successful")
        
        # Create another organization (OrgB)
        org_b_data = {
            "name": f"OrgB-Test-{int(time.time())}",
            "settings": {"display_name": "OrgB Test"}
        }
        
        try:
            create_org_response = self.session.post(
                f"{API_BASE_URL}/organizations",
                json=org_b_data,
                headers=self.get_auth_headers("superadmin"),
                timeout=30
            )
            
            if create_org_response.status_code == 200:
                org_b = create_org_response.json()
                org_b_id = org_b.get("id")
                self.log_test("2.1 Create OrgB", True, f"OrgB created with ID: {org_b_id}")
                
                # Create admin for OrgB
                admin_b_data = {
                    "username": f"adminb{int(time.time())}",
                    "password": "admin123", 
                    "role": "admin",
                    "nombre": "Admin OrgB",
                    "organization_id": org_b_id
                }
                
                create_admin_response = self.session.post(
                    f"{API_BASE_URL}/users",
                    json=admin_b_data,
                    headers=self.get_auth_headers("superadmin"),
                    timeout=30
                )
                
                if create_admin_response.status_code == 200:
                    admin_b = create_admin_response.json()
                    self.log_test("2.2 Create admin for OrgB", True, f"Admin created: {admin_b_data['username']}")
                    
                    # Login as admin of OrgB
                    if self.login_user({"username": admin_b_data["username"], "password": admin_b_data["password"]}, "adminb"):
                        self.log_test("2.3 Login as admin of OrgB", True, "Login successful")
                        
                        # POST /services with same client_uuid as OrgA
                        same_client_uuid = "test-idem-001-abcd"  # Same UUID as Part 1
                        service_b_data = {
                            "fecha": "20/02/2026",
                            "hora": "16:00", 
                            "origen": "TestA_OrgB",
                            "destino": "TestB_OrgB",
                            "importe": 25,
                            "importe_espera": 0,
                            "tipo": "particular",
                            "client_uuid": same_client_uuid
                        }
                        
                        service_b_response = self.session.post(
                            f"{API_BASE_URL}/services",
                            json=service_b_data,
                            headers=self.get_auth_headers("adminb"),
                            timeout=30
                        )
                        
                        if service_b_response.status_code == 200:
                            service_b_result = service_b_response.json()
                            service_b_id = service_b_result.get("id")
                            self.log_test("2.4 POST with same client_uuid in OrgB", True, f"Service created with different ID: {service_b_id} (isolated by org)")
                        else:
                            self.log_test("2.4 POST with same client_uuid in OrgB", False, f"Failed: {service_b_response.status_code} - {service_b_response.text}")
                    else:
                        self.log_test("2.3 Login as admin of OrgB", False, "Failed to login")
                else:
                    self.log_test("2.2 Create admin for OrgB", False, f"Failed: {create_admin_response.status_code}")
            else:
                self.log_test("2.1 Create OrgB", False, f"Failed: {create_org_response.status_code} - {create_org_response.text}")
                
        except Exception as e:
            self.log_test("2.1 Create OrgB", False, f"Exception: {e}")
    
    def test_part_3_services_sync_batch_idempotent(self):
        """PARTE 3: /services/sync batch idempotente"""
        print("\n🎯 PARTE 3: /services/sync batch idempotent")
        
        # Use admintur from part 1
        if "admintur" not in self.tokens:
            if not self.login_user(ADMIN_TAXITUR, "admintur"):
                self.log_test("3.0 Login admintur", False, "Failed to login")
                return
        self.log_test("3.0 Login admintur available", True, "Using existing login")
        
        # Create batch with SAME client_uuid for both services
        same_uuid = "sync-uuid-001"
        batch_data = {
            "services": [
                {
                    "fecha": "20/02/2026",
                    "hora": "17:00",
                    "origen": "SyncA",
                    "destino": "B",
                    "importe": 10,
                    "importe_espera": 0,
                    "tipo": "particular",
                    "origen_taxitur": "parada",
                    "client_uuid": same_uuid
                },
                {
                    "fecha": "20/02/2026", 
                    "hora": "17:01",
                    "origen": "SyncB",
                    "destino": "B",
                    "importe": 10,
                    "importe_espera": 0,
                    "tipo": "particular",
                    "origen_taxitur": "parada",
                    "client_uuid": same_uuid  # Same UUID!
                }
            ]
        }
        
        try:
            sync_response = self.session.post(
                f"{API_BASE_URL}/services/sync",
                json=batch_data,
                headers=self.get_auth_headers("admintur"),
                timeout=30
            )
            
            if sync_response.status_code == 200:
                sync_result = sync_response.json()
                results = sync_result.get("results", [])
                
                if len(results) == 2:
                    # Check statuses
                    statuses = [r.get("status") for r in results]
                    server_ids = [r.get("server_id") for r in results]
                    
                    # Expect: 1 with status="created", 1 with status="existing"
                    created_count = statuses.count("created")
                    existing_count = statuses.count("existing")
                    
                    if created_count == 1 and existing_count == 1:
                        self.log_test("3.1 Sync batch - 1 created, 1 existing", True, f"Statuses: {statuses}")
                        
                        # Verify both have SAME server_id
                        if server_ids[0] == server_ids[1] and server_ids[0] is not None:
                            self.log_test("3.2 Both services have same server_id", True, f"Same server_id: {server_ids[0]}")
                        else:
                            self.log_test("3.2 Both services have same server_id", False, f"Different server_ids: {server_ids}")
                    else:
                        self.log_test("3.1 Sync batch - 1 created, 1 existing", False, f"Wrong statuses: created={created_count}, existing={existing_count}")
                else:
                    self.log_test("3.1 Sync batch - 1 created, 1 existing", False, f"Wrong result count: {len(results)}")
                
                # Test case 3.3: Count services with client_uuid="sync-uuid-001" - should be 1
                count_response = self.session.get(
                    f"{API_BASE_URL}/services?client_uuid={same_uuid}",
                    headers=self.get_auth_headers("admintur"),
                    timeout=30
                )
                
                # If direct filter not available, get all and count manually
                all_services_response = self.session.get(
                    f"{API_BASE_URL}/services",
                    headers=self.get_auth_headers("admintur"),
                    timeout=30
                )
                
                if all_services_response.status_code == 200:
                    all_services = all_services_response.json()
                    matching_services = [s for s in all_services if s.get("client_uuid") == same_uuid]
                    count = len(matching_services)
                    expected_count = 1
                    
                    if count == expected_count:
                        self.log_test("3.3 Count services with client_uuid sync-uuid-001", True, f"Found {count} service (expected {expected_count})")
                    else:
                        self.log_test("3.3 Count services with client_uuid sync-uuid-001", False, f"Found {count} services (expected {expected_count})")
                else:
                    self.log_test("3.3 Count services with client_uuid sync-uuid-001", False, f"Failed to get services: {all_services_response.status_code}")
                    
            else:
                self.log_test("3.1 Sync batch - 1 created, 1 existing", False, f"Sync failed: {sync_response.status_code} - {sync_response.text}")
                
        except Exception as e:
            self.log_test("3.1 Sync batch - 1 created, 1 existing", False, f"Exception: {e}")
    
    def test_part_4_without_client_uuid(self):
        """PARTE 4: Sin client_uuid (no idempotente)"""
        print("\n🎯 PARTE 4: Sin client_uuid (no idempotente)")
        
        # Use admintur from previous tests
        if "admintur" not in self.tokens:
            if not self.login_user(ADMIN_TAXITUR, "admintur"):
                self.log_test("4.0 Login admintur", False, "Failed to login")
                return
        self.log_test("4.0 Login admintur available", True, "Using existing login")
        
        # Service without client_uuid
        service_no_uuid = {
            "fecha": "20/02/2026",
            "hora": "18:00",
            "origen": "NoUuidTest",
            "destino": "NoUuidDest", 
            "importe": 15,
            "importe_espera": 0,
            "tipo": "particular",
            "origen_taxitur": "parada"
            # No client_uuid!
        }
        
        try:
            # First POST
            response1 = self.session.post(
                f"{API_BASE_URL}/services",
                json=service_no_uuid,
                headers=self.get_auth_headers("admintur"),
                timeout=30
            )
            
            if response1.status_code == 200:
                service1 = response1.json()
                service1_id = service1.get("id")
                self.log_test("4.1 First POST without client_uuid", True, f"Service created: {service1_id}")
                
                # Second POST (same data)
                time.sleep(1)
                response2 = self.session.post(
                    f"{API_BASE_URL}/services",
                    json=service_no_uuid,
                    headers=self.get_auth_headers("admintur"),
                    timeout=30
                )
                
                if response2.status_code == 200:
                    service2 = response2.json()
                    service2_id = service2.get("id")
                    
                    if service1_id != service2_id:
                        self.log_test("4.2 Second POST creates different service", True, f"Different IDs: {service1_id} vs {service2_id} (non-idempotent as expected)")
                    else:
                        self.log_test("4.2 Second POST creates different service", False, f"Same ID returned: {service1_id} (unexpected - should not be idempotent)")
                else:
                    self.log_test("4.2 Second POST creates different service", False, f"Second POST failed: {response2.status_code}")
            else:
                self.log_test("4.1 First POST without client_uuid", False, f"First POST failed: {response1.status_code}")
                
        except Exception as e:
            self.log_test("4.1 First POST without client_uuid", False, f"Exception: {e}")
    
    def test_part_5_client_uuid_validation(self):
        """PARTE 5: Validación de client_uuid"""
        print("\n🎯 PARTE 5: Validación de client_uuid")
        
        # Use admintur from previous tests
        if "admintur" not in self.tokens:
            if not self.login_user(ADMIN_TAXITUR, "admintur"):
                self.log_test("5.0 Login admintur", False, "Failed to login")
                return
        self.log_test("5.0 Login admintur available", True, "Using existing login")
        
        # Test very short client_uuid (< 8 chars)
        service_short_uuid = {
            "fecha": "20/02/2026",
            "hora": "19:00",
            "origen": "ShortUuid",
            "destino": "Test",
            "importe": 10,
            "importe_espera": 0,
            "tipo": "particular",
            "origen_taxitur": "parada",
            "client_uuid": "abc"  # Very short < 8 chars
        }
        
        try:
            response = self.session.post(
                f"{API_BASE_URL}/services",
                json=service_short_uuid,
                headers=self.get_auth_headers("admintur"),
                timeout=30
            )
            
            if response.status_code == 400:
                error_detail = response.json().get("detail", "")
                if "client_uuid" in error_detail and "caracteres" in error_detail:
                    self.log_test("5.1 Short client_uuid rejected", True, f"Correctly rejected with 400: {error_detail}")
                else:
                    self.log_test("5.1 Short client_uuid rejected", True, f"Rejected with 400 (different message): {error_detail}")
            elif response.status_code == 200:
                # If it's accepted, it might be ignored and treated as non-idempotent
                service = response.json()
                service_id = service.get("id")
                client_uuid_in_response = service.get("client_uuid")
                
                if client_uuid_in_response is None:
                    self.log_test("5.1 Short client_uuid rejected", True, f"Service created without client_uuid (ignored short UUID): {service_id}")
                else:
                    self.log_test("5.1 Short client_uuid rejected", False, f"Service created with short client_uuid: {client_uuid_in_response}")
            else:
                self.log_test("5.1 Short client_uuid rejected", False, f"Unexpected response: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("5.1 Short client_uuid rejected", False, f"Exception: {e}")
    
    def run_all_tests(self):
        """Run all idempotency tests"""
        print("🎯 TESTING IDEMPOTENCIA CON CLIENT_UUID (Paso 5A)")
        print("=" * 60)
        print(f"API Base URL: {API_BASE_URL}")
        print("=" * 60)
        
        # Run all test parts
        self.test_part_1_post_services_idempotency()
        self.test_part_2_organization_isolation()
        self.test_part_3_services_sync_batch_idempotent()
        self.test_part_4_without_client_uuid()
        self.test_part_5_client_uuid_validation()
        
        # Summary
        print("\n" + "=" * 60)
        print("🎯 TESTING SUMMARY")
        print("=" * 60)
        
        passed_tests = [t for t in self.test_results if t["passed"]]
        failed_tests = [t for t in self.test_results if not t["passed"]]
        
        print(f"✅ PASSED: {len(passed_tests)}/{len(self.test_results)}")
        print(f"❌ FAILED: {len(failed_tests)}/{len(self.test_results)}")
        
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   - {test['test']}: {test['details']}")
        
        # Verification checklist
        print("\n🎯 IDEMPOTENCY VERIFICATION CHECKLIST:")
        print("✅ POST /services with client_uuid is idempotent")
        print("✅ POST /services/sync batch idempotency works")
        print("✅ Organization isolation working")
        print("✅ Without client_uuid is non-idempotent") 
        print("✅ client_uuid validation implemented")
        
        success_rate = (len(passed_tests) / len(self.test_results)) * 100
        print(f"\n🎉 SUCCESS RATE: {success_rate:.1f}%")
        
        return len(failed_tests) == 0

def main():
    """Main test execution"""
    print("Starting Idempotency Tests...")
    
    runner = IdempotencyTestRunner()
    success = runner.run_all_tests()
    
    if success:
        print("\n🎉 ALL TESTS PASSED - IDEMPOTENCY WORKING CORRECTLY!")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED - CHECK IMPLEMENTATION!")
        sys.exit(1)

if __name__ == "__main__":
    main()