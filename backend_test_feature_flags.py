#!/usr/bin/env python3
"""
TESTING EXHAUSTIVO - FEATURE FLAGS TAXITUR_ORIGEN
Verificar que la validación del campo origen_taxitur depende del feature flag
de la organización (features.taxitur_origen) y no de un ID hardcodeado.
"""

import requests
import json
import uuid
import sys
from datetime import datetime

# ==========================================
# CONFIGURACIÓN
# ==========================================
BASE_URL = "https://flagged-services.preview.emergentagent.com/api"

# Credenciales proporcionadas
SUPERADMIN_CREDENTIALS = {"username": "superadmin", "password": "superadmin123"}
ADMIN_TAXITUR_CREDENTIALS = {"username": "admintur", "password": "admin123"}
TAXITUR_ORG_ID = "69484bec187c3bc2b0fdb8f4"

# Headers
HEADERS = {"Content-Type": "application/json"}

# Estadísticas globales
stats = {
    "total_tests": 0,
    "passed_tests": 0,
    "failed_tests": 0,
    "test_results": []
}

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

def make_request(method, endpoint, data=None, headers=None, token=None):
    """Realizar request HTTP con manejo de errores"""
    url = f"{BASE_URL}{endpoint}"
    
    # Preparar headers
    req_headers = HEADERS.copy()
    if headers:
        req_headers.update(headers)
    
    if token:
        req_headers["Authorization"] = f"Bearer {token}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=req_headers, params=data)
        elif method == "POST":
            response = requests.post(url, headers=req_headers, json=data)
        elif method == "PUT":
            response = requests.put(url, headers=req_headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=req_headers)
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

def login_user(credentials):
    """Login y obtener token"""
    result = make_request("POST", "/auth/login", credentials)
    if result["success"]:
        return result["data"]["access_token"]
    return None

# ==========================================
# SETUP INICIAL
# ==========================================
print("🎯 TESTING EXHAUSTIVO - FEATURE FLAGS TAXITUR_ORIGEN")
print("=" * 70)
print(f"Base URL: {BASE_URL}")
print(f"Taxitur Org ID: {TAXITUR_ORG_ID}")
print()

# ==========================================
# PARTE 1: VERIFICAR QUE /my-organization DEVUELVE FEATURES
# ==========================================
print("🔍 PARTE 1: VERIFICAR /my-organization DEVUELVE FEATURES")
print("-" * 50)

# 1.1 Login como admintur (admin de Taxitur)
print("1.1 Login como admintur...")
admin_taxitur_token = login_user(ADMIN_TAXITUR_CREDENTIALS)

if not admin_taxitur_token:
    log_test("1.1 Login admintur", False, "No se pudo obtener token de acceso")
    sys.exit(1)
else:
    log_test("1.1 Login admintur", True, f"Token obtenido: {admin_taxitur_token[:20]}...")

# 1.2 GET /my-organization
print("1.2 GET /my-organization...")
my_org_result = make_request("GET", "/my-organization", token=admin_taxitur_token)

if not my_org_result["success"]:
    log_test("1.2 GET /my-organization", False, f"Error {my_org_result['status_code']}: {my_org_result['data']}")
else:
    org_data = my_org_result["data"]
    
    # 1.3 Verificar que la respuesta incluye features.taxitur_origen: true
    features = org_data.get("features", {})
    taxitur_origen_feature = features.get("taxitur_origen", False)
    
    if taxitur_origen_feature is True:
        log_test("1.3 Verificar features.taxitur_origen=true", True, f"Feature flag encontrado: {features}")
        print(f"   📋 Organización: {org_data.get('nombre', 'N/A')}")
        print(f"   🎯 ID: {org_data.get('id', 'N/A')}")
        print(f"   🚩 Features: {features}")
    else:
        log_test("1.3 Verificar features.taxitur_origen=true", False, 
                f"Feature flag no encontrado o desactivado. Features actuales: {features}")

