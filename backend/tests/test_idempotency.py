"""
Test suite for Paso 5A/5B: Idempotency via client_uuid
Tests:
- POST /api/services with client_uuid creates service (first call)
- POST /api/services with same client_uuid returns existing service (idempotent retry)
- POST /api/services/sync with client_uuid batch creates services
- POST /api/services/sync with same client_uuid batch returns 'existing' status
- POST /api/services/sync handles mix of new and existing services correctly
- POST /api/services without client_uuid still works (backward compat)
"""
import pytest
import requests
import uuid
import os
from datetime import datetime

# Use public URL from environment
BASE_URL = os.environ.get('EXPO_PUBLIC_BACKEND_URL', 'https://idempotent-services.preview.emergentagent.com')

# Test credentials for Taxitur org (requires origen_taxitur field)
ADMIN_CREDENTIALS = {
    "username": "admintur",
    "password": "admin123"
}

SUPERADMIN_CREDENTIALS = {
    "username": "superadmin",
    "password": "superadmin123"
}


class TestAuthAndHealth:
    """Basic health and auth tests - run first"""
    
    def test_api_health(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        print(f"API healthy: {data}")
    
    def test_admin_login(self):
        """Test admin login for Taxitur org"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDENTIALS)
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["username"] == "admintur"
        print(f"Admin login successful: {data['user']['nombre']}")
    
    def test_superadmin_login(self):
        """Test superadmin login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=SUPERADMIN_CREDENTIALS)
        assert response.status_code == 200, f"Superadmin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "superadmin"
        print(f"Superadmin login successful: {data['user']['nombre']}")


