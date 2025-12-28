#!/usr/bin/env python3
"""
Pruebas Exhaustivas de Backend - PR1 (SEGUNDA EJECUCIÓN)
Testing comprehensive backend functionality for PR1 features with specific test users
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Configuration from review request
BASE_URL = "https://taxiflow-18.preview.emergentagent.com/api"
TAXITUR_ORG_ID = "69484bec187c3bc2b0fdb8f4"
OTHER_ORG_ID = "69429aaecdbc9d2db23e0ed5"  # Taxi Tineo

# Test users from review request (already configured)
TEST_USERS = {
    "taxista_taxitur": {"username": "taxista_taxitur", "password": "test123"},
    "taxista_tineo": {"username": "taxista_tineo", "password": "test123"},
    "admin": {"username": "admin", "password": "admin123"}
}

# Test data from review request
TEST_DATA = {
    "taxitur_turno_id": "6951247a58935fb953225444",
    "taxitur_vehiculo_turno": "6951247958935fb953225440",  # TEST-TAXITUR
    "taxitur_vehiculo_segundo": "6951247a58935fb953225446",  # TEST-TAXITUR-2
    "tineo_turno_id": "6951247a58935fb953225445",
    "tineo_vehiculo_turno": "6951247958935fb953225441",  # TEST-TINEO
    "tineo_vehiculo_segundo": "6951247a58935fb953225447"  # TEST-TINEO-2
}

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
                print(f"✅ Login exitoso: {username}")
                return token
            else:
                print(f"❌ Login fallido para {username}: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Error login {username}: {e}")
            return None
    
    def make_request(self, method: str, endpoint: str, token: str = None, **kwargs) -> requests.Response:
        """Make authenticated request"""
        headers = kwargs.get('headers', {})
        if token:
            headers['Authorization'] = f'Bearer {token}'
        kwargs['headers'] = headers
        
        url = f"{BASE_URL}{endpoint}"
        return getattr(self.session, method.lower())(url, **kwargs)
    
    def setup_test_environment(self):
        """Setup test environment by logging in users"""
        print("\n🔧 CONFIGURANDO ENTORNO DE PRUEBAS...")
        print(f"API Base URL: {BASE_URL}")
        print(f"TAXITUR_ORG_ID: {TAXITUR_ORG_ID}")
        print(f"OTHER_ORG_ID: {OTHER_ORG_ID}")
        print()
        
        # Login all test users
        for user_key, credentials in TEST_USERS.items():
            token = self.login(credentials["username"], credentials["password"])
            if not token:
                print(f"❌ Error login {credentials['username']}")
                return False
        
        # Check if taxistas have active turnos, create if needed
        self._ensure_active_turnos()
        
        print()
        return True
    
    def _ensure_active_turnos(self):
        """Ensure taxistas have active turnos for testing"""
        print("🔄 Verificando turnos activos...")
        
        # Check taxista_taxitur
        taxitur_token = self.tokens["taxista_taxitur"]
        response = self.make_request("GET", "/turnos/activo", taxitur_token)
        if response.status_code != 200 or not response.json():
            print("📝 Creando turno activo para taxista_taxitur...")
            turno_data = {
                "taxista_id": "test_taxista_taxitur_id",
                "taxista_nombre": "Taxista Taxitur Test",
                "vehiculo_id": TEST_DATA["taxitur_vehiculo_turno"],
                "vehiculo_matricula": "TEST-TAXITUR",
                "fecha_inicio": "15/12/2024",
                "hora_inicio": "08:00",
                "km_inicio": 100000
            }
            self.make_request("POST", "/turnos", taxitur_token, json=turno_data)
        
        # Check taxista_tineo
        tineo_token = self.tokens["taxista_tineo"]
        response = self.make_request("GET", "/turnos/activo", tineo_token)
        if response.status_code != 200 or not response.json():
            print("📝 Creando turno activo para taxista_tineo...")
            turno_data = {
                "taxista_id": "test_taxista_tineo_id",
                "taxista_nombre": "Taxista Tineo Test",
                "vehiculo_id": TEST_DATA["tineo_vehiculo_turno"],
                "vehiculo_matricula": "TEST-TINEO",
                "fecha_inicio": "15/12/2024",
                "hora_inicio": "08:00",
                "km_inicio": 100000
            }
            self.make_request("POST", "/turnos", tineo_token, json=turno_data)
    
    def test_1_taxitur_origen_obligatorio(self):
        """Test 1: TAXITUR - Origen obligatorio"""
        print("\n🎯 TEST 1: TAXITUR - ORIGEN OBLIGATORIO")
        print("-" * 50)
        
        taxitur_token = self.tokens["taxista_taxitur"]
        tineo_token = self.tokens["taxista_tineo"]
        
        # Test 1.1: POST /api/services con taxista_taxitur SIN origen_taxitur
        service_data = {
            "fecha": "15/12/2024",
            "hora": "10:30",
            "origen": "Oviedo Centro",
            "destino": "Aeropuerto",
            "importe": 25.50,
            "importe_espera": 0,
            "kilometros": 15.2,
            "tipo": "particular",
            "metodo_pago": "efectivo"
            # NO incluimos origen_taxitur
        }
        
        response = self.make_request("POST", "/services", taxitur_token, json=service_data)
        self.log_test(
            "1.1", "POST", "/services", 
            response.status_code, 400,
            "POST /api/services con taxista_taxitur SIN origen_taxitur"
        )
        
        # Test 1.2: POST /api/services con taxista_taxitur CON origen_taxitur="parada"
        service_data["origen_taxitur"] = "parada"
        response = self.make_request("POST", "/services", taxitur_token, json=service_data)
        self.log_test(
            "1.2", "POST", "/services",
            response.status_code, 201,
            "POST /api/services con taxista_taxitur CON origen_taxitur='parada'"
        )
        
        # Test 1.3: POST /api/services con taxista_taxitur CON origen_taxitur="lagos"
        service_data["origen_taxitur"] = "lagos"
        service_data["hora"] = "11:00"  # Cambiar hora para evitar duplicados
        response = self.make_request("POST", "/services", taxitur_token, json=service_data)
        self.log_test(
            "1.3", "POST", "/services",
            response.status_code, 201,
            "POST /api/services con taxista_taxitur CON origen_taxitur='lagos'"
        )
        
        # Test 1.4: POST /api/services con taxista_tineo CON origen_taxitur="parada" (no permitido)
        service_data_tineo = {
            "fecha": "15/12/2024",
            "hora": "12:00",
            "origen": "Tineo Centro",
            "destino": "Hospital",
            "importe": 15.00,
            "importe_espera": 0,
            "kilometros": 8.5,
            "tipo": "particular",
            "metodo_pago": "efectivo",
            "origen_taxitur": "parada"  # No debería ser permitido para Taxi Tineo
        }
        
        response = self.make_request("POST", "/services", tineo_token, json=service_data_tineo)
        self.log_test(
            "1.4", "POST", "/services",
            response.status_code, 400,
            "POST /api/services con taxista_tineo CON origen_taxitur='parada' (no permitido)"
        )

    def test_2_vehiculo_cambiado_kilometros(self):
        """Test 2: VEHÍCULO CAMBIADO - Kilómetros condicionales"""
        print("\n🎯 TEST 2: VEHÍCULO CAMBIADO - KILÓMETROS CONDICIONALES")
        print("-" * 50)
        
        # Usar taxista_tineo para evitar conflicto con origen_taxitur
        tineo_token = self.tokens["taxista_tineo"]
        
        # Test 2.1: POST /api/services con vehiculo_id=TEST-TINEO-2 SIN km_inicio/km_fin
        service_data = {
            "fecha": "15/12/2024",
            "hora": "13:00",
            "origen": "Tineo Plaza",
            "destino": "Cangas",
            "importe": 30.00,
            "importe_espera": 0,
            "kilometros": 25.0,
            "tipo": "particular",
            "metodo_pago": "efectivo",
            "vehiculo_id": TEST_DATA["tineo_vehiculo_segundo"],  # TEST-TINEO-2
            "vehiculo_cambiado": True
            # NO incluimos km_inicio_vehiculo/km_fin_vehiculo
        }
        
        response = self.make_request("POST", "/services", tineo_token, json=service_data)
        self.log_test(
            "2.1", "POST", "/services",
            response.status_code, 400,
            "POST /api/services con vehiculo_id=TEST-TINEO-2 SIN km_inicio/km_fin"
        )
        
        # Test 2.2: POST /api/services con vehiculo_id=TEST-TINEO-2 y km_fin < km_inicio
        service_data.update({
            "km_inicio_vehiculo": 150,
            "km_fin_vehiculo": 100  # km_fin < km_inicio
        })
        
        response = self.make_request("POST", "/services", tineo_token, json=service_data)
        self.log_test(
            "2.2", "POST", "/services",
            response.status_code, 400,
            "POST /api/services con vehiculo_id=TEST-TINEO-2 y km_fin < km_inicio"
        )
        
        # Test 2.3: POST /api/services con vehiculo_id=TEST-TINEO-2 y km válidos (inicio=100, fin=150)
        service_data.update({
            "km_inicio_vehiculo": 100,
            "km_fin_vehiculo": 150
        })
        
        response = self.make_request("POST", "/services", tineo_token, json=service_data)
        self.log_test(
            "2.3", "POST", "/services",
            response.status_code, 201,
            "POST /api/services con vehiculo_id=TEST-TINEO-2 y km válidos (inicio=100, fin=150)"
        )
        
        # Test 2.4: POST /api/services con mismo vehículo del turno (sin km extra)
        service_data_normal = {
            "fecha": "15/12/2024",
            "hora": "14:00",
            "origen": "Tineo Centro",
            "destino": "Navelgas",
            "importe": 20.00,
            "importe_espera": 0,
            "kilometros": 12.0,
            "tipo": "particular",
            "metodo_pago": "tpv"
            # Sin vehiculo_id específico, usa el del turno
        }
        
        response = self.make_request("POST", "/services", tineo_token, json=service_data_normal)
        self.log_test(
            "2.4", "POST", "/services",
            response.status_code, 201,
            "POST /api/services con mismo vehículo del turno (sin km extra)"
        )

    def test_3_combustible_repostaje(self):
        """Test 3: COMBUSTIBLE - Repostaje en turnos"""
        print("\n🎯 TEST 3: COMBUSTIBLE - REPOSTAJE EN TURNOS")
        print("-" * 50)
        
        # Usar turno de taxista_tineo
        tineo_token = self.tokens["taxista_tineo"]
        turno_id = TEST_DATA["tineo_turno_id"]
        
        # Test 3.1: PUT /api/turnos/{turno_id}/combustible con repostado=true, litros=45, km=100050
        combustible_data = {
            "repostado": True,
            "litros": 45.0,
            "vehiculo_id": TEST_DATA["tineo_vehiculo_turno"],  # TEST-TINEO
            "km_vehiculo": 100050
        }
        
        response = self.make_request("PUT", f"/turnos/{turno_id}/combustible", tineo_token, json=combustible_data)
        self.log_test(
            "3.1", "PUT", f"/turnos/{turno_id}/combustible",
            response.status_code, 200,
            "PUT /api/turnos/{turno_id}/combustible con repostado=true, litros=45, km=100050"
        )
        
        # Test 3.2: PUT /api/turnos/{turno_id}/finalizar con km_fin > km_inicio
        finalizar_data = {
            "fecha_fin": "15/12/2024",
            "hora_fin": "18:00",  # Se ignorará, se usará hora del servidor
            "km_fin": 100100,
            "cerrado": True
        }
        
        response = self.make_request("PUT", f"/turnos/{turno_id}/finalizar", tineo_token, json=finalizar_data)
        self.log_test(
            "3.2", "PUT", f"/turnos/{turno_id}/finalizar",
            response.status_code, 200,
            "PUT /api/turnos/{turno_id}/finalizar con km_fin > km_inicio"
        )
        
        # Test 3.3: PUT /api/turnos/{turno_id}/combustible (turno ya cerrado)
        combustible_data_cerrado = {
            "repostado": True,
            "litros": 30.0,
            "vehiculo_id": TEST_DATA["tineo_vehiculo_turno"],
            "km_vehiculo": 100120
        }
        
        response = self.make_request("PUT", f"/turnos/{turno_id}/combustible", tineo_token, json=combustible_data_cerrado)
        self.log_test(
            "3.3", "PUT", f"/turnos/{turno_id}/combustible",
            response.status_code, 403,
            "PUT /api/turnos/{turno_id}/combustible (turno ya cerrado)"
        )

    def test_4_server_time(self):
        """Test 4: SERVER TIME"""
        print("\n🎯 TEST 4: SERVER TIME")
        print("-" * 50)
        
        tineo_token = self.tokens["taxista_tineo"]
        
        # Test 4.1: POST /api/turnos enviando hora_inicio="99:99"
        turno_data = {
            "taxista_id": "test_taxista_id",
            "taxista_nombre": "Test Taxista",
            "vehiculo_id": TEST_DATA["tineo_vehiculo_turno"],
            "vehiculo_matricula": "TEST-TINEO",
            "fecha_inicio": "15/12/2024",
            "hora_inicio": "99:99",  # Hora inválida, debería usar hora del servidor
            "km_inicio": 100200
        }
        
        response = self.make_request("POST", "/turnos", tineo_token, json=turno_data)
        if response.status_code == 200:
            turno_creado = response.json()
            hora_guardada = turno_creado.get("hora_inicio", "")
            server_time_used = hora_guardada != "99:99"
            
            self.log_test(
                "4.1", "POST", "/turnos",
                response.status_code, 200,
                f"POST /api/turnos enviando hora_inicio='99:99' - Hora guardada: {hora_guardada} (server time: {server_time_used})"
            )
            
            # Guardar ID del turno para test 4.2
            self.test_data["new_turno_id"] = turno_creado.get("id")
        else:
            self.log_test(
                "4.1", "POST", "/turnos",
                response.status_code, 200,
                "POST /api/turnos enviando hora_inicio='99:99'"
            )
        
        # Test 4.2: PUT /api/turnos/{id}/finalizar enviando hora_fin="99:99"
        if self.test_data.get("new_turno_id"):
            finalizar_data = {
                "fecha_fin": "15/12/2024",
                "hora_fin": "99:99",  # Hora inválida, debería usar hora del servidor
                "km_fin": 100250,
                "cerrado": True
            }
            
            response = self.make_request("PUT", f"/turnos/{self.test_data['new_turno_id']}/finalizar", tineo_token, json=finalizar_data)
            if response.status_code == 200:
                turno_finalizado = response.json()
                hora_fin_guardada = turno_finalizado.get("hora_fin", "")
                server_time_used = hora_fin_guardada != "99:99"
                
                self.log_test(
                    "4.2", "PUT", f"/turnos/{self.test_data['new_turno_id']}/finalizar",
                    response.status_code, 200,
                    f"PUT /api/turnos/{{id}}/finalizar enviando hora_fin='99:99' - Hora guardada: {hora_fin_guardada} (server time: {server_time_used})"
                )
            else:
                self.log_test(
                    "4.2", "PUT", f"/turnos/{self.test_data['new_turno_id']}/finalizar",
                    response.status_code, 200,
                    "PUT /api/turnos/{id}/finalizar enviando hora_fin='99:99'"
                )
        else:
            self.log_test(
                "4.2", "PUT", "/turnos/{id}/finalizar",
                0, 200,
                "No se pudo crear turno para test 4.2"
            )

    def test_5_exports(self):
        """Test 5: EXPORTS"""
        print("\n🎯 TEST 5: EXPORTS")
        print("-" * 50)
        
        admin_token = self.tokens["admin"]
        
        # Test 5.1: GET /api/services/export/csv con admin
        response = self.make_request("GET", "/services/export/csv", admin_token)
        if response.status_code == 200:
            content_type = response.headers.get("content-type", "")
            contains_columns = "metodo_pago" in response.text and "origen_taxitur" in response.text
            
            self.log_test(
                "5.1", "GET", "/services/export/csv",
                response.status_code, 200,
                f"GET /api/services/export/csv con admin - Content-Type: {content_type}, Contiene columnas: {contains_columns}"
            )
        else:
            self.log_test(
                "5.1", "GET", "/services/export/csv",
                response.status_code, 200,
                "GET /api/services/export/csv con admin"
            )
        
        # Test 5.2: GET /api/services/export/excel con admin
        response = self.make_request("GET", "/services/export/excel", admin_token)
        self.log_test(
            "5.2", "GET", "/services/export/excel",
            response.status_code, 200,
            f"GET /api/services/export/excel con admin - Content-Type: {response.headers.get('content-type', 'N/A')}"
        )
        
        # Test 5.3: GET /api/turnos/export/csv con admin
        response = self.make_request("GET", "/turnos/export/csv", admin_token)
        if response.status_code == 200:
            contains_combustible = "combustible" in response.text.lower()
            
            self.log_test(
                "5.3", "GET", "/turnos/export/csv",
                response.status_code, 200,
                f"GET /api/turnos/export/csv con admin - Contiene columnas de combustible: {contains_combustible}"
            )
        else:
            self.log_test(
                "5.3", "GET", "/turnos/export/csv",
                response.status_code, 200,
                "GET /api/turnos/export/csv con admin"
            )
        
        # Test 5.4: GET /api/turnos/combustible/estadisticas con admin
        response = self.make_request("GET", "/turnos/combustible/estadisticas", admin_token)
        self.log_test(
            "5.4", "GET", "/turnos/combustible/estadisticas",
            response.status_code, 200,
            "GET /api/turnos/combustible/estadisticas con admin"
        )

    def test_6_metodo_pago(self):
        """Test 6: MÉTODO DE PAGO"""
        print("\n🎯 TEST 6: MÉTODO DE PAGO")
        print("-" * 50)
        
        tineo_token = self.tokens["taxista_tineo"]
        
        # Test 6.1: POST /api/services con metodo_pago="efectivo"
        service_efectivo = {
            "fecha": "15/12/2024",
            "hora": "15:00",
            "origen": "Tineo",
            "destino": "Grado",
            "importe": 18.50,
            "importe_espera": 0,
            "kilometros": 15.0,
            "tipo": "particular",
            "metodo_pago": "efectivo"
        }
        
        response = self.make_request("POST", "/services", tineo_token, json=service_efectivo)
        self.log_test(
            "6.1", "POST", "/services",
            response.status_code, 201,
            "POST /api/services con metodo_pago='efectivo'"
        )
        
        # Test 6.2: POST /api/services con metodo_pago="tpv"
        service_tpv = {
            "fecha": "15/12/2024",
            "hora": "16:00",
            "origen": "Grado",
            "destino": "Oviedo",
            "importe": 22.00,
            "importe_espera": 2.50,
            "kilometros": 18.5,
            "tipo": "empresa",
            "metodo_pago": "tpv"
        }
        
        response = self.make_request("POST", "/services", tineo_token, json=service_tpv)
        self.log_test(
            "6.2", "POST", "/services",
            response.status_code, 201,
            "POST /api/services con metodo_pago='tpv'"
        )
        
        # Test 6.3: GET /api/services?metodo_pago=efectivo
        response = self.make_request("GET", "/services?metodo_pago=efectivo", tineo_token)
        if response.status_code == 200:
            services = response.json()
            efectivo_count = len([s for s in services if s.get("metodo_pago") == "efectivo"])
            
            self.log_test(
                "6.3", "GET", "/services?metodo_pago=efectivo",
                response.status_code, 200,
                f"GET /api/services?metodo_pago=efectivo - Servicios efectivo encontrados: {efectivo_count}"
            )
        else:
            self.log_test(
                "6.3", "GET", "/services?metodo_pago=efectivo",
                response.status_code, 200,
                "GET /api/services?metodo_pago=efectivo"
            )
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("📊 RESUMEN DE PRUEBAS EXHAUSTIVAS - PR1 (SEGUNDA EJECUCIÓN)")
        print("="*80)
        
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if "PASS" in r["result"]])
        failed_tests = total_tests - passed_tests
        
        print(f"\n📈 ESTADÍSTICAS GENERALES:")
        print(f"   Total de pruebas: {total_tests}")
        print(f"   ✅ Exitosas: {passed_tests}")
        print(f"   ❌ Fallidas: {failed_tests}")
        print(f"   📊 Tasa de éxito: {(passed_tests/total_tests*100):.1f}%")
        
        # Print results by test case
        print(f"\n📋 RESULTADOS POR CASO DE PRUEBA:")
        
        test_cases = {
            "1": "TAXITUR - Origen obligatorio",
            "2": "VEHÍCULO CAMBIADO - Kilómetros condicionales", 
            "3": "COMBUSTIBLE - Repostaje en turnos",
            "4": "SERVER TIME",
            "5": "EXPORTS",
            "6": "MÉTODO DE PAGO"
        }
        
        for case_num, case_name in test_cases.items():
            case_results = [r for r in self.results if r["name"].startswith(case_num + ".")]
            case_passed = len([r for r in case_results if "PASS" in r["result"]])
            case_total = len(case_results)
            
            print(f"\n   {case_num}. {case_name}:")
            for result in case_results:
                status_icon = "✅" if "PASS" in result["result"] else "❌"
                print(f"      {status_icon} {result['name']}: {result['status_code']} (esperado {result['expected']})")
        
        if failed_tests > 0:
            print(f"\n❌ DETALLES DE PRUEBAS FALLIDAS:")
            for result in self.results:
                if "FAIL" in result["result"]:
                    print(f"   • {result['name']}: {result['details']}")
                    print(f"     Status: {result['status_code']} (esperado {result['expected']})")
        
        print("\n" + "="*80)
        print("🎯 CONCLUSIÓN:")
        if failed_tests == 0:
            print("   ✅ TODAS LAS FUNCIONALIDADES PR1 ESTÁN OPERATIVAS")
            print("   🚀 Sistema listo para producción")
        else:
            print(f"   ⚠️  {failed_tests} funcionalidades requieren atención")
            print("   🔧 Revisar implementación antes de producción")
        print("="*80)
        
        return failed_tests == 0

def main():
    """Main test execution"""
    print("🚕 PRUEBAS EXHAUSTIVAS DE BACKEND - PR1 (SEGUNDA EJECUCIÓN)")
    print("=" * 80)
    print(f"🌐 Base URL: {BASE_URL}")
    print(f"🏢 TAXITUR_ORG_ID: {TAXITUR_ORG_ID}")
    print(f"🏢 OTHER_ORG_ID: {OTHER_ORG_ID}")
    print("=" * 80)
    
    tester = BackendTester()
    
    # Setup test environment
    if not tester.setup_test_environment():
        print("❌ Error configurando entorno de pruebas")
        return False
    
    # Execute all test cases
    try:
        tester.test_1_taxitur_origen_obligatorio()
        tester.test_2_vehiculo_cambiado_kilometros()
        tester.test_3_combustible_repostaje()
        tester.test_4_server_time()
        tester.test_5_exports()
        tester.test_6_metodo_pago()
    except Exception as e:
        print(f"❌ Error durante la ejecución de pruebas: {e}")
        import traceback
        traceback.print_exc()
    
    # Print summary
    success = tester.print_summary()
    
    if success:
        print("\n🎉 TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
        return True
    else:
        print("\n⚠️ ALGUNAS PRUEBAS FALLARON - REVISAR IMPLEMENTACIÓN")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)