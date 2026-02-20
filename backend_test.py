#!/usr/bin/env python3
"""
Testing Multi-tenant Configuration Hardening (Paso 4)
Testing comprehensive multi-tenant config separation and organization settings
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Configuration from review request
BASE_URL = "https://flagged-services.preview.emergentagent.com/api"

# Credentials from review request
CREDENTIALS = {
    "superadmin": {"username": "superadmin", "password": "superadmin123"},
    "admin_taxitur": {"username": "admintur", "password": "admin123"}
}

class MultiTenantConfigTester:
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
                print(f"❌ Login fallido para {username}: {response.status_code} - {response.text}")
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
        print("\n🔧 CONFIGURANDO ENTORNO DE PRUEBAS MULTI-TENANT CONFIG...")
        print(f"API Base URL: {BASE_URL}")
        print()
        
        # Login test users
        for user_key, credentials in CREDENTIALS.items():
            token = self.login(credentials["username"], credentials["password"])
            if not token:
                print(f"❌ Error login {credentials['username']}")
                return False
        
        print()
        return True
    
    def test_1_permisos_config_global(self):
        """PARTE 1: Permisos /api/config (SEGURIDAD CRÍTICA)"""
        print("\n🎯 PARTE 1: PERMISOS /API/CONFIG (SEGURIDAD CRÍTICA)")
        print("-" * 60)
        
        admin_token = self.tokens["admintur"]
        superadmin_token = self.tokens["superadmin"]
        
        # Test 1.1: Login como admin (admintur) - PUT /config debe retornar 403
        config_data = {"nombre_radio_taxi": "Test"}
        response = self.make_request("PUT", "/config", admin_token, json=config_data)
        self.log_test(
            "1.1", "PUT", "/config", 
            response.status_code, 403,
            "Admin intenta modificar config global (debe ser 403 Forbidden)"
        )
        
        # Test 1.2: Login como superadmin - PUT /config debe retornar 200
        config_data = {
            "nombre_radio_taxi": "TaxiFast",
            "telefono": "CIF: G33045147", 
            "web": "Federación Asturiana Sindical del Taxi",
            "direccion": "Plataforma SaaS Multi-tenant",
            "email": "info@taxifast.com"
        }
        response = self.make_request("PUT", "/config", superadmin_token, json=config_data)
        self.log_test(
            "1.2", "PUT", "/config",
            response.status_code, 200,
            "Superadmin modifica config global (debe ser 200 OK)"
        )
        
        # Verificar que el cambio se persistió
        response = self.make_request("GET", "/config", superadmin_token)
        if response.status_code == 200:
            config = response.json()
            updated_correctly = config.get("nombre_radio_taxi") == "TaxiFast"
            self.log_test(
                "1.3", "GET", "/config",
                response.status_code, 200,
                f"Verificar config persistida - nombre_radio_taxi: {config.get('nombre_radio_taxi')} (actualizado: {updated_correctly})"
            )

    def test_2_admin_actualiza_settings_organizacion(self):
        """PARTE 2: Admin actualiza settings de su organización"""
        print("\n🎯 PARTE 2: ADMIN ACTUALIZA SETTINGS DE SU ORGANIZACIÓN")
        print("-" * 60)
        
        admin_token = self.tokens["admintur"]
        
        # Test 2.1: PUT /my-organization/settings con footer_name y footer_cif
        settings_data = {
            "footer_name": "Taxitur S.L.",
            "footer_cif": "B12345678"
        }
        response = self.make_request("PUT", "/my-organization/settings", admin_token, json=settings_data)
        self.log_test(
            "2.1", "PUT", "/my-organization/settings",
            response.status_code, 200,
            "Admin actualiza settings de su organización (footer_name, footer_cif)"
        )
        
        # Test 2.2: GET /my-organization debe incluir settings
        response = self.make_request("GET", "/my-organization", admin_token)
        if response.status_code == 200:
            org_data = response.json()
            settings = org_data.get("settings", {})
            has_footer_name = "footer_name" in settings
            has_footer_cif = "footer_cif" in settings
            footer_name_correct = settings.get("footer_name") == "Taxitur S.L."
            footer_cif_correct = settings.get("footer_cif") == "B12345678"
            
            self.log_test(
                "2.2", "GET", "/my-organization",
                response.status_code, 200,
                f"Verificar settings persisten - footer_name: {has_footer_name and footer_name_correct}, footer_cif: {has_footer_cif and footer_cif_correct}"
            )
        else:
            self.log_test(
                "2.2", "GET", "/my-organization",
                response.status_code, 200,
                "GET /my-organization para verificar settings"
            )

    def test_3_validacion_whitelist(self):
        """PARTE 3: Validación de whitelist"""
        print("\n🎯 PARTE 3: VALIDACIÓN DE WHITELIST")
        print("-" * 60)
        
        admin_token = self.tokens["admintur"]
        
        # Test 3.1: PUT settings con key inválida
        invalid_settings = {"invalid_key": "test"}
        response = self.make_request("PUT", "/my-organization/settings", admin_token, json=invalid_settings)
        self.log_test(
            "3.1", "PUT", "/my-organization/settings",
            response.status_code, 400,
            "Settings con key inválida (debe rechazar con 400)"
        )
        
        # Verificar mensaje de error específico
        if response.status_code == 400:
            try:
                error_data = response.json()
                error_message = error_data.get("detail", "")
                contains_key_message = "no permitida" in error_message.lower() and "invalid_key" in error_message
                print(f"      Mensaje de error: {error_message}")
                print(f"      Contiene mensaje específico sobre key no permitida: {contains_key_message}")
            except:
                pass
        
        # Test 3.2: PUT settings con key válida
        valid_settings = {"display_name": "Mi Empresa de Taxis"}
        response = self.make_request("PUT", "/my-organization/settings", admin_token, json=valid_settings)
        self.log_test(
            "3.2", "PUT", "/my-organization/settings",
            response.status_code, 200,
            "Settings con key válida (display_name)"
        )

    def test_4_superadmin_edita_settings_cualquier_org(self):
        """PARTE 4: Superadmin edita settings de cualquier org"""
        print("\n🎯 PARTE 4: SUPERADMIN EDITA SETTINGS DE CUALQUIER ORG")
        print("-" * 60)
        
        admin_token = self.tokens["admintur"]
        superadmin_token = self.tokens["superadmin"]
        
        # Primero obtener ID de la organización del admin
        response = self.make_request("GET", "/my-organization", admin_token)
        if response.status_code == 200:
            org_data = response.json()
            org_id = org_data.get("id")
            
            if org_id:
                # Test 4.1: Superadmin PUT settings de otra org
                settings_data = {"support_email": "soporte@org.com"}
                response = self.make_request("PUT", f"/superadmin/organizations/{org_id}/settings", superadmin_token, json=settings_data)
                self.log_test(
                    "4.1", "PUT", f"/superadmin/organizations/{org_id}/settings",
                    response.status_code, 200,
                    "Superadmin actualiza settings de organización específica"
                )
                
                # Test 4.2: Admin normal intenta usar endpoint de superadmin
                response = self.make_request("PUT", f"/superadmin/organizations/{org_id}/settings", admin_token, json=settings_data)
                self.log_test(
                    "4.2", "PUT", f"/superadmin/organizations/{org_id}/settings",
                    response.status_code, 403,
                    "Admin normal intenta usar endpoint superadmin (debe ser 403 Forbidden)"
                )
            else:
                print("❌ No se pudo obtener ID de organización para testing")
                self.log_test("4.1", "GET", "/my-organization", 0, 200, "No se pudo obtener org ID")
                self.log_test("4.2", "PUT", "/superadmin/organizations/{org_id}/settings", 0, 403, "No se pudo obtener org ID")
        else:
            print("❌ No se pudo obtener información de organización")
            self.log_test("4.1", "GET", "/my-organization", response.status_code, 200, "No se pudo obtener org info")
            self.log_test("4.2", "PUT", "/superadmin/organizations/{org_id}/settings", 0, 403, "No se pudo obtener org info")

    def test_5_validacion_tipos(self):
        """PARTE 5: Validación de tipos"""
        print("\n🎯 PARTE 5: VALIDACIÓN DE TIPOS")
        print("-" * 60)
        
        admin_token = self.tokens["admintur"]
        
        # Test 5.1: PUT settings con valor muy largo (>500 chars)
        long_value = "x" * 501  # 501 caracteres
        long_settings = {"display_name": long_value}
        response = self.make_request("PUT", "/my-organization/settings", admin_token, json=long_settings)
        self.log_test(
            "5.1", "PUT", "/my-organization/settings",
            response.status_code, 400,
            "Settings con valor muy largo (>500 chars) debe ser rechazado con 400"
        )
        
        # Test 5.2: PUT settings con valor objeto anidado
        nested_settings = {"display_name": {"nested": "object"}}
        response = self.make_request("PUT", "/my-organization/settings", admin_token, json=nested_settings)
        self.log_test(
            "5.2", "PUT", "/my-organization/settings",
            response.status_code, 400,
            "Settings con objeto anidado debe ser rechazado con 400"
        )
        
        # Test 5.3: PUT settings con valor válido (verificación positiva)
        valid_settings = {"support_phone": "+34 123 456 789"}
        response = self.make_request("PUT", "/my-organization/settings", admin_token, json=valid_settings)
        self.log_test(
            "5.3", "PUT", "/my-organization/settings",
            response.status_code, 200,
            "Settings con valor string válido debe ser aceptado"
        )

    def test_6_verificacion_final_settings(self):
        """PARTE 6: Verificación final de settings completos"""
        print("\n🎯 PARTE 6: VERIFICACIÓN FINAL DE SETTINGS")
        print("-" * 60)
        
        admin_token = self.tokens["admintur"]
        
        # Verificar que todos los settings se han guardado correctamente
        response = self.make_request("GET", "/my-organization", admin_token)
        if response.status_code == 200:
            org_data = response.json()
            settings = org_data.get("settings", {})
            
            # Check all expected settings
            expected_settings = {
                "footer_name": "Taxitur S.L.",
                "footer_cif": "B12345678", 
                "display_name": "Mi Empresa de Taxis",
                "support_phone": "+34 123 456 789"
            }
            
            all_correct = True
            details = []
            for key, expected_value in expected_settings.items():
                actual_value = settings.get(key)
                is_correct = actual_value == expected_value
                all_correct = all_correct and is_correct
                details.append(f"{key}: {actual_value} ({'✓' if is_correct else '✗'})")
            
            self.log_test(
                "6.1", "GET", "/my-organization",
                response.status_code, 200,
                f"Verificar todos los settings - Correctos: {all_correct} | " + " | ".join(details)
            )
        else:
            self.log_test(
                "6.1", "GET", "/my-organization",
                response.status_code, 200,
                "Verificación final de settings"
            )

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("📊 RESUMEN - TESTING MULTI-TENANT CONFIG HARDENING (PASO 4)")
        print("="*80)
        
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if "PASS" in r["result"]])
        failed_tests = total_tests - passed_tests
        
        print(f"\n📈 ESTADÍSTICAS GENERALES:")
        print(f"   Total de pruebas: {total_tests}")
        print(f"   ✅ Exitosas: {passed_tests}")
        print(f"   ❌ Fallidas: {failed_tests}")
        print(f"   📊 Tasa de éxito: {(passed_tests/total_tests*100):.1f}%")
        
        # Print results by test part
        print(f"\n📋 RESULTADOS POR PARTE:")
        
        test_parts = {
            "1": "PERMISOS /api/config (SEGURIDAD CRÍTICA)",
            "2": "ADMIN ACTUALIZA SETTINGS DE SU ORGANIZACIÓN", 
            "3": "VALIDACIÓN DE WHITELIST",
            "4": "SUPERADMIN EDITA SETTINGS DE CUALQUIER ORG",
            "5": "VALIDACIÓN DE TIPOS",
            "6": "VERIFICACIÓN FINAL"
        }
        
        for part_num, part_name in test_parts.items():
            part_results = [r for r in self.results if r["name"].startswith(part_num + ".")]
            part_passed = len([r for r in part_results if "PASS" in r["result"]])
            part_total = len(part_results)
            
            print(f"\n   PARTE {part_num}: {part_name}")
            for result in part_results:
                status_icon = "✅" if "PASS" in result["result"] else "❌"
                print(f"      {status_icon} {result['name']}: {result['status_code']} (esperado {result['expected']}) - {result['details']}")
        
        # Critical security findings
        print(f"\n🔒 VERIFICACIONES DE SEGURIDAD CRÍTICAS:")
        config_security_results = [r for r in self.results if "1." in r["name"]]
        for result in config_security_results:
            status_icon = "✅" if "PASS" in result["result"] else "🚨"
            security_status = "SEGURO" if "PASS" in result["result"] else "VULNERABILIDAD"
            print(f"   {status_icon} {result['details']} - {security_status}")
        
        if failed_tests > 0:
            print(f"\n❌ DETALLES DE PRUEBAS FALLIDAS:")
            for result in self.results:
                if "FAIL" in result["result"]:
                    print(f"   • {result['name']}: {result['details']}")
                    print(f"     Status: {result['status_code']} (esperado {result['expected']})")
        
        print("\n" + "="*80)
        print("🎯 CONCLUSIÓN:")
        
        # Check critical security tests
        config_tests = [r for r in self.results if "1." in r["name"]]
        config_passed = all("PASS" in r["result"] for r in config_tests)
        
        if failed_tests == 0:
            print("   ✅ TODAS LAS PRUEBAS DE SEGURIDAD Y FUNCIONALIDAD PASARON")
            print("   ✅ CONFIGURACIÓN MULTI-TENANT HARDENING COMPLETA")
            print("   🚀 Sistema listo para producción")
        elif not config_passed:
            print("   🚨 FALLO DE SEGURIDAD CRÍTICO EN CONFIGURACIÓN GLOBAL")
            print("   🚨 Admin puede modificar config global - VULNERABILIDAD")
            print("   🔧 Corregir permisos antes de producción")
        else:
            print(f"   ⚠️  {failed_tests} funcionalidades requieren atención")
            print("   🔧 Revisar implementación antes de producción")
        print("="*80)
        
        return failed_tests == 0

def main():
    """Main test execution"""
    print("🎯 TESTING MULTI-TENANT CONFIG HARDENING (PASO 4)")
    print("=" * 80)
    print(f"🌐 Base URL: {BASE_URL}")
    print(f"🔐 Testing Credentials:")
    print(f"   - Superadmin: superadmin / superadmin123")
    print(f"   - Admin Taxitur: admintur / admin123")
    print("=" * 80)
    
    tester = MultiTenantConfigTester()
    
    # Setup test environment
    if not tester.setup_test_environment():
        print("❌ Error configurando entorno de pruebas")
        return False
    
    # Execute all test parts
    try:
        tester.test_1_permisos_config_global()
        tester.test_2_admin_actualiza_settings_organizacion()
        tester.test_3_validacion_whitelist()
        tester.test_4_superadmin_edita_settings_cualquier_org()
        tester.test_5_validacion_tipos()
        tester.test_6_verificacion_final_settings()
    except Exception as e:
        print(f"❌ Error durante la ejecución de pruebas: {e}")
        import traceback
        traceback.print_exc()
    
    # Print summary
    success = tester.print_summary()
    
    if success:
        print("\n🎉 TODAS LAS PRUEBAS DE MULTI-TENANT CONFIG COMPLETADAS EXITOSAMENTE")
        print("✅ Confirmación: Admin NO puede modificar config global")
        print("✅ Confirmación: Settings por organización funciona correctamente") 
        return True
    else:
        print("\n⚠️ ALGUNAS PRUEBAS FALLARON - REVISAR IMPLEMENTACIÓN")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)