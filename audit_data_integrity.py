#!/usr/bin/env python3
"""
Script de Auditoría de Integridad de Datos - TaxiFast Multi-tenant

Este script detecta y opcionalmente repara:
1. Datos sin organization_id (huérfanos)
2. Referencias cruzadas inválidas (taxista_id, vehiculo_id, empresa_id)
3. Usuarios sin organización que no son superadmin

Ejecución:
    # Solo auditoría (modo lectura)
    python3 audit_data_integrity.py
    
    # Auditoría + reparación
    python3 audit_data_integrity.py --fix
    
    # Con URL de MongoDB personalizada
    MONGO_URL="mongodb+srv://..." python3 audit_data_integrity.py

Variables de entorno:
    MONGO_URL: URL de conexión a MongoDB (default: mongodb://localhost:27017)
    DB_NAME: Nombre de la base de datos (default: test_database)
"""

import os
import sys
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId

# Configuración
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")

# Colores para output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def log_ok(msg: str):
    print(f"{GREEN}✓{RESET} {msg}")

def log_warn(msg: str):
    print(f"{YELLOW}⚠{RESET} {msg}")

def log_error(msg: str):
    print(f"{RED}✗{RESET} {msg}")

def log_info(msg: str):
    print(f"{BLUE}ℹ{RESET} {msg}")

def log_header(msg: str):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{msg}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

