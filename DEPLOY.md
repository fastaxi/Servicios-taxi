# Notas de Despliegue - TaxiFast

## Variable GIT_SHA

El endpoint `/health` devuelve el campo `git_sha` para verificar que commit esta desplegado.

### Como inyectarla

**Docker:**
```dockerfile
ARG GIT_SHA=unknown
ENV GIT_SHA=$GIT_SHA
```
Build:
```bash
docker build --build-arg GIT_SHA=$(git rev-parse --short HEAD) -t taxifast .
```

**PaaS / Vercel / EAS:**
Configurar la variable de entorno `GIT_SHA` en el panel del proveedor con el short SHA del commit desplegado.

**Supervisor (desarrollo local):**
Anadir a `backend/.env`:
```
GIT_SHA=abc1234
```

### Verificacion
```bash
curl -s https://<BACKEND_DOMAIN>/health | jq .git_sha
# Debe devolver el SHA del commit, no "unknown"
```

## Proximo paso: Generar APK en Mac local

### Pre-requisitos
- Node.js >= 18 (recomendado 20 LTS)
- Yarn: `npm install -g yarn`
- EAS CLI: `npm install -g eas-cli`
- Cuenta Expo: `eas login`
- Java JDK 17 (para builds locales Android)
- Android SDK (si se hace build local sin EAS)

### Comando para generar APK (desde /frontend)
```bash
# Build en la nube de EAS (recomendado):
eas build --platform android --profile preview

# Build local (requiere Android SDK):
eas build --platform android --profile preview --local
```

### Perfiles de build (eas.json)
- `preview`: APK para pruebas internas (distribucion interna)
- `production`: AAB para Google Play

### Antes de construir
1. Verificar `app.json` tiene la version correcta
2. Verificar `eas.json` tiene las variables de entorno correctas para el perfil
3. Comprobar que `EXPO_PUBLIC_BACKEND_URL` apunta al backend de produccion
