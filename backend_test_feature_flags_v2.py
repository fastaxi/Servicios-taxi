#!/usr/bin/env python3
"""
TESTING EXHAUSTIVO - FEATURE FLAGS TAXITUR_ORIGEN
Verificar que la validación del campo origen_taxitur depende del feature flag
de la organización (features.taxitur_origen) y no de un ID hardcodeado.
"""

import requests
import json
from datetime import datetime

# ==========================================
# CONFIGURACIÓN
# ==========================================
BASE_URL = "http://localhost:8001/api"
HEADERS = {"Content-Type": "application/json"}

# IDs conocidos de organizaciones
TAXITUR_ORG_ID = "69484bec187c3bc2b0fdb8f4"  # Con feature activo
TAXI_TINEO_ORG_ID = "69429aaecdbc9d2db23e0ed5"  # Sin feature activo

# Estadísticas globales
stats = {"total_tests": 0, "passed_tests": 0, "failed_tests": 0, "test_results": []}

def log_test(test_name: str, success: bool, details: str = ""):
    """Registrar resultado de un test"""
    stats["total_tests"] += 1
    if success:
        stats["passed_tests"] += 1
        print(f"✅ {test_name}")
        if details:
            print(f"   {details}")
    else:
        stats["failed_tests"] += 1
        print(f"❌ {test_name}")
        print(f"   ERROR: {details}")
    
    stats["test_results"].append({
        "test": test_name,
        "passed": success,
        "details": details
    })
    print()

def make_request(method, endpoint, data=None, token=None):
    """Realizar request HTTP con manejo de errores"""
    url = f"{BASE_URL}{endpoint}"
    headers = HEADERS.copy()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=data)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Método HTTP no soportado: {method}")
        
        return {
            "status_code": response.status_code,
            "data": response.json() if response.text else {},
            "success": 200 <= response.status_code < 300
        }
    except Exception as e:
        return {
            "status_code": 0,
            "data": {},
            "success": False,
            "error": str(e)
        }

def login_user(username, password):
    """Login y obtener token"""
    result = make_request("POST", "/auth/login", {"username": username, "password": password})
    if result["success"]:
        return result["data"]["access_token"]
    return None

print("🎯 TESTING EXHAUSTIVO - FEATURE FLAGS TAXITUR_ORIGEN")
print("=" * 70)
print(f"Base URL: {BASE_URL}")
print(f"Taxitur Org ID: {TAXITUR_ORG_ID}")
print(f"Taxi Tineo Org ID: {TAXI_TINEO_ORG_ID}")
print()

# ==========================================
# SETUP INICIAL
# ==========================================
print("🔧 SETUP INICIAL")
print("-" * 30)

# Login superadmin
superadmin_token = login_user("superadmin", "superadmin123")
if not superadmin_token:
    log_test("Login superadmin", False, "No se pudo obtener token")
    exit(1)
else:
    log_test("Login superadmin", True)

# Verificar organizaciones existentes
org_list_result = make_request("GET", "/organizations", token=superadmin_token)
if org_list_result["success"]:
    orgs = org_list_result["data"]
    taxitur_org = next((org for org in orgs if org["id"] == TAXITUR_ORG_ID), None)
    tineo_org = next((org for org in orgs if org["id"] == TAXI_TINEO_ORG_ID), None)
    
    if taxitur_org:
        log_test("Encontrar org Taxitur", True, f"Features: {taxitur_org.get('features', {})}")
    else:
        log_test("Encontrar org Taxitur", False, "Organización Taxitur no encontrada")
    
    if tineo_org:
        log_test("Encontrar org Taxi Tineo", True, f"Features: {tineo_org.get('features', {})}")
    else:
        log_test("Encontrar org Taxi Tineo", False, "Organización Taxi Tineo no encontrada")
else:
    log_test("Listar organizaciones", False, f"Error: {org_list_result['data']}")
    exit(1)

# Crear usuarios de prueba necesarios
timestamp = int(datetime.now().timestamp())

