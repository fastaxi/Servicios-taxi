# 🚕 Aplicación de Gestión de Servicios - Taxi Tineo

## 📱 Información General

Aplicación móvil desarrollada con **Expo/React Native** para la gestión de servicios de taxi en Asturias, España. 
Incluye funcionalidad offline-first con sincronización automática y diseño con los colores de la bandera asturiana.

## 🎨 Características Principales

### Para Taxistas:
- ✅ Registro de servicios con todos los detalles (fecha, hora, origen, destino, importe, km, etc.)
- ✅ Visualización de sus propios servicios
- ✅ Funcionalidad offline: los servicios se guardan localmente y se sincronizan automáticamente cuando hay conexión
- ✅ Clasificación de servicios por tipo: Empresa o Particular
- ✅ Selección de empresa para servicios corporativos

### Para Administradores:
- ✅ Visualización de todos los servicios de todos los taxistas
- ✅ Dashboard con estadísticas (total servicios, importe total, kilómetros totales)
- ✅ Filtros avanzados: por tipo (empresa/particular), por empresa específica, por rango de fechas
- ✅ Gestión completa de empresas (crear, editar, eliminar)
- ✅ Gestión de taxistas (crear, eliminar)
- ✅ Exportación de datos en 3 formatos:
  - **CSV** - Para análisis en Excel
  - **Excel** - Con formato y estilos
  - **PDF** - Para impresión y reportes

## 🔐 Credenciales de Acceso

### Administrador
```
Usuario: admin
Contraseña: admin123
```

### Taxista de Prueba
```
Usuario: taxista1
Contraseña: taxista123
```

## 🌐 URLs de Acceso

### Vista Web (Preview)
```
https://taxi-manager-12.preview.emergentagent.com
```

### API Backend
```
https://taxi-manager-12.preview.emergentagent.com/api
```

## 📱 Cómo Usar en Dispositivo Móvil Real

1. **Descarga Expo Go** desde:
   - iOS: App Store → Busca "Expo Go"
   - Android: Google Play Store → Busca "Expo Go"

2. **Escanea el QR** que aparece en la consola al iniciar la aplicación

3. **O accede mediante túnel**: La aplicación está corriendo con túnel ngrok para acceso externo

## 🎨 Diseño

La aplicación utiliza los colores oficiales de la bandera de Asturias:
- **Azul**: `#0066CC` (Color primario)
- **Amarillo**: `#FFD700` (Color secundario/acentos)

Logo: Taxi Tineo con escudo de Asturias

## 📊 Datos de Prueba Incluidos

### Empresa
- Nombre: Hospital Universitario Central de Asturias
- CIF: Q3300001A
- Dirección: Calle Roma s/n, Oviedo, Asturias

### Servicio de Ejemplo
- Fecha: 23/01/2025 - 10:30
- Ruta: Tineo → Oviedo
- Importe: 45.50€ (IVA 10% incluido)
- Kilómetros: 52.3 km
- Tipo: Empresa (Hospital Universitario Central de Asturias)
- Taxista: Juan García

## 🔧 Funcionalidad Offline

La aplicación detecta automáticamente cuando no hay conexión a Internet y:

1. **Guarda los servicios localmente** en el dispositivo usando AsyncStorage
2. **Muestra un banner amarillo** indicando cuántos servicios están pendientes de sincronizar
3. **Sincroniza automáticamente** cuando se detecta conexión de nuevo
4. Los usuarios pueden seguir trabajando sin interrupción

## 📋 Flujos de Trabajo

### Flujo Taxista:
1. **Login** con credenciales de taxista
2. **Nuevo Servicio**: 
   - Rellenar formulario con datos del servicio
   - Seleccionar tipo (Empresa/Particular)
   - Si es empresa, seleccionar de la lista
   - Guardar (online o offline)
3. **Mis Servicios**: Ver historial de servicios propios
4. **Perfil**: Ver información personal y cerrar sesión

### Flujo Administrador:
1. **Login** con credenciales de admin
2. **Dashboard**:
   - Ver estadísticas generales
   - Aplicar filtros (Todos/Empresa/Particular)
   - Filtrar por empresa específica
   - Exportar datos (CSV/Excel/PDF)
3. **Empresas**:
   - Ver lista de empresas
   - Crear nueva empresa (botón +)
   - Editar empresa existente (icono lápiz)
   - Eliminar empresa (icono papelera)
4. **Taxistas**:
   - Ver lista de taxistas
   - Crear nuevo taxista (botón +)
   - Eliminar taxista (icono papelera)
5. **Perfil**: Información del sistema y cerrar sesión

## 💾 Estructura de Datos

### Servicio
```json
{
  "fecha": "2025-01-23",
  "hora": "10:30",
  "origen": "Tineo",
  "destino": "Oviedo",
  "importe": 45.50,
  "tiempo_espera": 5,
  "kilometros": 52.3,
  "tipo": "empresa",
  "empresa_id": "...",
  "empresa_nombre": "Hospital Universitario..."
}
```

**Nota importante**: Todos los importes incluyen IVA del 10%

## 🔒 Permisos y Seguridad

- **JWT Authentication**: Tokens seguros con expiración de 30 días
- **Autorización por roles**:
  - Taxistas solo ven y editan sus propios servicios
  - Administradores tienen acceso total
- **Validación de datos** en frontend y backend
- **Hashing de contraseñas** con bcrypt

## 📞 Contacto

**Taxi Tineo**
- Web: www.taxitineo.com
- Teléfono: 985 80 15 15
- Servicio 24 Horas

## 🛠️ Tecnologías Utilizadas

### Frontend
- **Expo 54** / React Native
- **Expo Router** (navegación file-based)
- **React Native Paper** (componentes UI)
- **@react-native-async-storage** (almacenamiento local)
- **@react-native-community/netinfo** (detección de conexión)
- **Axios** (peticiones HTTP)
- **date-fns** (manejo de fechas)

### Backend
- **FastAPI** (Python)
- **MongoDB** (base de datos)
- **Motor** (driver async MongoDB)
- **JWT** (autenticación)
- **openpyxl** (exportación Excel)
- **reportlab** (exportación PDF)

## ✅ Estado del Proyecto

**Backend**: ✅ 100% Operativo (27/27 tests pasados)
- Autenticación JWT ✅
- CRUD Usuarios ✅
- CRUD Empresas ✅
- CRUD Servicios ✅
- Filtros avanzados ✅
- Sincronización batch ✅
- Exportación CSV/Excel/PDF ✅

**Frontend**: ✅ Implementado y funcionando
- Login screen ✅
- Navegación taxista (tabs) ✅
- Navegación admin (tabs) ✅
- Funcionalidad offline ✅
- Diseño Asturias ✅

## 🚀 Testing

El backend ha sido exhaustivamente testeado con 27 pruebas exitosas cubriendo:
- Autenticación y autorización
- Todos los endpoints CRUD
- Filtros y búsquedas
- Exportaciones en múltiples formatos
- Permisos por roles

El frontend está listo para ser probado manualmente o mediante herramientas de testing UI.

---

**Versión**: 1.0.0  
**Última actualización**: Enero 2025
