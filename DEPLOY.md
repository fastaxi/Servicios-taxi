# Notas de Despliegue - TaxiFast

## Variable GIT_SHA (autodeteccion)

El endpoint `/health` (y `/`, `/api/health`) devuelven el campo `git_sha`.

### Como funciona

El backend auto-detecta el SHA al arrancar con esta prioridad:
1. `git rev-parse --short HEAD` (si hay `.git` en el entorno — Emergent, dev local)
2. Variable de entorno `GIT_SHA` (inyectada por CI/CD en Docker)
3. `"unknown"` como ultimo recurso

**No hace falta configurar nada en Emergent** — el pod tiene `.git` y la deteccion es automatica.

### Para Docker / CI/CD

```dockerfile
ARG GIT_SHA=unknown
ENV GIT_SHA=$GIT_SHA
```

Build:
```bash
docker build --build-arg GIT_SHA=$(git rev-parse --short HEAD) -t taxifast .
```

### Verificacion

```bash
curl -s https://<BACKEND_DOMAIN>/api/health | jq .git_sha
# Debe devolver el SHA corto del commit desplegado
```

## Proximo paso: Generar APK en Mac local

### Pre-requisitos
- Node.js >= 18 (recomendado 20 LTS)
- Yarn: `npm install -g yarn`
- EAS CLI: `npm install -g eas-cli`
- Cuenta Expo: `eas login`
- Java JDK 17 (para builds locales Android)

### Comando (desde /frontend)
```bash
# Build en la nube de EAS (recomendado):
eas build --platform android --profile preview

# Build local (requiere Android SDK + JDK):
eas build --platform android --profile preview --local
```

### Antes de construir
1. Verificar `app.json` → version correcta
2. Verificar `eas.json` → `EXPO_PUBLIC_BACKEND_URL` apunta al backend de produccion
3. El perfil `preview` genera APK para pruebas internas
4. El perfil `production` genera AAB para Google Play