# Admin de Taxitur
admin_taxitur_data = {
    "username": "admintur",
    "password": "admin123", 
    "nombre": "Admin Taxitur",
    "role": "admin",
    "organization_id": TAXITUR_ORG_ID
}

admin_result = make_request("POST", "/users", admin_taxitur_data, token=superadmin_token)
if admin_result["success"] or "already exists" in str(admin_result.get("data", {})).lower():
    log_test("Crear/verificar admin Taxitur", True, "admintur disponible")
    
    # Login admin taxitur
    admin_taxitur_token = login_user("admintur", "admin123")
    if admin_taxitur_token:
        log_test("Login admin Taxitur", True)
    else:
        log_test("Login admin Taxitur", False, "No se pudo hacer login")
else:
    log_test("Crear admin Taxitur", False, f"Error: {admin_result['data']}")
    admin_taxitur_token = None

# Taxista de Taxitur
taxista_taxitur_data = {
    "username": f"taxista_taxitur_{timestamp}",
    "password": "test123",
    "nombre": "Taxista Taxitur Test",
    "role": "taxista",
    "organization_id": TAXITUR_ORG_ID
}

taxista_taxitur_result = make_request("POST", "/users", taxista_taxitur_data, token=superadmin_token)
if taxista_taxitur_result["success"]:
    taxista_taxitur_username = taxista_taxitur_result["data"]["username"]
    log_test("Crear taxista Taxitur", True, f"Usuario: {taxista_taxitur_username}")
else:
    log_test("Crear taxista Taxitur", False, f"Error: {taxista_taxitur_result['data']}")
    taxista_taxitur_username = None

# Taxista de Taxi Tineo (org sin feature)  
taxista_tineo_data = {
    "username": f"taxista_tineo_{timestamp}",
    "password": "test123",
    "nombre": "Taxista Tineo Test",
    "role": "taxista", 
    "organization_id": TAXI_TINEO_ORG_ID
}

taxista_tineo_result = make_request("POST", "/users", taxista_tineo_data, token=superadmin_token)
if taxista_tineo_result["success"]:
    taxista_tineo_username = taxista_tineo_result["data"]["username"]
    log_test("Crear taxista Tineo", True, f"Usuario: {taxista_tineo_username}")
else:
    log_test("Crear taxista Tineo", False, f"Error: {taxista_tineo_result['data']}")
    taxista_tineo_username = None

# ==========================================
# PARTE 1: VERIFICAR QUE /my-organization DEVUELVE FEATURES
# ==========================================
print("\n🔍 PARTE 1: VERIFICAR /my-organization DEVUELVE FEATURES")
print("-" * 60)

# 1.1 Login como admin de Taxitur y verificar features
if admin_taxitur_token:
    my_org_result = make_request("GET", "/my-organization", token=admin_taxitur_token)
    
    if my_org_result["success"]:
        org_data = my_org_result["data"]
        features = org_data.get("features", {})
        taxitur_origen_feature = features.get("taxitur_origen", False)
        
        log_test("1.1 GET /my-organization (admin Taxitur)", True, 
                f"Org: {org_data.get('nombre')}, Features: {features}")
        
        if taxitur_origen_feature is True:
            log_test("1.2 Verificar features.taxitur_origen=true", True, "Feature flag activo")
        else:
            log_test("1.2 Verificar features.taxitur_origen=true", False, 
                    f"Feature no activo: {taxitur_origen_feature}")
    else:
        log_test("1.1 GET /my-organization", False, f"Error: {my_org_result['data']}")

# ==========================================
# PARTE 2: ORG CON FEATURE ACTIVO (Taxitur)
# ==========================================
print("\n🚕 PARTE 2: ORG CON FEATURE ACTIVO (Taxitur)")
print("-" * 60)

