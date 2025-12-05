# MANUAL DE USUARIO - PANEL DE ADMINISTRACIÓN
## Taxi Tineo Sociedad Cooperativa

---

### INFORMACIÓN DEL SISTEMA

**Nombre:** Panel de Administración - Taxi Tineo  
**Versión:** 1.2.0  
**URL de Acceso:** https://servicios-taxi.vercel.app  
**Teléfono:** 985 801 515  
**Web:** https://www.taxitineo.com  
**Email:** info@taxitineo.com

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
10. [Preguntas Frecuentes](#10-preguntas-frecuentes)

---

## 1. INICIO DE SESIÓN

### Paso 1: Acceder al Panel Web

1. Abra su navegador web (Google Chrome, Firefox, Safari o Edge)
2. Escriba en la barra de direcciones: **https://servicios-taxi.vercel.app**
3. Presione Enter

### Paso 2: Ingresar Credenciales

Verá la pantalla de inicio de sesión con el logo de Taxi Tineo.

**Campos a completar:**
- **Usuario:** Ingrese su nombre de usuario de administrador
- **Contraseña:** Ingrese su contraseña

**Credencial por defecto del administrador:**
- Usuario: `admin`
- Contraseña: `admin123`

[!] **IMPORTANTE:** Se recomienda cambiar la contraseña por defecto la primera vez que ingrese al sistema.

### Paso 3: Iniciar Sesión

1. Haga clic en el botón azul **"Iniciar Sesión"**
2. El sistema validará sus credenciales
3. Si son correctas, será redirigido al Dashboard

[X] **Si aparece un error:**
- Verifique que el usuario y contraseña sean correctos
- Asegúrese de que no hay espacios al inicio o final
- Contacte al administrador del sistema si persiste el problema

---

## 2. DASHBOARD PRINCIPAL

Una vez iniciada la sesión, verá el **Panel Principal** con la siguiente información:

### Elementos del Dashboard

**A. Barra Lateral Izquierda (Menú de Navegación):**
- [Auto] Dashboard
- [Taxi] Servicios
- [Empresa] Empresas
- [Usuarios] Taxistas
- [Vehiculo] Vehículos
- [Turno] Turnos
- [Config] Configuración
- [Salir] Cerrar Sesión

**B. Panel Superior:**
- Nombre del usuario (Administrador)
- Rol del usuario

**C. Área Principal:**
- Tarjetas con estadísticas:
  - **Servicios:** Número total de servicios registrados
  - **Total Importe:** Suma total de ingresos
  - **Total KM:** Kilómetros totales recorridos

**D. Sección de Filtros:**
Permite filtrar los servicios por:
- Tipo (Todos, Cliente, Particular)
- Taxista (seleccionar un taxista específico o todos)
- Rango de fechas (Fecha Inicio - Fecha Fin)

**E. Tabla de Servicios:**
Muestra todos los servicios registrados con las columnas:
- Fecha
- Hora
- Taxista
- Origen
- Destino
- KM
- Importe
- Espera
- Total/Tipo
- Acciones (Editar/Eliminar)

---

## 3. GESTIÓN DE EMPRESAS/CLIENTES

Las empresas son los clientes corporativos que contratan servicios de taxi.

### Ver Lista de Empresas

1. Haga clic en **"Empresas"** en el menú lateral
2. Verá una tabla con todas las empresas registradas

**Columnas de la tabla:**
- Nombre
- CIF/NIF
- N° Cliente
- Contacto
- Teléfono
- Email
- Acciones (Editar/Eliminar)

### Agregar Nueva Empresa

1. En la pantalla de Empresas, busque el botón **"+"** (azul, esquina inferior derecha)
2. Haga clic en el botón
3. Aparecerá un formulario con los siguientes campos:

**Campos obligatorios:**
- **Nombre:** Nombre completo de la empresa
- **CIF/NIF:** Número de identificación fiscal
- **Número de Cliente:** Código único para la empresa

**Campos opcionales:**
- Contacto: Nombre de la persona de contacto
- Teléfono: Número de teléfono
- Email: Correo electrónico
- Dirección: Dirección física de la empresa

4. Complete todos los campos requeridos
5. Haga clic en **"Guardar"**
6. El sistema confirmará que la empresa fue creada

[OK] **Consejo:** El número de cliente debe ser único. No puede repetirse.

### Editar una Empresa

1. En la tabla de empresas, localice la empresa que desea editar
2. Haga clic en el ícono de lápiz () en la columna "Acciones"
3. Modifique los campos que desee cambiar
4. Haga clic en **"Guardar"**
5. Los cambios se aplicarán inmediatamente

### Eliminar una Empresa

1. Localice la empresa que desea eliminar
2. Haga clic en el ícono de papelera () en la columna "Acciones"
3. Aparecerá un mensaje de confirmación
4. Haga clic en **"Aceptar"** para confirmar la eliminación
5. La empresa será eliminada de forma permanente

[!] **ADVERTENCIA:** Esta acción no se puede deshacer. Asegúrese antes de eliminar.

---

## 4. GESTIÓN DE TAXISTAS

Los taxistas son los conductores que prestan el servicio de taxi.

### Ver Lista de Taxistas

1. Haga clic en **"Taxistas"** en el menú lateral
2. Verá una lista de todos los taxistas registrados

**Información mostrada:**
- Nombre del taxista
- Usuario de acceso
- Número de licencia
- Vehículo asignado
- Estado (Activo/Inactivo)
- Acciones (Editar/Eliminar)

### Agregar Nuevo Taxista

1. En la pantalla de Taxistas, haga clic en el botón **"+"** (azul)
2. Complete el formulario:

**Campos obligatorios:**
- **Nombre Completo:** Nombre y apellidos del taxista
- **Usuario:** Nombre de usuario para iniciar sesión en la app móvil
- **Contraseña:** Contraseña para acceder a la app
- **Número de Licencia:** Número de licencia de taxi

**Campos opcionales:**
- Teléfono
- Email
- Dirección

3. Haga clic en **"Guardar"**
4. El taxista podrá acceder a la app móvil con sus credenciales

[OK] **Importante:** El usuario debe ser único. Anote las credenciales para entregar al taxista.

### Editar un Taxista

1. Localice el taxista en la lista
2. Haga clic en el ícono de lápiz ()
3. Modifique los campos necesarios
4. Haga clic en **"Guardar"**

[Consejo] **Consejo:** Puede cambiar la contraseña de un taxista desde esta pantalla.

### Eliminar un Taxista

1. Localice el taxista que desea eliminar
2. Haga clic en el ícono de papelera ()
3. Confirme la eliminación

[!] **NOTA:** Al eliminar un taxista, sus servicios y turnos históricos se mantendrán en el sistema.

---

## 5. GESTIÓN DE VEHÍCULOS

Administre la flota de vehículos de la cooperativa.

### Ver Lista de Vehículos

1. Haga clic en **"Vehículos"** en el menú lateral
2. Verá una tabla con todos los vehículos

**Columnas:**
- Matrícula
- Marca
- Modelo
- Plazas
- KM Iniciales
- Fecha de Compra
- Estado (Activo/Inactivo)
- Acciones

### Agregar Nuevo Vehículo

1. Haga clic en el botón **"+"**
2. Complete el formulario:

**Campos obligatorios:**
- **Matrícula:** Matrícula del vehículo (ej: 1234ABC)
- **Marca:** Fabricante del vehículo (ej: Toyota)
- **Modelo:** Modelo del vehículo (ej: Corolla)
- **Plazas:** Número de asientos (incluyendo conductor)
- **KM Iniciales:** Kilometraje al registrar el vehículo

**Campos opcionales:**
- Fecha de Compra
- Notas adicionales

3. Haga clic en **"Guardar"**

[OK] **Nota:** La matrícula debe ser única en el sistema.

### Editar un Vehículo

1. Localice el vehículo en la tabla
2. Haga clic en el ícono de lápiz ()
3. Modifique los datos necesarios
4. Guarde los cambios

### Eliminar un Vehículo

1. Localice el vehículo
2. Haga clic en el ícono de papelera ()
3. Confirme la eliminación
4. Aparecerá un cuadro de diálogo de confirmación
5. Haga clic en **"Aceptar"**

---

## 6. GESTIÓN DE TURNOS

Los turnos son los períodos de trabajo de cada taxista.

### Ver Lista de Turnos

1. Haga clic en **"Turnos"** en el menú lateral
2. Verá una lista de todos los turnos registrados

**Información de cada turno:**
- Taxista
- Vehículo (matrícula)
- Fecha y hora de inicio
- Fecha y hora de fin
- KM inicio / KM fin / Total KM
- Número de servicios realizados
- Total en servicios a clientes (€)
- Total en servicios particulares (€)
- Total general (€)
- Estado: Activo, Cerrado, Liquidado
- Acciones (Ver servicios, Editar, Desliquidar, Cerrar)

### Filtros Disponibles

- **Todos / Activos / Cerrados / Liquidados**
- **Taxista:** Seleccionar un taxista específico
- **Aplicar / Limpiar:** Botones para aplicar o limpiar filtros

### Ver Servicios de un Turno

1. Localice el turno que desea consultar
2. Haga clic en **"Ver servicios"** (icono  o texto)
3. Se desplegará una lista con todos los servicios realizados en ese turno

**Información de cada servicio:**
- Fecha y hora
- Origen y destino
- Tipo (Empresa/Particular)
- Empresa (si aplica)
- Importe, importe de espera, total
- Kilómetros

### Editar un Turno (Solo Administrador)

1. Localice el turno
2. Haga clic en el ícono de lápiz ()
3. Puede modificar:
   - Fecha y hora de fin
   - KM de fin
   - Marcar como liquidado

4. Guarde los cambios

### Cerrar un Turno

Los turnos activos pueden ser cerrados manualmente:

1. Localice el turno activo
2. Haga clic en **"Cerrar"** o en el botón de cerrar
3. El sistema calculará automáticamente:
   - Total de servicios
   - Total de ingresos por clientes
   - Total de ingresos particulares
   - Kilómetros totales

### Marcar Turno como Liquidado

Una vez liquidado el turno con el taxista:

1. Edite el turno
2. Marque la casilla **"Liquidado"**
3. Guarde

[OK] El estado cambiará a "Liquidado" y aparecerá con un indicador visual (verde o badge).

### Eliminar un Turno

[!] **ATENCIÓN:** Al eliminar un turno, se eliminarán también TODOS los servicios asociados a ese turno.

1. Localice el turno
2. Haga clic en el ícono de papelera ()
3. Confirme la acción
4. El turno y sus servicios serán eliminados permanentemente

---

## 7. CONSULTA DE SERVICIOS

### Acceder a Servicios

1. Haga clic en **"Servicios"** en el menú lateral (o desde Dashboard)
2. Verá la tabla con todos los servicios registrados

### Filtros de Búsqueda

**Filtro por Tipo:**
- Todos
- Cliente (servicios a empresas)
- Particular (servicios a particulares)

**Filtro por Taxista:**
- Seleccione un taxista específico del dropdown
- O deje "Todos los taxistas" para ver todos

**Filtro por Fecha:**
- **Fecha Inicio:** Fecha desde la cual buscar
- **Fecha Fin:** Fecha hasta la cual buscar

**Aplicar Filtros:**
1. Configure los filtros deseados
2. Haga clic en el botón **"Limpiar"** para limpiar filtros
3. Haga clic en **"Exportar"** para descargar los datos filtrados

### Ver Detalles de un Servicio

En la tabla de servicios podrá ver:
- Fecha y hora del servicio
- Taxista que realizó el servicio
- Origen y destino
- Kilómetros recorridos
- Importe del servicio
- Importe de espera (si aplica)
- Total
- Tipo de servicio (Cliente/Particular)

---

## 8. EXPORTACIÓN DE DATOS

### Exportar Servicios

1. Vaya a la sección **"Servicios"**
2. Configure los filtros que desee aplicar (opcional)
3. Haga clic en el botón **"Exportar"** (esquina superior derecha)
4. Seleccione el formato:
   - **CSV:** Para abrir en Excel/Hojas de cálculo
   - **Excel:** Archivo .xlsx con formato
   - **PDF:** Documento imprimible

5. El archivo se descargará automáticamente

### Exportar Turnos

1. Vaya a la sección **"Turnos"**
2. Configure los filtros (estado, taxista)
3. Haga clic en **"Exportar"**
4. Seleccione el formato deseado

**Contenido de la exportación de turnos:**
- Información completa del turno (fechas, km, totales)
- **NOVEDAD:** Incluye el listado detallado de TODOS los servicios realizados en cada turno

[OK] **Esto es perfecto para:**
- Liquidación de turnos
- Auditorías
- Reportes detallados
- Contabilidad

### Formatos de Exportación

**CSV (Valores Separados por Comas):**
- Compatible con Excel, Google Sheets
- Fácil de importar a otros sistemas
- Ligero y rápido

**Excel (.xlsx):**
- Formato con colores y estilos
- Filas de turnos con fondo amarillo
- Filas de servicios con fondo gris
- Fácil de leer

**PDF:**
- Documento imprimible
- Formato profesional
- Ideal para entregar a taxistas o contabilidad

---

## 9. CONFIGURACIÓN DEL SISTEMA

### Acceder a Configuración

1. Haga clic en **"Configuración"** en el menú lateral
2. Verá el formulario de configuración general

### Campos Configurables

**Logo:**
- Haga clic en "Toca para seleccionar logo"
- Seleccione una imagen (formato cuadrado o rectangular recomendado)
- El logo aparecerá en la pantalla de login

**Información General:**
- **Nombre del Radio Taxi:** Taxi Tineo Sociedad Cooperativa
- **Teléfono:** 985801515
- **Página Web:** https://www.taxitineo.com
- **Email:** info@taxitineo.com
- **Dirección:** Tineo

### Guardar Configuración

1. Modifique los campos que desee cambiar
2. Haga clic en el botón azul **"Guardar Configuración"**
3. Los cambios se aplicarán inmediatamente
4. El logo y la información actualizada aparecerán en la app móvil

---

## 10. PREGUNTAS FRECUENTES

### ¿Cómo cambio mi contraseña de administrador?

Actualmente no hay una opción en la interfaz para cambiar contraseña. Contacte al soporte técnico para cambiarla.

### ¿Puedo recuperar un turno o servicio eliminado?

No. Las eliminaciones son permanentes. Se recomienda tener precaución al eliminar datos.

### ¿Los taxistas pueden ver todos los servicios?

No. Cada taxista solo puede ver sus propios servicios y turnos. El administrador ve todo.

### ¿Qué pasa si cierro sesión accidentalmente?

Simplemente vuelva a iniciar sesión con sus credenciales. Los datos no se pierden.

### ¿Puedo acceder desde mi teléfono móvil?

Sí. El panel web es responsive y funciona en navegadores móviles. Sin embargo, para taxistas se recomienda usar la app móvil.

### ¿Cómo exporto los datos de un mes específico?

1. Vaya a Servicios o Turnos
2. Use los filtros de fecha (Fecha Inicio y Fecha Fin)
3. Seleccione el rango del mes deseado
4. Haga clic en Exportar

### ¿El sistema guarda automáticamente?

Sí. Cada vez que hace clic en "Guardar" en cualquier formulario, los datos se guardan en la base de datos inmediatamente.

### ¿Necesito internet para usar el panel?

Sí. El panel de administración web requiere conexión a internet en todo momento.

### ¿Los datos están seguros?

Sí. El sistema usa:
- Conexión HTTPS cifrada
- Autenticación por usuario y contraseña
- Base de datos en la nube con respaldos automáticos

---

## SOPORTE TÉCNICO

**Si tiene problemas técnicos o preguntas:**

 **Teléfono:** 985 801 515  
 **Web:** https://www.taxitineo.com  
 **Email:** info@taxitineo.com

**Horario de atención:** Lunes a Viernes, 9:00 - 18:00

---

## INFORMACIÓN DE LA VERSIÓN

**Manual:** v1.0  
**Fecha:** Diciembre 2025  
**Sistema:** Taxi Tineo - Panel de Administración v1.2.0  
**URL:** https://servicios-taxi.vercel.app

---

**Taxi Tineo Sociedad Cooperativa**  
*Gestión profesional de servicios de taxi en Asturias*
