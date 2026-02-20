#!/usr/bin/env python3
"""
TESTING EXHAUSTIVO DE ÍNDICES ÚNICOS MULTI-TENANT

Verificar que los índices únicos ahora son por organización, no globales.
La misma matrícula/número de cliente puede existir en diferentes organizaciones 
pero NO puede duplicarse dentro de la misma organización.

API Base URL: https://flagged-services.preview.emergentagent.com/api

CREDENCIALES:
- Superadmin: superadmin / superadmin123  
- Admin Taxitur: admintur / admin123
"""

import requests
import json
import sys
from typing import Dict, List, Any, Optional

# Configuration
BASE_URL = "https://flagged-services.preview.emergentagent.com/api"
SUPERADMIN_CREDENTIALS = {"username": "superadmin", "password": "superadmin123"}
ADMIN_TAXITUR_CREDENTIALS = {"username": "admintur", "password": "admin123"}

class MultiTenantTester:
    def __init__(self):
        self.session = requests.Session()
        self.tokens = {}
        self.org_ids = {}
        self.test_results = []
        self.admin_users = {}  # Store created admin users
        
    def log_test(self, test_name: str, expected: str, actual: str, passed: bool, details: str = ""):
        """Log test result"""
        status = "PASS" if passed else "FAIL" 
        result = {
            "test": test_name,
            "expected": expected,
            "actual": actual,
            "status": status,
            "details": details
        }
        self.test_results.append(result)
        print(f"[{status}] {test_name}: Esperado {expected}, Obtenido {actual}")
        if details:
            print(f"      Detalles: {details}")
        
    def print_summary(self):
        """Print test summary"""
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["status"] == "PASS")
        failed = total - passed
        
        print("\n" + "="*80)
        print("RESUMEN DE PRUEBAS - ÍNDICES ÚNICOS MULTI-TENANT")
        print("="*80)
        print(f"Total tests: {total}")
        print(f"✅ PASSED: {passed}")
        print(f"❌ FAILED: {failed}")
        print(f"Success rate: {(passed/total*100):.1f}%" if total > 0 else "N/A")
        
        if failed > 0:
            print("\n❌ TESTS FALLIDOS:")
            for r in self.test_results:
                if r["status"] == "FAIL":
                    print(f"  - {r['test']}: {r['details']}")
        
        return failed == 0

    def login(self, credentials: Dict[str, str], role_name: str) -> str:
        """Login and get token"""
        print(f"\n🔐 LOGIN {role_name}...")
        response = self.session.post(f"{BASE_URL}/auth/login", json=credentials)
        
        if response.status_code == 200:
            token_data = response.json()
            token = token_data["access_token"]
            user = token_data["user"]
            self.tokens[role_name] = token
            print(f"✅ Login exitoso: {user['nombre']} (role: {user['role']})")
            return token
        else:
            error_msg = f"Login fallido {response.status_code}: {response.text}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)

    def api_call(self, method: str, endpoint: str, token: str, data: Dict = None, expected_status: int = 200) -> Dict:
        """Make API call with token"""
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{BASE_URL}{endpoint}"
        
        if method == "GET":
            response = self.session.get(url, headers=headers)
        elif method == "POST":
            response = self.session.post(url, headers=headers, json=data)
        elif method == "PUT":
            response = self.session.put(url, headers=headers, json=data)
        elif method == "DELETE":
            response = self.session.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")
            
        result = {
            "status_code": response.status_code,
            "data": response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
            "success": response.status_code == expected_status
        }
        
        return result

    def create_test_organizations(self) -> Dict[str, str]:
        """Crear organizaciones de prueba"""
        print("\n🏢 CREANDO ORGANIZACIONES DE PRUEBA...")
        
        superadmin_token = self.tokens["superadmin"]
        
        # Create TestOrgA
        org_a_data = {
            "nombre": "TestOrgA",
            "slug": "testorga", 
            "cif": "A12345678",
            "direccion": "Test Address A",
            "localidad": "Test City A",
            "provincia": "Test Province A"
        }
        
        result_a = self.api_call("POST", "/organizations", superadmin_token, org_a_data, 200)
        self.log_test(
            "Crear TestOrgA",
            "200",
            str(result_a["status_code"]),
            result_a["success"],
            f"Org ID: {result_a['data']['id'] if result_a['success'] else 'N/A'}"
        )
        
        if result_a["success"]:
            self.org_ids["TestOrgA"] = result_a["data"]["id"]
        
        # Create TestOrgB
        org_b_data = {
            "nombre": "TestOrgB",
            "slug": "testorgb",
            "cif": "B87654321", 
            "direccion": "Test Address B",
            "localidad": "Test City B",
            "provincia": "Test Province B"
        }
        
        result_b = self.api_call("POST", "/organizations", superadmin_token, org_b_data, 200)
        self.log_test(
            "Crear TestOrgB", 
            "200",
            str(result_b["status_code"]),
            result_b["success"],
            f"Org ID: {result_b['data']['id'] if result_b['success'] else 'N/A'}"
        )
        
        if result_b["success"]:
            self.org_ids["TestOrgB"] = result_b["data"]["id"]
            
        return self.org_ids

    def create_test_admins(self):
        """Crear administradores para las organizaciones de prueba"""
        print("\n👥 CREANDO ADMINS DE ORGANIZACIONES...")
        
        superadmin_token = self.tokens["superadmin"]
        
        # Use timestamp to ensure unique usernames
        import time
        timestamp = str(int(time.time()))[-6:]  # Last 6 digits
        
        # Create admin for TestOrgA
        admin_a_username = f"admin_testa_{timestamp}"
        admin_a_data = {
            "username": admin_a_username,
            "password": "admin123", 
            "nombre": "Admin Test A"
        }
        
        result_a = self.api_call(
            "POST", 
            f"/organizations/{self.org_ids['TestOrgA']}/admin", 
            superadmin_token, 
            admin_a_data, 
            200
        )
        self.log_test(
            f"Crear {admin_a_username}",
            "200",
            str(result_a["status_code"]), 
            result_a["success"],
            f"Admin creado para TestOrgA: {result_a['data'].get('detail', 'OK') if not result_a['success'] else 'OK'}"
        )
        
        # Create admin for TestOrgB
        admin_b_username = f"admin_testb_{timestamp}"
        admin_b_data = {
            "username": admin_b_username,
            "password": "admin123",
            "nombre": "Admin Test B"
        }
        
        result_b = self.api_call(
            "POST",
            f"/organizations/{self.org_ids['TestOrgB']}/admin",
            superadmin_token,
            admin_b_data,
            200
        )
        self.log_test(
            f"Crear {admin_b_username}", 
            "200",
            str(result_b["status_code"]),
            result_b["success"],
            f"Admin creado para TestOrgB: {result_b['data'].get('detail', 'OK') if not result_b['success'] else 'OK'}"
        )

        # Login as both admins to get their tokens
        if result_a["success"]:
            admin_a_token = self.login({"username": admin_a_username, "password": "admin123"}, "admin_testa")
            self.tokens["admin_testa"] = admin_a_token
        else:
            raise Exception(f"Failed to create admin for TestOrgA: {result_a['data']}")
            
        if result_b["success"]:
            admin_b_token = self.login({"username": admin_b_username, "password": "admin123"}, "admin_testb") 
            self.tokens["admin_testb"] = admin_b_token
        else:
            raise Exception(f"Failed to create admin for TestOrgB: {result_b['data']}")

    def test_vehiculos_multitenant_matricula(self):
        """PARTE 1: Vehículos - misma matrícula en diferentes orgs"""
        print("\n🚗 PARTE 1: TESTING VEHÍCULOS - MATRÍCULA MULTI-TENANT")
        
        matricula = "MULTI123"
        
        # Test 1.1: Login como admin_testa y crear vehículo con MULTI123
        print(f"\n1.1 Admin TestA crear vehículo con matrícula '{matricula}'")
        vehiculo_data_a = {
            "matricula": matricula,
            "plazas": 4,
            "marca": "Ford",
            "modelo": "Focus", 
            "km_iniciales": 50000,
            "fecha_compra": "01/01/2020",
            "activo": True
        }
        
        result_a1 = self.api_call("POST", "/vehiculos", self.tokens["admin_testa"], vehiculo_data_a, 200)
        self.log_test(
            f"TestOrgA: POST /vehiculos matrícula {matricula}",
            "200 (OK)",
            str(result_a1["status_code"]),
            result_a1["success"],
            "Primera vez en TestOrgA - debe permitir" 
        )
        
        # Test 1.2: Login como admin_testb y crear vehículo con misma matrícula MULTI123
        print(f"\n1.2 Admin TestB crear vehículo con misma matrícula '{matricula}' (diferente org)")
        vehiculo_data_b = {
            "matricula": matricula,
            "plazas": 5,
            "marca": "Volkswagen", 
            "modelo": "Passat",
            "km_iniciales": 30000,
            "fecha_compra": "15/06/2021", 
            "activo": True
        }
        
        result_b1 = self.api_call("POST", "/vehiculos", self.tokens["admin_testb"], vehiculo_data_b, 200)
        self.log_test(
            f"TestOrgB: POST /vehiculos matrícula {matricula}",
            "200 (OK - diferente org)",
            str(result_b1["status_code"]),
            result_b1["success"],
            "Misma matrícula en diferente org - debe permitir"
        )
        
        # Test 1.3: Admin TestB intenta crear otro vehículo con misma matrícula (duplicado en misma org)
        print(f"\n1.3 Admin TestB intentar duplicar matrícula '{matricula}' en misma org")
        vehiculo_data_b2 = {
            "matricula": matricula,
            "plazas": 4,
            "marca": "Renault",
            "modelo": "Megane", 
            "km_iniciales": 25000,
            "fecha_compra": "01/12/2022",
            "activo": True
        }
        
        result_b2 = self.api_call("POST", "/vehiculos", self.tokens["admin_testb"], vehiculo_data_b2, 400)
        self.log_test(
            f"TestOrgB: POST /vehiculos matrícula {matricula} (duplicado)", 
            "400 (ERROR - duplicado en misma org)",
            str(result_b2["status_code"]),
            result_b2["success"],
            f"Mensaje: {result_b2['data'].get('detail', 'N/A') if result_b2['status_code'] == 400 else 'N/A'}"
        )
        
        # Verificar mensaje de error específico
        if result_b2["status_code"] == 400 and isinstance(result_b2["data"], dict):
            error_msg = result_b2["data"].get("detail", "")
            expected_msg = "La matricula ya existe en tu organizacion"
            msg_correct = expected_msg.lower() in error_msg.lower()
            self.log_test(
                "Mensaje error matrícula duplicada",
                f"'{expected_msg}'",
                f"'{error_msg}'",
                msg_correct,
                "Verificar mensaje de error claro"
            )

    def test_empresas_multitenant_numero_cliente(self):
        """PARTE 2: Empresas - mismo numero_cliente en diferentes orgs"""
        print("\n🏢 PARTE 2: TESTING EMPRESAS - NUMERO_CLIENTE MULTI-TENANT")
        
        numero_cliente = "CLI001"
        
        # Test 2.1: Admin TestA crear empresa con numero_cliente CLI001
        print(f"\n2.1 Admin TestA crear empresa con numero_cliente '{numero_cliente}'")
        empresa_data_a = {
            "nombre": "EmpresaX",
            "numero_cliente": numero_cliente,
            "cif": "B11111111",
            "direccion": "Direccion A",
            "telefono": "111111111"
        }
        
        result_a1 = self.api_call("POST", "/companies", self.tokens["admin_testa"], empresa_data_a, 200)
        self.log_test(
            f"TestOrgA: POST /companies numero_cliente {numero_cliente}",
            "200 (OK)",
            str(result_a1["status_code"]),
            result_a1["success"],
            "Primera vez en TestOrgA - debe permitir"
        )
        
        # Test 2.2: Admin TestB crear empresa con mismo numero_cliente
        print(f"\n2.2 Admin TestB crear empresa con mismo numero_cliente '{numero_cliente}' (diferente org)")
        empresa_data_b = {
            "nombre": "EmpresaX",
            "numero_cliente": numero_cliente,
            "cif": "B22222222",
            "direccion": "Direccion B",
            "telefono": "222222222"
        }
        
        result_b1 = self.api_call("POST", "/companies", self.tokens["admin_testb"], empresa_data_b, 200)
        self.log_test(
            f"TestOrgB: POST /companies numero_cliente {numero_cliente}",
            "200 (OK - diferente org)",
            str(result_b1["status_code"]),
            result_b1["success"], 
            "Mismo numero_cliente en diferente org - debe permitir"
        )
        
        # Test 2.3: Admin TestB intentar crear otra empresa con mismo numero_cliente (duplicado en misma org)
        print(f"\n2.3 Admin TestB intentar duplicar numero_cliente '{numero_cliente}' en misma org")
        empresa_data_b2 = {
            "nombre": "EmpresaY",
            "numero_cliente": numero_cliente,
            "cif": "B33333333",
            "direccion": "Direccion C",
            "telefono": "333333333"
        }
        
        result_b2 = self.api_call("POST", "/companies", self.tokens["admin_testb"], empresa_data_b2, 400)
        self.log_test(
            f"TestOrgB: POST /companies numero_cliente {numero_cliente} (duplicado)",
            "400 (ERROR - duplicado en misma org)",
            str(result_b2["status_code"]),
            result_b2["success"],
            f"Mensaje: {result_b2['data'].get('detail', 'N/A') if result_b2['status_code'] == 400 else 'N/A'}"
        )
        
        # Verificar mensaje de error específico
        if result_b2["status_code"] == 400 and isinstance(result_b2["data"], dict):
            error_msg = result_b2["data"].get("detail", "")
            expected_msg = "El numero de cliente ya existe en tu organizacion"
            msg_correct = expected_msg.lower() in error_msg.lower()
            self.log_test(
                "Mensaje error numero_cliente duplicado",
                f"'{expected_msg}'",
                f"'{error_msg}'",
                msg_correct,
                "Verificar mensaje de error claro"
            )

    def test_superadmin_vehiculos_multitenant(self):
        """PARTE 4: Superadmin crea vehículos en diferentes orgs"""
        print("\n👑 PARTE 4: TESTING SUPERADMIN - VEHÍCULOS MULTI-TENANT")
        
        matricula = "SUPER123"
        
        # Test 4.1: Superadmin crear vehículo con SUPER123 en TestOrgA
        print(f"\n4.1 Superadmin crear vehículo matrícula '{matricula}' en TestOrgA")
        vehiculo_super_a = {
            "matricula": matricula,
            "organization_id": self.org_ids["TestOrgA"],
            "plazas": 4,
            "marca": "Mercedes",
            "modelo": "E-Class",
            "km_iniciales": 80000,
            "fecha_compra": "01/03/2019",
            "activo": True
        }
        
        result_sa1 = self.api_call("POST", "/superadmin/vehiculos", self.tokens["superadmin"], vehiculo_super_a, 200)
        self.log_test(
            f"Superadmin: POST vehiculo {matricula} en TestOrgA",
            "200 (OK)",
            str(result_sa1["status_code"]),
            result_sa1["success"],
            "Primera vez matrícula SUPER123 en TestOrgA"
        )
        
        # Test 4.2: Superadmin crear vehículo con SUPER123 en TestOrgB  
        print(f"\n4.2 Superadmin crear vehículo matrícula '{matricula}' en TestOrgB")
        vehiculo_super_b = {
            "matricula": matricula,
            "organization_id": self.org_ids["TestOrgB"],
            "plazas": 5,
            "marca": "BMW",
            "modelo": "Serie 3",
            "km_iniciales": 60000, 
            "fecha_compra": "15/08/2020",
            "activo": True
        }
        
        result_sa2 = self.api_call("POST", "/superadmin/vehiculos", self.tokens["superadmin"], vehiculo_super_b, 200)
        self.log_test(
            f"Superadmin: POST vehiculo {matricula} en TestOrgB",
            "200 (OK - diferente org)",
            str(result_sa2["status_code"]),
            result_sa2["success"], 
            "Misma matrícula en diferente org - debe permitir"
        )
        
        # Test 4.3: Superadmin intentar duplicar SUPER123 en TestOrgA
        print(f"\n4.3 Superadmin intentar duplicar matrícula '{matricula}' en TestOrgA")
        vehiculo_super_a2 = {
            "matricula": matricula,
            "organization_id": self.org_ids["TestOrgA"], 
            "plazas": 4,
            "marca": "Audi",
            "modelo": "A4",
            "km_iniciales": 90000,
            "fecha_compra": "01/10/2021",
            "activo": True
        }
        
        result_sa3 = self.api_call("POST", "/superadmin/vehiculos", self.tokens["superadmin"], vehiculo_super_a2, 400)
        self.log_test(
            f"Superadmin: POST vehiculo {matricula} en TestOrgA (duplicado)",
            "400 (ERROR - duplicado en misma org)",
            str(result_sa3["status_code"]),
            result_sa3["success"],
            f"Mensaje: {result_sa3['data'].get('detail', 'N/A') if result_sa3['status_code'] == 400 else 'N/A'}"
        )

    def verify_cross_org_data_isolation(self):
        """Verificar aislamiento de datos entre organizaciones"""
        print("\n🔒 VERIFICACIÓN: AISLAMIENTO DE DATOS ENTRE ORGANIZACIONES")
        
        # Test: Admin TestA debería ver solo sus vehículos
        result_a = self.api_call("GET", "/vehiculos", self.tokens["admin_testa"], expected_status=200)
        vehiculos_a = result_a["data"] if result_a["success"] else []
        
        # Test: Admin TestB debería ver solo sus vehículos  
        result_b = self.api_call("GET", "/vehiculos", self.tokens["admin_testb"], expected_status=200)
        vehiculos_b = result_b["data"] if result_b["success"] else []
        
        # Contar vehículos con matrícula MULTI123 y SUPER123 en cada org
        multi123_in_a = len([v for v in vehiculos_a if v.get("matricula") == "MULTI123"])
        multi123_in_b = len([v for v in vehiculos_b if v.get("matricula") == "MULTI123"])
        super123_in_a = len([v for v in vehiculos_a if v.get("matricula") == "SUPER123"]) 
        super123_in_b = len([v for v in vehiculos_b if v.get("matricula") == "SUPER123"])
        
        self.log_test(
            "Aislamiento vehiculos TestOrgA",
            "1 MULTI123, 1 SUPER123",
            f"{multi123_in_a} MULTI123, {super123_in_a} SUPER123",
            multi123_in_a == 1 and super123_in_a == 1,
            f"TestOrgA solo ve sus propios vehículos"
        )
        
        self.log_test(
            "Aislamiento vehiculos TestOrgB", 
            "1 MULTI123, 1 SUPER123",
            f"{multi123_in_b} MULTI123, {super123_in_b} SUPER123",
            multi123_in_b == 1 and super123_in_b == 1,
            f"TestOrgB solo ve sus propios vehículos"
        )

        # Test: Admin TestA debería ver solo sus empresas
        result_comp_a = self.api_call("GET", "/companies", self.tokens["admin_testa"], expected_status=200)
        companies_a = result_comp_a["data"] if result_comp_a["success"] else []
        
        # Test: Admin TestB debería ver solo sus empresas
        result_comp_b = self.api_call("GET", "/companies", self.tokens["admin_testb"], expected_status=200)
        companies_b = result_comp_b["data"] if result_comp_b["success"] else []
        
        # Contar empresas con numero_cliente CLI001 en cada org
        cli001_in_a = len([c for c in companies_a if c.get("numero_cliente") == "CLI001"])
        cli001_in_b = len([c for c in companies_b if c.get("numero_cliente") == "CLI001"])
        
        self.log_test(
            "Aislamiento empresas TestOrgA",
            "1 empresa CLI001",
            f"{cli001_in_a} empresa CLI001", 
            cli001_in_a == 1,
            f"TestOrgA solo ve sus propias empresas"
        )
        
        self.log_test(
            "Aislamiento empresas TestOrgB",
            "1 empresa CLI001", 
            f"{cli001_in_b} empresa CLI001",
            cli001_in_b == 1,
            f"TestOrgB solo ve sus propias empresas"
        )

    def test_existing_taxitur_admin(self):
        """Test con admin Taxitur existente si está disponible"""
        print("\n🚕 TESTING CON ADMIN TAXITUR (si existe)")
        
        try:
            # Intentar login con admintur/admin123
            admintur_token = self.login(ADMIN_TAXITUR_CREDENTIALS, "admintur")
            
            # Si el login es exitoso, hacer algunas pruebas básicas
            result = self.api_call("GET", "/vehiculos", admintur_token, expected_status=200)
            self.log_test(
                "Admin Taxitur - GET vehiculos",
                "200",
                str(result["status_code"]),
                result["success"],
                f"Admin Taxitur puede acceder a sus vehículos ({len(result['data'] if result['success'] else [])} encontrados)"
            )
            
            result = self.api_call("GET", "/companies", admintur_token, expected_status=200)
            self.log_test(
                "Admin Taxitur - GET companies", 
                "200",
                str(result["status_code"]),
                result["success"],
                f"Admin Taxitur puede acceder a sus empresas ({len(result['data'] if result['success'] else [])} encontradas)"
            )
            
        except Exception as e:
            self.log_test(
                "Login Admin Taxitur",
                "200",
                "FAILED", 
                False,
                f"Admin Taxitur no disponible o credenciales incorrectas: {e}"
            )

    def test_superadmin_global_view(self):
        """Verificar que superadmin puede ver datos de todas las organizaciones"""
        print("\n👑 VERIFICACIÓN: SUPERADMIN VE DATOS GLOBALES")
        
        # Superadmin debería ver todas las organizaciones
        result_orgs = self.api_call("GET", "/organizations", self.tokens["superadmin"], expected_status=200)
        orgs = result_orgs["data"] if result_orgs["success"] else []
        orgs_count = len(orgs)
        
        self.log_test(
            "Superadmin ve todas las organizaciones",
            "≥ 2 (TestOrgA + TestOrgB + posibles otras)",
            f"{orgs_count} organizaciones",
            orgs_count >= 2,
            f"Superadmin debe ver todas las orgs, incluyendo las de prueba"
        )
        
        # Superadmin debería ver todos los vehículos 
        result_veh = self.api_call("GET", "/superadmin/vehiculos", self.tokens["superadmin"], expected_status=200)
        vehiculos = result_veh["data"] if result_veh["success"] else []
        
        # Contar vehículos MULTI123 y SUPER123 que el superadmin puede ver
        multi123_total = len([v for v in vehiculos if v.get("matricula") == "MULTI123"])
        super123_total = len([v for v in vehiculos if v.get("matricula") == "SUPER123"])
        
        self.log_test(
            "Superadmin ve vehículos multi-tenant", 
            "2 MULTI123, 2 SUPER123",
            f"{multi123_total} MULTI123, {super123_total} SUPER123",
            multi123_total >= 2 and super123_total >= 2,
            "Superadmin debe ver vehículos de todas las organizaciones"
        )

    def cleanup_test_data(self):
        """Limpieza de datos de prueba (opcional)"""
        print("\n🧹 LIMPIEZA DE DATOS DE PRUEBA...")
        
        # Solo limpiar si las organizaciones de prueba fueron creadas
        for org_name in ["TestOrgA", "TestOrgB"]:
            if org_name in self.org_ids:
                try:
                    org_id = self.org_ids[org_name]
                    result = self.api_call("DELETE", f"/organizations/{org_id}", self.tokens["superadmin"], expected_status=200)
                    self.log_test(
                        f"Limpiar {org_name}",
                        "200 (eliminado)",
                        str(result["status_code"]),
                        result["success"],
                        f"Organización de prueba {org_name} eliminada"
                    )
                except Exception as e:
                    print(f"⚠️ No se pudo limpiar {org_name}: {e}")

    def run_all_tests(self):
        """Ejecutar todos los tests"""
        print("🚀 INICIANDO TESTING EXHAUSTIVO DE ÍNDICES ÚNICOS MULTI-TENANT")
        print("="*80)
        
        try:
            # Step 1: Login como superadmin
            self.login(SUPERADMIN_CREDENTIALS, "superadmin")
            
            # Step 2: Crear organizaciones de prueba
            org_ids = self.create_test_organizations()
            if len(org_ids) < 2:
                raise Exception("❌ No se pudieron crear las organizaciones de prueba")
                
            # Step 3: Crear admins de organizaciones
            self.create_test_admins()
            
            # Step 4: Test vehículos multi-tenant
            self.test_vehiculos_multitenant_matricula()
            
            # Step 5: Test empresas multi-tenant  
            self.test_empresas_multitenant_numero_cliente()
            
            # Step 6: Test superadmin vehículos multi-tenant
            self.test_superadmin_vehiculos_multitenant()
            
            # Step 7: Verificar aislamiento de datos
            self.verify_cross_org_data_isolation()
            
            # Step 8: Verificar superadmin vista global
            self.test_superadmin_global_view()
            
            # Step 9: Test con admin Taxitur existente (si está disponible)
            self.test_existing_taxitur_admin()
            
        except Exception as e:
            print(f"❌ ERROR CRÍTICO: {e}")
            self.log_test("Setup general", "Success", "FAILED", False, str(e))
        
        finally:
            # Step 10: Cleanup (comentado para preservar datos de debug)
            # self.cleanup_test_data()
            pass
        
        # Print summary
        success = self.print_summary()
        return success

if __name__ == "__main__":
    tester = MultiTenantTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 TODOS LOS TESTS PASARON - ÍNDICES MULTI-TENANT FUNCIONANDO CORRECTAMENTE")
        sys.exit(0)
    else:
        print("\n❌ ALGUNOS TESTS FALLARON - REVISAR IMPLEMENTACIÓN")
        sys.exit(1)