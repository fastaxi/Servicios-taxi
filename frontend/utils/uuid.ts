/**
 * UUID Generator for idempotent service creation
 * Uses expo-crypto for secure random UUID generation
 */
import * as Crypto from 'expo-crypto';

/**
 * Generates a new UUID v4 for client-side idempotency
 * This UUID should be persisted with the service data to ensure
 * that retries don't create duplicate services
 */
export const newClientUUID = (): string => {
  return Crypto.randomUUID();
};

/**
 * Validates a client_uuid format
 * Must be 8-64 characters
 */
export const isValidClientUUID = (uuid: string | null | undefined): boolean => {
  if (!uuid) return false;
  return uuid.length >= 8 && uuid.length <= 64;
};
