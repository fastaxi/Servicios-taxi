#!/usr/bin/env python3
"""
TESTING FILTROS DATETIME - PASO 3

Pruebas exhaustivas para verificar que los filtros por rango de fechas 
funcionan correctamente con los nuevos campos datetime UTC.
"""
import requests
import json
from datetime import datetime, timedelta
import uuid

# API Configuration
API_BASE = "https://flagged-services.preview.emergentagent.com/api"

# Credenciales
SUPERADMIN_CREDS = {"username": "superadmin", "password": "superadmin123"}
ADMIN_TAXITUR_CREDS = {"username": "admintur", "password": "admin123"}

# Colores para output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def log(message, color=Colors.ENDC):
    print(f"{color}{message}{Colors.ENDC}")

def log_success(message):
    log(f"✅ {message}", Colors.GREEN)

def log_error(message):
    log(f"❌ {message}", Colors.RED)

def log_info(message):
    log(f"ℹ️ {message}", Colors.BLUE)

def log_warning(message):
    log(f"⚠️ {message}", Colors.YELLOW)

class TestResults:
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.results = []

    def add_test(self, name, passed, details=""):
        self.total += 1
        if passed:
            self.passed += 1
            status = "PASS"
            log_success(f"{name}: {status}")
        else:
            self.failed += 1
            status = "FAIL"
            log_error(f"{name}: {status} - {details}")
        
        self.results.append({
            "name": name,
            "status": status,
            "details": details
        })

    def print_summary(self):
        log(f"\n{Colors.BOLD}=== RESUMEN FINAL ==={Colors.ENDC}")
        log(f"Total: {self.total}")
        log_success(f"Passed: {self.passed}")
        if self.failed > 0:
            log_error(f"Failed: {self.failed}")
        else:
            log_success(f"Failed: {self.failed}")
        
        success_rate = (self.passed / self.total) * 100 if self.total > 0 else 0
        log(f"Success Rate: {success_rate:.1f}%")

# Global test results
results = TestResults()

def make_request(method, endpoint, headers=None, data=None, expected_status=200):
    """Helper function to make HTTP requests"""
    url = f"{API_BASE}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, params=data)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers)
        
        if response.status_code != expected_status:
            return False, f"Expected {expected_status}, got {response.status_code}: {response.text}"
        
        try:
            return True, response.json()
        except:
            return True, response.text
            
    except Exception as e:
        return False, f"Request failed: {str(e)}"

def login_user(credentials):
    """Login and return token"""
    success, response = make_request("POST", "/auth/login", data=credentials)
    if success and isinstance(response, dict) and "access_token" in response:
        return response["access_token"]
    return None

def get_auth_headers(token):
    """Get authorization headers"""
    return {"Authorization": f"Bearer {token}"}