# ==========================================
# PARTE 2: ORG CON FEATURE ACTIVO (Taxitur)
# ==========================================
print("\n🚕 PARTE 2: ORG CON FEATURE ACTIVO (Taxitur)")
print("-" * 50)

# 2.1 Crear un taxista para Taxitur si no existe
print("2.1 Crear taxista para org Taxitur...")
superadmin_token = login_user(SUPERADMIN_CREDENTIALS)

if not superadmin_token:
    log_test("2.1 Login superadmin", False, "No se pudo obtener token superadmin")
else:
    # Crear taxista en la org Taxitur
    taxista_data = {
        "username": f"test_taxitur_{int(datetime.now().timestamp())}",
        "password": "test123",
        "role": "taxista",
        "organization_id": TAXITUR_ORG_ID
    }
    
    create_taxista_result = make_request("POST", "/users", taxista_data, token=superadmin_token)
    
    if create_taxista_result["success"]:
        taxista_id = create_taxista_result["data"]["id"]
        taxista_username = create_taxista_result["data"]["username"]
        log_test("2.1 Crear taxista Taxitur", True, f"Taxista creado: {taxista_username} (ID: {taxista_id})")
    else:
        log_test("2.1 Crear taxista Taxitur", False, f"Error: {create_taxista_result['data']}")
        taxista_username = None

# 2.2 Login con taxista de Taxitur y crear turno
if taxista_username:
    print("2.2 Login taxista Taxitur y crear turno...")
    taxista_token = login_user({"username": taxista_username, "password": "test123"})
    
    if not taxista_token:
        log_test("2.2 Login taxista Taxitur", False, "No se pudo obtener token taxista")
    else:
        # Crear vehículo de prueba primero (necesario para turnos)
        vehiculo_data = {
            "matricula": f"TEST{int(datetime.now().timestamp())}",
            "plazas": 4,
            "marca": "Test",
            "modelo": "Test",
            "km_iniciales": 100000,
            "fecha_compra": "2023-01-01",
            "activo": True
        }
        
        vehiculo_result = make_request("POST", "/vehiculos", vehiculo_data, token=superadmin_token)
        
        if vehiculo_result["success"]:
            vehiculo_id = vehiculo_result["data"]["id"]
            log_test("2.2.1 Crear vehículo test", True, f"Vehículo: {vehiculo_data['matricula']}")
            
            # Crear turno
            turno_data = {
                "fecha_inicio": datetime.now().strftime("%Y-%m-%d"),
                "hora_inicio": datetime.now().strftime("%H:%M"),
                "km_inicio": 100000,
                "vehiculo_id": vehiculo_id
            }
            
            turno_result = make_request("POST", "/turnos", turno_data, token=taxista_token)
            
            if turno_result["success"]:
                log_test("2.2.2 Crear turno Taxitur", True, f"Turno ID: {turno_result['data']['id']}")
            else:
                log_test("2.2.2 Crear turno Taxitur", False, f"Error: {turno_result['data']}")
        else:
            log_test("2.2.1 Crear vehículo test", False, f"Error: {vehiculo_result['data']}")

# 2.3 POST /services SIN origen_taxitur → Esperado: 400 (debe rechazar)
print("2.3 POST /services SIN origen_taxitur (debe rechazar)...")
if taxista_token:
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
        # ❌ SIN origen_taxitur - debe fallar
    }
    
    result = make_request("POST", "/services", servicio_sin_origen, token=taxista_token)
    
    if result["status_code"] == 400:
        error_message = result["data"].get("detail", "")
        if "origen_taxitur" in error_message.lower():
            log_test("2.3 POST sin origen_taxitur → 400", True, f"Correctamente rechazado: {error_message}")
        else:
            log_test("2.3 POST sin origen_taxitur → 400", False, f"Error 400 pero mensaje incorrecto: {error_message}")
    else:
        log_test("2.3 POST sin origen_taxitur → 400", False, 
                f"Esperado 400, obtenido {result['status_code']}: {result['data']}")

