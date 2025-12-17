#!/usr/bin/env python3
"""
Simple Multi-tenant Test - Key Functionality Verification
"""

import requests
import json

BASE_URL = "https://taxi-platform-47.preview.emergentagent.com/api"

def test_login(username, password):
    """Test login and return token"""
    try:
        response = requests.post(f"{BASE_URL}/auth/login", 
                               json={"username": username, "password": password},
                               timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("access_token"), data.get("user")
        else:
            print(f"Login failed for {username}: {response.status_code}")
            return None, None
    except Exception as e:
        print(f"Login error for {username}: {e}")
        return None, None

def test_auth_me(token):
    """Test /auth/me endpoint"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Auth/me failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"Auth/me error: {e}")
        return None

def test_organizations(token):
    """Test organizations endpoint"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/organizations", headers=headers, timeout=10)
        return response.status_code, response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"Organizations error: {e}")
        return None, None

def test_my_organization(token):
    """Test my-organization endpoint"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/my-organization", headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"My-organization failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"My-organization error: {e}")
        return None

def main():
    print("🚕 TaxiFast Multi-tenant - Simple Test")
    print("=" * 50)
    
    # Test 1: Authentication
    print("\n1. TESTING AUTHENTICATION:")
    
    # Superadmin
    token_super, user_super = test_login("superadmin", "superadmin123")
    print(f"✅ Superadmin login: {'SUCCESS' if token_super else 'FAILED'}")
    if user_super:
        print(f"   Role: {user_super.get('role')}")
    
    # Admin Tineo
    token_tineo, user_tineo = test_login("admin_tineo", "tineo123")
    print(f"✅ Admin Tineo login: {'SUCCESS' if token_tineo else 'FAILED'}")
    if user_tineo:
        print(f"   Org: {user_tineo.get('organization_nombre')}")
    
    # Admin Madrid
    token_madrid, user_madrid = test_login("admin_madrid", "madrid123")
    print(f"✅ Admin Madrid login: {'SUCCESS' if token_madrid else 'FAILED'}")
    if user_madrid:
        print(f"   Org: {user_madrid.get('organization_nombre')}")
    
    # Taxista Tineo
    token_tax_tineo, user_tax_tineo = test_login("taxista_tineo1", "tax123")
    print(f"✅ Taxista Tineo login: {'SUCCESS' if token_tax_tineo else 'FAILED'}")
    if user_tax_tineo:
        print(f"   Org: {user_tax_tineo.get('organization_nombre')}")
    
    # Taxista Madrid
    token_tax_madrid, user_tax_madrid = test_login("taxista_madrid1", "tax123")
    print(f"✅ Taxista Madrid login: {'SUCCESS' if token_tax_madrid else 'FAILED'}")
    if user_tax_madrid:
        print(f"   Org: {user_tax_madrid.get('organization_nombre')}")
    
    # Legacy admin
    token_legacy, user_legacy = test_login("admin", "admin123")
    print(f"✅ Legacy admin login: {'SUCCESS' if token_legacy else 'FAILED'}")
    if user_legacy:
        print(f"   Role: {user_legacy.get('role')}")
    
    # Test 2: Organization info in /auth/me
    print("\n2. TESTING /AUTH/ME ORGANIZATION INFO:")
    if token_tineo:
        me_data = test_auth_me(token_tineo)
        if me_data:
            print(f"✅ Admin Tineo /auth/me: org_id={me_data.get('organization_id')}, org_name={me_data.get('organization_nombre')}")
    
    if token_madrid:
        me_data = test_auth_me(token_madrid)
        if me_data:
            print(f"✅ Admin Madrid /auth/me: org_id={me_data.get('organization_id')}, org_name={me_data.get('organization_nombre')}")
    
    # Test 3: Organizations endpoint (superadmin only)
    print("\n3. TESTING ORGANIZATIONS ENDPOINT:")
    if token_super:
        status, orgs = test_organizations(token_super)
        print(f"✅ Superadmin /organizations: status={status}, count={len(orgs) if orgs else 0}")
    
    if token_tineo:
        status, orgs = test_organizations(token_tineo)
        print(f"✅ Admin Tineo /organizations: status={status} (should be 403)")
    
    # Test 4: MY-ORGANIZATION endpoint
    print("\n4. TESTING MY-ORGANIZATION ENDPOINT:")
    if token_tax_tineo:
        org_data = test_my_organization(token_tax_tineo)
        if org_data:
            print(f"✅ Taxista Tineo my-org: {org_data.get('nombre')} - {org_data.get('color_primario')}/{org_data.get('color_secundario')}")
    
    if token_tax_madrid:
        org_data = test_my_organization(token_tax_madrid)
        if org_data:
            print(f"✅ Taxista Madrid my-org: {org_data.get('nombre')} - {org_data.get('color_primario')}/{org_data.get('color_secundario')}")
    
    print("\n🎯 SIMPLE TEST COMPLETED")

if __name__ == "__main__":
    main()