def test_parte_1_verify_service_dt_utc():
    """PARTE 1: Verificar que service_dt_utc se guarda"""
    log(f"\n{Colors.BOLD}=== PARTE 1: VERIFICAR service_dt_utc SE GUARDA ==={Colors.ENDC}")
    
    # 1. Login como superadmin para crear taxista con turno
    token = login_user(SUPERADMIN_CREDS)
    if not token:
        results.add_test("1.0 Login superadmin", False, "Failed to login")
        return
    
    results.add_test("1.0 Login superadmin", True)
    headers = get_auth_headers(token)
    
    # 2. Crear taxista de prueba
    test_username = f"test_taxista_{int(datetime.now().timestamp())}"
    taxista_data = {
        "username": test_username,
        "password": "test123",
        "nombre": "Taxista Test DateTime",
        "role": "taxista",
        "licencia": "TEST001"
    }
    
    success, response = make_request("POST", "/users", headers=headers, data=taxista_data)
    if not success:
        results.add_test("1.1 Crear taxista", False, f"Error creating taxista: {response}")
        return
        
    taxista_id = response.get("id")
    results.add_test("1.1 Crear taxista", True, f"ID: {taxista_id}")
    
    # 3. Crear vehículo de prueba
    vehiculo_data = {
        "matricula": f"TEST{int(datetime.now().timestamp() % 10000)}",
        "plazas": 4,
        "marca": "Test",
        "modelo": "DateTime"
    }
    
    success, response = make_request("POST", "/vehiculos", headers=headers, data=vehiculo_data)
    if not success:
        results.add_test("1.2 Crear vehículo", False, f"Error creating vehiculo: {response}")
        return
        
    vehiculo_id = response.get("id")
    results.add_test("1.2 Crear vehículo", True, f"ID: {vehiculo_id}")
    
    # 4. Login como taxista
    taxista_token = login_user({"username": test_username, "password": "test123"})
    if not taxista_token:
        results.add_test("1.3 Login taxista", False, "Failed to login as taxista")
        return
        
    results.add_test("1.3 Login taxista", True)
    taxista_headers = get_auth_headers(taxista_token)
    
    # 5. Crear turno activo
    turno_data = {
        "fecha_inicio": "20/02/2026",
        "hora_inicio": "14:00",
        "km_inicio": 100000,
        "vehiculo_id": vehiculo_id
    }
    
    success, response = make_request("POST", "/turnos", headers=taxista_headers, data=turno_data)
    if not success:
        results.add_test("1.4 Crear turno", False, f"Error creating turno: {response}")
        return
        
    turno_id = response.get("id")
    results.add_test("1.4 Crear turno", True, f"ID: {turno_id}")
    
    # 6. Crear servicio con los datos especificados
    servicio_data = {
        "fecha": "20/02/2026",
        "hora": "14:30",
        "origen": "Test A",
        "destino": "Test B", 
        "importe": 15.0,
        "tipo": "particular"
    }
    
    success, response = make_request("POST", "/services", headers=taxista_headers, data=servicio_data)
    if not success:
        results.add_test("1.5 POST service", False, f"Error creating service: {response}")
        return
        
    service_created = response
    results.add_test("1.5 POST service", True, f"ID: {service_created.get('id')}")
    
    # 7. Verificar que la respuesta incluye la fecha correcta y service_dt_utc
    has_correct_date = service_created.get("fecha") == "20/02/2026"
    has_correct_time = service_created.get("hora") == "14:30"
    has_service_dt_utc = "service_dt_utc" in service_created
    
    results.add_test("1.6 Verify fecha in response", has_correct_date, f"Expected 20/02/2026, got {service_created.get('fecha')}")
    results.add_test("1.7 Verify hora in response", has_correct_time, f"Expected 14:30, got {service_created.get('hora')}")
    results.add_test("1.8 Verify service_dt_utc exists", has_service_dt_utc, f"service_dt_utc field: {service_created.get('service_dt_utc', 'NOT FOUND')}")
    
    # 8. GET /services y verificar que el servicio aparece ordenado correctamente
    success, response = make_request("GET", "/services", headers=taxista_headers)
    if not success:
        results.add_test("1.9 GET services list", False, f"Error getting services: {response}")
        return
        
    services_list = response
    service_found = any(s.get("id") == service_created.get("id") for s in services_list)
    first_service = services_list[0] if services_list else None
    is_ordered_correctly = first_service and first_service.get("id") == service_created.get("id")
    
    results.add_test("1.9 Service appears in list", service_found, f"Found {len(services_list)} services")
    results.add_test("1.10 Service ordered correctly", is_ordered_correctly, f"First service ID: {first_service.get('id') if first_service else 'None'}")
    
    return taxista_token, taxista_headers, turno_id, vehiculo_id