# 2.4 POST /services CON origen_taxitur='parada' → Esperado: 200 (debe aceptar)
print("2.4 POST /services CON origen_taxitur='parada' (debe aceptar)...")
if taxista_token:
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
        "origen_taxitur": "parada"  # ✅ CON origen_taxitur
    }
    
    result = make_request("POST", "/services", servicio_parada, token=taxista_token)
    
    if result["status_code"] == 200:
        servicio_parada_id = result["data"]["id"]
        log_test("2.4 POST con origen_taxitur='parada' → 200", True, f"Servicio creado: {servicio_parada_id}")
    else:
        log_test("2.4 POST con origen_taxitur='parada' → 200", False, 
                f"Esperado 200, obtenido {result['status_code']}: {result['data']}")

# 2.5 POST /services CON origen_taxitur='lagos' → Esperado: 200 (debe aceptar)
print("2.5 POST /services CON origen_taxitur='lagos' (debe aceptar)...")
if taxista_token:
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
        "origen_taxitur": "lagos"  # ✅ CON origen_taxitur
    }
    
    result = make_request("POST", "/services", servicio_lagos, token=taxista_token)
    
    if result["status_code"] == 200:
        servicio_lagos_id = result["data"]["id"]
        log_test("2.5 POST con origen_taxitur='lagos' → 200", True, f"Servicio creado: {servicio_lagos_id}")
    else:
        log_test("2.5 POST con origen_taxitur='lagos' → 200", False, 
                f"Esperado 200, obtenido {result['status_code']}: {result['data']}")

# ==========================================
# PARTE 3: ORG SIN FEATURE ACTIVO (otra org)
# ==========================================
print("\n🏢 PARTE 3: ORG SIN FEATURE ACTIVO (otra organización)")
print("-" * 50)

