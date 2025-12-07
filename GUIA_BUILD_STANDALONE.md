# 📱 Guía Completa: Crear Build Standalone de Taxi Tineo

## ✅ Configuración Completada

He configurado tu proyecto para crear builds standalone:

### Archivos Actualizados:
- ✅ `app.json` - Configurado con nombre "Taxi Tineo", colores Asturias, y permisos
- ✅ `eas.json` - Configuración de builds (development, preview, production)
- ✅ **Iconos personalizados instalados** - Tu imagen de taxi ahora es el icono oficial de la app:
  - `icon.png` (1024x1024) - Icono principal de la app
  - `adaptive-icon.png` (1024x1024) - Icono adaptativo para Android
  - `splash-icon.png` (200x200) - Icono para pantalla de carga
  - `splash.png` (1242x2688) - Pantalla de carga completa con fondo azul Asturias
  - `favicon.png` (48x48) - Icono para versión web

---

## 🚀 Pasos para Crear el Build

### **Paso 1: Crear Cuenta en Expo (si no tienes)**

Visita: https://expo.dev/signup

O usa tu cuenta de GitHub/Google para registrarte.

---

### **Paso 2: Login en EAS desde tu Terminal**

```bash
cd /app/frontend
eas login
```

Te pedirá tu email/usuario y contraseña de Expo.

---

### **Paso 3: Configurar el Proyecto en Expo**

```bash
eas build:configure
```

Esto enlazará tu proyecto con tu cuenta de Expo.

---

### **Paso 4: Crear el Build para Android (APK)**

#### **Opción A: Build Preview (Recomendado para empezar)**
```bash
eas build --platform android --profile preview
```

Este comando:
- Crea un APK que puedes instalar directamente
- No requiere publicar en Google Play Store
- Ideal para distribución interna (taxistas)
- Tarda aproximadamente 10-15 minutos

#### **Opción B: Build de Producción**
```bash
eas build --platform android --profile production
```

Este comando crea un APK optimizado para producción.

---

### **Paso 5: Descargar el APK**

Una vez completado el build:

1. EAS te dará un enlace para descargar el APK
2. También puedes verlo en: https://expo.dev/accounts/[tu-usuario]/projects/taxi-tineo-asturias/builds
3. Descarga el APK y compártelo con los taxistas

---

## 📲 Instalar la App en los Teléfonos de los Taxistas

### **En Android:**

1. **Descarga el APK** al teléfono (por WhatsApp, email, o USB)

2. **Habilita "Instalar desde fuentes desconocidas":**
   - Ve a Ajustes → Seguridad
   - Activa "Fuentes desconocidas" o "Instalar apps desconocidas"

3. **Instala el APK:**
   - Abre el archivo APK descargado
   - Toca "Instalar"
   - Espera a que termine la instalación
   - Toca "Abrir"

4. ✅ ¡La app está instalada y lista para usar!

---

## 🔄 Actualizar la App en el Futuro

Cuando hagas cambios:

1. Actualiza el número de versión en `app.json`:
   ```json
   "version": "1.1.0",
   "android": {
     "versionCode": 2
   }
   ```

2. Crea un nuevo build:
   ```bash
   eas build --platform android --profile preview
   ```

3. Distribuye el nuevo APK a los taxistas

---

## 💡 Notas Importantes

### **Backend URL:**
- La app usa: `https://taxi-manager-12.preview.emergentagent.com`
- Asegúrate de que el backend esté siempre desplegado y funcionando

### **Conexión a Internet:**
- Los taxistas necesitan conexión a internet para:
  - Login inicial
  - Sincronizar servicios
  - Crear/editar servicios

### **Funcionalidad Offline:**
- La app guarda servicios localmente si no hay internet
- Se sincronizan automáticamente cuando vuelve la conexión

---

## 🆘 Solución de Problemas

### **Error: "No se puede instalar la app"**
- Verifica que "Fuentes desconocidas" esté habilitado
- Intenta reiniciar el teléfono

### **Error al crear el build: "No project found"**
- Ejecuta: `eas build:configure` primero
- Verifica que estás logueado: `eas whoami`

### **Build falla en EAS:**
- Revisa los logs que EAS muestra
- Verifica que no haya errores de sintaxis en el código

---

## 📞 Contacto y Soporte

Si necesitas ayuda adicional:
- Revisa la documentación de EAS: https://docs.expo.dev/build/setup/
- Contacta con el desarrollador de la app

---

## ✨ Resumen Rápido

```bash
# 1. Login
cd /app/frontend
eas login

# 2. Crear build
eas build --platform android --profile preview

# 3. Esperar 10-15 minutos

# 4. Descargar APK del link que te da EAS

# 5. Distribuir APK a los taxistas
```

¡Listo! 🎉