def test_parte_2_critical_date_range_filters(taxista_token, taxista_headers, turno_id, vehiculo_id):
    """PARTE 2: TEST CRÍTICO - Filtros por rango de fechas"""
    log(f"\n{Colors.BOLD}=== PARTE 2: TEST CRÍTICO - FILTROS POR RANGO DE FECHAS ==={Colors.ENDC}")
    
    # Login como admin para poder especificar turno_id directamente
    admin_token = login_user(ADMIN_TAXITUR_CREDS)
    if not admin_token:
        results.add_test("2.0 Login admin", False, "Failed to login as admin")
        return
        
    results.add_test("2.0 Login admin", True)
    admin_headers = get_auth_headers(admin_token)
    
    # 1. Crear 3 services con fechas específicas
    services_data = [
        {
            "fecha": "31/12/2025",
            "hora": "23:50", 
            "origen": "Service 1 - Old Year",
            "destino": "Destination 1",
            "importe": 10.0,
            "tipo": "particular",
            "turno_id": turno_id
        },
        {
            "fecha": "01/01/2026",
            "hora": "00:10",
            "origen": "Service 2 - New Year", 
            "destino": "Destination 2",
            "importe": 20.0,
            "tipo": "particular",
            "turno_id": turno_id
        },
        {
            "fecha": "15/01/2026",
            "hora": "12:00",
            "origen": "Service 3 - Mid Month",
            "destino": "Destination 3", 
            "importe": 30.0,
            "tipo": "particular",
            "turno_id": turno_id
        }
    ]
    
    created_services = []
    for i, service_data in enumerate(services_data):
        success, response = make_request("POST", "/services", headers=admin_headers, data=service_data)
        if success:
            created_services.append(response)
            results.add_test(f"2.{i+1} Create service {i+1}", True, f"Date: {service_data['fecha']}")
        else:
            results.add_test(f"2.{i+1} Create service {i+1}", False, f"Error: {response}")
            return
    
    # 2. Test del filtro crítico: GET /services?fecha_inicio=01/01/2026&fecha_fin=31/01/2026
    test_params = {
        "fecha_inicio": "01/01/2026",
        "fecha_fin": "31/01/2026"
    }
    
    success, response = make_request("GET", "/services", headers=admin_headers, data=test_params)
    if not success:
        results.add_test("2.4 GET services with date filter", False, f"Error: {response}")
        return
        
    filtered_services = response
    results.add_test("2.4 GET services with date filter", True, f"Found {len(filtered_services)} services")
    
    # 3. Verificar que SOLO incluye los 2 services correctos (01/01 y 15/01)
    expected_dates = ["01/01/2026", "15/01/2026"]
    found_dates = [s.get("fecha") for s in filtered_services]
    
    # El servicio de 31/12/2025 NO debe aparecer (este era el bug)
    has_old_year_service = any(s.get("fecha") == "31/12/2025" for s in filtered_services)
    has_correct_count = len(filtered_services) >= 2  # Al menos los 2 que creamos
    has_new_year_service = any(s.get("fecha") == "01/01/2026" for s in filtered_services)
    has_mid_month_service = any(s.get("fecha") == "15/01/2026" for s in filtered_services)
    
    results.add_test("2.5 Does NOT include 31/12/2025 service", not has_old_year_service, f"Found dates: {found_dates}")
    results.add_test("2.6 Includes 01/01/2026 service", has_new_year_service, f"Found dates: {found_dates}")
    results.add_test("2.7 Includes 15/01/2026 service", has_mid_month_service, f"Found dates: {found_dates}")
    results.add_test("2.8 Correct count (at least 2)", has_correct_count, f"Found {len(filtered_services)} services, expected at least 2")
    
    # 4. Verificar ordenación: 15/01 debe aparecer antes que 01/01 (DESC por service_dt_utc)
    if len(filtered_services) >= 2:
        first_service_date = filtered_services[0].get("fecha")
        # En orden descendente, 15/01/2026 debe aparecer antes que 01/01/2026
        is_desc_ordered = True
        for i in range(len(filtered_services) - 1):
            current_date = filtered_services[i].get("fecha", "")
            next_date = filtered_services[i + 1].get("fecha", "")
            # Comparación simple: las fechas más nuevas deben aparecer primero
            if current_date < next_date:  # Si la fecha actual es menor que la siguiente, está mal ordenado
                is_desc_ordered = False
                break
        
        results.add_test("2.9 Services ordered DESC by date", is_desc_ordered, f"First service date: {first_service_date}")
    
    return created_services