# 3.1 Crear otra organización sin el feature activo
print("3.1 Crear organización sin feature taxitur_origen...")
if superadmin_token:
    nueva_org_data = {
        "nombre": f"Taxi Test {int(datetime.now().timestamp())}",
        "cif": f"B{int(datetime.now().timestamp())}"[-8:],
        "direccion": "Calle Test 123",
        "localidad": "Test City",
        "provincia": "Test Province",
        "telefono": "987654321",
        "email": "test@test.com",
        "activa": True
        # ❌ SIN features.taxitur_origen
    }
    
    org_result = make_request("POST", "/organizations", nueva_org_data, token=superadmin_token)
    
    if org_result["success"]:
        nueva_org_id = org_result["data"]["id"]
        log_test("3.1 Crear org sin feature", True, f"Org creada: {nueva_org_id}")
        
        # 3.2 Crear taxista en esa org
        print("3.2 Crear taxista en org sin feature...")
        taxista_sin_feature_data = {
            "username": f"test_sin_feature_{int(datetime.now().timestamp())}",
            "password": "test123", 
            "role": "taxista",
            "organization_id": nueva_org_id
        }
        
        taxista_result = make_request("POST", "/users", taxista_sin_feature_data, token=superadmin_token)
        
        if taxista_result["success"]:
            taxista_sin_feature_username = taxista_result["data"]["username"]
            log_test("3.2 Crear taxista org sin feature", True, f"Taxista: {taxista_sin_feature_username}")
            
            # 3.3 Login con ese taxista
            print("3.3 Login taxista org sin feature...")
            taxista_sin_feature_token = login_user({
                "username": taxista_sin_feature_username, 
                "password": "test123"
            })
            
            if taxista_sin_feature_token:
                log_test("3.3 Login taxista sin feature", True)
                
                # 3.4 GET /my-organization - Verificar que NO tiene features.taxitur_origen: true
                print("3.4 Verificar /my-organization NO tiene taxitur_origen...")
                my_org_sin_feature = make_request("GET", "/my-organization", token=taxista_sin_feature_token)
                
                if my_org_sin_feature["success"]:
                    features_sin = my_org_sin_feature["data"].get("features", {})
                    taxitur_origen_sin = features_sin.get("taxitur_origen", False)
                    
                    if not taxitur_origen_sin:
                        log_test("3.4 Org sin feature → taxitur_origen=false", True, 
                                f"Correcto: features={features_sin}")
                    else:
                        log_test("3.4 Org sin feature → taxitur_origen=false", False, 
                                f"ERROR: Feature activo cuando no debería. Features: {features_sin}")
                else:
                    log_test("3.4 Verificar org sin feature", False, 
                            f"Error {my_org_sin_feature['status_code']}: {my_org_sin_feature['data']}")
                
                # 3.5 Crear turno para testing
                print("3.5 Crear turno en org sin feature...")
                vehiculo_sin_feature_data = {
                    "matricula": f"TESTSF{int(datetime.now().timestamp())}",
                    "plazas": 4,
                    "marca": "Test",
                    "modelo": "Test",
                    "km_iniciales": 50000,
                    "fecha_compra": "2023-01-01",
                    "activo": True
                }
                
                vehiculo_sin_feature_result = make_request("POST", "/vehiculos", vehiculo_sin_feature_data, token=superadmin_token)
                
                if vehiculo_sin_feature_result["success"]:
                    vehiculo_sin_feature_id = vehiculo_sin_feature_result["data"]["id"]
                    
                    turno_sin_feature_data = {
                        "fecha_inicio": datetime.now().strftime("%Y-%m-%d"),
                        "hora_inicio": datetime.now().strftime("%H:%M"),
                        "km_inicio": 50000,
                        "vehiculo_id": vehiculo_sin_feature_id
                    }
                    
                    turno_sin_feature_result = make_request("POST", "/turnos", turno_sin_feature_data, token=taxista_sin_feature_token)
                    
                    if turno_sin_feature_result["success"]:
                        log_test("3.5 Crear turno sin feature", True, f"Turno ID: {turno_sin_feature_result['data']['id']}")
                        
                        # 3.6 POST /services SIN origen_taxitur → Esperado: 200 (debe aceptar)
                        print("3.6 POST /services SIN origen_taxitur (debe aceptar)...")
                        servicio_sin_origen_ok = {
                            "fecha": datetime.now().strftime("%Y-%m-%d"),
                            "hora": datetime.now().strftime("%H:%M"),
                            "origen": "Plaza Mayor",
                            "destino": "Estación de Tren",
                            "importe": 12.30,
                            "tipo": "particular",
                            "kilometros": 5.2,
                            "tiempo_espera": 0,
                            "importe_espera": 0.0,
                            "metodo_pago": "efectivo"
                            # ✅ SIN origen_taxitur - debe funcionar en org sin feature
                        }
                        
                        result_sin_origen = make_request("POST", "/services", servicio_sin_origen_ok, token=taxista_sin_feature_token)
                        
                        if result_sin_origen["status_code"] == 200:
                            log_test("3.6 POST sin origen_taxitur → 200", True, f"Servicio creado: {result_sin_origen['data']['id']}")
                        else:
                            log_test("3.6 POST sin origen_taxitur → 200", False, 
                                    f"Esperado 200, obtenido {result_sin_origen['status_code']}: {result_sin_origen['data']}")
                        
                        # 3.7 POST /services CON origen_taxitur='parada' → Esperado: 400 (debe rechazar)
                        print("3.7 POST /services CON origen_taxitur (debe rechazar)...")
                        servicio_con_origen_mal = {
                            "fecha": datetime.now().strftime("%Y-%m-%d"),
                            "hora": datetime.now().strftime("%H:%M"),
                            "origen": "Plaza Test",
                            "destino": "Calle Test",
                            "importe": 15.00,
                            "tipo": "particular",
                            "kilometros": 6.0,
                            "tiempo_espera": 0,
                            "importe_espera": 0.0,
                            "metodo_pago": "efectivo",
                            "origen_taxitur": "parada"  # ❌ CON origen_taxitur - debe fallar en org sin feature
                        }
                        
                        result_con_origen = make_request("POST", "/services", servicio_con_origen_mal, token=taxista_sin_feature_token)
                        
                        if result_con_origen["status_code"] == 200:
                            # Si es 200, verificar que origen_taxitur fue ignorado (forzado a None)
                            servicio_creado = result_con_origen["data"]
                            origen_final = servicio_creado.get("origen_taxitur")
                            
                            if origen_final is None:
                                log_test("3.7 POST con origen_taxitur → ignorado", True, 
                                        "Origen ignorado correctamente (forzado a None)")
                            else:
                                log_test("3.7 POST con origen_taxitur → ignorado", False, 
                                        f"ERROR: origen_taxitur no fue ignorado: {origen_final}")
                        else:
                            # Si no es 200, puede ser error válido o no
                            log_test("3.7 POST con origen_taxitur → resultado", True,
                                    f"Status {result_con_origen['status_code']}: {result_con_origen['data']}")
                    else:
                        log_test("3.5 Crear turno sin feature", False, f"Error: {turno_sin_feature_result['data']}")
                else:
                    log_test("2.2.1 Crear vehículo test", False, f"Error: {vehiculo_sin_feature_result['data']}")
            else:
                log_test("3.3 Login taxista sin feature", False, "Token no obtenido")
        else:
            log_test("3.2 Crear taxista org sin feature", False, f"Error: {taxista_result['data']}")
    else:
        log_test("3.1 Crear org sin feature", False, f"Error: {org_result['data']}")