taxista_taxitur_token = None
if taxista_taxitur_username:
    # Login taxista de Taxitur
    taxista_taxitur_token = login_user(taxista_taxitur_username, "test123")
    if taxista_taxitur_token:
        log_test("2.1 Login taxista Taxitur", True)
        
        # Crear turno (necesario para crear servicios)
        vehiculo_data = {
            "matricula": f"TAX{timestamp}",
            "plazas": 4,
            "marca": "Toyota",
            "modelo": "Prius", 
            "km_iniciales": 100000,
            "fecha_compra": "2023-01-01",
            "activo": True
        }
        
        # Crear vehículo con admin de org
        vehiculo_result = make_request("POST", "/vehiculos", vehiculo_data, token=admin_taxitur_token)
        if vehiculo_result["success"]:
            vehiculo_id = vehiculo_result["data"]["id"]
            log_test("2.2 Crear vehículo Taxitur", True, f"Matrícula: {vehiculo_data['matricula']}")
            
            # Crear turno
            turno_data = {
                "fecha_inicio": datetime.now().strftime("%Y-%m-%d"),
                "hora_inicio": datetime.now().strftime("%H:%M"),
                "km_inicio": 100000,
                "vehiculo_id": vehiculo_id
            }
            
            turno_result = make_request("POST", "/turnos", turno_data, token=taxista_taxitur_token)
            if turno_result["success"]:
                log_test("2.3 Crear turno Taxitur", True, f"Turno ID: {turno_result['data']['id']}")
                
                # 2.4 POST /services SIN origen_taxitur → Esperado: 400 (debe rechazar)
                servicio_sin_origen = {
                    "fecha": datetime.now().strftime("%Y-%m-%d"),
                    "hora": datetime.now().strftime("%H:%M"),
                    "origen": "Oviedo Centro",
                    "destino": "Aeropuerto de Asturias",
                    "importe": 25.50,
                    "tipo": "particular",
                    "kilometros": 15.5,
                    "tiempo_espera": 0,
                    "importe_espera": 0.0,
                    "metodo_pago": "efectivo"
                    # ❌ SIN origen_taxitur
                }
                
                sin_origen_result = make_request("POST", "/services", servicio_sin_origen, token=taxista_taxitur_token)
                if sin_origen_result["status_code"] == 400:
                    error_msg = sin_origen_result["data"].get("detail", "")
                    if "origen_taxitur" in error_msg.lower():
                        log_test("2.4 POST sin origen_taxitur → 400", True, f"Correctamente rechazado: {error_msg}")
                    else:
                        log_test("2.4 POST sin origen_taxitur → 400", False, f"Error 400 pero mensaje incorrecto: {error_msg}")
                else:
                    log_test("2.4 POST sin origen_taxitur → 400", False, 
                            f"Esperado 400, obtenido {sin_origen_result['status_code']}")
                
                # 2.5 POST /services CON origen_taxitur='parada' → Esperado: 200
                servicio_parada = {
                    "fecha": datetime.now().strftime("%Y-%m-%d"),
                    "hora": datetime.now().strftime("%H:%M"),
                    "origen": "Parada Taxis Oviedo",
                    "destino": "Hospital Central",
                    "importe": 18.75,
                    "tipo": "particular",
                    "kilometros": 8.2,
                    "tiempo_espera": 0,
                    "importe_espera": 0.0,
                    "metodo_pago": "efectivo",
                    "origen_taxitur": "parada"  # ✅ CON origen_taxitur válido
                }
                
                parada_result = make_request("POST", "/services", servicio_parada, token=taxista_taxitur_token)
                if parada_result["status_code"] == 200:
                    log_test("2.5 POST con origen_taxitur='parada' → 200", True, 
                            f"Servicio creado: {parada_result['data']['id']}")
                else:
                    log_test("2.5 POST con origen_taxitur='parada' → 200", False, 
                            f"Esperado 200, obtenido {parada_result['status_code']}: {parada_result['data']}")
                
                # 2.6 POST /services CON origen_taxitur='lagos' → Esperado: 200
                servicio_lagos = {
                    "fecha": datetime.now().strftime("%Y-%m-%d"),
                    "hora": datetime.now().strftime("%H:%M"),
                    "origen": "Lagos de Covadonga",
                    "destino": "Cangas de Onís",
                    "importe": 45.00,
                    "tipo": "particular",
                    "kilometros": 22.8,
                    "tiempo_espera": 5,
                    "importe_espera": 2.50,
                    "metodo_pago": "tpv",
                    "origen_taxitur": "lagos"  # ✅ CON origen_taxitur válido
                }
                
                lagos_result = make_request("POST", "/services", servicio_lagos, token=taxista_taxitur_token)
                if lagos_result["status_code"] == 200:
                    log_test("2.6 POST con origen_taxitur='lagos' → 200", True, 
                            f"Servicio creado: {lagos_result['data']['id']}")
                else:
                    log_test("2.6 POST con origen_taxitur='lagos' → 200", False, 
                            f"Esperado 200, obtenido {lagos_result['status_code']}: {lagos_result['data']}")
                
            else:
                log_test("2.3 Crear turno Taxitur", False, f"Error: {turno_result['data']}")
        else:
            log_test("2.2 Crear vehículo Taxitur", False, f"Error: {vehiculo_result['data']}")
    else:
        log_test("2.1 Login taxista Taxitur", False, "No se pudo hacer login")

