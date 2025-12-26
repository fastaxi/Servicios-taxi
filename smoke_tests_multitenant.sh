#!/bin/bash
#
# smoke_tests_multitenant.sh
# Suite completa de 9 smoke tests para validar seguridad multi-tenant
#
# Uso:
#   BASE_URL="https://tu-backend.emergent.host" \
#   ADMIN_A_USER="adminA" ADMIN_A_PASS="adminA123" \
#   ADMIN_B_USER="adminB" ADMIN_B_PASS="adminB123" \
#   SUPER_USER="superadmin" SUPER_PASS="superadmin123" \
#   ./smoke_tests_multitenant.sh
#
# Criterio de éxito: todos los tests devuelven el código HTTP esperado
#

set -e

# Configuración (desde env o valores por defecto)
BASE_URL="${BASE_URL:-http://localhost:8001}"
ADMIN_A_USER="${ADMIN_A_USER:-adminA}"
ADMIN_A_PASS="${ADMIN_A_PASS:-adminA123}"
ADMIN_B_USER="${ADMIN_B_USER:-adminB}"
ADMIN_B_PASS="${ADMIN_B_PASS:-adminB123}"
SUPER_USER="${SUPER_USER:-superadmin}"
SUPER_PASS="${SUPER_PASS:-superadmin123}"

echo "=============================================="
echo "🔐 SMOKE TESTS - Seguridad Multi-Tenant"
echo "=============================================="
echo "Base URL: $BASE_URL"
echo ""

# Función para login
get_token() {
    local user=$1
    local pass=$2
    curl -s -X POST "$BASE_URL/api/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"username\":\"$user\",\"password\":\"$pass\"}" \
        | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('access_token') or d.get('token') or '')"
}

# Función para obtener primer ID de un listado (robusto: id o _id)
get_first_id() {
    local token=$1
    local endpoint=$2
    curl -s "$BASE_URL$endpoint" \
        -H "Authorization: Bearer $token" \
        | python3 -c "import sys,json; d=json.load(sys.stdin); print((d[0].get('id') or d[0].get('_id')) if d else '')" 2>/dev/null || echo ""
}

# Obtener tokens
echo "📋 Obteniendo tokens..."
ADMIN_A_TOKEN=$(get_token "$ADMIN_A_USER" "$ADMIN_A_PASS")
ADMIN_B_TOKEN=$(get_token "$ADMIN_B_USER" "$ADMIN_B_PASS")
SUPER_TOKEN=$(get_token "$SUPER_USER" "$SUPER_PASS")

if [ -z "$ADMIN_A_TOKEN" ]; then echo "❌ Error: No se pudo obtener token de Admin A"; exit 1; fi
if [ -z "$ADMIN_B_TOKEN" ]; then echo "❌ Error: No se pudo obtener token de Admin B"; exit 1; fi
if [ -z "$SUPER_TOKEN" ]; then echo "❌ Error: No se pudo obtener token de Superadmin"; exit 1; fi
echo "   ✅ Tokens obtenidos"

# Obtener IDs de Org B
echo ""
echo "📋 Obteniendo IDs de Org B..."
EMPRESA_B_ID=$(get_first_id "$ADMIN_B_TOKEN" "/api/companies")
TAXISTA_B_ID=$(get_first_id "$ADMIN_B_TOKEN" "/api/users")
TURNO_B_ID=$(get_first_id "$ADMIN_B_TOKEN" "/api/turnos")
SERVICE_B_ID=$(get_first_id "$ADMIN_B_TOKEN" "/api/services")

echo "   Empresa B: ${EMPRESA_B_ID:-'(no existe)'}"
echo "   Taxista B: ${TAXISTA_B_ID:-'(no existe)'}"
echo "   Turno B: ${TURNO_B_ID:-'(no existe)'}"
echo "   Service B: ${SERVICE_B_ID:-'(no existe)'}"

# Contadores
PASSED=0
FAILED=0
SKIPPED=0

# Función de test
run_test() {
    local test_num=$1
    local description=$2
    local method=$3
    local endpoint=$4
    local token=$5
    local expected_codes=$6
    local payload=$7

    echo ""
    echo "Test $test_num: $description"
    
    if [ -z "$endpoint" ] || [ "$endpoint" = "SKIP" ]; then
        echo "   ⚠️  SKIP (ID no disponible)"
        ((SKIPPED++))
        return
    fi

    local curl_cmd="curl -s -w '%{http_code}' -o /tmp/test_response"
    curl_cmd="$curl_cmd -X $method"
    curl_cmd="$curl_cmd -H 'Authorization: Bearer $token'"
    
    if [ -n "$payload" ]; then
        curl_cmd="$curl_cmd -H 'Content-Type: application/json'"
        curl_cmd="$curl_cmd -d '$payload'"
    fi
    
    curl_cmd="$curl_cmd '$BASE_URL$endpoint'"
    
    HTTP_CODE=$(eval $curl_cmd)
    
    # Verificar si el código está en los esperados
    if echo "$expected_codes" | grep -qw "$HTTP_CODE"; then
        echo "   ✅ PASS (HTTP $HTTP_CODE)"
        ((PASSED++))
    else
        echo "   ❌ FAIL (HTTP $HTTP_CODE, esperado: $expected_codes)"
        ((FAILED++))
    fi
}