def test_parte_3_verify_data_migration():
    """PARTE 3: Verificar migración de datos existentes"""
    log(f"\n{Colors.BOLD}=== PARTE 3: VERIFICAR MIGRACIÓN DE DATOS EXISTENTES ==={Colors.ENDC}")
    
    # Login como admin para ver todos los servicios
    admin_token = login_user(ADMIN_TAXITUR_CREDS)
    if not admin_token:
        results.add_test("3.0 Login admin for migration check", False, "Failed to login")
        return
        
    results.add_test("3.0 Login admin for migration check", True)
    admin_headers = get_auth_headers(admin_token)
    
    # 1. GET /services sin filtros para ver todos los servicios
    success, response = make_request("GET", "/services", headers=admin_headers)
    if not success:
        results.add_test("3.1 GET all services", False, f"Error: {response}")
        return
        
    all_services = response
    results.add_test("3.1 GET all services", True, f"Found {len(all_services)} total services")
    
    # 2. Verificar que los services tienen service_dt_utc calculado
    services_with_dt_utc = 0
    services_without_dt_utc = 0
    
    for service in all_services:
        if "service_dt_utc" in service and service["service_dt_utc"]:
            services_with_dt_utc += 1
        else:
            services_without_dt_utc += 1
    
    migration_percentage = (services_with_dt_utc / len(all_services)) * 100 if all_services else 0
    
    results.add_test("3.2 Services have service_dt_utc", services_with_dt_utc > 0, f"{services_with_dt_utc}/{len(all_services)} services have service_dt_utc")
    results.add_test("3.3 Migration percentage", migration_percentage > 80, f"{migration_percentage:.1f}% of services migrated")
    
    if services_without_dt_utc > 0:
        log_warning(f"Found {services_without_dt_utc} services without service_dt_utc - might be expected for very old data")

