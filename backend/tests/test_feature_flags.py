"""
Test Suite for Paso 6: Feature Flags Superadmin UI
Tests PUT /api/superadmin/organizations/{org_id}/features endpoint

Test cases:
1. Superadmin can toggle taxitur_origen to true/false (200)
2. Admin gets 403 Forbidden
3. Invalid feature key returns 400
4. Non-boolean value returns 400
5. Empty features object returns 400
6. Merge preserves existing features
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://idempotent-services.preview.emergentagent.com')
if BASE_URL.endswith('/'):
    BASE_URL = BASE_URL.rstrip('/')

# Test credentials from review request
SUPERADMIN_CREDS = {"username": "superadmin", "password": "superadmin123"}
ADMIN_CREDS = {"username": "admintur", "password": "admin123"}
TAXITUR_ORG_ID = "69484bec187c3bc2b0fdb8f4"


@pytest.fixture(scope="module")
def superadmin_token():
    """Get authentication token for superadmin"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json=SUPERADMIN_CREDS,
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 200, f"Superadmin login failed: {response.text}"
    token = response.json().get("access_token")
    assert token, "No access_token in superadmin login response"
    return token


@pytest.fixture(scope="module")
def admin_token():
    """Get authentication token for admin (Taxitur)"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json=ADMIN_CREDS,
        headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    token = response.json().get("access_token")
    assert token, "No access_token in admin login response"
    return token


class TestFeatureFlagsAuthorization:
    """Test authorization rules for feature flags endpoint"""

    def test_superadmin_can_toggle_feature_on(self, superadmin_token):
        """Superadmin can toggle taxitur_origen to true (200)"""
        response = requests.put(
            f"{BASE_URL}/api/superadmin/organizations/{TAXITUR_ORG_ID}/features",
            json={"features": {"taxitur_origen": True}},
            headers={
                "Authorization": f"Bearer {superadmin_token}",
                "Content-Type": "application/json"
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "features" in data, "Response should contain 'features'"
        assert data["features"].get("taxitur_origen") == True, "taxitur_origen should be True"
        assert "message" in data, "Response should contain success message"

    def test_superadmin_can_toggle_feature_off(self, superadmin_token):
        """Superadmin can toggle taxitur_origen to false (200)"""
        response = requests.put(
            f"{BASE_URL}/api/superadmin/organizations/{TAXITUR_ORG_ID}/features",
            json={"features": {"taxitur_origen": False}},
            headers={
                "Authorization": f"Bearer {superadmin_token}",
                "Content-Type": "application/json"
            }
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["features"].get("taxitur_origen") == False, "taxitur_origen should be False"

    def test_admin_gets_403_forbidden(self, admin_token):
        """Admin user cannot access superadmin feature flags endpoint (403)"""
        response = requests.put(
            f"{BASE_URL}/api/superadmin/organizations/{TAXITUR_ORG_ID}/features",
            json={"features": {"taxitur_origen": True}},
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            }
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"

    def test_no_token_gets_403(self):
        """Request without token returns 403 (FastAPI HTTPBearer convention)"""
        response = requests.put(
            f"{BASE_URL}/api/superadmin/organizations/{TAXITUR_ORG_ID}/features",
            json={"features": {"taxitur_origen": True}},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        assert "Not authenticated" in response.json().get("detail", "")


class TestFeatureFlagsValidation:
    """Test input validation for feature flags endpoint"""

    def test_invalid_feature_key_returns_400(self, superadmin_token):
        """Invalid feature key returns 400"""
        response = requests.put(
            f"{BASE_URL}/api/superadmin/organizations/{TAXITUR_ORG_ID}/features",
            json={"features": {"invalid_feature_key": True}},
            headers={
                "Authorization": f"Bearer {superadmin_token}",
                "Content-Type": "application/json"
            }
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        data = response.json()
        assert "detail" in data, "Response should contain error detail"
        assert "invalid_feature_key" in data["detail"].lower() or "no permitida" in data["detail"].lower(), \
            f"Error should mention invalid key: {data['detail']}"

    def test_non_boolean_value_returns_400(self, superadmin_token):
        """Non-boolean value returns 400"""
        # Test with string value
        response = requests.put(
            f"{BASE_URL}/api/superadmin/organizations/{TAXITUR_ORG_ID}/features",
            json={"features": {"taxitur_origen": "yes"}},
            headers={
                "Authorization": f"Bearer {superadmin_token}",
                "Content-Type": "application/json"
            }
        )
        assert response.status_code == 400, f"Expected 400 for string, got {response.status_code}: {response.text}"
        
        # Test with integer value
        response2 = requests.put(
            f"{BASE_URL}/api/superadmin/organizations/{TAXITUR_ORG_ID}/features",
            json={"features": {"taxitur_origen": 1}},
            headers={
                "Authorization": f"Bearer {superadmin_token}",
                "Content-Type": "application/json"
            }
        )
        assert response2.status_code == 400, f"Expected 400 for int, got {response2.status_code}: {response2.text}"

    def test_empty_features_object_returns_400(self, superadmin_token):
        """Empty features object returns 400"""
        response = requests.put(
            f"{BASE_URL}/api/superadmin/organizations/{TAXITUR_ORG_ID}/features",
            json={"features": {}},
            headers={
                "Authorization": f"Bearer {superadmin_token}",
                "Content-Type": "application/json"
            }
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"

    def test_missing_features_key_returns_400(self, superadmin_token):
        """Missing features key returns 400"""
        response = requests.put(
            f"{BASE_URL}/api/superadmin/organizations/{TAXITUR_ORG_ID}/features",
            json={"taxitur_origen": True},  # Wrong format - should be inside "features"
            headers={
                "Authorization": f"Bearer {superadmin_token}",
                "Content-Type": "application/json"
            }
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"


class TestFeatureFlagsMerge:
    """Test that feature flags merge without deleting existing keys"""

    def test_merge_preserves_existing_features(self, superadmin_token):
        """Sending one feature key doesn't delete others - merge behavior"""
        # First, set taxitur_origen to True
        response1 = requests.put(
            f"{BASE_URL}/api/superadmin/organizations/{TAXITUR_ORG_ID}/features",
            json={"features": {"taxitur_origen": True}},
            headers={
                "Authorization": f"Bearer {superadmin_token}",
                "Content-Type": "application/json"
            }
        )
        assert response1.status_code == 200, f"Setup failed: {response1.text}"
        
        # Get current org state
        response_get = requests.get(
            f"{BASE_URL}/api/organizations/{TAXITUR_ORG_ID}",
            headers={"Authorization": f"Bearer {superadmin_token}"}
        )
        assert response_get.status_code == 200, f"GET org failed: {response_get.text}"
        org_data = response_get.json()
        initial_features = org_data.get("features", {})
        
        # Verify taxitur_origen is set
        assert initial_features.get("taxitur_origen") == True, "taxitur_origen should be True initially"
        
        # Now toggle it to False - this should NOT delete the key entirely
        response2 = requests.put(
            f"{BASE_URL}/api/superadmin/organizations/{TAXITUR_ORG_ID}/features",
            json={"features": {"taxitur_origen": False}},
            headers={
                "Authorization": f"Bearer {superadmin_token}",
                "Content-Type": "application/json"
            }
        )
        assert response2.status_code == 200, f"Toggle off failed: {response2.text}"
        
        # Verify the key still exists with False value
        final_features = response2.json().get("features", {})
        assert "taxitur_origen" in final_features, "taxitur_origen key should still exist after toggle"
        assert final_features["taxitur_origen"] == False, "taxitur_origen should be False after toggle"


