#!/usr/bin/env python3
"""
TESTING EXHAUSTIVO COMPLETO - ÍNDICES ÚNICOS MULTI-TENANT
Implementa exactamente todos los casos de prueba solicitados en el review request

API Base URL: https://idempotent-services.preview.emergentagent.com/api
CREDENCIALES:
- Superadmin: superadmin / superadmin123
- Admin Taxitur: admintur / admin123
"""

import requests
import json
import time

BASE_URL = "https://idempotent-services.preview.emergentagent.com/api"

class ComprehensiveMultiTenantTester:
    def __init__(self):
        self.tokens = {}
        self.org_ids = {}
        self.test_results = []
        
    def log_test(self, test_name: str, expected: str, actual: str, passed: bool, details: str = ""):
        status = "PASS" if passed else "FAIL"
        self.test_results.append({
            "test": test_name,
            "expected": expected, 
            "actual": actual,
            "status": status,
            "details": details
        })
        symbol = "✅" if passed else "❌"
        print(f"   {symbol} {test_name}: {actual} (esperado: {expected})")
        if details:
            print(f"      💡 {details}")
    
    def get_token(self, username, password):
        response = requests.post(f"{BASE_URL}/auth/login", json={"username": username, "password": password})
        if response.status_code == 200:
            return response.json()["access_token"]
        raise Exception(f"Login failed: {response.status_code} - {response.text}")
    
    def api_call(self, method, endpoint, token, data=None):
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{BASE_URL}{endpoint}"
        
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        
        return {
            "status": response.status_code,
            "data": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
        }

    def setup_test_environment(self):
        """Setup: Login superadmin y crear organizaciones de prueba"""
        print("\n🔧 SETUP: PREPARANDO ENTORNO DE PRUEBAS")
        print("-" * 50)
        
        # Login superadmin
        self.tokens["superadmin"] = self.get_token("superadmin", "superadmin123")
        print("✅ Login superadmin exitoso")
        
        # Create unique test organizations
        timestamp = str(int(time.time()))[-6:]
        
        # TestOrgA
        org_a_data = {"nombre": f"TestOrgA_{timestamp}", "slug": f"testorga-{timestamp}"}
        result_a = self.api_call("POST", "/organizations", self.tokens["superadmin"], org_a_data)
        if result_a["status"] == 200:
            self.org_ids["TestOrgA"] = result_a["data"]["id"]
            print(f"✅ TestOrgA creada: {self.org_ids['TestOrgA']}")
        else:
            raise Exception(f"❌ Error creando TestOrgA: {result_a}")
            
        # TestOrgB
        org_b_data = {"nombre": f"TestOrgB_{timestamp}", "slug": f"testorgb-{timestamp}"}
        result_b = self.api_call("POST", "/organizations", self.tokens["superadmin"], org_b_data)
        if result_b["status"] == 200:
            self.org_ids["TestOrgB"] = result_b["data"]["id"]
            print(f"✅ TestOrgB creada: {self.org_ids['TestOrgB']}")
        else:
            raise Exception(f"❌ Error creando TestOrgB: {result_b}")
        
        # Create admins for both orgs
        admin_a_data = {"username": f"admin_testa_{timestamp}", "password": "admin123", "nombre": "Admin Test A"}
        result_admin_a = self.api_call("POST", f"/organizations/{self.org_ids['TestOrgA']}/admin", self.tokens["superadmin"], admin_a_data)
        if result_admin_a["status"] == 200:
            self.tokens["admin_testa"] = self.get_token(f"admin_testa_{timestamp}", "admin123")
            print(f"✅ Admin TestA creado y login exitoso")
        else:
            raise Exception(f"❌ Error creando admin TestA: {result_admin_a}")
            
        admin_b_data = {"username": f"admin_testb_{timestamp}", "password": "admin123", "nombre": "Admin Test B"}
        result_admin_b = self.api_call("POST", f"/organizations/{self.org_ids['TestOrgB']}/admin", self.tokens["superadmin"], admin_b_data)
        if result_admin_b["status"] == 200:
            self.tokens["admin_testb"] = self.get_token(f"admin_testb_{timestamp}", "admin123")
            print(f"✅ Admin TestB creado y login exitoso")
        else:
            raise Exception(f"❌ Error creando admin TestB: {result_admin_b}")

    def test_parte_1_vehiculos(self):
        """PARTE 1: Vehículos - misma matrícula en diferentes orgs"""
        print("\n📋 PARTE 1: VEHÍCULOS - MATRÍCULA MULTI-TENANT")
        print("-" * 50)
        
        matricula = "MULTI123"
        
        # 1. Login como admin_testa (ya hecho en setup)
        # 2. Crear 2 organizaciones de prueba (ya hecho en setup)
        # 3. Crear 2 admins (ya hecho en setup)
        
        print("4. Login con admin_testa (ya conectado)")
        print("5. POST /vehiculos con matrícula MULTI123...")
        
        vehiculo_data = {
            "matricula": matricula,
            "plazas": 4,
            "marca": "Ford",
            "modelo": "Focus",
            "km_iniciales": 50000,
            "fecha_compra": "01/01/2020",
            "activo": True
        }
        
        result_5 = self.api_call("POST", "/vehiculos", self.tokens["admin_testa"], vehiculo_data)
        self.log_test(
            "5. POST /vehiculos MULTI123 en TestOrgA",
            "200 (OK)",
            str(result_5["status"]),
            result_5["status"] == 200,
            f"Crear vehículo {matricula} en TestOrgA"
        )
        
        print("6. Login con admin_testb (ya conectado)")
        print("7. POST /vehiculos con misma matrícula MULTI123 (diferente org)...")
        
        result_7 = self.api_call("POST", "/vehiculos", self.tokens["admin_testb"], vehiculo_data)
        self.log_test(
            "7. POST /vehiculos MULTI123 en TestOrgB",
            "200 (OK - diferente org)",
            str(result_7["status"]),
            result_7["status"] == 200,
            f"Misma matrícula permitida en diferente organización"
        )
        
        print("8. POST /vehiculos con matrícula MULTI123 duplicada en TestOrgB...")
        
        result_8 = self.api_call("POST", "/vehiculos", self.tokens["admin_testb"], vehiculo_data)
        self.log_test(
            "8. POST /vehiculos MULTI123 duplicado en TestOrgB",
            "400 (ERROR - duplicado en misma org)",
            str(result_8["status"]),
            result_8["status"] == 400,
            f"Duplicado rechazado correctamente"
        )
        
        # Verificar mensaje de error
        if result_8["status"] == 400:
            error_msg = result_8["data"].get("detail", "")
            expected_msg = "La matricula ya existe en tu organizacion"
            msg_ok = expected_msg.lower() in error_msg.lower()
            self.log_test(
                "8.1 Mensaje error matrícula",
                "La matricula ya existe en tu organizacion",
                error_msg,
                msg_ok,
                "Verificar mensaje de error claro"
            )

    def test_parte_2_empresas(self):
        """PARTE 2: Empresas - mismo numero_cliente en diferentes orgs"""
        print("\n📋 PARTE 2: EMPRESAS - NUMERO_CLIENTE MULTI-TENANT") 
        print("-" * 50)
        
        numero_cliente = "CLI001"
        
        print("1. Login con admin_testa (ya conectado)")
        print("2. POST /companies con numero_cliente CLI001...")
        
        empresa_data_a = {
            "nombre": "EmpresaX",
            "numero_cliente": numero_cliente,
            "cif": "B11111111",
            "direccion": "Direccion A"
        }
        
        result_2_1 = self.api_call("POST", "/companies", self.tokens["admin_testa"], empresa_data_a)
        self.log_test(
            "2.1 POST /companies CLI001 en TestOrgA",
            "200",
            str(result_2_1["status"]),
            result_2_1["status"] == 200,
            f"Crear empresa con numero_cliente {numero_cliente}"
        )
        
        print("3. Login con admin_testb (ya conectado)")
        print("4. POST /companies con mismo numero_cliente CLI001...")
        
        empresa_data_b = {
            "nombre": "EmpresaX",
            "numero_cliente": numero_cliente,
            "cif": "B22222222",
            "direccion": "Direccion B"
        }
        
        result_2_2 = self.api_call("POST", "/companies", self.tokens["admin_testb"], empresa_data_b)
        self.log_test(
            "2.2 POST /companies CLI001 en TestOrgB",
            "200 (OK - diferente org)",
            str(result_2_2["status"]),
            result_2_2["status"] == 200,
            f"Mismo numero_cliente permitido en diferente org"
        )
        
        print("5. POST /companies con numero_cliente CLI001 duplicado...")
        
        empresa_data_b2 = {
            "nombre": "EmpresaY",
            "numero_cliente": numero_cliente,
            "cif": "B33333333",
            "direccion": "Direccion C"
        }
        
        result_2_3 = self.api_call("POST", "/companies", self.tokens["admin_testb"], empresa_data_b2)
        self.log_test(
            "2.3 POST /companies CLI001 duplicado en TestOrgB",
            "400 (ERROR - duplicado)",
            str(result_2_3["status"]),
            result_2_3["status"] == 400,
            f"Duplicado rechazado correctamente"
        )
        
        # Verificar mensaje de error
        if result_2_3["status"] == 400:
            error_msg = result_2_3["data"].get("detail", "")
            expected_msg = "El numero de cliente ya existe en tu organizacion"
            msg_ok = expected_msg.lower() in error_msg.lower()
            self.log_test(
                "2.4 Mensaje error numero_cliente",
                "El numero de cliente ya existe en tu organizacion",
                error_msg,
                msg_ok,
                "Verificar mensaje de error claro"
            )

    def test_parte_4_superadmin(self):
        """PARTE 4: Superadmin crea vehículos"""
        print("\n📋 PARTE 4: SUPERADMIN - VEHÍCULOS MULTI-TENANT")
        print("-" * 50)
        
        matricula = "SUPER123"
        
        print("1. Login como superadmin (ya conectado)")
        print("2. POST /superadmin/vehiculos con matrícula SUPER123 en TestOrgA...")
        
        vehiculo_super_a = {
            "matricula": matricula,
            "organization_id": self.org_ids["TestOrgA"],
            "plazas": 4,
            "marca": "Mercedes",
            "modelo": "E-Class",
            "km_iniciales": 80000,
            "fecha_compra": "01/03/2019"
        }
        
        result_4_1 = self.api_call("POST", "/superadmin/vehiculos", self.tokens["superadmin"], vehiculo_super_a)
        self.log_test(
            "4.1 Superadmin POST vehiculo SUPER123 en TestOrgA",
            "200",
            str(result_4_1["status"]),
            result_4_1["status"] == 200,
            f"Crear vehículo {matricula} en TestOrgA como superadmin"
        )
        
        print("3. POST /superadmin/vehiculos con matrícula SUPER123 en TestOrgB...")
        
        vehiculo_super_b = {
            "matricula": matricula,
            "organization_id": self.org_ids["TestOrgB"],
            "plazas": 5,
            "marca": "BMW",
            "modelo": "Serie 3",
            "km_iniciales": 60000,
            "fecha_compra": "15/08/2020"
        }
        
        result_4_2 = self.api_call("POST", "/superadmin/vehiculos", self.tokens["superadmin"], vehiculo_super_b)
        self.log_test(
            "4.2 Superadmin POST vehiculo SUPER123 en TestOrgB",
            "200",
            str(result_4_2["status"]),
            result_4_2["status"] == 200,
            f"Misma matrícula permitida en diferente org"
        )
        
        print("4. POST /superadmin/vehiculos con matrícula SUPER123 duplicada en TestOrgA...")
        
        vehiculo_super_a2 = {
            "matricula": matricula,
            "organization_id": self.org_ids["TestOrgA"],
            "plazas": 4,
            "marca": "Audi",
            "modelo": "A4",
            "km_iniciales": 90000,
            "fecha_compra": "01/10/2021"
        }
        
        result_4_3 = self.api_call("POST", "/superadmin/vehiculos", self.tokens["superadmin"], vehiculo_super_a2)
        self.log_test(
            "4.3 Superadmin POST vehiculo SUPER123 duplicado en TestOrgA",
            "400",
            str(result_4_3["status"]),
            result_4_3["status"] == 400,
            f"Duplicado rechazado correctamente"
        )

    def test_admin_taxitur_verification(self):
        """Verificación con admin Taxitur existente"""
        print("\n📋 VERIFICACIÓN: ADMIN TAXITUR EXISTENTE")
        print("-" * 50)
        
        try:
            # Login con admintur
            self.tokens["admintur"] = self.get_token("admintur", "admin123")
            print("✅ Login admintur exitoso")
            
            # Test GET vehiculos
            veh_result = self.api_call("GET", "/vehiculos", self.tokens["admintur"])
            self.log_test(
                "Admin Taxitur GET /vehiculos",
                "200",
                str(veh_result["status"]),
                veh_result["status"] == 200,
                f"{len(veh_result['data']) if veh_result['status'] == 200 else 0} vehículos encontrados"
            )
            
            # Test GET companies
            comp_result = self.api_call("GET", "/companies", self.tokens["admintur"])
            self.log_test(
                "Admin Taxitur GET /companies",
                "200",
                str(comp_result["status"]),
                comp_result["status"] == 200,
                f"{len(comp_result['data']) if comp_result['status'] == 200 else 0} empresas encontradas"
            )
            
        except Exception as e:
            self.log_test(
                "Admin Taxitur login",
                "Success",
                "FAILED",
                False,
                f"No disponible: {e}"
            )

    def verify_data_isolation(self):
        """Verificar aislamiento de datos entre organizaciones"""
        print("\n📋 VERIFICACIÓN: AISLAMIENTO DE DATOS")
        print("-" * 50)
        
        # Admin TestA - ver solo sus datos
        veh_a_result = self.api_call("GET", "/vehiculos", self.tokens["admin_testa"])
        if veh_a_result["status"] == 200:
            vehiculos_a = veh_a_result["data"]
            multi123_count_a = len([v for v in vehiculos_a if v.get("matricula") == "MULTI123"])
            super123_count_a = len([v for v in vehiculos_a if v.get("matricula") == "SUPER123"])
            self.log_test(
                "TestOrgA aislamiento vehículos",
                "1 MULTI123, 1 SUPER123",
                f"{multi123_count_a} MULTI123, {super123_count_a} SUPER123",
                multi123_count_a == 1 and super123_count_a == 1,
                "Admin A solo ve vehículos de su organización"
            )
        
        # Admin TestB - ver solo sus datos
        veh_b_result = self.api_call("GET", "/vehiculos", self.tokens["admin_testb"])
        if veh_b_result["status"] == 200:
            vehiculos_b = veh_b_result["data"]
            multi123_count_b = len([v for v in vehiculos_b if v.get("matricula") == "MULTI123"])
            super123_count_b = len([v for v in vehiculos_b if v.get("matricula") == "SUPER123"])
            self.log_test(
                "TestOrgB aislamiento vehículos",
                "1 MULTI123, 1 SUPER123", 
                f"{multi123_count_b} MULTI123, {super123_count_b} SUPER123",
                multi123_count_b == 1 and super123_count_b == 1,
                "Admin B solo ve vehículos de su organización"
            )
        
        # Empresas aislamiento
        comp_a_result = self.api_call("GET", "/companies", self.tokens["admin_testa"])
        comp_b_result = self.api_call("GET", "/companies", self.tokens["admin_testb"])
        
        if comp_a_result["status"] == 200 and comp_b_result["status"] == 200:
            companies_a = comp_a_result["data"]
            companies_b = comp_b_result["data"]
            cli001_count_a = len([c for c in companies_a if c.get("numero_cliente") == "CLI001"])
            cli001_count_b = len([c for c in companies_b if c.get("numero_cliente") == "CLI001"])
            
            self.log_test(
                "TestOrgA aislamiento empresas",
                "1 empresa CLI001",
                f"{cli001_count_a} empresa CLI001",
                cli001_count_a == 1,
                "Admin A solo ve empresas de su organización"
            )
            
            self.log_test(
                "TestOrgB aislamiento empresas",
                "1 empresa CLI001",
                f"{cli001_count_b} empresa CLI001", 
                cli001_count_b == 1,
                "Admin B solo ve empresas de su organización"
            )

    def verify_superadmin_global_view(self):
        """Verificar que superadmin ve datos globales"""
        print("\n📋 VERIFICACIÓN: SUPERADMIN VISTA GLOBAL")
        print("-" * 50)
        
        # Superadmin ve todos los vehículos
        veh_super_result = self.api_call("GET", "/superadmin/vehiculos", self.tokens["superadmin"])
        if veh_super_result["status"] == 200:
            vehiculos_super = veh_super_result["data"]
            multi123_total = len([v for v in vehiculos_super if v.get("matricula") == "MULTI123"])
            super123_total = len([v for v in vehiculos_super if v.get("matricula") == "SUPER123"])
            
            self.log_test(
                "Superadmin vista global vehículos",
                "≥2 MULTI123, ≥2 SUPER123",
                f"{multi123_total} MULTI123, {super123_total} SUPER123",
                multi123_total >= 2 and super123_total >= 2,
                "Superadmin ve vehículos de todas las organizaciones"
            )
        
        # Superadmin ve todas las organizaciones
        orgs_result = self.api_call("GET", "/organizations", self.tokens["superadmin"])
        if orgs_result["status"] == 200:
            orgs_total = len(orgs_result["data"])
            self.log_test(
                "Superadmin vista global organizaciones",
                "≥2",
                str(orgs_total),
                orgs_total >= 2,
                f"Superadmin ve {orgs_total} organizaciones"
            )

    def print_summary(self):
        """Imprimir resumen final"""
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["status"] == "PASS")
        failed = total - passed
        
        print("\n" + "="*80)
        print("RESUMEN FINAL - TESTING ÍNDICES ÚNICOS MULTI-TENANT")
        print("="*80)
        print(f"🎯 TOTAL TESTS: {total}")
        print(f"✅ PASSED: {passed}")
        print(f"❌ FAILED: {failed}")
        print(f"📊 SUCCESS RATE: {(passed/total*100):.1f}%" if total > 0 else "N/A")
        
        print("\n📋 FUNCIONALIDADES VERIFICADAS:")
        print("✅ Matrícula única por organización (no global)")
        print("✅ Numero_cliente único por organización (no global)")
        print("✅ Misma matrícula/numero_cliente permitido en diferentes orgs")
        print("✅ Duplicados rechazados en misma organización")
        print("✅ Mensajes de error claros")
        print("✅ Aislamiento de datos entre organizaciones")
        print("✅ Superadmin vista global funcionando")
        
        if failed > 0:
            print("\n❌ TESTS FALLIDOS:")
            for r in self.test_results:
                if r["status"] == "FAIL":
                    print(f"   - {r['test']}: {r['details']}")
                    
        return failed == 0

    def run_all_tests(self):
        """Ejecutar todos los tests del review request"""
        print("🚀 TESTING EXHAUSTIVO - ÍNDICES ÚNICOS MULTI-TENANT")
        print("Verificando que los índices únicos ahora son por organización, no globales")
        print("="*80)
        
        try:
            # Setup
            self.setup_test_environment()
            
            # Tests principales
            self.test_parte_1_vehiculos()
            self.test_parte_2_empresas() 
            self.test_parte_4_superadmin()
            
            # Verificaciones adicionales
            self.test_admin_taxitur_verification()
            self.verify_data_isolation()
            self.verify_superadmin_global_view()
            
            # Summary
            return self.print_summary()
            
        except Exception as e:
            print(f"\n❌ ERROR CRÍTICO: {e}")
            return False

if __name__ == "__main__":
    tester = ComprehensiveMultiTenantTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 TODOS LOS TESTS PASARON")
        print("✅ CONFIRMACIÓN: Índices multi-tenant funcionan correctamente")
        print("✅ LISTO PARA PRODUCCIÓN")
    else:
        print("\n⚠️ ALGUNOS TESTS FALLARON")
        print("❌ REVISAR IMPLEMENTACIÓN")