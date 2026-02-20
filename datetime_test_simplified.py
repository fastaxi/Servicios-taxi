#!/usr/bin/env python3
"""
TESTING FILTROS DATETIME - PASO 3 - SIMPLIFIED
Test crítico de filtros por rango de fechas
"""
import requests
import json
from datetime import datetime
import sys

# API Configuration  
API_BASE = "https://flagged-services.preview.emergentagent.com/api"
ADMIN_TAXITUR_CREDS = {"username": "admintur", "password": "admin123"}

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def log_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.ENDC}")

def log_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.ENDC}")

def log_info(message):
    print(f"{Colors.BLUE}ℹ️ {message}{Colors.ENDC}")

def make_request(method, endpoint, headers=None, data=None):
    """Helper function to make HTTP requests"""
    url = f"{API_BASE}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, params=data)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data)
        
        return response.status_code, response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
    except Exception as e:
        return 500, f"Request failed: {str(e)}"

def main():
    print(f"{Colors.BOLD}🚕 TESTING FILTROS DATETIME - PASO 3{Colors.ENDC}")
    print(f"{Colors.BOLD}Enfoque en el test crítico de filtros por rango de fechas{Colors.ENDC}\n")
    
    # Login
    status, response = make_request("POST", "/auth/login", data=ADMIN_TAXITUR_CREDS)
    if status != 200:
        log_error(f"Login failed: {response}")
        sys.exit(1)
    
    token = response["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    log_success("Login admin successful")
    
    print(f"\n{Colors.BOLD}=== PARTE 1: VERIFICAR SERVICIOS EXISTENTES ==={Colors.ENDC}")
    
    # Get all services to see structure
    status, services = make_request("GET", "/services", headers=headers)
    if status != 200:
        log_error(f"Failed to get services: {services}")
        sys.exit(1)
    
    log_info(f"Found {len(services)} services")
    
    # Check if service_dt_utc exists in services
    services_with_dt_utc = 0
    services_without_dt_utc = 0
    
    for i, service in enumerate(services[:5]):  # Check first 5 services
        has_dt_utc = 'service_dt_utc' in service
        if has_dt_utc:
            services_with_dt_utc += 1
            log_info(f"Service {i+1}: fecha={service.get('fecha')}, service_dt_utc={service.get('service_dt_utc')}")
        else:
            services_without_dt_utc += 1
            log_info(f"Service {i+1}: fecha={service.get('fecha')}, NO service_dt_utc")
    
    log_info(f"Services with service_dt_utc: {services_with_dt_utc}/{len(services[:5])}")
    
    print(f"\n{Colors.BOLD}=== PARTE 2: CREAR SERVICIOS DE PRUEBA ==={Colors.ENDC}")
    
    # Get available turno and vehiculo
    status, vehiculos = make_request("GET", "/vehiculos", headers=headers)
    if status != 200 or not vehiculos:
        log_error(f"No vehicles available: {vehiculos}")
        sys.exit(1)
        
    vehiculo_id = vehiculos[0]['id']
    log_info(f"Using vehicle: {vehiculos[0]['matricula']}")
    
    # Check if there's an active turno
    status, turno_response = make_request("GET", "/turnos/activo", headers=headers)
    turno_id = None
    
    if status == 404 or not turno_response:
        # Create a turno
        turno_data = {
            "fecha_inicio": "20/02/2026",
            "hora_inicio": "08:00",
            "km_inicio": 100000,
            "vehiculo_id": vehiculo_id
        }
        status, response = make_request("POST", "/turnos", headers=headers, data=turno_data)
        if status == 200:
            turno_id = response['id']
            log_success(f"Created turno: {turno_id}")
        else:
            log_error(f"Failed to create turno: {response}")
            # Continue without turno_id for admin testing
    elif status == 200 and turno_response:
        turno_id = turno_response['id']
        log_success(f"Using existing active turno: {turno_id}")
    
    # Create test services with specific dates - KEY TEST
    test_services = [
        {
            "fecha": "31/12/2025", 
            "hora": "23:50",
            "origen": "Test Service 1 - Old Year",
            "destino": "Destination 1",
            "importe": 10.0,
            "tipo": "particular"
        },
        {
            "fecha": "01/01/2026",
            "hora": "00:10", 
            "origen": "Test Service 2 - New Year",
            "destino": "Destination 2",
            "importe": 20.0,
            "tipo": "particular"
        },
        {
            "fecha": "15/01/2026",
            "hora": "12:00",
            "origen": "Test Service 3 - Mid Month", 
            "destino": "Destination 3",
            "importe": 30.0,
            "tipo": "particular"
        }
    ]
    
    created_services = []
    for i, service_data in enumerate(test_services):
        if turno_id:
            service_data["turno_id"] = turno_id
            
        status, response = make_request("POST", "/services", headers=headers, data=service_data)
        if status == 200:
            created_services.append(response)
            has_dt_utc = 'service_dt_utc' in response
            log_success(f"Created service {i+1}: {service_data['fecha']}, service_dt_utc: {has_dt_utc}")
            if has_dt_utc:
                log_info(f"  service_dt_utc value: {response.get('service_dt_utc')}")
        else:
            log_error(f"Failed to create service {i+1}: {response}")
    
    print(f"\n{Colors.BOLD}=== PARTE 3: TEST CRÍTICO - FILTRO POR RANGO DE FECHAS ==={Colors.ENDC}")
    
    # The critical test: fecha_inicio=01/01/2026&fecha_fin=31/01/2026
    test_params = {
        "fecha_inicio": "01/01/2026",
        "fecha_fin": "31/01/2026"
    }
    
    status, filtered_services = make_request("GET", "/services", headers=headers, data=test_params)
    if status != 200:
        log_error(f"Date filter failed: {filtered_services}")
        sys.exit(1)
    
    log_info(f"Filter query: {test_params}")
    log_info(f"Found {len(filtered_services)} services with date filter")
    
    # Analysis of results
    found_dates = []
    services_with_dt_utc_in_filter = 0
    
    for service in filtered_services:
        fecha = service.get('fecha')
        found_dates.append(fecha)
        if 'service_dt_utc' in service:
            services_with_dt_utc_in_filter += 1
    
    log_info(f"Dates found: {found_dates}")
    log_info(f"Services with service_dt_utc in filtered results: {services_with_dt_utc_in_filter}/{len(filtered_services)}")
    
    # Check for the bug: should NOT include 31/12/2025
    has_old_year_service = any(fecha == "31/12/2025" for fecha in found_dates)
    has_new_year_service = any(fecha == "01/01/2026" for fecha in found_dates) 
    has_mid_month_service = any(fecha == "15/01/2026" for fecha in found_dates)
    
    print(f"\n{Colors.BOLD}=== RESULTADO DEL TEST CRÍTICO ==={Colors.ENDC}")
    
    if has_old_year_service:
        log_error("BUG DETECTADO: El servicio de 31/12/2025 aparece en el filtro 01/01/2026-31/01/2026")
        log_error("Esto indica que los filtros siguen usando comparación de strings en lugar de datetime UTC")
    else:
        log_success("CORRECTO: El servicio de 31/12/2025 NO aparece en el filtro")
    
    if has_new_year_service:
        log_success("CORRECTO: El servicio de 01/01/2026 aparece en el filtro")
    else:
        log_error("PROBLEMA: El servicio de 01/01/2026 NO aparece en el filtro")
    
    if has_mid_month_service:
        log_success("CORRECTO: El servicio de 15/01/2026 aparece en el filtro") 
    else:
        log_error("PROBLEMA: El servicio de 15/01/2026 NO aparece en el filtro")
    
    print(f"\n{Colors.BOLD}=== VERIFICACIÓN DE ORDENACIÓN ==={Colors.ENDC}")
    
    if len(filtered_services) >= 2:
        # Check ordering - should be DESC by service_dt_utc or date
        fechas_ordenadas = [s.get('fecha') for s in filtered_services]
        log_info(f"Orden de fechas en resultado: {fechas_ordenadas}")
        
        # Simple check: more recent dates should appear first
        is_properly_ordered = True
        for i in range(len(fechas_ordenadas) - 1):
            current = fechas_ordenadas[i]
            next_date = fechas_ordenadas[i + 1]
            # 15/01/2026 should come before 01/01/2026 in DESC order
            if current == "01/01/2026" and next_date == "15/01/2026":
                is_properly_ordered = False
                break
        
        if is_properly_ordered:
            log_success("ORDENACIÓN CORRECTA: Servicios ordenados por fecha descendente")
        else:
            log_error("PROBLEMA DE ORDENACIÓN: Los servicios no están correctamente ordenados")
    
    # Final summary
    print(f"\n{Colors.BOLD}=== RESUMEN FINAL ==={Colors.ENDC}")
    
    migration_ok = services_with_dt_utc_in_filter > 0
    filter_ok = not has_old_year_service and has_new_year_service and has_mid_month_service
    
    if migration_ok and filter_ok:
        log_success("✅ FILTROS DE FECHA FUNCIONANDO CORRECTAMENTE")
        log_success("✅ service_dt_utc implementado y funcionando") 
        log_success("✅ Bug de comparación de strings RESUELTO")
        print(f"\n{Colors.GREEN}🎉 PASO 3 COMPLETADO EXITOSAMENTE{Colors.ENDC}")
    else:
        if not migration_ok:
            log_error("❌ service_dt_utc no está siendo usado en los filtros")
        if not filter_ok:
            log_error("❌ Los filtros de fecha no funcionan correctamente")  
            log_error("❌ Posible bug de comparación de strings persiste")
        print(f"\n{Colors.RED}⚠️ SE REQUIEREN AJUSTES EN LA IMPLEMENTACIÓN{Colors.ENDC}")

if __name__ == "__main__":
    main()