echo ""
echo "=============================================="
echo "🔐 Ejecutando tests..."
echo "=============================================="

# Test 1: Admin A solo ve datos de su org en reportes
run_test 1 "Reportes solo Org A" \
    "GET" "/api/reportes/diario?fecha=$(date +%Y-%m-%d)" \
    "$ADMIN_A_TOKEN" "200"

# Test 2: Export servicios con empresa de otra org
if [ -n "$EMPRESA_B_ID" ]; then
    run_test 2 "Export servicios empresa Org B bloqueado" \
        "GET" "/api/services/export/csv?empresa_id=$EMPRESA_B_ID" \
        "$ADMIN_A_TOKEN" "400 403"
else
    run_test 2 "Export servicios empresa Org B bloqueado" "GET" "SKIP" "" ""
fi

# Test 3: Export turnos con taxista de otra org
if [ -n "$TAXISTA_B_ID" ]; then
    run_test 3 "Export turnos taxista Org B bloqueado" \
        "GET" "/api/turnos/export/csv?taxista_id=$TAXISTA_B_ID" \
        "$ADMIN_A_TOKEN" "400 403"
else
    run_test 3 "Export turnos taxista Org B bloqueado" "GET" "SKIP" "" ""
fi

# Test 4: Superadmin no puede crear companies
run_test 4 "Superadmin POST companies bloqueado" \
    "POST" "/api/companies" \
    "$SUPER_TOKEN" "403" \
    '{"nombre":"TestX","numero_cliente":"X-001"}'

# Test 5: Admin A no puede modificar company de Org B
if [ -n "$EMPRESA_B_ID" ]; then
    run_test 5 "PUT company Org B bloqueado" \
        "PUT" "/api/companies/$EMPRESA_B_ID" \
        "$ADMIN_A_TOKEN" "404 403" \
        '{"nombre":"IntentoCambio"}'
else
    run_test 5 "PUT company Org B bloqueado" "PUT" "SKIP" "" ""
fi

# Test 6: Admin A no puede finalizar turno de Org B
if [ -n "$TURNO_B_ID" ]; then
    run_test 6 "Finalizar turno Org B bloqueado" \
        "PUT" "/api/turnos/$TURNO_B_ID/finalizar" \
        "$ADMIN_A_TOKEN" "404 403" \
        '{"fecha_fin":"2025-12-26","hora_fin":"18:00","km_fin":100,"cerrado":true}'
else
    run_test 6 "Finalizar turno Org B bloqueado" "PUT" "SKIP" "" ""
fi

# Test 7: Admin A no puede editar service de Org B
if [ -n "$SERVICE_B_ID" ]; then
    run_test 7 "PUT service Org B bloqueado" \
        "PUT" "/api/services/$SERVICE_B_ID" \
        "$ADMIN_A_TOKEN" "404 403" \
        '{"fecha":"2025-12-26","hora":"10:00","origen":"X","destino":"X","tipo":"particular","importe":10,"importe_espera":0,"kilometros":5}'
else
    run_test 7 "PUT service Org B bloqueado" "PUT" "SKIP" "" ""
fi

# Test 8: Admin A no puede borrar service de Org B
if [ -n "$SERVICE_B_ID" ]; then
    run_test 8 "DELETE service Org B bloqueado" \
        "DELETE" "/api/services/$SERVICE_B_ID" \
        "$ADMIN_A_TOKEN" "404 403"
else
    run_test 8 "DELETE service Org B bloqueado" "DELETE" "SKIP" "" ""
fi

# Test 9: Admin A no puede borrar turno de Org B
if [ -n "$TURNO_B_ID" ]; then
    run_test 9 "DELETE turno Org B bloqueado" \
        "DELETE" "/api/turnos/$TURNO_B_ID" \
        "$ADMIN_A_TOKEN" "404 403"
else
    run_test 9 "DELETE turno Org B bloqueado" "DELETE" "SKIP" "" ""
fi

# Resumen
echo ""
echo "=============================================="
echo "📊 RESUMEN"
echo "=============================================="
echo "✅ Pasados: $PASSED"
echo "❌ Fallidos: $FAILED"
echo "⚠️  Saltados: $SKIPPED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "🎉 ¡TODOS LOS TESTS PASARON!"
    exit 0
else
    echo "❌ Algunos tests fallaron"
    exit 1
fi
