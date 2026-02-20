import React, { createContext, useState, useContext, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';
import axios from 'axios';
import { useAuth } from './AuthContext';
import { newClientUUID, isValidClientUUID } from '../utils/uuid';

import { API_URL } from '../config/api';

interface PendingService {
  client_uuid: string;
  fecha: string;
  hora: string;
  origen: string;
  destino: string;
  importe: number;
  importe_espera?: number;
  tipo: string;
  [key: string]: any;
}

interface SyncResult {
  client_uuid: string | null;
  server_id: string;
  status: 'created' | 'existing' | 'failed' | 'created_no_uuid';
  error?: string;
}

interface SyncContextType {
  pendingServices: number;
  syncStatus: 'idle' | 'syncing' | 'success' | 'error';
  syncServices: () => Promise<void>;
  addPendingService: (service: any) => Promise<void>;
}

const SyncContext = createContext<SyncContextType | undefined>(undefined);

const PENDING_SERVICES_KEY = 'pendingServices';

export function SyncProvider({ children }: { children: React.ReactNode }) {
  const [pendingServices, setPendingServices] = useState(0);
  const [syncStatus, setSyncStatus] = useState<'idle' | 'syncing' | 'success' | 'error'>('idle');
  const { token } = useAuth();

  useEffect(() => {
    loadAndMigratePendingServices();
    
    // Listen for network changes
    const unsubscribe = NetInfo.addEventListener(state => {
      if (state.isConnected && pendingServices > 0) {
        syncServices();
      }
    });

    return () => unsubscribe();
  }, [pendingServices, token]);

  /**
   * Load pending services and migrate any that don't have client_uuid
   */
  const loadAndMigratePendingServices = async () => {
    try {
      const pending = await AsyncStorage.getItem(PENDING_SERVICES_KEY);
      if (pending) {
        const services: PendingService[] = JSON.parse(pending);
        let needsUpdate = false;
        
        // Migrate services that don't have client_uuid
        const migratedServices = services.map(service => {
          if (!isValidClientUUID(service.client_uuid)) {
            needsUpdate = true;
            return {
              ...service,
              client_uuid: newClientUUID()
            };
          }
          return service;
        });
        
        // Persist migrated services if needed
        if (needsUpdate) {
          await AsyncStorage.setItem(PENDING_SERVICES_KEY, JSON.stringify(migratedServices));
          console.log('[SyncContext] Migrated pending services with client_uuid');
        }
        
        setPendingServices(migratedServices.length);
      }
    } catch (error) {
      console.error('[SyncContext] Error loading pending services:', error);
    }
  };

  /**
   * Add a service to the pending queue
   * Ensures client_uuid is set for idempotency
   */
  const addPendingService = async (service: any) => {
    try {
      const pending = await AsyncStorage.getItem(PENDING_SERVICES_KEY);
      const services: PendingService[] = pending ? JSON.parse(pending) : [];
      
      // Ensure client_uuid exists
      const serviceWithUUID: PendingService = {
        ...service,
        client_uuid: service.client_uuid || newClientUUID()
      };
      
      services.push(serviceWithUUID);
      await AsyncStorage.setItem(PENDING_SERVICES_KEY, JSON.stringify(services));
      setPendingServices(services.length);
      
      console.log(`[SyncContext] Added pending service with client_uuid: ${serviceWithUUID.client_uuid}`);
      
      // Try to sync immediately if connected
      const netInfo = await NetInfo.fetch();
      if (netInfo.isConnected) {
        await syncServices();
      }
    } catch (error) {
      console.error('[SyncContext] Error adding pending service:', error);
    }
  };

  /**
   * Sync all pending services to the server
   * Uses client_uuid for idempotency - safe to retry
   */
  const syncServices = async () => {
    if (!token || syncStatus === 'syncing') return;

    try {
      setSyncStatus('syncing');
      const pending = await AsyncStorage.getItem(PENDING_SERVICES_KEY);
      
      if (!pending) {
        setSyncStatus('idle');
        return;
      }

      const services: PendingService[] = JSON.parse(pending);
      
      if (services.length === 0) {
        setSyncStatus('idle');
        return;
      }

      console.log(`[SyncContext] Syncing ${services.length} services...`);

      const response = await axios.post<{
        message: string;
        results: SyncResult[];
        errors: string[] | null;
      }>(
        `${API_URL}/services/sync`,
        { services },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      const results = response.data.results || [];
      const syncedUUIDs = new Set<string>();
      
      // Collect UUIDs of successfully synced services
      results.forEach(result => {
        if (result.status === 'created' || result.status === 'existing') {
          if (result.client_uuid) {
            syncedUUIDs.add(result.client_uuid);
          }
        }
      });
      
      // Remove synced services from pending queue
      const remainingServices = services.filter(
        service => !syncedUUIDs.has(service.client_uuid)
      );
      
      if (remainingServices.length === 0) {
        await AsyncStorage.removeItem(PENDING_SERVICES_KEY);
      } else {
        await AsyncStorage.setItem(PENDING_SERVICES_KEY, JSON.stringify(remainingServices));
        console.log(`[SyncContext] ${remainingServices.length} services still pending after sync`);
      }
      
      setPendingServices(remainingServices.length);
      
      const syncedCount = services.length - remainingServices.length;
      console.log(`[SyncContext] Synced ${syncedCount} services successfully`);
      
      setSyncStatus('success');
      setTimeout(() => setSyncStatus('idle'), 2000);
    } catch (error) {
      console.error('[SyncContext] Sync error:', error);
      setSyncStatus('error');
      setTimeout(() => setSyncStatus('idle'), 3000);
    }
  };

  return (
    <SyncContext.Provider value={{ pendingServices, syncStatus, syncServices, addPendingService }}>
      {children}
    </SyncContext.Provider>
  );
}

export function useSync() {
  const context = useContext(SyncContext);
  if (context === undefined) {
    throw new Error('useSync must be used within a SyncProvider');
  }
  return context;
}
