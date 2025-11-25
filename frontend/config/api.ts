/**
 * Configuración centralizada de la API
 * Si EXPO_PUBLIC_BACKEND_URL no está definida, usa la URL de producción por defecto
 */
export const API_BASE_URL = process.env.EXPO_PUBLIC_BACKEND_URL || 'https://taxitineo.preview.emergentagent.com';
export const API_URL = `${API_BASE_URL}/api`;

console.log('[API Config] API_BASE_URL:', API_BASE_URL);
console.log('[API Config] API_URL:', API_URL);
