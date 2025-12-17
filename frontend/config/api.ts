import Constants from 'expo-constants';

// API configuration
const getApiUrl = () => {
  // In Expo app, try to get from expo config first
  if (typeof window === 'undefined') {
    // Server-side or mobile - use expo config
    const expoUrl = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL;
    if (expoUrl) return expoUrl;
  }
  
  // Client-side - try environment variable
  const envUrl = process.env.EXPO_PUBLIC_BACKEND_URL;
  if (envUrl) return envUrl;
  
  // Development fallback - will be replaced in production
  if (process.env.NODE_ENV === 'development') {
    return 'http://localhost:8001';
  }
  
  // Production should always have EXPO_PUBLIC_BACKEND_URL set
  throw new Error('Backend URL not configured. Set EXPO_PUBLIC_BACKEND_URL environment variable.');
};

export const API_BASE_URL = getBackendUrl();
export const API_URL = `${API_BASE_URL}/api`;

console.log('[API Config] API_BASE_URL:', API_BASE_URL);
console.log('[API Config] API_URL:', API_URL);
