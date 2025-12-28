// Constantes de la aplicación

// ID de la organización Taxitur para reglas específicas de origen parada/lagos
export const TAXITUR_ORG_ID = "69484bec187c3bc2b0fdb8f4";

// Helper para determinar si el usuario pertenece a Taxitur
export const isTaxiturOrg = (organizationId: string | null | undefined): boolean => {
  return organizationId === TAXITUR_ORG_ID;
};
