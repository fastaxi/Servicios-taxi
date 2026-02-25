# TaxiFast - PRD (Product Requirements Document)

## Problem Statement
Full-stack multi-tenant taxi services management app. FastAPI backend + Expo React Native frontend + MongoDB. Supports `taxista`, `admin`, and `superadmin` roles with organization-based feature flags and settings.

## Core Requirements
1. **Feature Flag System (Paso 1)** - Dynamic `features.taxitur_origen` at org level
2. **Tenant-Scoped Indexes (Paso 2)** - Unique per org for `matricula`, `numero_cliente`
3. **UTC DateTime Handling (Paso 3)** - Proper datetime fields for filtering/sorting
4. **Multi-tenant Config (Paso 4)** - Separate global vs org-specific settings
5. **Backend Idempotency (Paso 5A)** - `client_uuid` on `POST /services` and `/services/sync`
6. **Frontend Offline Queue (Paso 5B)** - `client_uuid` generation, persistent offline queue, idempotent sync
7. **Superadmin Feature Flags UI (Paso 6)** - Toggle feature flags per organization from superadmin panel

## Architecture
```
backend/server.py                           - Monolithic FastAPI backend
frontend/utils/uuid.ts                      - UUID generation (web + mobile safe)
frontend/contexts/SyncContext.tsx            - Offline queue (QueuedService type, AsyncStorage)
frontend/app/(tabs)/new-service.tsx          - Service creation with stable UUID + offline fallback
frontend/app/(tabs)/services.tsx             - Service list with pending sync UI
frontend/app/(superadmin)/organizations.tsx  - Superadmin org management + feature flag toggles
```

## What's Been Implemented

### Paso 1: Feature Flags ✅
### Paso 2: Tenant-Scoped Indexes ✅
### Paso 3: UTC DateTime ✅
### Paso 4: Multi-tenant Config ✅
### Paso 5A: Backend Idempotency ✅
### Paso 5B: Frontend Offline Queue ✅ (2026-02-25)
### Paso 6: Superadmin Feature Flags UI ✅ (2026-02-25)
- Backend: `PUT /api/superadmin/organizations/{org_id}/features`
  - Whitelist: `ALLOWED_FEATURE_KEYS = {"taxitur_origen"}`
  - Only boolean values, only superadmin, merge without deleting existing keys
  - Validation: 403 for non-superadmin, 400 for invalid key/type
- Frontend: Toggle switch in organizations screen (superadmin)
  - Shows "Taxitur: Origen Parada/Lagos" with on/off state
  - OnChange calls endpoint and refreshes org list
- Testing: 100% backend (12/12), 100% frontend

## Prioritized Backlog

### P2
- Robust font solution for Spanish special characters (currently stripped as workaround)

## Key Credentials
- Superadmin: `superadmin` / `superadmin123`
- Taxitur Admin: `admintur` / `admin123`
- Test Taxista: `taxista_orgb_test` / `test123`
- Taxitur org_id: `69484bec187c3bc2b0fdb8f4`

## Key API Endpoints
- `POST /api/services` - Idempotent with `client_uuid`
- `POST /api/services/sync` - Batch sync with per-item idempotency
- `PUT /api/my-organization/settings` - Admin updates own org settings
- `PUT /api/superadmin/organizations/{org_id}/settings` - Superadmin updates any org settings
- `PUT /api/superadmin/organizations/{org_id}/features` - Superadmin toggles feature flags