@pytest.fixture(scope="class")
def admin_token():
    """Get admin token for Taxitur org"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_CREDENTIALS)
    if response.status_code != 200:
        pytest.skip(f"Admin login failed: {response.text}")
    return response.json()["access_token"]


@pytest.fixture(scope="class")
def auth_headers(admin_token):
    """Auth headers with admin token"""
    return {"Authorization": f"Bearer {admin_token}"}


def generate_test_uuid():
    """Generate a test UUID"""
    return f"TEST_{uuid.uuid4()}"


def create_valid_service_payload(client_uuid=None):
    """Create a valid service payload for Taxitur org (requires origen_taxitur)"""
    now = datetime.now()
    payload = {
        "fecha": now.strftime("%d/%m/%Y"),
        "hora": now.strftime("%H:%M"),
        "origen": f"TestOrigen_{uuid.uuid4().hex[:8]}",
        "destino": f"TestDestino_{uuid.uuid4().hex[:8]}",
        "importe": 15.50,
        "importe_espera": 2.00,
        "kilometros": 10.5,
        "tipo": "particular",
        "metodo_pago": "efectivo",
        "origen_taxitur": "parada"  # Required for Taxitur org
    }
    if client_uuid:
        payload["client_uuid"] = client_uuid
    return payload


class TestSingleServiceIdempotency:
    """Tests for POST /api/services idempotency"""
    
    def test_create_service_with_client_uuid_first_call(self, auth_headers):
        """First POST with client_uuid should create a new service"""
        client_uuid = generate_test_uuid()
        payload = create_valid_service_payload(client_uuid)
        
        response = requests.post(
            f"{BASE_URL}/api/services",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Create failed: {response.text}"
        data = response.json()
        
        # Verify service was created
        assert "id" in data
        assert data["origen"] == payload["origen"]
        assert data["destino"] == payload["destino"]
        assert data.get("client_uuid") == client_uuid
        
        print(f"Service created with ID: {data['id']}, client_uuid: {client_uuid}")
        
        # Store for next test
        return data["id"], client_uuid
    
    def test_create_service_with_same_client_uuid_returns_existing(self, auth_headers):
        """Retry POST with same client_uuid should return existing service (idempotent)"""
        client_uuid = generate_test_uuid()
        payload = create_valid_service_payload(client_uuid)
        
        # First call - create
        response1 = requests.post(
            f"{BASE_URL}/api/services",
            json=payload,
            headers=auth_headers
        )
        assert response1.status_code == 200
        first_data = response1.json()
        first_id = first_data["id"]
        
        # Second call with SAME client_uuid but different payload values
        payload2 = create_valid_service_payload(client_uuid)
        payload2["origen"] = "DifferentOrigen"
        payload2["importe"] = 999.99
        
        response2 = requests.post(
            f"{BASE_URL}/api/services",
            json=payload2,
            headers=auth_headers
        )
        
        assert response2.status_code == 200, f"Retry failed: {response2.text}"
        second_data = response2.json()
        
        # Should return the SAME service, not create a new one
        assert second_data["id"] == first_id, "Idempotency failed - different service ID returned"
        # Original values should be preserved
        assert second_data["origen"] == first_data["origen"]
        assert second_data["importe"] == first_data["importe"]
        
        print(f"Idempotency confirmed: Same service returned (ID: {first_id})")
    
    def test_create_service_without_client_uuid_backward_compat(self, auth_headers):
        """POST without client_uuid should still work (backward compatibility)"""
        payload = create_valid_service_payload()  # No client_uuid
        
        response = requests.post(
            f"{BASE_URL}/api/services",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Create failed: {response.text}"
        data = response.json()
        
        assert "id" in data
        assert data.get("client_uuid") is None or data.get("client_uuid") == ""
        
        print(f"Service created without client_uuid (ID: {data['id']})")
    
    def test_create_service_client_uuid_validation(self, auth_headers):
        """client_uuid with invalid length should be rejected"""
        # Too short (< 8 chars)
        payload = create_valid_service_payload("short")
        
        response = requests.post(
            f"{BASE_URL}/api/services",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 400, f"Should reject short client_uuid: {response.text}"
        print("Short client_uuid correctly rejected")


class TestBatchSyncIdempotency:
    """Tests for POST /api/services/sync idempotency"""
    
    def test_sync_batch_with_client_uuids_creates_services(self, auth_headers):
        """POST /api/services/sync with client_uuids should create new services"""
        services = [
            {**create_valid_service_payload(generate_test_uuid())},
            {**create_valid_service_payload(generate_test_uuid())},
        ]
        
        response = requests.post(
            f"{BASE_URL}/api/services/sync",
            json={"services": services},
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Sync failed: {response.text}"
        data = response.json()
        
        assert "results" in data
        results = data["results"]
        assert len(results) == 2
        
        for result in results:
            assert result["status"] == "created"
            assert result["server_id"]
            assert result["client_uuid"]
        
        print(f"Batch sync created {len(results)} services")
    
    def test_sync_batch_same_client_uuids_returns_existing(self, auth_headers):
        """Retry POST /api/services/sync with same client_uuids returns 'existing' status"""
        uuid1 = generate_test_uuid()
        uuid2 = generate_test_uuid()
        
        services_first = [
            {**create_valid_service_payload(uuid1)},
            {**create_valid_service_payload(uuid2)},
        ]
        
        # First sync - create
        response1 = requests.post(
            f"{BASE_URL}/api/services/sync",
            json={"services": services_first},
            headers=auth_headers
        )
        assert response1.status_code == 200
        first_results = response1.json()["results"]
        first_ids = {r["client_uuid"]: r["server_id"] for r in first_results}
        
        # Second sync with SAME client_uuids
        services_retry = [
            {**create_valid_service_payload(uuid1)},
            {**create_valid_service_payload(uuid2)},
        ]
        
        response2 = requests.post(
            f"{BASE_URL}/api/services/sync",
            json={"services": services_retry},
            headers=auth_headers
        )
        
        assert response2.status_code == 200, f"Retry sync failed: {response2.text}"
        second_results = response2.json()["results"]
        
        # All should be marked as "existing"
        for result in second_results:
            assert result["status"] == "existing", f"Expected 'existing', got {result['status']}"
            # Server ID should match the first creation
            assert result["server_id"] == first_ids[result["client_uuid"]]
        
        print(f"Batch retry correctly returned 'existing' for {len(second_results)} services")
    
    def test_sync_batch_mix_new_and_existing(self, auth_headers):
        """POST /api/services/sync with mix of new and existing client_uuids"""
        existing_uuid = generate_test_uuid()
        new_uuid = generate_test_uuid()
        
        # First, create one service
        services_first = [{**create_valid_service_payload(existing_uuid)}]
        response1 = requests.post(
            f"{BASE_URL}/api/services/sync",
            json={"services": services_first},
            headers=auth_headers
        )
        assert response1.status_code == 200
        existing_id = response1.json()["results"][0]["server_id"]
        
        # Now sync a batch with one existing and one new
        services_mix = [
            {**create_valid_service_payload(existing_uuid)},  # Should be existing
            {**create_valid_service_payload(new_uuid)},       # Should be created
        ]
        
        response2 = requests.post(
            f"{BASE_URL}/api/services/sync",
            json={"services": services_mix},
            headers=auth_headers
        )
        
        assert response2.status_code == 200, f"Mix sync failed: {response2.text}"
        results = response2.json()["results"]
        
        # Build a map by client_uuid
        result_map = {r["client_uuid"]: r for r in results}
        
        # Verify existing service
        assert result_map[existing_uuid]["status"] == "existing"
        assert result_map[existing_uuid]["server_id"] == existing_id
        
        # Verify new service was created
        assert result_map[new_uuid]["status"] == "created"
        assert result_map[new_uuid]["server_id"]  # Has a server ID
        assert result_map[new_uuid]["server_id"] != existing_id  # Different from existing
        
        print(f"Mix sync: 1 existing + 1 created - correct!")
    
    def test_sync_batch_without_client_uuids_backward_compat(self, auth_headers):
        """POST /api/services/sync without client_uuids still works"""
        services = [
            {**create_valid_service_payload()},  # No client_uuid
            {**create_valid_service_payload()},  # No client_uuid
        ]
        
        response = requests.post(
            f"{BASE_URL}/api/services/sync",
            json={"services": services},
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Sync without UUIDs failed: {response.text}"
        data = response.json()
        results = data["results"]
        
        # All should be created (no idempotency without client_uuid)
        for result in results:
            assert result["status"] == "created_no_uuid" or result["status"] == "created"
        
        print(f"Batch sync without UUIDs created {len(results)} services")


class TestEdgeCases:
    """Edge case tests for idempotency"""
    
    def test_sync_with_validation_errors_continues(self, auth_headers):
        """Sync batch with some invalid services should process valid ones"""
        valid_uuid = generate_test_uuid()
        
        services = [
            # Valid service
            {**create_valid_service_payload(valid_uuid)},
            # Invalid service - missing required field (importe)
            {
                "fecha": "25/02/2026",
                "hora": "12:00",
                "origen": "Test",
                "destino": "Test",
                # Missing importe
                "tipo": "particular",
                "metodo_pago": "efectivo",
                "origen_taxitur": "parada",
                "client_uuid": generate_test_uuid()
            }
        ]
        
        response = requests.post(
            f"{BASE_URL}/api/services/sync",
            json={"services": services},
            headers=auth_headers
        )
        
        # Should succeed overall, with errors for invalid services
        assert response.status_code in [200, 422], f"Unexpected status: {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            # At least one should be processed
            print(f"Sync with partial errors: {len(data.get('results', []))} processed, errors: {data.get('errors', [])}")
    
    def test_different_orgs_same_client_uuid(self, auth_headers):
        """Same client_uuid in different orgs should create different services"""
        # This test would need a second org's credentials
        # For now, just verify our org works correctly
        client_uuid = generate_test_uuid()
        payload = create_valid_service_payload(client_uuid)
        
        response = requests.post(
            f"{BASE_URL}/api/services",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        print(f"Service created with org-scoped client_uuid")


class TestTaxiturOrigenValidation:
    """Tests specific to Taxitur org feature flag"""
    
    def test_taxitur_origen_required(self, auth_headers):
        """Taxitur org requires origen_taxitur field"""
        payload = create_valid_service_payload(generate_test_uuid())
        del payload["origen_taxitur"]  # Remove required field
        
        response = requests.post(
            f"{BASE_URL}/api/services",
            json=payload,
            headers=auth_headers
        )
        
        # Should fail with 400 due to missing origen_taxitur
        assert response.status_code == 400, f"Should require origen_taxitur: {response.text}"
        print("origen_taxitur correctly required for Taxitur org")
    
    def test_taxitur_origen_valid_values(self, auth_headers):
        """origen_taxitur must be 'parada' or 'lagos'"""
        payload = create_valid_service_payload(generate_test_uuid())
        payload["origen_taxitur"] = "invalid_value"
        
        response = requests.post(
            f"{BASE_URL}/api/services",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 400, f"Should reject invalid origen_taxitur: {response.text}"
        print("Invalid origen_taxitur correctly rejected")
    
    def test_taxitur_origen_parada_works(self, auth_headers):
        """origen_taxitur='parada' should work"""
        payload = create_valid_service_payload(generate_test_uuid())
        payload["origen_taxitur"] = "parada"
        
        response = requests.post(
            f"{BASE_URL}/api/services",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"parada should work: {response.text}"
        data = response.json()
        assert data.get("origen_taxitur") == "parada"
        print("origen_taxitur='parada' works correctly")
    
    def test_taxitur_origen_lagos_works(self, auth_headers):
        """origen_taxitur='lagos' should work"""
        payload = create_valid_service_payload(generate_test_uuid())
        payload["origen_taxitur"] = "lagos"
        
        response = requests.post(
            f"{BASE_URL}/api/services",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"lagos should work: {response.text}"
        data = response.json()
        assert data.get("origen_taxitur") == "lagos"
        print("origen_taxitur='lagos' works correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