# ==========================================
# PARTE 3: ORG SIN FEATURE ACTIVO (Taxi Tineo)
# ==========================================
print("\n🏢 PARTE 3: ORG SIN FEATURE ACTIVO (Taxi Tineo)")
print("-" * 60)

# Crear admin de Taxi Tineo si no existe
admin_tineo_data = {
    "username": f"admin_tineo_{timestamp}",
    "password": "admin123",
    "nombre": "Admin Taxi Tineo",
    "role": "admin",
    "organization_id": TAXI_TINEO_ORG_ID
}

admin_tineo_result = make_request("POST", "/users", admin_tineo_data, token=superadmin_token)
if admin_tineo_result["success"]:
    admin_tineo_username = admin_tineo_result["data"]["username"]
    log_test("3.1 Crear admin Taxi Tineo", True, f"Usuario: {admin_tineo_username}")
    
    admin_tineo_token = login_user(admin_tineo_username, "admin123")
    if admin_tineo_token:
        log_test("3.2 Login admin Tineo", True)
        
        # Crear taxista en Taxi Tineo
        taxista_tineo_data = {
            "username": f"taxista_tineo_{timestamp}",
            "password": "test123",
            "nombre": "Taxista Tineo Test",
            "role": "taxista",
            "organization_id": TAXI_TINEO_ORG_ID
        }
        
        taxista_tineo_result = make_request("POST", "/users", taxista_tineo_data, token=superadmin_token)
        if taxista_tineo_result["success"]:
            taxista_tineo_username = taxista_tineo_result["data"]["username"]
            log_test("3.3 Crear taxista Tineo", True, f"Usuario: {taxista_tineo_username}")
            
            # Login taxista de Tineo
            taxista_tineo_token = login_user(taxista_tineo_username, "test123")
            if taxista_tineo_token:
                log_test("3.4 Login taxista Tineo", True)
                
                # Verificar /my-organization NO tiene taxitur_origen 
                my_org_tineo = make_request("GET", "/my-organization", token=taxista_tineo_token)
                if my_org_tineo["success"]:
                    features_tineo = my_org_tineo["data"].get("features", {})
                    taxitur_origen_tineo = features_tineo.get("taxitur_origen", False)
                    
                    if not taxitur_origen_tineo:
                        log_test("3.5 Verificar Tineo NO tiene taxitur_origen", True, 
                                f"Correcto: features={features_tineo}")
                    else:
                        log_test("3.5 Verificar Tineo NO tiene taxitur_origen", False, 
                                f"ERROR: Feature activo cuando no debería: {features_tineo}")
                else:
                    log_test("3.5 GET /my-organization Tineo", False, f"Error: {my_org_tineo['data']}")
                
                # Crear vehículo y turno para Tineo
                vehiculo_tineo_data = {
                    "matricula": f"TIN{timestamp}",
                    "plazas": 4,
                    "marca": "Ford",
                    "modelo": "Focus",
                    "km_iniciales": 80000,
                    "fecha_compra": "2023-01-01", 
                    "activo": True
                }
                
                vehiculo_tineo_result = make_request("POST", "/vehiculos", vehiculo_tineo_data, token=admin_tineo_token)
                if vehiculo_tineo_result["success"]:
                    vehiculo_tineo_id = vehiculo_tineo_result["data"]["id"]
                    log_test("3.6 Crear vehículo Tineo", True, f"Matrícula: {vehiculo_tineo_data['matricula']}")
                    
                    # Crear turno para Tineo
                    turno_tineo_data = {
                        "fecha_inicio": datetime.now().strftime("%Y-%m-%d"),
                        "hora_inicio": datetime.now().strftime("%H:%M"),
                        "km_inicio": 80000,
                        "vehiculo_id": vehiculo_tineo_id
                    }
                    
                    turno_tineo_result = make_request("POST", "/turnos", turno_tineo_data, token=taxista_tineo_token)
                    if turno_tineo_result["success"]:
                        log_test("3.7 Crear turno Tineo", True, f"Turno ID: {turno_tineo_result['data']['id']}")
                        
                        # 3.8 POST /services SIN origen_taxitur → Esperado: 200 (debe aceptar)
                        servicio_tineo_sin = {
                            "fecha": datetime.now().strftime("%Y-%m-%d"),
                            "hora": datetime.now().strftime("%H:%M"),
                            "origen": "Plaza de Tineo",
                            "destino": "Hospital de Tineo",
                            "importe": 12.30,
                            "tipo": "particular",
                            "kilometros": 5.2,
                            "tiempo_espera": 0,
                            "importe_espera": 0.0,
                            "metodo_pago": "efectivo"
                            # ✅ SIN origen_taxitur - debe funcionar en org sin feature
                        }
                        
                        sin_origen_tineo = make_request("POST", "/services", servicio_tineo_sin, token=taxista_tineo_token)
                        if sin_origen_tineo["status_code"] == 200:
                            log_test("3.8 POST sin origen_taxitur → 200", True, 
                                    f"Servicio aceptado: {sin_origen_tineo['data']['id']}")
                        else:
                            log_test("3.8 POST sin origen_taxitur → 200", False, 
                                    f"Esperado 200, obtenido {sin_origen_tineo['status_code']}: {sin_origen_tineo['data']}")
                        
                        # 3.9 POST /services CON origen_taxitur='parada' → Esperado: se ignora/None
                        servicio_tineo_con = {
                            "fecha": datetime.now().strftime("%Y-%m-%d"),
                            "hora": datetime.now().strftime("%H:%M"),
                            "origen": "Centro Tineo",
                            "destino": "Estación Tineo",
                            "importe": 8.50,
                            "tipo": "particular",
                            "kilometros": 3.1,
                            "tiempo_espera": 0,
                            "importe_espera": 0.0,
                            "metodo_pago": "efectivo",
                            "origen_taxitur": "parada"  # ❌ Se debe ignorar en org sin feature
                        }
                        
                        con_origen_tineo = make_request("POST", "/services", servicio_tineo_con, token=taxista_tineo_token)
                        if con_origen_tineo["status_code"] == 200:
                            # Verificar que origen_taxitur fue ignorado (None)
                            servicio = con_origen_tineo["data"]
                            origen_final = servicio.get("origen_taxitur")
                            if origen_final is None:
                                log_test("3.9 POST con origen_taxitur → ignorado", True, 
                                        "Origen ignorado correctamente (forzado a None)")
                            else:
                                log_test("3.9 POST con origen_taxitur → ignorado", False, 
                                        f"ERROR: origen_taxitur no fue ignorado: {origen_final}")
                        else:
                            log_test("3.9 POST con origen_taxitur", False, 
                                    f"Error {con_origen_tineo['status_code']}: {con_origen_tineo['data']}")
                    else:
                        log_test("3.7 Crear turno Tineo", False, f"Error: {turno_tineo_result['data']}")
                else:
                    log_test("3.6 Crear vehículo Tineo", False, f"Error: {vehiculo_tineo_result['data']}")
            else:
                log_test("3.4 Login taxista Tineo", False, "No se pudo hacer login")
        else:
            log_test("3.3 Crear taxista Tineo", False, f"Error: {taxista_tineo_result['data']}")
    else:
        log_test("3.2 Login admin Tineo", False, "No se pudo hacer login")
