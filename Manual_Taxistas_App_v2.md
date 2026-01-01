# MANUAL DE USUARIO - APP MÓVIL PARA TAXISTAS
## TaxiFast v2.0.0

---

### INFORMACIÓN DE LA APLICACIÓN

**Nombre:** TaxiFast - App Móvil  
**Versión:** 2.0.0  
**Plataforma:** Android  
**Fecha:** Diciembre 2025

---

## ÍNDICE

1. [Instalación de la App](#1-instalación-de-la-app)
2. [Inicio de Sesión](#2-inicio-de-sesión)
3. [Iniciar un Turno](#3-iniciar-un-turno)
4. [Registrar un Servicio](#4-registrar-un-servicio)
5. [Cambio de Vehículo](#5-cambio-de-vehículo)
6. [Registrar Repostaje](#6-registrar-repostaje)
7. [Ver Mis Servicios](#7-ver-mis-servicios)
8. [Finalizar un Turno](#8-finalizar-un-turno)
9. [Historial de Turnos](#9-historial-de-turnos)
10. [Mi Perfil](#10-mi-perfil)
11. [Preguntas Frecuentes](#11-preguntas-frecuentes)
12. [Solución de Problemas](#12-solución-de-problemas)

---

## 1. INSTALACIÓN DE LA APP

### Requisitos

- Teléfono o tablet **Android** (versión 5.0 o superior)
- Conexión a Internet
- Archivo APK proporcionado por el administrador

### Paso 1: Descargar el APK

**Por WhatsApp o Email:**
1. Recibirá un mensaje con el archivo APK
2. Descargue el archivo tocando sobre él
3. Se guardará en la carpeta "Descargas"

### Paso 2: Permitir Instalación

⚠️ **IMPORTANTE:** Android bloquea instalaciones por seguridad.

**Para Android 8.0 o superior:**
1. Al instalar, aparecerá: "Por razones de seguridad..."
2. Toque **"Configuración"**
3. Active **"Permitir desde esta fuente"**
4. Vuelva atrás

**Para versiones anteriores:**
1. Vaya a **Ajustes** → **Seguridad**
2. Active **"Orígenes desconocidos"**

### Paso 3: Instalar

1. Abra la carpeta **"Descargas"**
2. Toque el archivo **"TaxiFast.apk"**
3. Toque **"Instalar"**
4. Cuando termine, toque **"Abrir"**

✅ **¡App instalada!**

---

## 2. INICIO DE SESIÓN

### Abrir la App

1. Busque el ícono de **TaxiFast** en su pantalla
2. Toque para abrir
3. Verá la pantalla de login con el logo

### Ingresar Credenciales

El administrador le proporcionará:
- **Usuario:** Su nombre de usuario único
- **Contraseña:** Su contraseña personal

1. Escriba su **usuario**
2. Escriba su **contraseña**
3. Toque **"Iniciar Sesión"**

### Menú Principal

Una vez dentro, verá cuatro opciones en la barra inferior:

| Ícono | Sección | Función |
|-------|---------|----------|
| 📋 | Mis Servicios | Ver servicios registrados |
| ➕ | Nuevo Servicio | Registrar un nuevo servicio |
| ⏰ | Turnos | Gestionar su turno de trabajo |
| 👤 | Perfil | Ver su información y cerrar sesión |

---

## 3. INICIAR UN TURNO

⚠️ **IMPORTANTE:** Debe iniciar un turno ANTES de poder registrar servicios.

### ¿Qué es un Turno?

Un turno registra:
- Hora de inicio y fin de su jornada
- Kilómetros iniciales y finales del vehículo
- Todos los servicios realizados
- Repostajes de combustible (si los hay)

### Pasos para Iniciar Turno

1. Toque **⏰ Turnos** en la barra inferior
2. Toque el botón **"Iniciar Turno"**
3. Complete el formulario:

| Campo | Descripción |
|-------|-------------|
| **Vehículo** | Seleccione el vehículo que usará (matrícula) |
| **Fecha Inicio** | Se completa automáticamente |
| **Hora Inicio** | Se completa automáticamente (hora de España) |
| **KM Inicio** | Ingrese el kilometraje actual del cuentakilómetros |

4. Toque **"Iniciar Turno"**

✅ **¡Turno Activo!** Ya puede registrar servicios.

### Notas Importantes

- Solo puede tener **UN turno activo** a la vez
- **Anote bien** el kilometraje inicial (mire el cuentakilómetros)
- La hora se registra automáticamente del servidor (hora de España)

---

## 4. REGISTRAR UN SERVICIO

### Acceder al Formulario

1. Toque **➕ Nuevo Servicio** en la barra inferior
2. Aparecerá el formulario de registro

### Campos del Formulario

#### Información Básica (Obligatorios)

| Campo | Descripción | Ejemplo |
|-------|-------------|----------|
| **Fecha** | Fecha del servicio | 31/12/2025 |
| **Hora** | Hora del servicio | 10:30 |
| **Origen** | Lugar de recogida | Cangas del Narcea |
| **Destino** | Lugar de destino | Aeropuerto de Asturias |

#### Tipo de Servicio

| Opción | Cuándo usar |
|--------|-------------|
| **Empresa/Cliente** | Servicio contratado por una empresa |
| **Particular** | Servicio a un cliente individual |

**Si es Empresa:** Seleccione la empresa de la lista desplegable.

#### 💳 Método de Pago (NUEVO)

| Opción | Descripción |
|--------|-------------|
| **Efectivo** | El cliente pagó en efectivo |
| **TPV** | El cliente pagó con tarjeta |

#### Información Económica (Opcionales pero recomendados)

| Campo | Descripción |
|-------|-------------|
| **Importe (€)** | Precio del servicio |
| **Importe Espera (€)** | Cargo adicional por espera |
| **Kilómetros** | Distancia recorrida (opcional) |

### Guardar el Servicio

1. Revise que los datos sean correctos
2. Toque **"Guardar Servicio"**
3. El servicio se registra en su turno activo

✅ **Servicio Registrado**

---

## 5. CAMBIO DE VEHÍCULO

### ¿Cuándo usar esta función?

Si durante un turno necesita usar un vehículo **diferente** al que inició el turno.

**Ejemplo:** Inició turno con vehículo 1234-ABC pero para un servicio específico usó el 5678-XYZ.

### Cómo Registrar un Cambio de Vehículo

Al crear un nuevo servicio:

1. Active el switch **"¿Vehículo diferente al del turno?"**
2. Aparecerán campos adicionales:

| Campo | Descripción | Obligatorio |
|-------|-------------|-------------|
| **Vehículo** | Seleccione el otro vehículo | ✅ Sí |
| **KM Inicio Vehículo** | Kilometraje al empezar con este vehículo | ✅ Sí |
| **KM Fin Vehículo** | Kilometraje al terminar con este vehículo | ✅ Sí |

### Validaciones

- El **KM Fin** debe ser **mayor o igual** que el KM Inicio
- Ambos campos de KM son obligatorios si cambia de vehículo

---

## 6. REGISTRAR REPOSTAJE

### ¿Qué es?

Puede registrar los repostajes de combustible que realice durante su turno.

### Cómo Registrar un Repostaje

1. Vaya a **⏰ Turnos**
2. En su turno activo, busque la sección **"Combustible"**
3. Toque **"Registrar Repostaje"**
4. Complete el formulario:

| Campo | Descripción |
|-------|-------------|
| **¿Ha repostado?** | Sí / No |
| **Litros** | Cantidad de combustible (ej: 45.5) |
| **Vehículo** | Vehículo que repostó |
| **KM Vehículo** | Kilometraje en el momento del repostaje |

5. Toque **"Guardar"**

### Notas

- Solo puede registrar repostaje mientras el turno está **activo**
- Una vez cerrado el turno, no puede modificar el repostaje
- El repostaje aparecerá en el resumen del turno

---

## 7. VER MIS SERVICIOS

### Acceder a Mis Servicios

1. Toque **📋 Mis Servicios** en la barra inferior
2. Verá la lista de servicios de su turno actual

### Información Mostrada

Cada servicio muestra:
- Fecha y hora
- Origen → Destino
- Importe total
- Tipo (Empresa/Particular)
- Método de pago (💵 Efectivo / 💳 TPV)
- Kilómetros

### Filtrar Servicios

Puede filtrar por:
- **Fecha Inicio** y **Fecha Fin**
- **Tipo:** Todos, Empresa, Particular

### Editar un Servicio

1. Toque sobre el servicio que desea modificar
2. Edite los campos necesarios
3. Toque **"Guardar"**

⚠️ Solo puede editar servicios de turnos **activos** o **no cerrados**.

---

## 8. FINALIZAR UN TURNO

### Cuándo Finalizar

Al terminar su jornada de trabajo.

### Pasos para Finalizar

1. Vaya a **⏰ Turnos**
2. Verá el resumen de su turno activo:
   - Servicios realizados
   - Total de kilómetros
   - Total cobrado (clientes y particulares)
   - Repostaje (si lo hay)

3. Toque **"Finalizar Turno"**
4. Complete:

| Campo | Descripción |
|-------|-------------|
| **Fecha Fin** | Se completa automáticamente |
| **Hora Fin** | Se completa automáticamente (hora de España) |
| **KM Fin** | **MUY IMPORTANTE** - Kilometraje final del vehículo |

5. Toque **"Finalizar"**

### Resumen Automático

El sistema calcula:
- **Total KM:** KM Fin - KM Inicio
- **Servicios:** Cantidad de servicios realizados
- **Total Clientes:** Suma de servicios a empresas
- **Total Particulares:** Suma de servicios particulares
- **Total General:** Suma total

✅ **Turno Finalizado**

---

## 9. HISTORIAL DE TURNOS

### Ver Turnos Anteriores

1. Vaya a **⏰ Turnos**
2. Desplácese hacia abajo para ver turnos anteriores

### Información de Cada Turno

| Campo | Descripción |
|-------|-------------|
| Matrícula | Vehículo utilizado |
| Estado | Activo / Cerrado / Liquidado |
| Inicio | Fecha y hora de inicio |
| Fin | Fecha y hora de fin |
| KM | Kilómetros inicial → final (total) |
| ⛽ Repostaje | Litros repostados (si aplica) |
| Servicios | Cantidad de servicios |
| Totales | Clientes / Particulares / Total |

### Ver Servicios de un Turno

1. Toque **"Ver servicios"** o el ícono de expandir
2. Se desplegará la lista de servicios del turno
3. Cada servicio muestra:
   - Fecha y hora
   - Origen → Destino
   - Tipo y empresa (si aplica)
   - Matrícula del vehículo usado
   - Importe y método de pago

---

## 10. MI PERFIL

### Acceder al Perfil

1. Toque **👤 Perfil** en la barra inferior

### Información Disponible

- Nombre completo
- Usuario de acceso
- Número de licencia
- Teléfono (si está registrado)
- Email (si está registrado)

### Cerrar Sesión

1. En la pantalla de Perfil
2. Toque **"Cerrar Sesión"** (botón rojo)
3. Volverá a la pantalla de login

---

## 11. PREGUNTAS FRECUENTES

### ¿Necesito internet para usar la app?

**Sí**, necesita conexión para:
- Iniciar sesión
- Registrar servicios
- Iniciar/finalizar turnos

### ¿Qué hago si olvidé mi contraseña?

Contacte al administrador para que le genere una nueva.

### ¿Puedo usar la app en varios teléfonos?

Sí, pero no se recomienda tener sesión abierta en varios dispositivos al mismo tiempo.

### ¿Qué pasa si me equivoco en un servicio?

Puede editarlo mientras el turno esté activo o no cerrado.

### ¿Por qué no puedo crear un servicio?

Debe tener un **turno activo**. Vaya a Turnos e inicie uno.

### ¿Qué es el método de pago?

- **Efectivo:** El cliente pagó en metálico
- **TPV:** El cliente pagó con tarjeta

### ¿Cuándo debo marcar "vehículo diferente"?

Cuando use un vehículo distinto al que inició el turno.

### ¿Puedo modificar un repostaje?

Solo mientras el turno esté activo.

### ¿La hora que aparece es correcta?

Sí, la app usa la **hora de España** (Europe/Madrid).

---

## 12. SOLUCIÓN DE PROBLEMAS

| Problema | Solución |
|----------|----------|
| No puedo instalar la app | Active "Orígenes desconocidos" en Ajustes |
| No puedo iniciar sesión | Verifique usuario/contraseña. Contacte admin. |
| Error de red | Verifique conexión a internet |
| No puedo iniciar turno | Cierre el turno anterior primero |
| Los servicios no se guardan | Verifique que tiene turno activo |
| La app va lenta | Cierre otras apps, reinicie el teléfono |
| Hora incorrecta | Actualice la app (versión 2.0.0 corrige esto) |

---

## CONTACTO Y SOPORTE

**Si necesita ayuda:**

Contacte con su administrador o con el soporte técnico de su organización.

---

**Manual de Usuario - App TaxiFast v2.0.0**  
*Actualizado: Diciembre 2025*
