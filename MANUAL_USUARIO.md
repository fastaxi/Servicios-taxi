# 📱 MANUAL DE USUARIO - APLICACIÓN TAXI ASTURIAS

## Versión 1.0 - 2025

---

## 📋 ÍNDICE

1. [Introducción](#introducción)
2. [Inicio de Sesión](#inicio-de-sesión)
3. [Módulo Taxista](#módulo-taxista)
   - [Registrar Servicio](#registrar-servicio)
   - [Mis Servicios](#mis-servicios)
   - [Gestión de Turnos](#gestión-de-turnos-taxista)
   - [Historial](#historial)
   - [Perfil](#perfil-taxista)
4. [Módulo Administrador](#módulo-administrador)
   - [Dashboard](#dashboard)
   - [Gestión de Usuarios](#gestión-de-usuarios)
   - [Gestión de Clientes](#gestión-de-clientes)
   - [Gestión de Vehículos](#gestión-de-vehículos)
   - [Gestión de Turnos](#gestión-de-turnos-admin)
   - [Exportaciones](#exportaciones)
   - [Configuración](#configuración)
5. [Preguntas Frecuentes](#preguntas-frecuentes)
6. [Soporte Técnico](#soporte-técnico)

---

## 1. INTRODUCCIÓN

La **Aplicación Taxi Asturias** es una herramienta diseñada para la gestión integral de servicios de taxi en la región de Asturias. Permite a los taxistas registrar sus servicios de manera rápida y eficiente, mientras que los administradores pueden supervisar todas las operaciones, gestionar usuarios, clientes y vehículos, y obtener reportes detallados.

### Características principales:
- ✅ Registro rápido de servicios
- ✅ Gestión de turnos de trabajo
- ✅ Control de kilometraje por turno
- ✅ Diferenciación entre servicios de empresa y particulares
- ✅ Exportación de datos (CSV, Excel, PDF)
- ✅ Gestión completa de clientes y vehículos
- ✅ Informes y estadísticas en tiempo real

---

## 2. INICIO DE SESIÓN

### Acceso a la aplicación

1. Abra la aplicación en su dispositivo móvil
2. Ingrese su **nombre de usuario**
3. Ingrese su **contraseña**
4. Pulse el botón **"Iniciar Sesión"**

### Credenciales por defecto:
- **Administrador:** 
  - Usuario: `admin`
  - Contraseña: `admin123`

- **Taxista:** (creado por el administrador)
  - Usuario: asignado por el administrador
  - Contraseña: asignada por el administrador

> **Nota:** Se recomienda cambiar la contraseña al primer inicio de sesión.

---

## 3. MÓDULO TAXISTA

### 3.1 REGISTRAR SERVICIO

Para registrar un nuevo servicio de taxi:

1. Pulse la pestaña **"Nuevo Servicio"** en la barra inferior
2. Complete los siguientes campos:

   **Información básica:**
   - **Fecha:** Seleccione la fecha del servicio
   - **Hora:** Seleccione la hora del servicio
   - **Origen:** Localidad de origen (ej: tu localidad)
   - **Destino:** Localidad de destino (ej: Oviedo)

   **Detalles económicos:**
   - **Importe (€):** Costo del servicio sin espera
   - **Importe de Espera (€):** Costo adicional por tiempo de espera (opcional)
   - **Kilómetros:** Distancia recorrida

   **Tipo de servicio:**
   - Seleccione **"Empresa"** o **"Particular"**
   - Si es empresa, seleccione el cliente de la lista desplegable

   **Estado de pago y facturación:**
   - ☑️ **Cobrado:** Marque si el servicio ya ha sido cobrado
   - ☑️ **Facturar:** Marque si el servicio debe ser facturado

3. Pulse **"Guardar Servicio"**

> **Importante:** Debe tener un turno activo para registrar servicios. Si no tiene turno abierto, la aplicación le pedirá iniciar uno.

### 3.2 MIS SERVICIOS

Visualice todos los servicios registrados:

**Vista de turno activo:**
- Muestra únicamente los servicios del turno actual
- Resumen en tiempo real: nº de servicios, km totales, importes

**Funciones disponibles:**
- **Ver Historial:** Muestra todos los servicios anteriores agrupados por fecha
- **Editar:** Pulse sobre un servicio para modificarlo
- **Ver detalles:** Visualice origen, destino, importe total, estado de cobro y facturación

**Información mostrada en cada servicio:**
- Fecha y hora
- Origen → Destino
- Importe total (servicio + espera)
- Kilómetros
- Tipo (Empresa/Particular)
- Estado: ✅ Cobrado, 📄 Facturar

### 3.3 GESTIÓN DE TURNOS (TAXISTA)

#### Iniciar Turno

1. Vaya a la pestaña **"Turnos"**
2. Pulse **"Iniciar Turno"**
3. Complete la información:
   - **Vehículo:** Seleccione de la lista asignada
   - **Fecha de Inicio:** Se completa automáticamente (modificable)
   - **Hora de Inicio:** Se completa automáticamente (formato HH:mm)
   - **KM Iniciales:** Kilómetros del odómetro al inicio
4. Pulse **"Iniciar Turno"**

#### Durante el Turno

La pantalla de turnos muestra:
- **Estado:** Turno activo
- **Vehículo:** Matrícula del vehículo asignado
- **Hora de inicio**
- **KM iniciales**
- **Estadísticas en tiempo real:**
  - Nº de servicios realizados
  - Total de kilómetros del turno
  - Total cobrado a clientes (empresas)
  - Total cobrado a particulares
  - **Total general**

#### Finalizar Turno

1. Pulse **"Finalizar Turno"**
2. Complete:
   - **Fecha de Fin:** Modificable si es necesario
   - **Hora de Fin:** Formato HH:mm (ej: 14:30)
   - **KM Finales:** Kilómetros del odómetro al finalizar
3. Pulse **"Finalizar Turno"**
4. El sistema calcula automáticamente:
   - Total de kilómetros del turno
   - Totales económicos
   - Cantidad de servicios

#### Ver Historial de Turnos

- Lista de turnos ordenados del más reciente al más antiguo
- Pulse sobre un turno para **expandir** y ver servicios individuales
- Información de cada turno:
  - Fecha y horario
  - Vehículo utilizado
  - Kilómetros totales
  - Servicios realizados
  - Importes totales
  - Estado: Cerrado/Liquidado

### 3.4 PERFIL (TAXISTA)

En la sección de perfil puede:
- Ver sus datos personales
- Ver licencia de taxi asignada
- Ver vehículo(s) asignado(s)
- **Cerrar sesión**

---

## 4. MÓDULO ADMINISTRADOR

### 4.1 DASHBOARD

El dashboard principal muestra:

**Estadísticas generales:**
- Total de servicios registrados
- Total de taxistas activos
- Total de clientes
- Ingresos totales

**Lista de servicios:**
- Vista completa de todos los servicios registrados
- Información mostrada:
  - Taxista que realizó el servicio
  - Fecha y hora
  - Origen → Destino
  - Importe total
  - Tipo (Empresa/Particular)
  - Cliente (si aplica)

**Filtros disponibles:**
- **Por tipo:** Todos / Empresa / Particular
- **Por empresa:** Seleccione un cliente específico
- **Por taxista:** Seleccione un taxista específico
- **Por fechas:** Rango de fechas (Desde - Hasta)

**Acciones:**
- **Exportar:** Botón para exportar datos filtrados
- **Editar servicio:** Pulse sobre cualquier servicio

### 4.2 GESTIÓN DE USUARIOS

Administre los taxistas de la empresa:

#### Ver Usuarios
- Lista completa de taxistas
- Información mostrada:
  - Nombre
  - Usuario (login)
  - Licencia de taxi
  - Vehículo asignado
  - Estado: Activo/Inactivo

#### Crear Nuevo Taxista

1. Pulse el botón **"+"** (Agregar)
2. Complete el formulario:
   - **Nombre completo**
   - **Nombre de usuario** (para login)
   - **Contraseña**
   - **Licencia de taxi**
   - **Vehículo asignado** (seleccione de la lista)
3. Pulse **"Guardar"**

#### Editar Taxista

1. Pulse sobre un taxista de la lista
2. Modifique los campos necesarios
3. Pulse **"Guardar"**

#### Eliminar Taxista

1. Pulse sobre un taxista
2. Pulse **"Eliminar"**
3. Confirme la acción

> **Nota:** No se puede eliminar un taxista con servicios registrados.

### 4.3 GESTIÓN DE CLIENTES

Administre las empresas y clientes corporativos:

#### Ver Clientes
- Lista completa de empresas
- Información mostrada:
  - Número de cliente
  - Nombre
  - CIF/DNI
  - Localidad
  - Teléfono

#### Crear Nuevo Cliente

1. Pulse el botón **"+"** (Agregar)
2. Complete el formulario (campos en orden):
   - **Número de Cliente:** Identificador único
   - **Fecha de Alta:** Fecha de registro
   - **Nombre:** Razón social o nombre completo
   - **CIF/DNI:** Documento de identificación
   - **Dirección:** Dirección completa
   - **Código Postal**
   - **Localidad**
   - **Provincia**
   - **Teléfono**
   - **Email**
   - **Notas:** Información adicional (opcional)
3. Pulse **"Guardar"**

> **Importante:** El Número de Cliente debe ser único. El sistema validará que no exista duplicado.

#### Ver Detalle de Cliente

1. Pulse sobre el **nombre** de un cliente
2. Se abrirá un modal con toda la información en modo lectura
3. Pulse **"Cerrar"** para volver

#### Editar Cliente

1. Pulse sobre el icono de **lápiz** junto al cliente
2. Modifique los campos necesarios
3. Pulse **"Guardar"**

#### Eliminar Cliente

1. Pulse sobre el icono de **papelera** junto al cliente
2. Confirme la acción

> **Nota:** No se puede eliminar un cliente con servicios asociados.

### 4.4 GESTIÓN DE VEHÍCULOS

Administre la flota de vehículos:

#### Ver Vehículos
- Lista completa de vehículos
- Información mostrada:
  - Matrícula
  - Marca y modelo
  - Plazas
  - KM iniciales
  - Fecha de compra
  - Taxista asignado

#### Registrar Nuevo Vehículo

1. Pulse el botón **"+"** (Agregar)
2. Complete el formulario:
   - **Matrícula:** Formato español (ej: 1234ABC)
   - **Marca:** Mercedes, Toyota, etc.
   - **Modelo:** E-Class, Prius, etc.
   - **Plazas:** Número de asientos (ej: 5)
   - **KM Iniciales:** Kilometraje al incorporar el vehículo
   - **Fecha de Compra**
3. Pulse **"Guardar"**

> **Importante:** La matrícula debe ser única.

#### Editar Vehículo

1. Pulse sobre un vehículo de la lista
2. Modifique los campos necesarios
3. Pulse **"Guardar"**

#### Eliminar Vehículo

1. Pulse sobre un vehículo
2. Pulse **"Eliminar"**
3. Confirme la acción

### 4.5 GESTIÓN DE TURNOS (ADMIN)

Control completo sobre todos los turnos de trabajo:

#### Vistas Disponibles

**1. Vista Lista:**
- Cards expandibles por turno
- Pulse para ver servicios individuales del turno

**2. Vista Tabla:**
- Tabla comparativa con todas las columnas:
  - Taxista
  - Vehículo
  - Fecha
  - KM (kilómetros del turno)
  - Servs. (cantidad de servicios)
  - Total € (importe total)
  - Estado (Activo/Cerrado/Liquidado)

**3. Vista Estadísticas:**
- Totales generales:
  - Total de turnos
  - Promedio de servicios por turno
  - Promedio de kilómetros por turno
  - Promedio de ingresos por turno
  - Turnos pendientes de liquidación

#### Filtros

- **Por taxista:** Seleccione un taxista específico
- **Por estado:**
  - **Todos:** Muestra todos los turnos
  - **Activos:** Solo turnos en curso
  - **Cerrados:** Turnos finalizados pero no liquidados
  - **Liquidados:** Turnos cerrados y marcados como liquidados

#### Acciones Administrativas

**Editar Turno:**
1. Pulse sobre el nombre del taxista (vista tabla) o el card (vista lista)
2. Puede modificar:
   - Fecha y hora de inicio
   - Fecha y hora de fin
   - KM iniciales y finales
   - Estado: liquidado/no liquidado
3. Pulse **"Guardar"**

**Cerrar Turno:**
- Si un taxista olvida cerrar su turno, el admin puede hacerlo
- Complete fecha fin, hora fin y km finales

**Marcar como Liquidado:**
- Active el switch "Liquidado" en la edición del turno
- Útil para control de pagos y liquidaciones con taxistas

**Exportar Turnos:**
1. Pulse el botón **"Exportar"**
2. Seleccione formato: CSV, Excel o PDF
3. Los filtros activos se aplican a la exportación

### 4.6 EXPORTACIONES

El sistema permite exportar datos en tres formatos:

#### Formatos Disponibles

**CSV (valores separados por comas):**
- Compatible con Excel, Google Sheets
- Ideal para análisis de datos
- Tamaño de archivo pequeño

**Excel (.xlsx):**
- Formato Microsoft Excel nativo
- Incluye formato visual (colores, encabezados)
- Columnas con ancho ajustado

**PDF:**
- Formato de documento portable
- Listo para imprimir
- Ideal para reportes oficiales

#### Exportación de Servicios (Dashboard)

**Datos incluidos:**
- Fecha y hora
- Taxista
- Origen y destino
- Importe e importe de espera
- Kilómetros
- Tipo (empresa/particular)
- Empresa (si aplica)

**Cómo exportar:**
1. En el Dashboard, aplique los filtros deseados
2. Pulse el botón **"Exportar"**
3. Seleccione el formato
4. El archivo se descargará automáticamente

#### Exportación de Turnos

**Datos incluidos:**
- Taxista y vehículo
- Fecha y hora de inicio/fin
- KM iniciales y finales
- Total de kilómetros
- Cantidad de servicios
- Importes (clientes, particulares, total)
- Estado (cerrado/liquidado)

**Cómo exportar:**
1. En Turnos (admin), aplique los filtros deseados
2. Pulse el botón **"Exportar"**
3. Seleccione el formato
4. El archivo se descargará automáticamente

### 4.7 CONFIGURACIÓN

Personalice la aplicación:

**Información de la Empresa:**
- Nombre de la empresa
- Logo corporativo
- Teléfono de contacto
- Email de contacto
- Dirección

**Cómo modificar:**
1. Vaya a la pestaña **"Config"**
2. Complete los campos deseados
3. Para cambiar el logo:
   - Pulse **"Seleccionar Imagen"**
   - Elija una imagen de su galería
4. Pulse **"Guardar Configuración"**

---

## 5. PREGUNTAS FRECUENTES

**P: ¿Qué hago si olvido cerrar mi turno?**
R: Contacte al administrador. Él puede cerrar el turno manualmente desde el panel de administración.

**P: ¿Puedo editar un servicio después de crearlo?**
R: Sí, tanto taxistas como administradores pueden editar servicios. El taxista solo puede editar sus propios servicios.

**P: ¿Qué significa "cobrado" y "facturar"?**
R: 
- **Cobrado:** Indica que el importe ya fue cobrado al cliente
- **Facturar:** Indica que el servicio debe incluirse en la próxima factura

**P: ¿Cómo sé cuántos kilómetros llevo en el turno?**
R: En la pantalla de "Turnos" se muestra un resumen en tiempo real con todos los totales, incluyendo kilómetros.

**P: ¿Puedo trabajar con varios vehículos?**
R: Sí, el administrador puede asignarle varios vehículos. Al iniciar cada turno, seleccione el vehículo que va a utilizar.

**P: ¿Por qué no puedo crear un servicio?**
R: Debe tener un turno activo. Si no tiene uno, pulse en la pestaña "Turnos" e inicie un nuevo turno.

**P: ¿Los datos se guardan si pierdo conexión?**
R: La aplicación tiene funcionalidad offline. Los datos se guardarán localmente y se sincronizarán cuando recupere la conexión.

**P: ¿Cómo cambio mi contraseña?**
R: Contacte al administrador para que restablezca su contraseña.

**P: ¿Qué formato debe tener la matrícula?**
R: Formato español estándar: 1234ABC (4 números + 3 letras).

**P: ¿Puedo eliminar un servicio?**
R: Solo el administrador puede eliminar servicios.

---

## 6. SOPORTE TÉCNICO

Para asistencia técnica o consultas:

**Contacto:**
- Consulte la información de contacto en la sección "Config" de la aplicación
- Los administradores tienen acceso completo a todas las funcionalidades

**Problemas comunes:**

| Problema | Solución |
|----------|----------|
| No puedo iniciar sesión | Verifique usuario y contraseña. Contacte al administrador. |
| La app no responde | Cierre y vuelva a abrir la aplicación |
| No veo mis servicios | Verifique que tiene un turno activo |
| Error al exportar | Verifique conexión a internet |
| No aparece un cliente | Verifique que el cliente fue creado por el admin |

---

**Manual de Usuario - Aplicación Taxi Asturias v1.0**
*Actualizado: 2025*