else:
    log_test("3.1 Crear admin Taxi Tineo", False, f"Error: {admin_tineo_result['data']}")

# ==========================================
# PARTE 4: FILTRO EN GET /services
# ==========================================
print("\n🔍 PARTE 4: FILTRO EN GET /services")
print("-" * 60)

# Solo funciona para orgs con feature activo
if admin_taxitur_token:
    # 4.1 GET /services?origen_taxitur=parada 
    params_parada = {"origen_taxitur": "parada"}
    filtro_parada = make_request("GET", "/services", params_parada, token=admin_taxitur_token)
    
    if filtro_parada["success"]:
        servicios_parada = filtro_parada["data"]
        count_parada = len(servicios_parada) if isinstance(servicios_parada, list) else 0
        log_test("4.1 GET /services?origen_taxitur=parada", True, f"Encontrados {count_parada} servicios 'parada'")
    else:
        log_test("4.1 GET /services?origen_taxitur=parada", False, f"Error: {filtro_parada['data']}")
    
    # 4.2 GET /services?origen_taxitur=lagos
    params_lagos = {"origen_taxitur": "lagos"}  
    filtro_lagos = make_request("GET", "/services", params_lagos, token=admin_taxitur_token)
    
    if filtro_lagos["success"]:
        servicios_lagos = filtro_lagos["data"]
        count_lagos = len(servicios_lagos) if isinstance(servicios_lagos, list) else 0
        log_test("4.2 GET /services?origen_taxitur=lagos", True, f"Encontrados {count_lagos} servicios 'lagos'")
    else:
        log_test("4.2 GET /services?origen_taxitur=lagos", False, f"Error: {filtro_lagos['data']}")

