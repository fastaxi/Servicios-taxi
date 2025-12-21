# 📱 Guía para Generar APK de TaxiFast

## 🔧 Requisitos Previos (Una sola vez)

### En Mac o Windows:

1. **Instalar Node.js** (si no lo tienes):
   - Descarga desde: https://nodejs.org (versión LTS)

2. **Instalar EAS CLI**:
   ```bash
   npm install -g eas-cli
   ```

3. **Iniciar sesión en Expo**:
   ```bash
   eas login
   ```
   - Usuario: `ivantaxi`
   - Contraseña: (la que usaste para crear la cuenta)

---

## 🚀 Pasos para Generar el APK

### En Mac (Terminal):

```bash
# 1. Ir a la carpeta del proyecto
cd /Users/ivan/Servicios-taxi/frontend

# 2. Actualizar código desde GitHub
cd ..
git pull origin main
cd frontend

# 3. Instalar dependencias (si es necesario)
npm install --legacy-peer-deps

# 4. Generar APK
eas build --platform android --profile preview
```

### En Windows 11 (PowerShell o CMD):

```bash
# 1. Clonar el proyecto (primera vez)
git clone https://github.com/fastaxi/Servicios-taxi.git
cd Servicios-taxi\frontend

# Si ya lo tienes clonado, actualizar:
cd C:\ruta\a\Servicios-taxi
git pull origin main
cd frontend

# 2. Instalar dependencias
npm install --legacy-peer-deps

# 3. Iniciar sesión en EAS (si no lo has hecho)
eas login

# 4. Generar APK
eas build --platform android --profile preview
```

---

## ⏳ Durante el Build

- El build tarda **10-20 minutos**
- Puedes cerrar la terminal, el build continúa en la nube
- Recibirás un email cuando termine
- O puedes ver el progreso en: https://expo.dev

---

## 📥 Descargar el APK

Cuando termine, tienes tres opciones:

1. **Desde el email** que te envía Expo

2. **Desde la terminal**:
   ```bash
   eas build:list
   ```
   Copia el enlace del último build

3. **Desde la web**: https://expo.dev → Tu proyecto → Builds

---

## 📲 Instalar en el Móvil Android

1. Descarga el archivo `.apk` en el móvil Android
2. Abre el archivo
3. Si pide permiso para "instalar apps desconocidas", acéptalo
4. Instala y abre la app

---

## 🔑 Credenciales Importantes

| Servicio | Usuario | Contraseña |
|----------|---------|------------|
| Expo/EAS | `ivantaxi` | (tu contraseña) |
| GitHub | `fastaxi` | (usar token) |
| App Superadmin | `superadmin` | `superadmin123` |

---

## ❗ Solución de Errores Comunes

| Error | Solución |
|-------|----------|
| `EACCES permission denied` | Mac: `sudo npm install -g eas-cli` |
| `eas: command not found` | Reinstalar: `npm install -g eas-cli` |
| `peer dependency conflict` | Usar `npm install --legacy-peer-deps` |
| `Not logged in` | Ejecutar `eas login` |
| `Invalid credentials` en git | Usar Personal Access Token de GitHub |

---

## 🔐 Crear Token de GitHub (si es necesario)

1. Ve a: https://github.com/settings/tokens
2. Click **"Generate new token (classic)"**
3. Ponle un nombre (ej: "TaxiFast")
4. Selecciona permisos: marca **repo** (todo el checkbox)
5. Click **"Generate token"**
6. **¡Copia el token!** (solo lo verás una vez)

Para usar el token en git push:
```bash
git push https://TU_TOKEN@github.com/fastaxi/Servicios-taxi.git main
```

---

## 📋 Resumen Rápido

```bash
# Actualizar y generar APK (Mac)
cd /Users/ivan/Servicios-taxi
git pull origin main
cd frontend
npm install --legacy-peer-deps
eas build --platform android --profile preview
```

```bash
# Actualizar y generar APK (Windows)
cd C:\ruta\a\Servicios-taxi
git pull origin main
cd frontend
npm install --legacy-peer-deps
eas build --platform android --profile preview
```

---

## 📞 URLs Importantes

- **Panel Web Admin**: https://servicios-taxi.vercel.app
- **Backend API**: https://taxitineo.emergent.host/api
- **Expo Dashboard**: https://expo.dev
- **GitHub Repo**: https://github.com/fastaxi/Servicios-taxi

---

*Última actualización: Junio 2025*