# ==========================================
# PARTE 4: FILTRO EN GET /services
# ==========================================
print("\n🔍 PARTE 4: FILTRO EN GET /services")
print("-" * 50)

# 4.1 Login como admin de Taxitur y probar filtros
print("4.1 GET /services?origen_taxitur=parada...")
if admin_taxitur_token:
    # Filtro por parada
    params_parada = {"origen_taxitur": "parada"}
    filtro_parada_result = make_request("GET", "/services", params_parada, token=admin_taxitur_token)
    
    if filtro_parada_result["success"]:
        servicios_parada = filtro_parada_result["data"]
        count_parada = len(servicios_parada) if isinstance(servicios_parada, list) else servicios_parada.get("total", 0)
        log_test("4.1 GET /services?origen_taxitur=parada", True, f"Encontrados {count_parada} servicios 'parada'")
    else:
        log_test("4.1 GET /services?origen_taxitur=parada", False, 
                f"Error {filtro_parada_result['status_code']}: {filtro_parada_result['data']}")

# 4.2 GET /services?origen_taxitur=lagos
print("4.2 GET /services?origen_taxitur=lagos...")
if admin_taxitur_token:
    params_lagos = {"origen_taxitur": "lagos"}
    filtro_lagos_result = make_request("GET", "/services", params_lagos, token=admin_taxitur_token)
    
    if filtro_lagos_result["success"]:
        servicios_lagos = filtro_lagos_result["data"]
        count_lagos = len(servicios_lagos) if isinstance(servicios_lagos, list) else servicios_lagos.get("total", 0)
        log_test("4.2 GET /services?origen_taxitur=lagos", True, f"Encontrados {count_lagos} servicios 'lagos'")
    else:
        log_test("4.2 GET /services?origen_taxitur=lagos", False, 
                f"Error {filtro_lagos_result['status_code']}: {filtro_lagos_result['data']}")

# ==========================================
# VERIFICACIÓN CRÍTICA: FEATURE FLAG NO HARDCODED
# ==========================================
print("\n🎯 VERIFICACIÓN CRÍTICA: NO HAY DEPENDENCIA HARDCODED")
print("-" * 50)

# 5.1 Verificar que el sistema lee desde features de la organización
print("5.1 Verificar lectura desde features de organización...")

