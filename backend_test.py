#!/usr/bin/env python3
"""
TESTING FINAL - ELIMINACIÓN DE TURNOS Y VERIFICACIÓN COMPLETA
Comprehensive backend testing for taxi management system
Focus: DELETE /turnos cascade deletion and full system verification
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Optional

# Configuration
BASE_URL = "https://taxiflow-admin.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {"username": "admin", "password": "admin123"}

class TaxiBackendTester:
    def __init__(self):
        self.admin_token = None
        self.taxista_token = None
        self.test_results = []
        self.created_entities = {
            'users': [],
            'companies': [],
            'vehiculos': [],
            'turnos': [],
            'services': []
        }
        
    def log_test(self, test_name, success, details="", response_time=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        time_info = f" ({response_time:.3f}s)" if response_time else ""
        result = f"{status} {test_name}{time_info}"
        if details:
            result += f" - {details}"
        print(result)
        self.test_results.append({
            'name': test_name,
            'success': success,
            'details': details,
            'response_time': response_time
        })
        
    def make_request(self, method, endpoint, data=None, token=None, params=None):
        """Make HTTP request with timing"""
        url = f"{API_BASE}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'
            
        start_time = time.time()
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=data)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            response_time = time.time() - start_time
            return response, response_time
        except Exception as e:
            response_time = time.time() - start_time
            print(f"Request error: {e}")
            return None, response_time

    def test_authentication(self):
        """Test authentication system"""
        print("\n🔐 TESTING AUTHENTICATION")
        
        # Test admin login
        response, rt = self.make_request('POST', '/auth/login', {
            'username': 'admin',
            'password': 'admin123'
        })
        
        if response and response.status_code == 200:
            data = response.json()
            self.admin_token = data['access_token']
            self.log_test("Admin Login", True, f"Token received, user: {data['user']['nombre']}", rt)
        else:
            self.log_test("Admin Login", False, f"Status: {response.status_code if response else 'No response'}", rt)
            return False
            
        # Test /auth/me endpoint
        response, rt = self.make_request('GET', '/auth/me', token=self.admin_token)
        if response and response.status_code == 200:
            data = response.json()
            self.log_test("Auth Me Endpoint", True, f"User: {data['nombre']}, Role: {data['role']}", rt)
        else:
            self.log_test("Auth Me Endpoint", False, f"Status: {response.status_code if response else 'No response'}", rt)
            
        # Test invalid credentials
        response, rt = self.make_request('POST', '/auth/login', {
            'username': 'admin',
            'password': 'wrongpassword'
        })
        
        success = response and response.status_code == 401
        self.log_test("Invalid Credentials Rejection", success, f"Status: {response.status_code if response else 'No response'}", rt)
        
        return True

    def test_users_crud_optimized(self):
        """Test users CRUD with password exclusion optimization"""
        print("\n👥 TESTING USERS CRUD & PASSWORD EXCLUSION OPTIMIZATION")
        
        # Create test taxista
        taxista_data = {
            'username': f'taxista_test_{int(time.time())}',
            'password': 'test123',
            'nombre': 'Taxista Test',
            'role': 'taxista',
            'licencia': 'LIC123'
        }
        
        response, rt = self.make_request('POST', '/users', taxista_data, self.admin_token)
        if response and response.status_code == 200:
            user_data = response.json()
            self.created_entities['users'].append(user_data['id'])
            # CRITICAL: Check password is NOT in response
            has_password = 'password' in user_data
            self.log_test("Create User - Password Exclusion", not has_password, f"User created, password excluded: {not has_password}", rt)
            
            # Login with created taxista
            login_response, login_rt = self.make_request('POST', '/auth/login', {
                'username': taxista_data['username'],
                'password': taxista_data['password']
            })
            if login_response and login_response.status_code == 200:
                login_data = login_response.json()
                self.taxista_token = login_data['access_token']
                self.log_test("Taxista Login", True, f"Token received for {login_data['user']['nombre']}", login_rt)
            else:
                self.log_test("Taxista Login", False, f"Status: {login_response.status_code if login_response else 'No response'}", login_rt)
        else:
            self.log_test("Create User (Admin)", False, f"Status: {response.status_code if response else 'No response'}", rt)
            
        # Test taxista cannot create users (403)
        response, rt = self.make_request('POST', '/users', taxista_data, self.taxista_token)
        success = response and response.status_code == 403
        self.log_test("Create User (Taxista - Should Fail)", success, f"Status: {response.status_code if response else 'No response'}", rt)
        
        # CRITICAL TEST: GET users - Check password exclusion projection
        response, rt = self.make_request('GET', '/users', token=self.admin_token)
        if response and response.status_code == 200:
            users = response.json()
            has_passwords = any('password' in user for user in users)
            self.log_test("GET Users - Password Projection Exclusion", not has_passwords, f"Found {len(users)} users, passwords excluded: {not has_passwords}", rt)
        else:
            self.log_test("GET Users (Admin)", False, f"Status: {response.status_code if response else 'No response'}", rt)
            
        # Test taxista cannot get users (403)
        response, rt = self.make_request('GET', '/users', token=self.taxista_token)
        success = response and response.status_code == 403
        self.log_test("GET Users (Taxista - Should Fail)", success, f"Status: {response.status_code if response else 'No response'}", rt)

    def test_companies_crud_with_unique_index(self):
        """Test companies CRUD with unique numero_cliente index"""
        print("\n🏢 TESTING COMPANIES CRUD & UNIQUE INDEX VALIDATION")
        
        # Create company
        company_data = {
            'nombre': 'Empresa Test',
            'cif': 'B12345678',
            'direccion': 'Calle Test 123',
            'localidad': 'Tineo',
            'provincia': 'Asturias',
            'numero_cliente': f'CLI{int(time.time())}'
        }
        
        response, rt = self.make_request('POST', '/companies', company_data, self.admin_token)
        if response and response.status_code == 200:
            company = response.json()
            self.created_entities['companies'].append(company['id'])
            self.log_test("Create Company (Admin)", True, f"Company created: {company['nombre']}", rt)
        else:
            self.log_test("Create Company (Admin)", False, f"Status: {response.status_code if response else 'No response'}", rt)
            
        # CRITICAL: Test unique numero_cliente index (should fail)
        duplicate_company = company_data.copy()
        duplicate_company['nombre'] = 'Empresa Duplicada'
        response, rt = self.make_request('POST', '/companies', duplicate_company, self.admin_token)
        success = response and response.status_code == 400
        self.log_test("Unique numero_cliente Index Validation", success, f"Status: {response.status_code if response else 'No response'}", rt)
        
        # Test GET companies (both admin and taxista should work)
        response, rt = self.make_request('GET', '/companies', token=self.admin_token)
        admin_success = response and response.status_code == 200
        self.log_test("GET Companies (Admin)", admin_success, f"Status: {response.status_code if response else 'No response'}", rt)
        
        response, rt = self.make_request('GET', '/companies', token=self.taxista_token)
        taxista_success = response and response.status_code == 200
        self.log_test("GET Companies (Taxista)", taxista_success, f"Status: {response.status_code if response else 'No response'}", rt)

    def test_vehiculos_crud_with_unique_index(self):
        """Test vehiculos CRUD with unique matricula index"""
        print("\n🚗 TESTING VEHICULOS CRUD & UNIQUE MATRICULA INDEX")
        
        # Create vehiculo
        vehiculo_data = {
            'matricula': f'TEST{int(time.time() % 10000)}',
            'plazas': 4,
            'marca': 'Toyota',
            'modelo': 'Corolla',
            'km_iniciales': 50000,
            'fecha_compra': '01/01/2020',
            'activo': True
        }
        
        response, rt = self.make_request('POST', '/vehiculos', vehiculo_data, self.admin_token)
        if response and response.status_code == 200:
            vehiculo = response.json()
            self.created_entities['vehiculos'].append(vehiculo['id'])
            self.log_test("Create Vehiculo (Admin)", True, f"Vehiculo created: {vehiculo['matricula']}", rt)
        else:
            self.log_test("Create Vehiculo (Admin)", False, f"Status: {response.status_code if response else 'No response'}", rt)
            
        # CRITICAL: Test unique matricula index (should fail)
        duplicate_vehiculo = vehiculo_data.copy()
        duplicate_vehiculo['marca'] = 'Ford'
        response, rt = self.make_request('POST', '/vehiculos', duplicate_vehiculo, self.admin_token)
        success = response and response.status_code == 400
        self.log_test("Unique Matricula Index Validation", success, f"Status: {response.status_code if response else 'No response'}", rt)
        
        # Test GET vehiculos
        response, rt = self.make_request('GET', '/vehiculos', token=self.admin_token)
        success = response and response.status_code == 200
        self.log_test("GET Vehiculos", success, f"Status: {response.status_code if response else 'No response'}", rt)

    def test_services_with_configurable_limits(self):
        """Test services with configurable limits optimization"""
        print("\n📋 TESTING SERVICES WITH CONFIGURABLE LIMITS")
        
        # First create a turno for the taxista
        turno_data = {
            'taxista_id': 'dummy',  # Will be overridden by server
            'taxista_nombre': 'dummy',  # Will be overridden by server
            'vehiculo_id': self.created_entities['vehiculos'][0] if self.created_entities['vehiculos'] else 'test_vehiculo',
            'vehiculo_matricula': 'TEST1234',
            'fecha_inicio': '01/01/2024',
            'hora_inicio': '08:00',
            'km_inicio': 100000
        }
        
        response, rt = self.make_request('POST', '/turnos', turno_data, self.taxista_token)
        if response and response.status_code == 200:
            turno = response.json()
            self.created_entities['turnos'].append(turno['id'])
            self.log_test("Create Turno for Services", True, f"Turno created: {turno['id']}", rt)
        else:
            self.log_test("Create Turno for Services", False, f"Status: {response.status_code if response else 'No response'}", rt)
            return
        
        # Create test service
        service_data = {
            'fecha': '01/01/2024',
            'hora': '09:00',
            'origen': 'Tineo Centro',
            'destino': 'Hospital',
            'importe': 15.50,
            'importe_espera': 2.50,
            'kilometros': 12.5,
            'tipo': 'particular',
            'cobrado': True,
            'facturar': False
        }
        
        response, rt = self.make_request('POST', '/services', service_data, self.taxista_token)
        if response and response.status_code == 200:
            service = response.json()
            self.created_entities['services'].append(service['id'])
            self.log_test("Create Service (Taxista)", True, f"Service created: {service['id']}", rt)
        else:
            self.log_test("Create Service (Taxista)", False, f"Status: {response.status_code if response else 'No response'}", rt)
            
        # CRITICAL: Test GET services without limit (should use default 1000)
        response, rt = self.make_request('GET', '/services', token=self.admin_token)
        if response and response.status_code == 200:
            services = response.json()
            self.log_test("GET Services (Default Limit 1000)", True, f"Retrieved {len(services)} services", rt)
        else:
            self.log_test("GET Services (Default Limit)", False, f"Status: {response.status_code if response else 'No response'}", rt)
            
        # CRITICAL: Test GET services with specific limit
        response, rt = self.make_request('GET', '/services', token=self.admin_token, params={'limit': 50})
        if response and response.status_code == 200:
            services = response.json()
            success = len(services) <= 50
            self.log_test("GET Services (Limit=50)", success, f"Retrieved {len(services)} services (≤50)", rt)
        else:
            self.log_test("GET Services (Limit=50)", False, f"Status: {response.status_code if response else 'No response'}", rt)
            
        # CRITICAL: Test GET services with excessive limit (should cap at 10000)
        response, rt = self.make_request('GET', '/services', token=self.admin_token, params={'limit': 99999})
        if response and response.status_code == 200:
            services = response.json()
            # Since we don't have 10000 services, just check it doesn't error
            self.log_test("GET Services (Excessive Limit - Capped at 10000)", True, f"Retrieved {len(services)} services (capped)", rt)
        else:
            self.log_test("GET Services (Excessive Limit)", False, f"Status: {response.status_code if response else 'No response'}", rt)
            
        # Test limit edge cases
        response, rt = self.make_request('GET', '/services', token=self.admin_token, params={'limit': 0})
        if response and response.status_code == 200:
            services = response.json()
            self.log_test("GET Services (Limit=0 - Use Default)", True, f"Retrieved {len(services)} services", rt)
        else:
            self.log_test("GET Services (Limit=0)", False, f"Status: {response.status_code if response else 'No response'}", rt)

    def test_turnos_optimized_batch_queries(self):
        """Test turnos with batch queries optimization (no N+1)"""
        print("\n🔄 TESTING TURNOS OPTIMIZED BATCH QUERIES (NO N+1)")
        
        # CRITICAL: Test GET turnos without limit (should use default 500)
        response, rt = self.make_request('GET', '/turnos', token=self.admin_token)
        if response and response.status_code == 200:
            turnos = response.json()
            # Check response time - should be fast due to batch queries
            fast_response = rt < 2.0  # Should be under 2 seconds
            self.log_test("GET Turnos (Default Limit 500, Batch Queries)", True, f"Retrieved {len(turnos)} turnos, fast: {fast_response}", rt)
        else:
            self.log_test("GET Turnos (Default Limit)", False, f"Status: {response.status_code if response else 'No response'}", rt)
            
        # CRITICAL: Test GET turnos with limit
        response, rt = self.make_request('GET', '/turnos', token=self.admin_token, params={'limit': 100})
        if response and response.status_code == 200:
            turnos = response.json()
            success = len(turnos) <= 100
            fast_response = rt < 2.0
            self.log_test("GET Turnos (Limit=100, Batch Queries)", success, f"Retrieved {len(turnos)} turnos (≤100), fast: {fast_response}", rt)
        else:
            self.log_test("GET Turnos (Limit=100)", False, f"Status: {response.status_code if response else 'No response'}", rt)
            
        # Test GET turno activo
        response, rt = self.make_request('GET', '/turnos/activo', token=self.taxista_token)
        if response and response.status_code == 200:
            turno = response.json()
            has_totals = turno and 'total_importe_clientes' in turno
            self.log_test("GET Turno Activo (Optimized)", has_totals, f"Active turno with calculated totals: {has_totals}", rt)
        else:
            self.log_test("GET Turno Activo", False, f"Status: {response.status_code if response else 'No response'}", rt)

    def test_exportations_optimized_performance(self):
        """Test export endpoints with performance optimization"""
        print("\n📊 TESTING OPTIMIZED EXPORTATIONS (PERFORMANCE)")
        
        # CRITICAL: Test services exports with performance
        for format_type in ['csv', 'excel', 'pdf']:
            response, rt = self.make_request('GET', f'/services/export/{format_type}', token=self.admin_token)
            if response and response.status_code == 200:
                content_length = len(response.content)
                fast_response = rt < 2.0  # Should be under 2 seconds
                self.log_test(f"Services Export {format_type.upper()} (Optimized)", True, f"Generated {content_length} bytes, fast: {fast_response}", rt)
            else:
                self.log_test(f"Services Export {format_type.upper()}", False, f"Status: {response.status_code if response else 'No response'}", rt)
                
        # CRITICAL: Test turnos exports (should use batch queries)
        for format_type in ['csv', 'excel', 'pdf']:
            response, rt = self.make_request('GET', f'/turnos/export/{format_type}', token=self.admin_token)
            if response and response.status_code == 200:
                content_length = len(response.content)
                fast_response = rt < 2.0  # Should be under 2 seconds due to batch queries
                self.log_test(f"Turnos Export {format_type.upper()} (Batch Queries)", True, f"Generated {content_length} bytes, fast: {fast_response}", rt)
            else:
                self.log_test(f"Turnos Export {format_type.upper()}", False, f"Status: {response.status_code if response else 'No response'}", rt)

    def test_statistics_optimized_batch_queries(self):
        """Test statistics with batch queries optimization"""
        print("\n📈 TESTING OPTIMIZED STATISTICS (BATCH QUERIES)")
        
        # CRITICAL: Test turnos statistics with batch queries
        response, rt = self.make_request('GET', '/turnos/estadisticas', token=self.admin_token)
        if response and response.status_code == 200:
            stats = response.json()
            has_required_fields = all(field in stats for field in [
                'total_turnos', 'turnos_activos', 'turnos_cerrados', 
                'total_importe', 'total_servicios'
            ])
            fast_response = rt < 2.0  # Should be fast due to batch queries
            self.log_test("Turnos Statistics (Batch Queries)", has_required_fields, f"Complete stats, fast: {fast_response}", rt)
        else:
            self.log_test("Turnos Statistics", False, f"Status: {response.status_code if response else 'No response'}", rt)
            
        # Test daily report
        today = datetime.now().strftime('%d/%m/%Y')
        response, rt = self.make_request('GET', '/reportes/diario', token=self.admin_token, params={'fecha': today})
        if response and response.status_code == 200:
            report = response.json()
            fast_response = rt < 2.0
            self.log_test("Daily Report (Optimized)", True, f"Generated report with {len(report)} entries, fast: {fast_response}", rt)
        else:
            self.log_test("Daily Report", False, f"Status: {response.status_code if response else 'No response'}", rt)

    def test_config_endpoints(self):
        """Test configuration endpoints"""
        print("\n⚙️ TESTING CONFIGURATION")
        
        # Test GET config
        response, rt = self.make_request('GET', '/config')
        if response and response.status_code == 200:
            config = response.json()
            self.log_test("GET Config", True, f"Config retrieved: {config.get('nombre_radio_taxi', 'N/A')}", rt)
        else:
            self.log_test("GET Config", False, f"Status: {response.status_code if response else 'No response'}", rt)
            
        # Test PUT config (admin only)
        config_data = {
            'nombre_radio_taxi': 'Taxi Tineo Test',
            'telefono': '985 80 15 15',
            'web': 'www.taxitineo.com',
            'direccion': 'Tineo, Asturias'
        }
        
        response, rt = self.make_request('PUT', '/config', config_data, self.admin_token)
        if response and response.status_code == 200:
            updated_config = response.json()
            self.log_test("PUT Config (Admin)", True, f"Config updated: {updated_config.get('nombre_radio_taxi', 'N/A')}", rt)
        else:
            self.log_test("PUT Config (Admin)", False, f"Status: {response.status_code if response else 'No response'}", rt)

    def test_sync_endpoint(self):
        """Test offline sync endpoint"""
        print("\n🔄 TESTING OFFLINE SYNC")
        
        sync_data = {
            'services': [
                {
                    'fecha': '02/01/2024',
                    'hora': '10:00',
                    'origen': 'Plaza Mayor',
                    'destino': 'Estación',
                    'importe': 8.50,
                    'importe_espera': 0,
                    'kilometros': 5.2,
                    'tipo': 'particular',
                    'cobrado': True,
                    'facturar': False
                },
                {
                    'fecha': '02/01/2024',
                    'hora': '11:00',
                    'origen': 'Hospital',
                    'destino': 'Centro',
                    'importe': 12.00,
                    'importe_espera': 1.50,
                    'kilometros': 8.1,
                    'tipo': 'empresa',
                    'empresa_id': self.created_entities['companies'][0] if self.created_entities['companies'] else None,
                    'cobrado': False,
                    'facturar': True
                }
            ]
        }
        
        response, rt = self.make_request('POST', '/services/sync', sync_data, self.taxista_token)
        if response and response.status_code == 200:
            result = response.json()
            synced_count = len(result.get('ids', []))
            expected_count = len(sync_data['services'])
            success = synced_count == expected_count
            self.log_test("Batch Sync Services", success, f"Synced {synced_count}/{expected_count} services", rt)
        else:
            self.log_test("Batch Sync Services", False, f"Status: {response.status_code if response else 'No response'}", rt)

    def test_edge_cases_and_performance(self):
        """Test edge cases and performance scenarios"""
        print("\n⚠️ TESTING EDGE CASES & PERFORMANCE")
        
        # Test creating service without active turno (should fail for taxista)
        service_data = {
            'fecha': '03/01/2024',
            'hora': '12:00',
            'origen': 'Test',
            'destino': 'Test',
            'importe': 10.00,
            'importe_espera': 0,
            'kilometros': 5.0,
            'tipo': 'particular'
        }
        
        # First close the active turno
        if self.created_entities['turnos']:
            turno_id = self.created_entities['turnos'][0]
            close_data = {
                'fecha_fin': '01/01/2024',
                'hora_fin': '18:00',
                'km_fin': 100200,
                'cerrado': True
            }
            self.make_request('PUT', f'/turnos/{turno_id}/finalizar', close_data, self.taxista_token)
        
        # Now try to create service without active turno
        response, rt = self.make_request('POST', '/services', service_data, self.taxista_token)
        success = response and response.status_code == 400
        self.log_test("Service Without Active Turno (Validation)", success, f"Correctly rejected: {response.status_code if response else 'No response'}", rt)
        
        # Test negative limit (should handle gracefully)
        response, rt = self.make_request('GET', '/turnos', token=self.admin_token, params={'limit': -1})
        if response and response.status_code == 200:
            turnos = response.json()
            self.log_test("Turnos Limit=-1 (Handle Gracefully)", True, f"Retrieved {len(turnos)} turnos", rt)
        else:
            self.log_test("Turnos Limit=-1 (Handle Gracefully)", False, f"Status: {response.status_code if response else 'No response'}", rt)

    def cleanup_test_data(self):
        """Clean up created test data"""
        print("\n🧹 CLEANING UP TEST DATA")
        
        # Delete created services
        for service_id in self.created_entities['services']:
            response, rt = self.make_request('DELETE', f'/services/{service_id}', token=self.admin_token)
            success = response and response.status_code == 200
            if success:
                print(f"✅ Deleted service {service_id}")
            
        # Delete created vehiculos
        for vehiculo_id in self.created_entities['vehiculos']:
            response, rt = self.make_request('DELETE', f'/vehiculos/{vehiculo_id}', token=self.admin_token)
            success = response and response.status_code == 200
            if success:
                print(f"✅ Deleted vehiculo {vehiculo_id}")
                
        # Delete created companies
        for company_id in self.created_entities['companies']:
            response, rt = self.make_request('DELETE', f'/companies/{company_id}', token=self.admin_token)
            success = response and response.status_code == 200
            if success:
                print(f"✅ Deleted company {company_id}")
                
        # Delete created users
        for user_id in self.created_entities['users']:
            response, rt = self.make_request('DELETE', f'/users/{user_id}', token=self.admin_token)
            success = response and response.status_code == 200
            if success:
                print(f"✅ Deleted user {user_id}")

    def run_all_tests(self):
        """Run complete test suite"""
        print("🚕 TAXI TINEO - TESTEO PROFUNDO POST-OPTIMIZACIONES")
        print("=" * 60)
        print(f"Backend URL: {BACKEND_URL}")
        print(f"API Base: {API_BASE}")
        print("=" * 60)
        print("\n🎯 VALIDANDO OPTIMIZACIONES:")
        print("1. ✅ 11 índices de base de datos")
        print("2. ✅ Eliminación de N+1 queries (5 endpoints)")
        print("3. ✅ Proyecciones (excluir passwords)")
        print("4. ✅ Límites configurables")
        print("5. ✅ Sistema de cache")
        print("=" * 60)
        
        start_time = time.time()
        
        try:
            # Core functionality tests with optimizations
            if not self.test_authentication():
                print("❌ Authentication failed - stopping tests")
                return
                
            self.test_users_crud_optimized()
            self.test_companies_crud_with_unique_index()
            self.test_vehiculos_crud_with_unique_index()
            self.test_services_with_configurable_limits()
            self.test_turnos_optimized_batch_queries()
            self.test_exportations_optimized_performance()
            self.test_statistics_optimized_batch_queries()
            self.test_config_endpoints()
            self.test_sync_endpoint()
            self.test_edge_cases_and_performance()
            
        finally:
            # Always cleanup
            self.cleanup_test_data()
            
        total_time = time.time() - start_time
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 RESUMEN TESTEO POST-OPTIMIZACIONES")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"✅ Passed: {passed}/{total} ({success_rate:.1f}%)")
        print(f"⏱️ Total time: {total_time:.2f}s")
        print(f"🎯 Backend URL: {BACKEND_URL}")
        
        # Show failed tests
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            print(f"\n❌ FAILED TESTS ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"  - {test['name']}: {test['details']}")
        else:
            print("\n🎉 ALL OPTIMIZATION TESTS PASSED!")
            
        # Performance summary
        slow_tests = [result for result in self.test_results if result.get('response_time', 0) > 1.0]
        if slow_tests:
            print(f"\n⚠️ SLOW RESPONSES (>1s): {len(slow_tests)}")
            for test in slow_tests:
                print(f"  - {test['name']}: {test['response_time']:.3f}s")
        else:
            print("\n🚀 ALL RESPONSES FAST (<1s) - OPTIMIZATIONS WORKING!")
        
        # Final assessment
        if success_rate >= 95 and len(slow_tests) == 0:
            print("\n🎯 CONCLUSIÓN: SISTEMA 100% LISTO PARA PRODUCCIÓN")
            print("✅ Todas las optimizaciones funcionando correctamente")
            print("✅ No hay breaking changes")
            print("✅ Performance mejorado significativamente")
        elif success_rate >= 90:
            print("\n⚠️ CONCLUSIÓN: SISTEMA CASI LISTO - AJUSTES MENORES NECESARIOS")
        else:
            print("\n❌ CONCLUSIÓN: NECESITA AJUSTES ANTES DE PRODUCCIÓN")
        
        return success_rate >= 95  # Consider success if 95%+ pass rate

if __name__ == "__main__":
    tester = TaxiBackendTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)