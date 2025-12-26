#!/usr/bin/env python3
"""
Smoke Tests - Cross-Tenant Security by _id (turnos + services)
Verifica que un admin de Org A no puede acceder a recursos de Org B por ID directo.

Uso:
    pip install requests
    BASE_URL="https://TU_BACKEND" \
    ADMIN_A_USER="adminA" ADMIN_A_PASS="adminA123" \
    ADMIN_B_USER="adminB" ADMIN_B_PASS="adminB123" \
    python smoke_cross_tenant_ids_api.py

Criterio de éxito: devuelve 403 o 404 en todos los casos (nunca 200/204).
"""

import os
import sys
import requests

# Configuración desde variables de entorno
BASE_URL = os.environ.get("BASE_URL", "http://localhost:8001").rstrip("/")
ADMIN_A_USER = os.environ.get("ADMIN_A_USER", "adminA")
ADMIN_A_PASS = os.environ.get("ADMIN_A_PASS", "adminA123")
ADMIN_B_USER = os.environ.get("ADMIN_B_USER", "adminB")
ADMIN_B_PASS = os.environ.get("ADMIN_B_PASS", "adminB123")


def login(user: str, password: str) -> str:
    """Login y obtener token JWT"""
    r = requests.post(
        f"{BASE_URL}/api/auth/login",  # Endpoint correcto de la API
        json={"username": user, "password": password},
        timeout=20,
    )
    if r.status_code != 200:
        print(f"❌ Login failed for {user}: {r.status_code} - {r.text}")
        sys.exit(1)
    data = r.json()
    # Fallback robusto para diferentes estructuras de respuesta
    token = data.get("access_token") or data.get("token")
    if not token:
        print(f"❌ No token in response for {user}: {data}")
        sys.exit(1)
    return token


def auth_headers(token: str) -> dict:
    """Headers de autenticación"""
    return {"Authorization": f"Bearer {token}"}


def get_one_id(token: str, endpoint: str) -> str:
    """Obtener el ID del primer elemento de un listado"""
    r = requests.get(f"{BASE_URL}{endpoint}", headers=auth_headers(token), timeout=20)
    if r.status_code != 200:
        print(f"❌ Failed to get {endpoint}: {r.status_code} - {r.text}")
        sys.exit(1)
    data = r.json()
    if not isinstance(data, list):
        raise SystemExit(f"Expected list from {endpoint}, got: {type(data)}")
    if not data:
        raise SystemExit(f"No items returned from {endpoint}. Create one in Org B to test.")
    # La API devuelve "id" (no "_id")
    return data[0]["id"]


def expect_not_allowed(method: str, url: str, token: str, payload=None, expected=(403, 404)):
    """Ejecutar request y verificar que está bloqueado (403 o 404)"""
    fn = getattr(requests, method.lower())
    kwargs = {"headers": auth_headers(token), "timeout": 20}
    if payload:
        kwargs["json"] = payload
    r = fn(url, **kwargs)
    if r.status_code not in expected:
        print(f"❌ FAIL {method} {url} -> {r.status_code}")
        print(f"   Response: {r.text[:500]}")
        sys.exit(1)
    print(f"✅ PASS {method} {url} -> {r.status_code}")


def main():
    print("=" * 60)
    print("🔐 SMOKE TESTS - Cross-Tenant Security by ID")
    print("=" * 60)
    print(f"   Base URL: {BASE_URL}")
    print(f"   Admin A: {ADMIN_A_USER}")
    print(f"   Admin B: {ADMIN_B_USER}")
    print()

    # Login
    print("📋 Obteniendo tokens...")
    tokenA = login(ADMIN_A_USER, ADMIN_A_PASS)
    tokenB = login(ADMIN_B_USER, ADMIN_B_PASS)
    print("   ✅ Tokens obtenidos")
    print()

    # Obtener IDs de Org B
    print("📋 Obteniendo IDs de Org B...")
    try:
        turno_id_B = get_one_id(tokenB, "/api/turnos")
        print(f"   ✅ Turno B ID: {turno_id_B}")
    except SystemExit as e:
        print(f"   ⚠️  No hay turnos en Org B: {e}")
        turno_id_B = None

    try:
        service_id_B = get_one_id(tokenB, "/api/services")
        print(f"   ✅ Service B ID: {service_id_B}")
    except SystemExit as e:
        print(f"   ⚠️  No hay services en Org B: {e}")
        service_id_B = None
    print()

    # Tests
    print("🔐 Ejecutando tests de seguridad...")
    tests_passed = 0
    tests_total = 0

    # 1) Admin A no puede finalizar un turno de Org B
    if turno_id_B:
        tests_total += 1
        try:
            expect_not_allowed(
                "PUT",
                f"{BASE_URL}/api/turnos/{turno_id_B}/finalizar",
                tokenA,
                payload={"fecha_fin": "2025-12-26", "hora_fin": "18:00", "km_fin": 100, "cerrado": True}
            )
            tests_passed += 1
        except SystemExit:
            pass

    # 2) Admin A no puede editar un service de Org B
    if service_id_B:
        tests_total += 1
        try:
            expect_not_allowed(
                "PUT",
                f"{BASE_URL}/api/services/{service_id_B}",
                tokenA,
                payload={
                    "fecha": "2025-12-26",
                    "hora": "10:00",
                    "origen": "cross-tenant-test",
                    "destino": "cross-tenant-test",
                    "tipo": "particular",
                    "importe": 10.0,
                    "importe_espera": 0.0,
                    "kilometros": 5.0
                },
            )
            tests_passed += 1
        except SystemExit:
            pass

    # 3) Admin A no puede borrar un service de Org B
    if service_id_B:
        tests_total += 1
        try:
            expect_not_allowed("DELETE", f"{BASE_URL}/api/services/{service_id_B}", tokenA)
            tests_passed += 1
        except SystemExit:
            pass

    # 4) Admin A no puede borrar un turno de Org B
    if turno_id_B:
        tests_total += 1
        try:
            expect_not_allowed("DELETE", f"{BASE_URL}/api/turnos/{turno_id_B}", tokenA)
            tests_passed += 1
        except SystemExit:
            pass

    # Resumen
    print()
    print("=" * 60)
    print(f"📊 RESUMEN: {tests_passed}/{tests_total} tests pasados")
    print("=" * 60)

    if tests_total == 0:
        print("⚠️  No se ejecutaron tests (no hay datos en Org B)")
        sys.exit(1)
    elif tests_passed == tests_total:
        print("🎉 ¡Todos los tests de cross-tenant por ID pasaron!")
        sys.exit(0)
    else:
        print("❌ Algunos tests fallaron")
        sys.exit(1)


if __name__ == "__main__":
    main()