class TestFeatureFlagsOrgValidation:
    """Test organization validation for feature flags"""

    def test_invalid_org_id_returns_400(self, superadmin_token):
        """Invalid org_id format returns 400"""
        response = requests.put(
            f"{BASE_URL}/api/superadmin/organizations/invalid-id/features",
            json={"features": {"taxitur_origen": True}},
            headers={
                "Authorization": f"Bearer {superadmin_token}",
                "Content-Type": "application/json"
            }
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"

    def test_nonexistent_org_returns_404(self, superadmin_token):
        """Non-existent org_id returns 404"""
        # Valid ObjectId format but doesn't exist
        fake_org_id = "000000000000000000000000"
        response = requests.put(
            f"{BASE_URL}/api/superadmin/organizations/{fake_org_id}/features",
            json={"features": {"taxitur_origen": True}},
            headers={
                "Authorization": f"Bearer {superadmin_token}",
                "Content-Type": "application/json"
            }
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}: {response.text}"


class TestFeatureFlagsIntegration:
    """Test feature flags integration - how they affect other endpoints"""

    def test_feature_flag_visible_in_get_organizations(self, superadmin_token):
        """Feature flags should be visible in GET /organizations response"""
        # First set a feature flag
        requests.put(
            f"{BASE_URL}/api/superadmin/organizations/{TAXITUR_ORG_ID}/features",
            json={"features": {"taxitur_origen": True}},
            headers={
                "Authorization": f"Bearer {superadmin_token}",
                "Content-Type": "application/json"
            }
        )
        
        # Get organizations list
        response = requests.get(
            f"{BASE_URL}/api/organizations",
            headers={"Authorization": f"Bearer {superadmin_token}"}
        )
        assert response.status_code == 200, f"GET organizations failed: {response.text}"
        
        orgs = response.json()
        taxitur_org = next((o for o in orgs if o["id"] == TAXITUR_ORG_ID), None)
        assert taxitur_org is not None, f"Taxitur org not found in list"
        assert "features" in taxitur_org, "Org should have 'features' field"
        assert taxitur_org["features"].get("taxitur_origen") == True, "taxitur_origen should be visible"


class TestCleanup:
    """Cleanup: Re-enable taxitur_origen for Taxitur org"""

    def test_restore_taxitur_origen_enabled(self, superadmin_token):
        """Restore taxitur_origen to True for Taxitur org (expected production state)"""
        response = requests.put(
            f"{BASE_URL}/api/superadmin/organizations/{TAXITUR_ORG_ID}/features",
            json={"features": {"taxitur_origen": True}},
            headers={
                "Authorization": f"Bearer {superadmin_token}",
                "Content-Type": "application/json"
            }
        )
        assert response.status_code == 200, f"Restore failed: {response.text}"
        data = response.json()
        assert data["features"].get("taxitur_origen") == True, "taxitur_origen should be restored to True"
        print(f"\n✅ Restored taxitur_origen=True for Taxitur org ({TAXITUR_ORG_ID})")
