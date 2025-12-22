import Constants from 'expo-constants';

// API configuration - Robusta para móvil, web y desarrollo
const getApiUrl = () => {
  // 1. Primero intentar desde expo config (funciona en móvil y puede funcionar en web)
  const expoUrl = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL;
  if (expoUrl) {
    return expoUrl;
  }
  
  // 2. Fallback a variable de entorno (funciona en web/Vercel)
  const envUrl = process.env.EXPO_PUBLIC_BACKEND_URL;
  if (envUrl) {
    return envUrl;
  }
  
  // 3. En desarrollo, usar localhost
  if (process.env.NODE_ENV === 'development' || __DEV__) {
    console.warn('[API Config] Using development fallback URL');
    return 'http://localhost:8001';
  }
  
  // 4. Fallback final a producción conocida (evita crash)
  console.warn('[API Config] No backend URL configured, using production fallback');
  return 'https://taxitineo.emergent.host';
};

const API_BASE_URL = getApiUrl();
export const API_URL = `${API_BASE_URL}/api`;

console.log('[API Config] API_BASE_URL:', API_BASE_URL);
console.log('[API Config] API_URL:', API_URL);
