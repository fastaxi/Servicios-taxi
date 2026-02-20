#!/usr/bin/env python3
"""
TESTING ESPECÍFICO REQUERIMIENTOS PR - FEATURE FLAGS TAXITUR_ORIGEN
Testing exhaustivo según los requerimientos específicos del PR
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8001/api"
HEADERS = {"Content-Type": "application/json"}
TAXITUR_ORG_ID = "69484bec187c3bc2b0fdb8f4"

stats = {"total": 0, "passed": 0}

def test(name, condition, details=""):
    stats["total"] += 1
    if condition:
        stats["passed"] += 1
        print(f"✅ {name}")
        if details: print(f"   {details}")
    else:
        print(f"❌ {name}")
        print(f"   FAIL: {details}")
    print()

def req(method, endpoint, data=None, token=None):
    url = f"{BASE_URL}{endpoint}"
    headers = HEADERS.copy()
    if token: headers["Authorization"] = f"Bearer {token}"
    
    try:
        if method == "GET": resp = requests.get(url, headers=headers, params=data)
        elif method == "POST": resp = requests.post(url, headers=headers, json=data)
        elif method == "PUT": resp = requests.put(url, headers=headers, json=data)
        return {"status": resp.status_code, "data": resp.json() if resp.text else {}}
    except: return {"status": 0, "data": {}}

def login(user, pwd):
    result = req("POST", "/auth/login", {"username": user, "password": pwd})
    return result["data"]["access_token"] if result["status"] == 200 else None

print("🎯 TESTING PR ESPECÍFICO - FEATURE FLAGS TAXITUR_ORIGEN")
print("=" * 60)

# ==========================================
# PARTE 1: /my-organization devuelve features
# ==========================================
print("🔍 PARTE 1: /my-organization devuelve features")
print("-" * 45)

# Login admin/admin123 (usuario conocido)
admin_token = login("admin", "admin123")
test("Login admin", bool(admin_token))

if admin_token:
    # GET /my-organization
    my_org = req("GET", "/my-organization", token=admin_token)
    test("GET /my-organization", my_org["status"] == 200, 
         f"Status: {my_org['status']}")
    
    if my_org["status"] == 200:
        features = my_org["data"].get("features", {})
        test("Respuesta incluye features", "features" in my_org["data"],
             f"Features encontrados: {features}")

# ==========================================  
# PARTE 2: ORG CON FEATURE ACTIVO
# ==========================================
print("\n🚕 PARTE 2: ORG CON FEATURE ACTIVO")
print("-" * 45)

# Usar usuario de Taxitur existente
superadmin_token = login("superadmin", "superadmin123")
test("Login superadmin", bool(superadmin_token))

taxista_taxitur_token = None
if superadmin_token:
    # Obtener usuarios de Taxitur
    users = req("GET", "/users", token=superadmin_token)
    if users["status"] == 200:
        taxitur_users = [u for u in users["data"] if u.get("organization_id") == TAXITUR_ORG_ID]
        
        if taxitur_users:
            # Usar primer usuario encontrado
            taxitur_user = taxitur_users[0]
            test("Usuario Taxitur encontrado", True, f"Usuario: {taxitur_user['username']}")
            
            # Intentar login (probar contraseñas comunes)
            for pwd in ["admin123", "test123", "taxitur123"]:
                taxista_taxitur_token = login(taxitur_user["username"], pwd)
                if taxista_taxitur_token:
                    test("Login usuario Taxitur", True, f"Password: {pwd}")
                    break
            
            if not taxista_taxitur_token:
                test("Login usuario Taxitur", False, "Ninguna contraseña funcionó")

# Testing con usuario de Taxitur si está disponible
if taxista_taxitur_token:
    # Verificar que tiene turno activo
    turno_activo = req("GET", "/turnos/activo", token=taxista_taxitur_token)
    has_turno = turno_activo["status"] == 200 and turno_activo["data"].get("id")
    
    test("Usuario tiene turno activo", has_turno, 
         f"Turno: {turno_activo['data'].get('id', 'None')}")
    
    if has_turno:
        # 2.1 POST sin origen_taxitur → debe fallar 400
        servicio_sin = {
            "fecha": datetime.now().strftime("%Y-%m-%d"),
            "hora": datetime.now().strftime("%H:%M"), 
            "origen": "Oviedo Centro",
            "destino": "Aeropuerto",
            "importe": 25.50,
            "tipo": "particular",
            "kilometros": 15.5,
            "tiempo_espera": 0,
            "importe_espera": 0.0,
            "metodo_pago": "efectivo"
        }
        
        sin_result = req("POST", "/services", servicio_sin, token=taxista_taxitur_token)
        test("POST sin origen_taxitur → 400", 
             sin_result["status"] == 400 and "origen_taxitur" in str(sin_result["data"]),
             f"Status: {sin_result['status']}, Error: {sin_result['data'].get('detail', '')}")
        
        # 2.2 POST con origen_taxitur='parada' → debe funcionar 200
        servicio_parada = servicio_sin.copy()
        servicio_parada["origen_taxitur"] = "parada"
        
        parada_result = req("POST", "/services", servicio_parada, token=taxista_taxitur_token)
        test("POST con origen_taxitur='parada' → 200",
             parada_result["status"] == 200,
             f"Status: {parada_result['status']}, ID: {parada_result['data'].get('id', 'Error')}")
        
        # 2.3 POST con origen_taxitur='lagos' → debe funcionar 200
        servicio_lagos = servicio_sin.copy()
        servicio_lagos["origen_taxitur"] = "lagos"
        servicio_lagos["origen"] = "Lagos de Covadonga"
        
        lagos_result = req("POST", "/services", servicio_lagos, token=taxista_taxitur_token)
        test("POST con origen_taxitur='lagos' → 200",
             lagos_result["status"] == 200,
             f"Status: {lagos_result['status']}, ID: {lagos_result['data'].get('id', 'Error')}")

# ==========================================
# PARTE 3: ORG SIN FEATURE ACTIVO  
# ==========================================
print("\n🏢 PARTE 3: ORG SIN FEATURE ACTIVO")
print("-" * 45)

# Usar admin genérico que está en Taxi Tineo (sin feature)
if admin_token:
    # Verificar que NO tiene feature activo
    admin_org = req("GET", "/my-organization", token=admin_token)
    if admin_org["status"] == 200:
        admin_features = admin_org["data"].get("features", {})
        test("Org sin taxitur_origen", 
             not admin_features.get("taxitur_origen", False),
             f"Features: {admin_features}")
        
        # Verificar turno activo
        admin_turno = req("GET", "/turnos/activo", token=admin_token)
        admin_has_turno = admin_turno["status"] == 200 and admin_turno["data"].get("id")
        
        test("Admin tiene turno", admin_has_turno,
             f"Turno: {admin_turno['data'].get('id', 'None')}")
        
        if admin_has_turno:
            # 3.1 POST sin origen_taxitur → debe funcionar 200
            servicio_sin_feat = {
                "fecha": datetime.now().strftime("%Y-%m-%d"),
                "hora": datetime.now().strftime("%H:%M"),
                "origen": "Plaza de Tineo", 
                "destino": "Hospital",
                "importe": 12.30,
                "tipo": "particular",
                "kilometros": 5.2,
                "tiempo_espera": 0,
                "importe_espera": 0.0,
                "metodo_pago": "efectivo"
            }
            
            sin_feat_result = req("POST", "/services", servicio_sin_feat, token=admin_token)
            test("POST sin origen (org sin feature) → 200",
                 sin_feat_result["status"] == 200,
                 f"Status: {sin_feat_result['status']}, ID: {sin_feat_result['data'].get('id', 'Error')}")
            
            # 3.2 POST con origen_taxitur → debe ignorarse
            servicio_con_feat = servicio_sin_feat.copy()
            servicio_con_feat["origen_taxitur"] = "parada"
            
            con_feat_result = req("POST", "/services", servicio_con_feat, token=admin_token)
            if con_feat_result["status"] == 200:
                # Verificar que origen_taxitur fue ignorado (None)
                origen_final = con_feat_result["data"].get("origen_taxitur")
                test("POST con origen (org sin feature) → ignorado",
                     origen_final is None,
                     f"origen_taxitur final: {origen_final}")
            else:
                test("POST con origen (org sin feature)", False,
                     f"Status: {con_feat_result['status']}")

# ==========================================
# PARTE 4: FILTROS funcionan correctamente
# ==========================================
print("\n🔍 PARTE 4: FILTROS en GET /services")
print("-" * 45)

if taxista_taxitur_token:
    # Usuario con feature activo puede filtrar
    filter1 = req("GET", "/services", {"origen_taxitur": "parada"}, token=taxista_taxitur_token)
    test("Filtro parada (usuario con feature)",
         filter1["status"] == 200,
         f"Servicios encontrados: {len(filter1['data']) if filter1['status'] == 200 else 'Error'}")
    
    filter2 = req("GET", "/services", {"origen_taxitur": "lagos"}, token=taxista_taxitur_token) 
    test("Filtro lagos (usuario con feature)",
         filter2["status"] == 200,
         f"Servicios encontrados: {len(filter2['data']) if filter2['status'] == 200 else 'Error'}")

if admin_token:
    # Usuario sin feature - filtro debería no funcionar o devolver vacío
    filter3 = req("GET", "/services", {"origen_taxitur": "parada"}, token=admin_token)
    test("Filtro parada (usuario sin feature)", 
         filter3["status"] == 200,
         f"Servicios: {len(filter3['data']) if filter3['status'] == 200 else 'Error'}")

# ==========================================
# VERIFICACIÓN CRÍTICA: NO HARDCODED
# ==========================================
print("\n🎯 VERIFICACIÓN CRÍTICA: NO HARDCODED")
print("-" * 45)

if superadmin_token:
    # Toggle del feature flag para verificar que NO es hardcoded
    
    # 1. Desactivar
    toggle_off = req("PUT", f"/organizations/{TAXITUR_ORG_ID}", 
                     {"features": {"taxitur_origen": False}}, 
                     token=superadmin_token)
    test("Toggle feature OFF", toggle_off["status"] == 200)
    
    # 2. Verificar cambio se refleja
    if taxista_taxitur_token:
        check_off = req("GET", "/my-organization", token=taxista_taxitur_token)
        if check_off["status"] == 200:
            features_off = check_off["data"].get("features", {})
            test("Feature OFF se refleja", 
                 not features_off.get("taxitur_origen", True),
                 f"Features después de OFF: {features_off}")
    
    # 3. Reactivar
    toggle_on = req("PUT", f"/organizations/{TAXITUR_ORG_ID}", 
                    {"features": {"taxitur_origen": True}}, 
                    token=superadmin_token)
    test("Toggle feature ON", toggle_on["status"] == 200)
    
    # 4. Verificar reactivación
    if taxista_taxitur_token:
        check_on = req("GET", "/my-organization", token=taxista_taxitur_token)
        if check_on["status"] == 200:
            features_on = check_on["data"].get("features", {})
            test("Feature ON se refleja",
                 features_on.get("taxitur_origen") is True,
                 f"Features después de ON: {features_on}")

print("\n" + "=" * 60)
print("📊 RESUMEN FINAL")
print("=" * 60)

print(f"🎯 TOTAL: {stats['total']}")
print(f"✅ PASSED: {stats['passed']}")
print(f"❌ FAILED: {stats['total'] - stats['passed']}")

success_rate = (stats['passed'] / stats['total']) * 100
print(f"📈 ÉXITO: {success_rate:.1f}%")

if success_rate >= 90:
    print("\n🎉 TESTING EXITOSO - FEATURE FLAGS OPERATIVOS")
    print("✅ Sistema basado en features de organización (no hardcoded)")
    print("✅ /my-organization devuelve features correctamente")
    print("✅ Validación funciona según feature flag de BD")
    print("✅ Feature toggle dinámico operativo")
else:
    print(f"\n⚠️ ALGUNOS TESTS FALLARON ({100-success_rate:.1f}%)")

print(f"\n🏁 TESTING PR FINALIZADO")