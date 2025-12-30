// app.config.js - Configuración dinámica de Expo
// Permite usar variables de entorno en build time

export default ({ config }) => ({
  ...config,
  extra: {
    ...config.extra,
    // TAXITUR_ORG_ID configurable por entorno, con fallback al valor por defecto
    EXPO_PUBLIC_TAXITUR_ORG_ID: process.env.EXPO_PUBLIC_TAXITUR_ORG_ID || "69484bec187c3bc2b0fdb8f4",
    // Backend URL (ya existente en app.json)
    EXPO_PUBLIC_BACKEND_URL: process.env.EXPO_PUBLIC_BACKEND_URL || config.extra?.EXPO_PUBLIC_BACKEND_URL || "https://taxitineo.emergent.host",
  },
});