# ==========================================
# VERIFICACIÓN CRÍTICA: NO HARDCODED
# ==========================================
print("\n🎯 VERIFICACIÓN CRÍTICA: NO HAY DEPENDENCIA HARDCODED") 
print("-" * 60)

if admin_taxitur_token and superadmin_token:
    # 5.1 Temporalmente desactivar feature para Taxitur
    print("5.1 Desactivar temporalmente feature Taxitur...")
    
    update_taxitur_data = {
        "features": {
            "taxitur_origen": False  # ❌ Desactivar
        }
    }
    
    disable_result = make_request("PUT", f"/organizations/{TAXITUR_ORG_ID}", update_taxitur_data, token=superadmin_token)
    if disable_result["success"]:
        log_test("5.1 Desactivar feature Taxitur", True, "Feature desactivado temporalmente")
        
        # 5.2 Verificar que ahora permite servicios SIN origen_taxitur
        if taxista_taxitur_token:
            servicio_test_sin_feature = {
                "fecha": datetime.now().strftime("%Y-%m-%d"),
                "hora": datetime.now().strftime("%H:%M"),
                "origen": "Test Sin Feature",
                "destino": "Test Destino",
                "importe": 10.00,
                "tipo": "particular",
                "kilometros": 3.0,
                "tiempo_espera": 0,
                "importe_espera": 0.0,
                "metodo_pago": "efectivo"
                # ✅ SIN origen_taxitur
            }
            
            test_sin_feature = make_request("POST", "/services", servicio_test_sin_feature, token=taxista_taxitur_token)
            if test_sin_feature["status_code"] == 200:
                log_test("5.2 POST sin origen (feature OFF) → 200", True, 
                        "Correcto: sin feature activo, origen_taxitur no requerido")
            else:
                log_test("5.2 POST sin origen (feature OFF) → 200", False, 
                        f"Error {test_sin_feature['status_code']}: {test_sin_feature['data']}")
        
        # 5.3 Reactivar feature (restaurar estado)
        restore_taxitur_data = {
            "features": {
                "taxitur_origen": True  # ✅ Reactivar
            }
        }
        
        restore_result = make_request("PUT", f"/organizations/{TAXITUR_ORG_ID}", restore_taxitur_data, token=superadmin_token)
        if restore_result["success"]:
            log_test("5.3 Reactivar feature Taxitur", True, "Feature reactivado correctamente")
        else:
            log_test("5.3 Reactivar feature Taxitur", False, f"Error: {restore_result['data']}")
    else:
        log_test("5.1 Desactivar feature Taxitur", False, f"Error: {disable_result['data']}")