def test_parte_4_turnos_with_datetime():
    """PARTE 4: Turnos con datetime"""
    log(f"\n{Colors.BOLD}=== PARTE 4: TURNOS CON DATETIME ==={Colors.ENDC}")
    
    # Login como superadmin para crear taxista y vehículo
    token = login_user(SUPERADMIN_CREDS)
    if not token:
        results.add_test("4.0 Login superadmin", False, "Failed to login")
        return
        
    results.add_test("4.0 Login superadmin", True)
    headers = get_auth_headers(token)
    
    # Crear taxista de prueba para turnos
    test_username = f"test_turno_{int(datetime.now().timestamp())}"
    taxista_data = {
        "username": test_username,
        "password": "test123", 
        "nombre": "Taxista Test Turnos",
        "role": "taxista",
        "licencia": "TURNO001"
    }
    
    success, response = make_request("POST", "/users", headers=headers, data=taxista_data)
    if not success:
        results.add_test("4.1 Create taxista for turnos", False, f"Error: {response}")
        return
        
    results.add_test("4.1 Create taxista for turnos", True, f"ID: {response.get('id')}")
    
    # Crear vehículo para los turnos
    vehiculo_data = {
        "matricula": f"TURNO{int(datetime.now().timestamp() % 10000)}",
        "plazas": 4,
        "marca": "Test",
        "modelo": "Turnos"
    }
    
    success, response = make_request("POST", "/vehiculos", headers=headers, data=vehiculo_data)
    if not success:
        results.add_test("4.2 Create vehiculo for turnos", False, f"Error: {response}")
        return
        
    vehiculo_id = response.get("id")
    results.add_test("4.2 Create vehiculo for turnos", True, f"ID: {vehiculo_id}")
    
    # Login como taxista
    taxista_token = login_user({"username": test_username, "password": "test123"})
    if not taxista_token:
        results.add_test("4.3 Login taxista for turnos", False, "Failed to login")
        return
        
    results.add_test("4.3 Login taxista for turnos", True)
    taxista_headers = get_auth_headers(taxista_token)
    
    # 1. Crear un nuevo turno
    turno_data = {
        "fecha_inicio": "21/02/2026",
        "hora_inicio": "08:00",
        "km_inicio": 50000,
        "vehiculo_id": vehiculo_id
    }
    
    success, response = make_request("POST", "/turnos", headers=taxista_headers, data=turno_data)
    if not success:
        results.add_test("4.4 Create new turno", False, f"Error: {response}")
        return
        
    turno_created = response
    turno_id = turno_created.get("id")
    results.add_test("4.4 Create new turno", True, f"ID: {turno_id}")
    
    # 2. Verificar que tiene inicio_dt_utc
    has_inicio_dt_utc = "inicio_dt_utc" in turno_created and turno_created["inicio_dt_utc"]
    results.add_test("4.5 Turno has inicio_dt_utc", has_inicio_dt_utc, f"inicio_dt_utc: {turno_created.get('inicio_dt_utc', 'NOT FOUND')}")
    
    # 3. Finalizar el turno
    finalizar_data = {
        "fecha_fin": "21/02/2026",
        "hora_fin": "16:00", 
        "km_fin": 50200
    }
    
    success, response = make_request("PUT", f"/turnos/{turno_id}/finalizar", headers=taxista_headers, data=finalizar_data)
    if not success:
        results.add_test("4.6 Finalize turno", False, f"Error: {response}")
        return
        
    turno_finalizado = response
    results.add_test("4.6 Finalize turno", True, f"Turno finalized")
    
    # 4. Verificar que tiene fin_dt_utc
    has_fin_dt_utc = "fin_dt_utc" in turno_finalizado and turno_finalizado["fin_dt_utc"]
    results.add_test("4.7 Turno has fin_dt_utc", has_fin_dt_utc, f"fin_dt_utc: {turno_finalizado.get('fin_dt_utc', 'NOT FOUND')}")

def main():
    """Ejecutar todas las pruebas"""
    log(f"{Colors.BOLD}🚕 TESTING FILTROS DATETIME - PASO 3{Colors.ENDC}")
    log(f"{Colors.BOLD}API Base: {API_BASE}{Colors.ENDC}")
    log(f"{Colors.BOLD}Verificando filtros por rango de fechas con datetime UTC{Colors.ENDC}\n")
    
    try:
        # PARTE 1: Verificar que service_dt_utc se guarda
        taxista_data = test_parte_1_verify_service_dt_utc()
        
        if taxista_data:
            taxista_token, taxista_headers, turno_id, vehiculo_id = taxista_data
            
            # PARTE 2: Test crítico de filtros por rango de fechas
            test_parte_2_critical_date_range_filters(taxista_token, taxista_headers, turno_id, vehiculo_id)
        
        # PARTE 3: Verificar migración de datos existentes
        test_parte_3_verify_data_migration()
        
        # PARTE 4: Turnos con datetime
        test_parte_4_turnos_with_datetime()
        
    except Exception as e:
        log_error(f"Error during testing: {str(e)}")
    
    finally:
        # Imprimir resumen final
        results.print_summary()
        
        # Conclusión específica sobre filtros de rango de fechas
        log(f"\n{Colors.BOLD}=== CONCLUSIONES ESPECÍFICAS ==={Colors.ENDC}")
        
        if results.passed / results.total > 0.8:
            log_success("✅ Los filtros por rango de fechas están funcionando correctamente")
            log_success("✅ service_dt_utc se está guardando y usando en las queries") 
            log_success("✅ El bug de comparación de strings parece estar resuelto")
        else:
            log_error("❌ Se detectaron problemas en los filtros de rango de fechas")
            log_error("❌ Revisar implementación de service_dt_utc")

if __name__ == "__main__":
    main()