#!/usr/bin/env python3
"""
Backend Testing Suite for PR1 New Functionalities
Testing exhaustive scenarios for Taxitur-specific features and new endpoints
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "https://taxiflow-18.preview.emergentagent.com/api"
TAXITUR_ORG_ID = "69484bec187c3bc2b0fdb8f4"

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.tokens = {}
        self.test_data = {}
        self.results = []
        
    def log_test(self, name: str, method: str, endpoint: str, status_code: int, expected: int, details: str = ""):
        """Log test result"""
        passed = status_code == expected
        result = "✅ PASS" if passed else "❌ FAIL"
        self.results.append({
            "name": name,
            "method": method,
            "endpoint": endpoint,
            "status_code": status_code,
            "expected": expected,
            "result": result,
            "details": details
        })
        print(f"{result} | {name} | {method} {endpoint} | {status_code} (expected {expected}) | {details}")
        
    def login(self, username: str, password: str) -> Optional[str]:
        """Login and return token"""
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", json={
                "username": username,
                "password": password
            })
            if response.status_code == 200:
                data = response.json()
                token = data["access_token"]
                self.tokens[username] = token
                return token
            return None
        except Exception as e:
            print(f"Login failed for {username}: {e}")
            return None
    
    def make_request(self, method: str, endpoint: str, token: str = None, **kwargs) -> requests.Response:
        """Make authenticated request"""
        headers = kwargs.get('headers', {})
        if token:
            headers['Authorization'] = f'Bearer {token}'
        kwargs['headers'] = headers
        
        url = f"{BASE_URL}{endpoint}"
        return getattr(self.session, method.lower())(url, **kwargs)
    
    def setup_test_data(self):
        """Setup test organizations, users, and vehicles"""
        print("\n🔧 SETTING UP TEST DATA...")
        
        # Login as superadmin to create test data
        superadmin_token = self.login("superadmin", "superadmin123")
        if not superadmin_token:
            print("❌ Failed to login as superadmin")
            return False
            
        # Create Taxitur organization (if not exists)
        taxitur_org = {
            "nombre": "Taxitur Test",
            "slug": "taxitur-test",
            "cif": "B12345678",
            "activa": True
        }
        
        # Create Non-Taxitur organization
        other_org = {
            "nombre": "Radio Taxi Madrid Test",
            "slug": "radio-taxi-madrid-test", 
            "cif": "B87654321",
            "activa": True
        }
        
        # Try to create organizations
        for org_name, org_data in [("taxitur", taxitur_org), ("other", other_org)]:
            response = self.make_request("POST", "/organizations", superadmin_token, json=org_data)
            if response.status_code in [200, 201]:
                org_id = response.json()["id"]
                self.test_data[f"{org_name}_org_id"] = org_id
                print(f"✅ Created {org_name} organization: {org_id}")
            else:
                # Try to find existing organization
                response = self.make_request("GET", "/organizations", superadmin_token)
                if response.status_code == 200:
                    orgs = response.json()
                    for org in orgs:
                        if org_data["slug"] in org.get("slug", ""):
                            self.test_data[f"{org_name}_org_id"] = org["id"]
                            print(f"✅ Found existing {org_name} organization: {org['id']}")
                            break
        
        # Override Taxitur org ID with the configured one
        self.test_data["taxitur_org_id"] = TAXITUR_ORG_ID
        
        # Create test vehicles for each organization
        for org_type in ["taxitur", "other"]:
            org_id = self.test_data.get(f"{org_type}_org_id")
            if org_id:
                vehicle_data = {
                    "matricula": f"TEST{org_type.upper()}123",
                    "marca": "Toyota",
                    "modelo": "Prius",
                    "licencia": f"LIC{org_type.upper()}123",
                    "plazas": 4,
                    "km_iniciales": 50000,
                    "fecha_compra": "01/01/2020",
                    "activo": True,
                    "organization_id": org_id
                }
                
                response = self.make_request("POST", "/superadmin/vehiculos", superadmin_token, json=vehicle_data)
                if response.status_code in [200, 201]:
                    vehicle_id = response.json()["id"]
                    self.test_data[f"{org_type}_vehicle_id"] = vehicle_id
                    print(f"✅ Created {org_type} vehicle: {vehicle_id}")
        
        # Create test taxistas for each organization
        for org_type in ["taxitur", "other"]:
            org_id = self.test_data.get(f"{org_type}_org_id")
            if org_id:
                taxista_data = {
                    "username": f"taxista_{org_type}_test",
                    "password": "test123",
                    "nombre": f"Taxista {org_type.title()} Test",
                    "telefono": "666777888",
                    "email": f"taxista_{org_type}@test.com",
                    "licencia": f"LIC{org_type.upper()}456",
                    "activo": True,
                    "organization_id": org_id
                }
                
                response = self.make_request("POST", "/superadmin/taxistas", superadmin_token, json=taxista_data)
                if response.status_code in [200, 201]:
                    taxista_id = response.json()["id"]
                    self.test_data[f"{org_type}_taxista_id"] = taxista_id
                    
                    # Assign vehicle to taxista
                    vehicle_id = self.test_data.get(f"{org_type}_vehicle_id")
                    if vehicle_id:
                        assign_data = {"vehiculo_id": vehicle_id}
                        self.make_request("PUT", f"/superadmin/taxistas/{taxista_id}/vehiculo", 
                                        superadmin_token, json=assign_data)
                    
                    print(f"✅ Created {org_type} taxista: {taxista_id}")
                    
                    # Login taxista to get token
                    token = self.login(f"taxista_{org_type}_test", "test123")
                    if token:
                        self.test_data[f"{org_type}_taxista_token"] = token
        
        # Create admin tokens
        admin_token = self.login("admin", "admin123")
        if admin_token:
            self.test_data["admin_token"] = admin_token
            
        return True
    
    def test_taxitur_origen_obligatorio(self):
        """Test Case 1: TAXITUR - Origen obligatorio"""
        print("\n🎯 TEST CASE 1: TAXITUR - Origen obligatorio")
        
        taxitur_token = self.test_data.get("taxitur_taxista_token")
        other_token = self.test_data.get("other_taxista_token")
        
        if not taxitur_token or not other_token:
            print("❌ Missing taxista tokens for testing")
            return
            
        # First create active turnos for both taxistas
        for org_type, token in [("taxitur", taxitur_token), ("other", other_token)]:
            vehicle_id = self.test_data.get(f"{org_type}_vehicle_id")
            if vehicle_id:
                turno_data = {
                    "taxista_id": self.test_data.get(f"{org_type}_taxista_id"),
                    "taxista_nombre": f"Taxista {org_type.title()} Test",
                    "vehiculo_id": vehicle_id,
                    "vehiculo_matricula": f"TEST{org_type.upper()}123",
                    "fecha_inicio": datetime.now().strftime("%d/%m/%Y"),
                    "hora_inicio": "08:00",
                    "km_inicio": 100000
                }
                
                response = self.make_request("POST", "/turnos", token, json=turno_data)
                if response.status_code in [200, 201]:
                    self.test_data[f"{org_type}_turno_id"] = response.json()["id"]
        
        # 1.1 Crear servicio SIN origen_taxitur en org Taxitur → Debe devolver 400/422
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
            # NO incluir origen_taxitur
        }
        
        response = self.make_request("POST", "/services", taxitur_token, json=service_data)
        self.log_test(
            "1.1 Crear servicio SIN origen_taxitur en org Taxitur",
            "POST", "/services", 
            response.status_code, 400,
            "Debe rechazar servicio sin origen_taxitur en organización Taxitur"
        )
        
        # 1.2 Crear servicio CON origen_taxitur="parada" en org Taxitur → Debe devolver 200/201
        service_data["origen_taxitur"] = "parada"
        response = self.make_request("POST", "/services", taxitur_token, json=service_data)
        self.log_test(
            "1.2 Crear servicio CON origen_taxitur='parada' en org Taxitur",
            "POST", "/services",
            response.status_code, 201,
            "Debe aceptar servicio con origen_taxitur='parada'"
        )
        
        # 1.3 Crear servicio CON origen_taxitur="lagos" en org Taxitur → Debe devolver 200/201
        service_data["origen_taxitur"] = "lagos"
        response = self.make_request("POST", "/services", taxitur_token, json=service_data)
        self.log_test(
            "1.3 Crear servicio CON origen_taxitur='lagos' en org Taxitur",
            "POST", "/services",
            response.status_code, 201,
            "Debe aceptar servicio con origen_taxitur='lagos'"
        )
        
        # 1.4 Crear servicio CON origen_taxitur en org NO-Taxitur → Debe devolver 400
        service_data["origen_taxitur"] = "parada"
        response = self.make_request("POST", "/services", other_token, json=service_data)
        self.log_test(
            "1.4 Crear servicio CON origen_taxitur en org NO-Taxitur",
            "POST", "/services",
            response.status_code, 400,
            "Debe rechazar campo origen_taxitur fuera de organización Taxitur"
        )
    
    def test_vehiculo_cambiado_kilometros(self):
        """Test Case 2: VEHÍCULO CAMBIADO - Kilómetros condicionales"""
        print("\n🎯 TEST CASE 2: VEHÍCULO CAMBIADO - Kilómetros condicionales")
        
        taxitur_token = self.test_data.get("taxitur_taxista_token")
        if not taxitur_token:
            print("❌ Missing taxitur taxista token")
            return
            
        # Create a different vehicle for testing
        admin_token = self.test_data.get("admin_token")
        if admin_token:
            different_vehicle = {
                "matricula": "TESTDIFF456",
                "marca": "Ford",
                "modelo": "Focus",
                "plazas": 4,
                "km_iniciales": 75000,
                "fecha_compra": "01/06/2021",
                "activo": True
            }
            
            response = self.make_request("POST", "/vehiculos", admin_token, json=different_vehicle)
            if response.status_code in [200, 201]:
                different_vehicle_id = response.json()["id"]
                self.test_data["different_vehicle_id"] = different_vehicle_id
        
        different_vehicle_id = self.test_data.get("different_vehicle_id")
        default_vehicle_id = self.test_data.get("taxitur_vehicle_id")
        
        if not different_vehicle_id or not default_vehicle_id:
            print("❌ Missing vehicle IDs for testing")
            return
        
        # 2.1 Crear servicio con vehículo diferente SIN km_inicio_vehiculo/km_fin_vehiculo → 400/422
        service_data = {
            "fecha": datetime.now().strftime("%d/%m/%Y"),
            "hora": "11:00",
            "origen": "Centro",
            "destino": "Hospital",
            "importe": 18.75,
            "importe_espera": 2.50,
            "kilometros": 8.5,
            "tipo": "particular",
            "metodo_pago": "efectivo",
            "origen_taxitur": "parada",
            "vehiculo_id": different_vehicle_id,
            "vehiculo_cambiado": True
            # NO incluir km_inicio_vehiculo/km_fin_vehiculo
        }
        
        response = self.make_request("POST", "/services", taxitur_token, json=service_data)
        self.log_test(
            "2.1 Crear servicio con vehículo diferente SIN km campos",
            "POST", "/services",
            response.status_code, 400,
            "Debe rechazar servicio con vehículo cambiado sin km_inicio/fin_vehiculo"
        )
        
        # 2.2 Crear servicio con vehículo diferente y km_fin < km_inicio → 400/422
        service_data.update({
            "km_inicio_vehiculo": 75500,
            "km_fin_vehiculo": 75400  # Menor que inicio
        })
        
        response = self.make_request("POST", "/services", taxitur_token, json=service_data)
        self.log_test(
            "2.2 Crear servicio con km_fin < km_inicio",
            "POST", "/services",
            response.status_code, 400,
            "Debe rechazar servicio con km_fin menor que km_inicio"
        )
        
        # 2.3 Crear servicio con vehículo diferente y km válidos → 200/201
        service_data.update({
            "km_inicio_vehiculo": 75500,
            "km_fin_vehiculo": 75510  # Mayor que inicio
        })
        
        response = self.make_request("POST", "/services", taxitur_token, json=service_data)
        self.log_test(
            "2.3 Crear servicio con vehículo diferente y km válidos",
            "POST", "/services",
            response.status_code, 201,
            "Debe aceptar servicio con vehículo cambiado y km válidos"
        )
        
        # 2.4 Crear servicio con mismo vehículo del turno → 200/201
        service_data_same = {
            "fecha": datetime.now().strftime("%d/%m/%Y"),
            "hora": "12:00",
            "origen": "Estación",
            "destino": "Universidad",
            "importe": 12.30,
            "importe_espera": 0,
            "kilometros": 6.8,
            "tipo": "particular",
            "metodo_pago": "tpv",
            "origen_taxitur": "lagos",
            "vehiculo_id": default_vehicle_id,
            "vehiculo_cambiado": False
            # No necesita km_inicio/fin_vehiculo
        }
        
        response = self.make_request("POST", "/services", taxitur_token, json=service_data_same)
        self.log_test(
            "2.4 Crear servicio con mismo vehículo del turno",
            "POST", "/services",
            response.status_code, 201,
            "Debe aceptar servicio con vehículo por defecto sin km extra"
        )
    
    def test_combustible_repostaje(self):
        """Test Case 3: COMBUSTIBLE - Repostaje en turnos"""
        print("\n🎯 TEST CASE 3: COMBUSTIBLE - Repostaje en turnos")
        
        taxitur_token = self.test_data.get("taxitur_taxista_token")
        turno_id = self.test_data.get("taxitur_turno_id")
        vehicle_id = self.test_data.get("taxitur_vehicle_id")
        
        if not all([taxitur_token, turno_id, vehicle_id]):
            print("❌ Missing required data for combustible testing")
            return
        
        # 3.1 PUT /api/turnos/{id}/combustible en turno ACTIVO → 200
        combustible_data = {
            "repostado": True,
            "litros": 45.5,
            "vehiculo_id": vehicle_id,
            "km_vehiculo": 100150
        }
        
        response = self.make_request("PUT", f"/turnos/{turno_id}/combustible", taxitur_token, json=combustible_data)
        self.log_test(
            "3.1 PUT combustible en turno ACTIVO",
            "PUT", f"/turnos/{turno_id}/combustible",
            response.status_code, 200,
            "Debe permitir registrar combustible en turno activo"
        )
        
        # 3.2 Finalizar turno con PUT /api/turnos/{id}/finalizar → 200
        finalizar_data = {
            "fecha_fin": datetime.now().strftime("%d/%m/%Y"),
            "hora_fin": "18:00",
            "km_fin": 100200,
            "cerrado": True
        }
        
        response = self.make_request("PUT", f"/turnos/{turno_id}/finalizar", taxitur_token, json=finalizar_data)
        self.log_test(
            "3.2 Finalizar turno",
            "PUT", f"/turnos/{turno_id}/finalizar",
            response.status_code, 200,
            "Debe permitir finalizar turno"
        )
        
        # 3.3 Intentar PUT /api/turnos/{id}/combustible en turno YA CERRADO → 403/400
        response = self.make_request("PUT", f"/turnos/{turno_id}/combustible", taxitur_token, json=combustible_data)
        self.log_test(
            "3.3 PUT combustible en turno YA CERRADO",
            "PUT", f"/turnos/{turno_id}/combustible",
            response.status_code, 403,
            "Debe bloquear registro de combustible en turno cerrado"
        )
    
    def test_server_time(self):
        """Test Case 4: SERVER TIME - Hora del servidor"""
        print("\n🎯 TEST CASE 4: SERVER TIME - Hora del servidor")
        
        other_token = self.test_data.get("other_taxista_token")
        other_vehicle_id = self.test_data.get("other_vehicle_id")
        other_taxista_id = self.test_data.get("other_taxista_id")
        
        if not all([other_token, other_vehicle_id, other_taxista_id]):
            print("❌ Missing required data for server time testing")
            return
        
        # 4.1 POST /api/turnos con hora_inicio personalizada → Backend debe IGNORAR
        custom_time = "06:30"  # Hora personalizada del cliente
        turno_data = {
            "taxista_id": other_taxista_id,
            "taxista_nombre": "Taxista Other Test",
            "vehiculo_id": other_vehicle_id,
            "vehiculo_matricula": "TESTOTHER123",
            "fecha_inicio": datetime.now().strftime("%d/%m/%Y"),
            "hora_inicio": custom_time,  # Esta debe ser ignorada
            "km_inicio": 50100
        }
        
        response = self.make_request("POST", "/turnos", other_token, json=turno_data)
        if response.status_code in [200, 201]:
            turno_created = response.json()
            server_time = turno_created.get("hora_inicio", "")
            
            # Verificar que la hora del servidor es diferente a la enviada
            time_ignored = server_time != custom_time
            self.log_test(
                "4.1 POST turnos ignora hora_inicio del cliente",
                "POST", "/turnos",
                response.status_code, 201,
                f"Hora servidor: {server_time}, Cliente: {custom_time}, Ignorada: {time_ignored}"
            )
            
            new_turno_id = turno_created["id"]
            self.test_data["other_turno_id"] = new_turno_id
            
            # 4.2 PUT /api/turnos/{id}/finalizar con hora_fin personalizada → Backend debe IGNORAR
            custom_end_time = "23:45"  # Hora personalizada del cliente
            finalizar_data = {
                "fecha_fin": datetime.now().strftime("%d/%m/%Y"),
                "hora_fin": custom_end_time,  # Esta debe ser ignorada
                "km_fin": 50250,
                "cerrado": True
            }
            
            response = self.make_request("PUT", f"/turnos/{new_turno_id}/finalizar", other_token, json=finalizar_data)
            if response.status_code == 200:
                turno_finalizado = response.json()
                server_end_time = turno_finalizado.get("hora_fin", "")
                
                # Verificar que la hora del servidor es diferente a la enviada
                end_time_ignored = server_end_time != custom_end_time
                self.log_test(
                    "4.2 PUT finalizar ignora hora_fin del cliente",
                    "PUT", f"/turnos/{new_turno_id}/finalizar",
                    response.status_code, 200,
                    f"Hora servidor: {server_end_time}, Cliente: {custom_end_time}, Ignorada: {end_time_ignored}"
                )
            else:
                self.log_test(
                    "4.2 PUT finalizar ignora hora_fin del cliente",
                    "PUT", f"/turnos/{new_turno_id}/finalizar",
                    response.status_code, 200,
                    "Error al finalizar turno"
                )
        else:
            self.log_test(
                "4.1 POST turnos ignora hora_inicio del cliente",
                "POST", "/turnos",
                response.status_code, 201,
                "Error al crear turno para test de server time"
            )
    
    def test_exports_nuevas_columnas(self):
        """Test Case 5: EXPORTS - Columnas nuevas y org_filter"""
        print("\n🎯 TEST CASE 5: EXPORTS - Columnas nuevas y org_filter")
        
        admin_token = self.test_data.get("admin_token")
        if not admin_token:
            print("❌ Missing admin token for exports testing")
            return
        
        # 5.1 GET /api/services/export/csv → Debe incluir columnas nuevas
        response = self.make_request("GET", "/services/export/csv", admin_token)
        if response.status_code == 200:
            csv_content = response.text
            required_columns = ["metodo_pago", "origen_taxitur", "vehiculo_matricula", "km_inicio_vehiculo", "km_fin_vehiculo"]
            columns_found = all(col in csv_content for col in required_columns)
            
            self.log_test(
                "5.1 GET services/export/csv incluye columnas nuevas",
                "GET", "/services/export/csv",
                response.status_code, 200,
                f"Columnas encontradas: {columns_found}, Content-Length: {len(csv_content)}"
            )
        else:
            self.log_test(
                "5.1 GET services/export/csv incluye columnas nuevas",
                "GET", "/services/export/csv",
                response.status_code, 200,
                "Error al obtener CSV de servicios"
            )
        
        # 5.2 GET /api/services/export/excel → Debe incluir las mismas columnas nuevas
        response = self.make_request("GET", "/services/export/excel", admin_token)
        self.log_test(
            "5.2 GET services/export/excel incluye columnas nuevas",
            "GET", "/services/export/excel",
            response.status_code, 200,
            f"Content-Type: {response.headers.get('content-type', 'N/A')}, Size: {len(response.content)} bytes"
        )
        
        # 5.3 GET /api/turnos/export/csv → Debe incluir columnas de combustible
        response = self.make_request("GET", "/turnos/export/csv", admin_token)
        if response.status_code == 200:
            csv_content = response.text
            combustible_columns = ["combustible_repostado", "combustible_litros", "combustible_vehiculo", "combustible_km"]
            combustible_found = any(col in csv_content for col in combustible_columns)
            
            self.log_test(
                "5.3 GET turnos/export/csv incluye columnas combustible",
                "GET", "/turnos/export/csv",
                response.status_code, 200,
                f"Columnas combustible encontradas: {combustible_found}, Content-Length: {len(csv_content)}"
            )
        else:
            self.log_test(
                "5.3 GET turnos/export/csv incluye columnas combustible",
                "GET", "/turnos/export/csv",
                response.status_code, 200,
                "Error al obtener CSV de turnos"
            )
    
    def test_estadisticas_combustible(self):
        """Test Case 6: ENDPOINT DE ESTADÍSTICAS COMBUSTIBLE"""
        print("\n🎯 TEST CASE 6: ENDPOINT DE ESTADÍSTICAS COMBUSTIBLE")
        
        admin_token = self.test_data.get("admin_token")
        if not admin_token:
            print("❌ Missing admin token for statistics testing")
            return
        
        # 6.1 GET /api/turnos/combustible/estadisticas → Debe devolver estadísticas agregadas
        response = self.make_request("GET", "/turnos/combustible/estadisticas", admin_token)
        if response.status_code == 200:
            stats = response.json()
            required_fields = ["total_repostajes", "total_litros", "promedio_litros"]
            fields_present = all(field in stats for field in required_fields)
            
            self.log_test(
                "6.1 GET turnos/combustible/estadisticas",
                "GET", "/turnos/combustible/estadisticas",
                response.status_code, 200,
                f"Campos requeridos presentes: {fields_present}, Stats: {json.dumps(stats, indent=2)}"
            )
        else:
            self.log_test(
                "6.1 GET turnos/combustible/estadisticas",
                "GET", "/turnos/combustible/estadisticas",
                response.status_code, 200,
                f"Error al obtener estadísticas de combustible: {response.text}"
            )
    
    def test_metodo_pago(self):
        """Test Case 7: MÉTODO DE PAGO"""
        print("\n🎯 TEST CASE 7: MÉTODO DE PAGO")
        
        other_token = self.test_data.get("other_taxista_token")
        if not other_token:
            print("❌ Missing other taxista token for payment method testing")
            return
        
        # 7.1 Crear servicio con metodo_pago="efectivo" → 200/201
        service_efectivo = {
            "fecha": datetime.now().strftime("%d/%m/%Y"),
            "hora": "14:00",
            "origen": "Plaza España",
            "destino": "Centro Comercial",
            "importe": 15.80,
            "importe_espera": 1.20,
            "kilometros": 7.3,
            "tipo": "particular",
            "metodo_pago": "efectivo"
        }
        
        response = self.make_request("POST", "/services", other_token, json=service_efectivo)
        self.log_test(
            "7.1 Crear servicio con metodo_pago='efectivo'",
            "POST", "/services",
            response.status_code, 201,
            "Debe aceptar método de pago efectivo"
        )
        
        # 7.2 Crear servicio con metodo_pago="tpv" → 200/201
        service_tpv = {
            "fecha": datetime.now().strftime("%d/%m/%Y"),
            "hora": "15:00",
            "origen": "Hospital",
            "destino": "Residencia",
            "importe": 22.40,
            "importe_espera": 0,
            "kilometros": 11.8,
            "tipo": "empresa",
            "metodo_pago": "tpv"
        }
        
        response = self.make_request("POST", "/services", other_token, json=service_tpv)
        self.log_test(
            "7.2 Crear servicio con metodo_pago='tpv'",
            "POST", "/services",
            response.status_code, 201,
            "Debe aceptar método de pago TPV"
        )
        
        # 7.3 Filtrar servicios por metodo_pago → GET /api/services?metodo_pago=efectivo
        response = self.make_request("GET", "/services?metodo_pago=efectivo", other_token)
        if response.status_code == 200:
            services = response.json()
            efectivo_services = [s for s in services if s.get("metodo_pago") == "efectivo"]
            
            self.log_test(
                "7.3 Filtrar servicios por metodo_pago=efectivo",
                "GET", "/services?metodo_pago=efectivo",
                response.status_code, 200,
                f"Servicios encontrados: {len(services)}, Con efectivo: {len(efectivo_services)}"
            )
        else:
            self.log_test(
                "7.3 Filtrar servicios por metodo_pago=efectivo",
                "GET", "/services?metodo_pago=efectivo",
                response.status_code, 200,
                "Error al filtrar servicios por método de pago"
            )
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("📊 RESUMEN DE PRUEBAS EXHAUSTIVAS - PR1 NUEVAS FUNCIONALIDADES")
        print("="*80)
        
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if "PASS" in r["result"]])
        failed_tests = total_tests - passed_tests
        
        print(f"\n📈 ESTADÍSTICAS GENERALES:")
        print(f"   Total de pruebas: {total_tests}")
        print(f"   ✅ Exitosas: {passed_tests}")
        print(f"   ❌ Fallidas: {failed_tests}")
        print(f"   📊 Tasa de éxito: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ PRUEBAS FALLIDAS ({failed_tests}):")
            for result in self.results:
                if "FAIL" in result["result"]:
                    print(f"   • {result['name']}")
                    print(f"     {result['method']} {result['endpoint']}")
                    print(f"     Status: {result['status_code']} (esperado {result['expected']})")
                    print(f"     Detalles: {result['details']}")
                    print()
        
        print(f"\n✅ PRUEBAS EXITOSAS ({passed_tests}):")
        for result in self.results:
            if "PASS" in result["result"]:
                print(f"   • {result['name']} - {result['method']} {result['endpoint']}")
        
        print("\n" + "="*80)
        print("🎯 CONCLUSIÓN:")
        if failed_tests == 0:
            print("   ✅ TODAS LAS FUNCIONALIDADES PR1 ESTÁN OPERATIVAS")
            print("   🚀 Sistema listo para producción")
        else:
            print(f"   ⚠️  {failed_tests} funcionalidades requieren atención")
            print("   🔧 Revisar implementación antes de producción")
        print("="*80)

def main():
    """Main test execution"""
    print("🚀 INICIANDO PRUEBAS EXHAUSTIVAS DE BACKEND - PR1 NUEVAS FUNCIONALIDADES")
    print("="*80)
    print(f"🌐 Base URL: {BASE_URL}")
    print(f"🏢 TAXITUR_ORG_ID: {TAXITUR_ORG_ID}")
    print("="*80)
    
    tester = BackendTester()
    
    # Setup test data
    if not tester.setup_test_data():
        print("❌ Failed to setup test data. Aborting tests.")
        return
    
    # Execute all test cases
    try:
        tester.test_taxitur_origen_obligatorio()
        tester.test_vehiculo_cambiado_kilometros()
        tester.test_combustible_repostaje()
        tester.test_server_time()
        tester.test_exports_nuevas_columnas()
        tester.test_estadisticas_combustible()
        tester.test_metodo_pago()
    except Exception as e:
        print(f"❌ Error during testing: {e}")
    
    # Print summary
    tester.print_summary()

if __name__ == "__main__":
    main()