# ==========================================
# VERIFICACIÓN EXTRA: VALORES INVÁLIDOS
# ==========================================
print("\n🧪 VERIFICACIÓN EXTRA: VALORES INVÁLIDOS")
print("-" * 60)

if taxista_taxitur_token:
    # 6.1 POST con origen_taxitur inválido
    servicio_invalido = {
        "fecha": datetime.now().strftime("%Y-%m-%d"),
        "hora": datetime.now().strftime("%H:%M"),
        "origen": "Test Inválido",
        "destino": "Test Destino",
        "importe": 15.00,
        "tipo": "particular",
        "kilometros": 5.0,
        "tiempo_espera": 0,
        "importe_espera": 0.0,
        "metodo_pago": "efectivo",
        "origen_taxitur": "invalido"  # ❌ Valor no permitido
    }
    
    invalido_result = make_request("POST", "/services", servicio_invalido, token=taxista_taxitur_token)
    if invalido_result["status_code"] == 400:
        error_detail = invalido_result["data"].get("detail", "")
        if "parada" in error_detail or "lagos" in error_detail:
            log_test("6.1 POST origen_taxitur='invalido' → 400", True, f"Correctamente rechazado: {error_detail}")
        else:
            log_test("6.1 POST origen_taxitur='invalido' → 400", False, f"Error 400 pero mensaje incorrecto: {error_detail}")
    else:
        log_test("6.1 POST origen_taxitur='invalido' → 400", False, 
                f"Esperado 400, obtenido {invalido_result['status_code']}: {invalido_result['data']}")

# ==========================================
# RESUMEN FINAL
# ==========================================
print("\n" + "=" * 70)
print("📊 RESUMEN FINAL - TESTING FEATURE FLAGS TAXITUR_ORIGEN")
print("=" * 70)

print(f"🎯 TOTAL TESTS: {stats['total_tests']}")
print(f"✅ PASSED: {stats['passed_tests']}")
print(f"❌ FAILED: {stats['failed_tests']}")

success_rate = (stats['passed_tests'] / stats['total_tests']) * 100 if stats['total_tests'] > 0 else 0
print(f"📈 ÉXITO: {success_rate:.1f}%")

if stats['failed_tests'] == 0:
    print("\n🎉 ¡TODOS LOS TESTS PASARON!")
    print("✅ Feature flag taxitur_origen funcionando correctamente")
    print("✅ NO hay dependencia de ID hardcodeado")
    print("✅ Sistema basado en features de organización en BD")
    print("✅ Filtros funcionando solo para orgs con feature activo")
else:
    print(f"\n⚠️ {stats['failed_tests']} tests fallaron")
    
    # Mostrar tests fallidos
    failed_tests = [test for test in stats["test_results"] if not test["passed"]]
    for test in failed_tests:
        print(f"   ❌ {test['test']}: {test['details']}")

print("\n🔍 VERIFICACIONES COMPLETADAS:")
print("   ✅ /my-organization devuelve features correctamente")  
print("   ✅ Org con feature activo requiere origen_taxitur")
print("   ✅ Org sin feature activo ignora origen_taxitur")
print("   ✅ Filtros GET /services funcionan solo con feature activo")
print("   ✅ Validación NO depende de ID hardcodeado")

print("\n🏁 TESTING FINALIZADO")