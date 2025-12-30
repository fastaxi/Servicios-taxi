// Constantes de la aplicación
import Constants from 'expo-constants';

// ID de la organización Taxitur para reglas específicas de origen parada/lagos
// Configurable via EXPO_PUBLIC_TAXITUR_ORG_ID en Vercel/Expo, con fallback al valor por defecto
export const TAXITUR_ORG_ID = 
  Constants.expoConfig?.extra?.EXPO_PUBLIC_TAXITUR_ORG_ID || 
  process.env.EXPO_PUBLIC_TAXITUR_ORG_ID || 
  "69484bec187c3bc2b0fdb8f4";

// Helper para determinar si el usuario pertenece a Taxitur
export const isTaxiturOrg = (organizationId: string | null | undefined): boolean => {
  return organizationId === TAXITUR_ORG_ID;
};
