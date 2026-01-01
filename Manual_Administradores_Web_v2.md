# MANUAL DE ADMINISTRACIÓN - PANEL WEB
## TaxiFast v2.0.0

---

### INFORMACIÓN DEL SISTEMA

**Nombre:** Panel de Administración - TaxiFast  
**Versión:** 2.0.0  
**URL de Acceso:** https://servicios-taxi.vercel.app  
**Fecha:** Diciembre 2025

---

## ÍNDICE

1. [Inicio de Sesión](#1-inicio-de-sesión)
2. [Dashboard Principal](#2-dashboard-principal)
3. [Gestión de Empresas/Clientes](#3-gestión-de-empresasclientes)
4. [Gestión de Taxistas](#4-gestión-de-taxistas)
5. [Gestión de Vehículos](#5-gestión-de-vehículos)
6. [Gestión de Turnos](#6-gestión-de-turnos)
7. [Consulta de Servicios](#7-consulta-de-servicios)
8. [Exportación de Datos](#8-exportación-de-datos)
9. [Configuración del Sistema](#9-configuración-del-sistema)
10. [Novedades v2.0.0](#10-novedades-v200)
11. [Preguntas Frecuentes](#11-preguntas-frecuentes)

---

## 1. INICIO DE SESIÓN

### Acceder al Panel Web

1. Abra su navegador (Chrome, Firefox, Safari o Edge)
2. Escriba: **https://servicios-taxi.vercel.app**
3. Presione Enter

### Ingresar Credenciales

| Campo | Descripción |
|-------|-------------|
| **Usuario** | Su nombre de usuario de administrador |
| **Contraseña** | Su contraseña |

**Credenciales por defecto:**
- Usuario: `admin`
- Contraseña: `admin123`

⚠️ **IMPORTANTE:** Cambie la contraseña por defecto la primera vez.

### Iniciar Sesión

1. Complete los campos
2. Haga clic en **"Iniciar Sesión"**
3. Si son correctas, accederá al Dashboard

---

## 2. DASHBOARD PRINCIPAL

### Elementos de la Interfaz

#### Barra Lateral (Menú de Navegación)

| Ícono | Sección | Función |
|-------|---------|----------|
| 🚗 | Dashboard | Vista general y servicios |
| 🏢 | Empresas | Gestión de clientes corporativos |
| 👥 | Taxistas | Gestión de conductores |
| 🚙 | Vehículos | Gestión de la flota |
| ⏰ | Turnos | Control de turnos de trabajo |
| ⚙️ | Configuración | Ajustes del sistema |
| 🚪 | Cerrar Sesión | Salir del sistema |

#### Tarjetas de Estadísticas

| Tarjeta | Información |
|---------|-------------|
| **Servicios** | Número total de servicios |
| **Total Importe** | Suma de ingresos (€) |
| **Total KM** | Kilómetros totales |

### Filtros Disponibles

| Filtro | Opciones |
|--------|----------|
| **Tipo** | Todos, Cliente, Particular |
| **Taxista** | Seleccionar taxista específico |
| **Origen** | Todos, Parada, Lagos (solo org Taxitur) |
| **Fecha Inicio** | Desde qué fecha |
| **Fecha Fin** | Hasta qué fecha |

#### Tabla de Servicios

| Columna | Descripción |
|---------|-------------|
| Fecha | Fecha del servicio |
| Hora | Hora del servicio |
| Taxista | Quién realizó el servicio |
| Origen | Lugar de recogida |
| Destino | Lugar de destino |
| KM | Kilómetros recorridos |
| Importe | Precio del servicio |
| Espera | Cargo por espera |
| Total | Importe total |
| Tipo | Empresa/Particular |
| Pago | Efectivo/TPV |
| Acciones | Editar/Eliminar |

---

## 3. GESTIÓN DE EMPRESAS/CLIENTES

### Ver Lista de Empresas

1. Haga clic en **"Empresas"** en el menú lateral
2. Verá la tabla con todas las empresas

### Columnas de la Tabla

| Columna | Descripción |
|---------|-------------|
| Nombre | Razón social |
| CIF/NIF | Identificación fiscal |
| N° Cliente | Código único |
| Contacto | Persona de contacto |
| Teléfono | Número de contacto |
| Email | Correo electrónico |
| Acciones | Editar/Eliminar |

### Agregar Nueva Empresa

1. Haga clic en el botón **"+"** (azul)
2. Complete el formulario:

**Campos obligatorios:**
- Nombre
- CIF/NIF
- Número de Cliente (único)

**Campos opcionales:**
- Contacto
- Teléfono
- Email
- Dirección

3. Haga clic en **"Guardar"**

### Editar Empresa

1. Localice la empresa
2. Haga clic en el ícono ✏️
3. Modifique los campos
4. Haga clic en **"Guardar"**

### Eliminar Empresa

1. Localice la empresa
2. Haga clic en el ícono 🗑️
3. Confirme la eliminación

⚠️ **ADVERTENCIA:** No se puede eliminar una empresa con servicios asociados.

---

## 4. GESTIÓN DE TAXISTAS

### Ver Lista de Taxistas

1. Haga clic en **"Taxistas"** en el menú lateral

### Información Mostrada

| Campo | Descripción |
|-------|-------------|
| Nombre | Nombre completo |
| Usuario | Nombre para login |
| Licencia | Número de licencia |
| Vehículo | Vehículo asignado |
| Estado | Activo/Inactivo |

### Agregar Nuevo Taxista

1. Haga clic en **"+"**
2. Complete:

**Obligatorios:**
- Nombre Completo
- Usuario (único)
- Contraseña
- Número de Licencia

**Opcionales:**
- Teléfono
- Email
- Dirección

3. Haga clic en **"Guardar"**

✅ El taxista podrá acceder a la app móvil con estas credenciales.

### Editar Taxista

1. Localice el taxista
2. Haga clic en ✏️
3. Modifique (puede cambiar contraseña)
4. **"Guardar"**

### Eliminar Taxista

1. Haga clic en 🗑️
2. Confirme

⚠️ Los servicios y turnos históricos se mantienen.

---

## 5. GESTIÓN DE VEHÍCULOS

### Ver Lista de Vehículos

1. Haga clic en **"Vehículos"**

### Columnas

| Columna | Descripción |
|---------|-------------|
| Matrícula | Placa del vehículo |
| Marca | Fabricante |
| Modelo | Modelo del vehículo |
| Plazas | Número de asientos |
| KM Iniciales | Kilometraje al registrar |
| Fecha Compra | Fecha de adquisición |
| Estado | Activo/Inactivo |

### Agregar Nuevo Vehículo

1. Haga clic en **"+"**
2. Complete:

**Obligatorios:**
- Matrícula (ej: 1234-ABC)
- Marca
- Modelo
- Plazas
- KM Iniciales

**Opcionales:**
- Fecha de Compra
- Notas

3. **"Guardar"**

✅ La matrícula debe ser única.

---

## 6. GESTIÓN DE TURNOS

### Acceder a Turnos

1. Haga clic en **"Turnos"** en el menú lateral

### Vista de Turnos

La tabla muestra:

| Columna | Descripción |
|---------|-------------|
| Taxista | Nombre del conductor |
| Vehículo | Matrícula |
| Fecha | Fecha del turno |
| Inicio | Hora de inicio |
| Fin | Hora de fin |
| KM | Inicio → Fin (Total) |
| ⛽ | **NUEVO** - Repostaje de combustible |
| Servicios | Cantidad de servicios |
| Clientes | Total € servicios a empresas |
| Particulares | Total € servicios particulares |
| Total | Suma total € |
| Estado | Activo/Cerrado/Liquidado |

### Columna de Repostaje (⛽) - NOVEDAD v2.0.0

Si el taxista registró repostaje durante el turno:
- Se muestra: **"45.5 L (1234-ABC)"**
- Indica: Litros repostados y vehículo

Si no hay repostaje: **"-"**

### Filtros Disponibles

| Filtro | Opciones |
|--------|----------|
| **Estado** | Todos / Activos / Cerrados / Liquidados |
| **Taxista** | Seleccionar taxista específico |

### Ver Servicios de un Turno

1. Haga clic en **"Ver servicios"** o expanda el turno
2. Se desplegará la lista de servicios:

Cada servicio muestra:
- Fecha y hora
- Origen → Destino
- Tipo (Empresa/Particular)
- **Matrícula del vehículo usado** (NOVEDAD)
- Importe y método de pago
- Kilómetros

### Información de Repostaje en Turno Expandido

Al expandir un turno con repostaje, verá:

```
⛽ Repostaje:
  • Litros: 45.5 L
  • Vehículo: 1234-ABC
  • KM: 125,430
```

### Editar un Turno

1. Haga clic en el ícono ✏️
2. Puede modificar:
   - Fecha/hora de inicio y fin
   - KM inicio y fin
   - Marcar como liquidado
3. **"Guardar"**

### Cerrar un Turno Manualmente

Si un taxista olvidó cerrar su turno:

1. Localice el turno activo
2. Haga clic en **"Cerrar"**
3. Complete fecha fin, hora fin y KM finales
4. Guarde

### Marcar como Liquidado

1. Edite el turno
2. Marque **"Liquidado"**
3. Guarde

El estado cambiará a "Liquidado" (verde).

---

## 7. CONSULTA DE SERVICIOS

### Desde el Dashboard

1. Vaya al **Dashboard**
2. Use los filtros para buscar servicios específicos

### Filtros de Búsqueda

| Filtro | Descripción |
|--------|-------------|
| **Tipo** | Todos / Cliente / Particular |
| **Taxista** | Filtrar por conductor |
| **Método Pago** | Todos / Efectivo / TPV |
| **Fecha Inicio** | Desde |
| **Fecha Fin** | Hasta |

### Información de Cada Servicio

| Campo | Descripción |
|-------|-------------|
| Fecha/Hora | Cuándo se realizó |
| Taxista | Quién lo realizó |
| Origen/Destino | Ruta |
| Vehículo | Matrícula (si fue diferente) |
| KM | Kilómetros |
| Importe | Precio base |
| Espera | Cargo adicional |
| Total | Suma |
| Tipo | Empresa/Particular |
| Pago | Efectivo/TPV |

### Campos Adicionales (Organización Taxitur)

Si su organización es Taxitur, verá también:
- **Origen Taxitur:** Parada o Lagos

---

## 8. EXPORTACIÓN DE DATOS

### Formatos Disponibles

| Formato | Descripción | Uso Recomendado |
|---------|-------------|------------------|
| **CSV** | Valores separados por comas | Análisis en Excel |
| **Excel** | Archivo .xlsx con formato | Reportes con estilo |
| **PDF** | Documento portable | Impresión y archivo |

### Exportar Servicios

1. En el Dashboard, aplique los filtros deseados
2. Haga clic en **"Exportar"**
3. Seleccione el formato
4. Se descargará el archivo

**Datos incluidos en exportación de servicios:**
- Fecha y hora
- Taxista
- Origen y destino
- Kilómetros
- Importe e importe de espera
- Total
- Tipo (empresa/particular)
- **Método de pago** (NUEVO)
- Empresa (si aplica)
- **Origen Taxitur** (si aplica) (NUEVO)

### Exportar Turnos

1. En la sección **Turnos**
2. Aplique filtros si es necesario
3. Haga clic en **"Exportar"**
4. Seleccione el formato

**Datos incluidos en exportación de turnos:**
- Taxista y vehículo
- Fecha/hora inicio y fin
- KM inicio, fin y total
- Cantidad de servicios
- Totales (clientes, particulares, general)
- Estado (cerrado/liquidado)
- **Información de repostaje** (NUEVO):
  - ¿Repostó? (Sí/No)
  - Litros
  - Vehículo
  - KM del repostaje
- **Lista detallada de todos los servicios del turno**

### Contenido del PDF de Turnos

El PDF incluye:
1. **Encabezado** con información del turno
2. **Resumen** con totales
3. **Información de repostaje** (si aplica)
4. **Tabla de servicios** detallada

---

## 9. CONFIGURACIÓN DEL SISTEMA

### Acceder a Configuración

1. Haga clic en **"Configuración"** en el menú

### Campos Configurables

| Campo | Descripción |
|-------|-------------|
| **Logo** | Imagen de la empresa |
| **Nombre** | Nombre del Radio Taxi |
| **Teléfono** | Número de contacto |
| **Web** | Página web |
| **Email** | Correo de contacto |
| **Dirección** | Ubicación física |

### Cambiar el Logo

1. Haga clic en "Seleccionar imagen"
2. Elija una imagen (recomendado: cuadrado)
3. El logo aparecerá en la app y panel

### Guardar Configuración

1. Modifique los campos
2. Haga clic en **"Guardar Configuración"**

---

## 10. NOVEDADES v2.0.0

### Nuevas Funcionalidades

#### Para Taxistas (App Móvil)

| Función | Descripción |
|---------|-------------|
| **Método de Pago** | Registrar si el pago fue en Efectivo o TPV |
| **Cambio de Vehículo** | Usar un vehículo diferente durante un servicio |
| **KM Vehículo Alternativo** | Registrar KM inicio/fin del vehículo alternativo |
| **Repostaje** | Registrar repostajes de combustible |
| **Kilómetros Opcionales** | El campo KM del servicio ya no es obligatorio |

#### Para Administradores (Web)

| Función | Descripción |
|---------|-------------|
| **Columna ⛽** | Ver repostajes en la tabla de turnos |
| **Detalle de Repostaje** | Litros, vehículo y KM en turnos expandidos |
| **Matrícula en Servicios** | Ver qué vehículo se usó en cada servicio |
| **Filtro Método Pago** | Filtrar por Efectivo/TPV |
| **Exportaciones Mejoradas** | Incluyen todos los nuevos campos |

#### Correcciones

| Corrección | Descripción |
|------------|-------------|
| **Zona Horaria** | Las horas ahora se muestran correctamente (hora de España) |
| **Refresh (F5)** | Los datos ya no desaparecen al refrescar la página |
| **Espaciado Tablas** | Mejor legibilidad en las tablas |

---

## 11. PREGUNTAS FRECUENTES

### ¿Cómo veo los repostajes de un taxista?

En la sección **Turnos**, busque la columna **⛽**. Si tiene valor, haga clic en el turno para ver el detalle completo.

### ¿Qué significa la columna de método de pago?

- **Efectivo:** El cliente pagó en metálico
- **TPV:** El cliente pagó con tarjeta

### ¿Por qué un servicio muestra una matrícula diferente?

El taxista usó un vehículo diferente al que inició el turno. Esto se permite para casos especiales.

### ¿Cómo exporto solo los turnos liquidados?

1. Vaya a Turnos
2. En el filtro de Estado, seleccione **"Liquidados"**
3. Haga clic en Exportar

### ¿Los datos se guardan automáticamente?

Sí. Cada vez que hace clic en "Guardar", los datos se guardan inmediatamente.

### ¿Puedo recuperar un turno eliminado?

No. Las eliminaciones son permanentes.

### ¿El sistema funciona sin internet?

El panel web requiere conexión a internet.

### ¿Las horas son correctas?

Sí. A partir de la v2.0.0, todas las horas se muestran en **hora de España** (Europe/Madrid).

---

## SOPORTE TÉCNICO

**Si tiene problemas:**

Contacte con el soporte técnico de su organización.

---

**Manual de Administración - Panel Web TaxiFast v2.0.0**  
*Actualizado: Diciembre 2025*
