/**
 * UUID Generator for idempotent service creation (Paso 5B)
 * Works on mobile (expo-crypto) and web (crypto.randomUUID)
 */
import { Platform } from 'react-native';

/**
 * Generates a new UUID v4 for client-side idempotency.
 * This UUID must be persisted with the service data to ensure
 * that retries don't create duplicate services.
 */
export const generateClientUUID = (): string => {
  // Web: use native crypto API
  if (Platform.OS === 'web' && typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  // Mobile: use expo-crypto (imported dynamically to avoid web issues)
  try {
    const ExpoCrypto = require('expo-crypto');
    return ExpoCrypto.randomUUID();
  } catch {
    // Ultimate fallback: manual UUID v4
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0;
      const v = c === 'x' ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }
};

// Backward-compatible aliases
export const newClientUUID = generateClientUUID;

/**
 * Validates a client_uuid format (8-64 chars)
 */
export const isValidClientUUID = (uuid: string | null | undefined): boolean => {
  if (!uuid) return false;
  return uuid.length >= 8 && uuid.length <= 64;
};