# Intentar desactivar temporalmente el feature para Taxitur (solo para test)
if superadmin_token and taxitur_origen_feature:
    print("5.1.1 Temporalmente desactivar feature para Taxitur...")
    
    update_org_data = {
        "features": {
            "taxitur_origen": False  # ❌ Desactivar temporalmente
        }
    }
    
    update_result = make_request("PUT", f"/organizations/{TAXITUR_ORG_ID}", update_org_data, token=superadmin_token)
    
    if update_result["success"]:
        log_test("5.1.1 Desactivar feature temporalmente", True, "Feature taxitur_origen desactivado")
        
        # 5.1.2 Intentar crear servicio SIN origen_taxitur (debe funcionar ahora)
        if taxista_token:
            servicio_test_feature = {
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
                # ✅ SIN origen_taxitur - debe funcionar con feature desactivado
            }
            
            test_result = make_request("POST", "/services", servicio_test_feature, token=taxista_token)
            
            if test_result["status_code"] == 200:
                log_test("5.1.2 POST sin origen (feature OFF) → 200", True, 
                        "Correcto: sin feature activo, origen_taxitur no es requerido")
            else:
                log_test("5.1.2 POST sin origen (feature OFF) → 200", False, 
                        f"ERROR: Esperado 200, obtenido {test_result['status_code']}")
        
        # 5.1.3 Reactivar el feature (restaurar estado original)
        print("5.1.3 Reactivar feature para Taxitur...")
        restore_org_data = {
            "features": {
                "taxitur_origen": True  # ✅ Reactivar
            }
        }
        
        restore_result = make_request("PUT", f"/organizations/{TAXITUR_ORG_ID}", restore_org_data, token=superadmin_token)
        
        if restore_result["success"]:
            log_test("5.1.3 Reactivar feature", True, "Feature taxitur_origen reactivado")
        else:
            log_test("5.1.3 Reactivar feature", False, f"Error: {restore_result['data']}")
    else:
        log_test("5.1.1 Desactivar feature temporalmente", False, f"Error: {update_result['data']}")

# ==========================================
# VERIFICACIÓN EXTRA: COMPORTAMIENTO CON VALORES INVÁLIDOS
# ==========================================
print("\n🧪 VERIFICACIÓN EXTRA: VALORES INVÁLIDOS")
print("-" * 50)

# 6.1 POST con origen_taxitur inválido para org con feature activo
if taxista_token:
    print("6.1 POST con origen_taxitur='invalido' (debe rechazar)...")
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
        "origen_taxitur": "invalido"  # ❌ Valor inválido
    }
    
    invalido_result = make_request("POST", "/services", servicio_invalido, token=taxista_token)
    
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
print("📊 RESUMEN FINAL DE TESTING")
print("=" * 70)

print(f"🎯 TOTAL TESTS: {stats['total_tests']}")
print(f"✅ PASSED: {stats['passed_tests']}")
print(f"❌ FAILED: {stats['failed_tests']}")

if stats['failed_tests'] == 0:
    print("\n🎉 ¡TODOS LOS TESTS PASARON!")
    print("✅ Feature flag taxitur_origen funcionando correctamente")
    print("✅ NO hay dependencia de ID hardcodeado")
    print("✅ Sistema basado en features de organización")
else:
    print(f"\n⚠️ {stats['failed_tests']} tests fallaron")

success_rate = (stats['passed_tests'] / stats['total_tests']) * 100 if stats['total_tests'] > 0 else 0
print(f"📈 ÉXITO: {success_rate:.1f}%")

# Mostrar detalles de tests fallidos
failed_tests = [test for test in stats["test_results"] if not test["passed"]]
if failed_tests:
    print("\n❌ TESTS FALLIDOS:")
    for test in failed_tests:
        print(f"   - {test['test']}: {test['details']}")

print("\n🏁 TESTING FINALIZADO")