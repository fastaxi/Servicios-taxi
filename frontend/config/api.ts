import Constants from 'expo-constants';

/**
 * Configuración centralizada de la API
 * Usa Constants.expoConfig.extra para builds de producción
 * y process.env para desarrollo local
 */
const getBackendUrl = () => {
  // En builds compilados (APK), la URL viene desde app.json extra
  const extraUrl = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL;
  
  // En desarrollo, viene de process.env
  const envUrl = process.env.EXPO_PUBLIC_BACKEND_URL;
  
  // Fallback a la URL de producción
  const defaultUrl = 'https://taxitineo.preview.emergentagent.com';
  
  return extraUrl || envUrl || defaultUrl;
};

export const API_BASE_URL = getBackendUrl();
export const API_URL = `${API_BASE_URL}/api`;

console.log('[API Config] API_BASE_URL:', API_BASE_URL);
console.log('[API Config] API_URL:', API_URL);