class DataAuditor:
    def __init__(self, fix_mode: bool = False):
        self.fix_mode = fix_mode
        self.client = MongoClient(MONGO_URL)
        self.db = self.client[DB_NAME]
        self.issues = []
        self.fixes = []
        
    def run_full_audit(self):
        """Ejecutar auditoría completa"""
        log_header("AUDITORÍA DE INTEGRIDAD DE DATOS - TaxiFast")
        
        if self.fix_mode:
            log_warn("MODO FIX ACTIVADO - Se aplicarán correcciones")
        else:
            log_info("Modo lectura - No se modificarán datos")
        
        print(f"\nConectado a: {MONGO_URL}")
        print(f"Base de datos: {DB_NAME}\n")
        
        # 1. Auditar usuarios sin organización
        self.audit_users_without_org()
        
        # 2. Auditar datos huérfanos (sin organization_id)
        self.audit_orphan_data()
        
        # 3. Auditar referencias cruzadas inválidas
        self.audit_invalid_references()
        
        # 4. Auditar servicios con turno_id inválido
        self.audit_service_turno_references()
        
        # Resumen
        self.print_summary()
        
    def audit_users_without_org(self):
        """Auditar usuarios que no son superadmin y no tienen organización"""
        log_header("1. USUARIOS SIN ORGANIZACIÓN")
        
        users_without_org = list(self.db.users.find({
            "role": {"$ne": "superadmin"},
            "$or": [
                {"organization_id": None},
                {"organization_id": {"$exists": False}}
            ]
        }))
        
        if not users_without_org:
            log_ok("No hay usuarios problemáticos (sin org y no superadmin)")
            return
            
        for user in users_without_org:
            issue = f"Usuario '{user.get('username')}' (rol: {user.get('role')}) sin organization_id"
            log_error(issue)
            self.issues.append({
                "type": "user_without_org",
                "collection": "users",
                "id": str(user["_id"]),
                "details": issue
            })
            
            if self.fix_mode:
                # En modo fix, desactivar el usuario
                self.db.users.update_one(
                    {"_id": user["_id"]},
                    {"$set": {"activo": False, "_audit_disabled": True, "_audit_date": datetime.utcnow()}}
                )
                log_warn(f"  → Usuario desactivado (requiere asignación manual de organización)")
                self.fixes.append(f"Desactivado usuario {user.get('username')}")
    
    def audit_orphan_data(self):
        """Auditar documentos sin organization_id en colecciones críticas"""
        log_header("2. DATOS HUÉRFANOS (sin organization_id)")
        
        collections_to_check = ["vehiculos", "turnos", "services", "companies"]
        
        for coll_name in collections_to_check:
            orphans = list(self.db[coll_name].find({
                "$or": [
                    {"organization_id": None},
                    {"organization_id": {"$exists": False}}
                ]
            }))
            
            if orphans:
                log_error(f"{coll_name}: {len(orphans)} documentos sin organization_id")
                for doc in orphans[:5]:  # Mostrar solo los primeros 5
                    self.issues.append({
                        "type": "orphan_data",
                        "collection": coll_name,
                        "id": str(doc["_id"]),
                        "details": f"Documento sin organization_id"
                    })
                if len(orphans) > 5:
                    log_info(f"  ... y {len(orphans) - 5} más")
            else:
                log_ok(f"{coll_name}: OK - Todos los documentos tienen organization_id")
    
    def audit_invalid_references(self):
        """Auditar referencias cruzadas inválidas"""
        log_header("3. REFERENCIAS CRUZADAS INVÁLIDAS")
        
        # 3.1 Turnos con taxista_id que no existe
        log_info("Verificando turnos.taxista_id...")
        turnos = list(self.db.turnos.find({"taxista_id": {"$exists": True, "$ne": None}}))
        invalid_taxista_refs = 0
        for turno in turnos:
            try:
                taxista = self.db.users.find_one({"_id": ObjectId(turno["taxista_id"])})
                if not taxista:
                    invalid_taxista_refs += 1
                    self.issues.append({
                        "type": "invalid_ref",
                        "collection": "turnos",
                        "id": str(turno["_id"]),
                        "details": f"taxista_id '{turno['taxista_id']}' no existe"
                    })
            except:
                invalid_taxista_refs += 1
                
        if invalid_taxista_refs:
            log_error(f"Turnos con taxista_id inválido: {invalid_taxista_refs}")
        else:
            log_ok("Turnos: Todas las referencias a taxistas son válidas")
        
        # 3.2 Turnos con vehiculo_id que no existe
        log_info("Verificando turnos.vehiculo_id...")
        turnos_with_vehiculo = list(self.db.turnos.find({"vehiculo_id": {"$exists": True, "$ne": None, "$ne": ""}}))
        invalid_vehiculo_refs = 0
        for turno in turnos_with_vehiculo:
            try:
                vehiculo = self.db.vehiculos.find_one({"_id": ObjectId(turno["vehiculo_id"])})
                if not vehiculo:
                    invalid_vehiculo_refs += 1
                    self.issues.append({
                        "type": "invalid_ref",
                        "collection": "turnos",
                        "id": str(turno["_id"]),
                        "details": f"vehiculo_id '{turno['vehiculo_id']}' no existe"
                    })
            except:
                pass  # vehiculo_id puede ser string vacío o inválido
                
        if invalid_vehiculo_refs:
            log_error(f"Turnos con vehiculo_id inválido: {invalid_vehiculo_refs}")
        else:
            log_ok("Turnos: Todas las referencias a vehículos son válidas")
        
        # 3.3 Servicios con empresa_id que no existe
        log_info("Verificando services.empresa_id...")
        services_with_empresa = list(self.db.services.find({"empresa_id": {"$exists": True, "$ne": None, "$ne": ""}}))
        invalid_empresa_refs = 0
        for service in services_with_empresa:
            try:
                empresa = self.db.companies.find_one({"_id": ObjectId(service["empresa_id"])})
                if not empresa:
                    invalid_empresa_refs += 1
                    self.issues.append({
                        "type": "invalid_ref",
                        "collection": "services",
                        "id": str(service["_id"]),
                        "details": f"empresa_id '{service['empresa_id']}' no existe"
                    })
            except:
                pass
                
        if invalid_empresa_refs:
            log_error(f"Servicios con empresa_id inválido: {invalid_empresa_refs}")
        else:
            log_ok("Servicios: Todas las referencias a empresas son válidas")
    
    def audit_service_turno_references(self):
        """Auditar servicios con turno_id inválido"""
        log_header("4. SERVICIOS CON TURNO INVÁLIDO")
        
        services_with_turno = list(self.db.services.find({"turno_id": {"$exists": True, "$ne": None, "$ne": ""}}))
        invalid_turno_refs = 0
        
        for service in services_with_turno:
            try:
                turno = self.db.turnos.find_one({"_id": ObjectId(service["turno_id"])})
                if not turno:
                    invalid_turno_refs += 1
                    self.issues.append({
                        "type": "invalid_ref",
                        "collection": "services",
                        "id": str(service["_id"]),
                        "details": f"turno_id '{service['turno_id']}' no existe"
                    })
            except:
                pass
                
        if invalid_turno_refs:
            log_error(f"Servicios con turno_id inválido: {invalid_turno_refs}")
        else:
            log_ok("Servicios: Todas las referencias a turnos son válidas")
    
    def print_summary(self):
        """Imprimir resumen de la auditoría"""
        log_header("RESUMEN DE AUDITORÍA")
        
        if not self.issues:
            log_ok("¡No se encontraron problemas de integridad!")
            return
            
        print(f"\n{RED}Total de problemas encontrados: {len(self.issues)}{RESET}")
        
        # Agrupar por tipo
        by_type = {}
        for issue in self.issues:
            t = issue["type"]
            by_type[t] = by_type.get(t, 0) + 1
            
        print("\nDesglose por tipo:")
        for t, count in by_type.items():
            print(f"  - {t}: {count}")
            
        if self.fixes:
            print(f"\n{GREEN}Correcciones aplicadas: {len(self.fixes)}{RESET}")
            for fix in self.fixes:
                print(f"  - {fix}")
        elif self.issues:
            print(f"\n{YELLOW}Ejecuta con --fix para aplicar correcciones automáticas{RESET}")

def main():
    fix_mode = "--fix" in sys.argv
    
    try:
        auditor = DataAuditor(fix_mode=fix_mode)
        auditor.run_full_audit()
    except Exception as e:
        log_error(f"Error durante la auditoría: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
