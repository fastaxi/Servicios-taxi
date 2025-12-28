#!/usr/bin/env python3
"""
Debugging Backend Test - Focused on specific issues
"""

import requests
import json
from datetime import datetime

BASE_URL = "https://taxiflow-18.preview.emergentagent.com/api"
TAXITUR_ORG_ID = "69484bec187c3bc2b0fdb8f4"

def login(username, password):
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "username": username,
        "password": password
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def make_request(method, endpoint, token=None, **kwargs):
    headers = kwargs.get('headers', {})
    if token:
        headers['Authorization'] = f'Bearer {token}'
    kwargs['headers'] = headers
    
    url = f"{BASE_URL}{endpoint}"
    return getattr(requests, method.lower())(url, **kwargs)

def debug_admin_organization():
    """Debug admin user organization assignment"""
    print("🔍 DEBUGGING ADMIN ORGANIZATION ASSIGNMENT")
    
    # Login as admin
    admin_token = login("admin", "admin123")
    if not admin_token:
        print("❌ Failed to login as admin")
        return
    
    # Check admin user info
    response = make_request("GET", "/auth/me", admin_token)
    if response.status_code == 200:
        admin_info = response.json()
        print(f"✅ Admin info: {json.dumps(admin_info, indent=2)}")
        
        # Check if admin has organization
        if not admin_info.get("organization_id"):
            print("⚠️ Admin has no organization_id - this explains 403 errors on exports")
            
            # Try to assign admin to an organization
            superadmin_token = login("superadmin", "superadmin123")
            if superadmin_token:
                # Get organizations
                orgs_response = make_request("GET", "/organizations", superadmin_token)
                if orgs_response.status_code == 200:
                    orgs = orgs_response.json()
                    if orgs:
                        # Assign admin to first organization
                        admin_id = admin_info["id"]
                        org_id = orgs[0]["id"]
                        assign_response = make_request("PUT", f"/users/{admin_id}/assign-organization/{org_id}", superadmin_token)
                        print(f"📝 Assign admin to org result: {assign_response.status_code} - {assign_response.text}")
        else:
            print(f"✅ Admin has organization_id: {admin_info.get('organization_id')}")
    else:
        print(f"❌ Failed to get admin info: {response.status_code} - {response.text}")

def debug_taxitur_validation():
    """Debug Taxitur organization validation"""
    print("\n🔍 DEBUGGING TAXITUR VALIDATION")
    
    # Login as superadmin to check organizations
    superadmin_token = login("superadmin", "superadmin123")
    if not superadmin_token:
        print("❌ Failed to login as superadmin")
        return
    
    # Get all organizations
    response = make_request("GET", "/organizations", superadmin_token)
    if response.status_code == 200:
        orgs = response.json()
        print(f"📋 Organizations found: {len(orgs)}")
        for org in orgs:
            print(f"  - {org['id']}: {org['nombre']} (slug: {org.get('slug', 'N/A')})")
            if org['id'] == TAXITUR_ORG_ID:
                print(f"    ✅ This is the TAXITUR organization!")
    
    # Check if we have a taxista in Taxitur org
    taxistas_response = make_request("GET", "/superadmin/taxistas", superadmin_token)
    if taxistas_response.status_code == 200:
        taxistas = taxistas_response.json()
        taxitur_taxistas = [t for t in taxistas if t.get("organization_id") == TAXITUR_ORG_ID]
        print(f"🚕 Taxistas in Taxitur org: {len(taxitur_taxistas)}")
        for t in taxitur_taxistas:
            print(f"  - {t['username']}: {t['nombre']}")

def debug_service_creation():
    """Debug service creation with different scenarios"""
    print("\n🔍 DEBUGGING SERVICE CREATION")
    
    # Login as taxista
    taxista_token = login("taxista_taxitur_test", "test123")
    if not taxista_token:
        print("❌ Failed to login as taxista_taxitur_test")
        return
    
    # Check taxista info
    response = make_request("GET", "/auth/me", taxista_token)
    if response.status_code == 200:
        taxista_info = response.json()
        print(f"✅ Taxista info: {json.dumps(taxista_info, indent=2)}")
        
        # Check if taxista has active turno
        turno_response = make_request("GET", "/turnos/activo", taxista_token)
        print(f"🔄 Active turno check: {turno_response.status_code}")
        if turno_response.status_code == 200:
            turno = turno_response.json()
            if turno:
                print(f"✅ Active turno: {turno['id']}")
            else:
                print("❌ No active turno found")
            
            # Try to create service without origen_taxitur
            service_data = {
                "fecha": datetime.now().strftime("%d/%m/%Y"),
                "hora": "10:00",
                "origen": "Plaza Mayor",
                "destino": "Aeropuerto",
                "importe": 25.50,
                "importe_espera": 0,
                "kilometros": 15.2,
                "tipo": "particular",
                "metodo_pago": "efectivo"
            }
            
            response = make_request("POST", "/services", taxista_token, json=service_data)
            print(f"🚫 Service without origen_taxitur: {response.status_code} - {response.text}")
            
            # Try with origen_taxitur
            service_data["origen_taxitur"] = "parada"
            response = make_request("POST", "/services", taxista_token, json=service_data)
            print(f"✅ Service with origen_taxitur='parada': {response.status_code} - {response.text}")
            
        else:
            print(f"❌ No active turno: {turno_response.text}")
    else:
        print(f"❌ Failed to get taxista info: {response.status_code} - {response.text}")

def main():
    print("🔍 DEBUGGING BACKEND ISSUES")
    print("="*50)
    
    debug_admin_organization()
    debug_taxitur_validation()
    debug_service_creation()

if __name__ == "__main__":
    main()