import React, { createContext, useState, useContext, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';
import axios from 'axios';
import { useAuth } from './AuthContext';

import { API_URL } from '../config/api';

interface SyncContextType {
  pendingServices: number;
  syncStatus: 'idle' | 'syncing' | 'success' | 'error';
  syncServices: () => Promise<void>;
  addPendingService: (service: any) => Promise<void>;
}

const SyncContext = createContext<SyncContextType | undefined>(undefined);

export function SyncProvider({ children }: { children: React.ReactNode }) {
  const [pendingServices, setPendingServices] = useState(0);
  const [syncStatus, setSyncStatus] = useState<'idle' | 'syncing' | 'success' | 'error'>('idle');
  const { token } = useAuth();

  useEffect(() => {
    loadPendingCount();
    
    // Listen for network changes
    const unsubscribe = NetInfo.addEventListener(state => {
      if (state.isConnected && pendingServices > 0) {
        syncServices();
      }
    });

    return () => unsubscribe();
  }, [pendingServices, token]);

  const loadPendingCount = async () => {
    try {
      const pending = await AsyncStorage.getItem('pendingServices');
      if (pending) {
        const services = JSON.parse(pending);
        setPendingServices(services.length);
      }
    } catch (error) {
      console.error('Error loading pending count:', error);
    }
  };

  const addPendingService = async (service: any) => {
    try {
      const pending = await AsyncStorage.getItem('pendingServices');
      const services = pending ? JSON.parse(pending) : [];
      services.push(service);
      await AsyncStorage.setItem('pendingServices', JSON.stringify(services));
      setPendingServices(services.length);
      
      // Try to sync immediately if connected
      const netInfo = await NetInfo.fetch();
      if (netInfo.isConnected) {
        await syncServices();
      }
    } catch (error) {
      console.error('Error adding pending service:', error);
    }
  };

  const syncServices = async () => {
    if (!token || syncStatus === 'syncing') return;

    try {
      setSyncStatus('syncing');
      const pending = await AsyncStorage.getItem('pendingServices');
      
      if (!pending) {
        setSyncStatus('idle');
        return;
      }

      const services = JSON.parse(pending);
      
      if (services.length === 0) {
        setSyncStatus('idle');
        return;
      }

      const response = await axios.post(
        `${API_URL}/services/sync`,
        { services },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      // Clear pending services
      await AsyncStorage.removeItem('pendingServices');
      setPendingServices(0);
      setSyncStatus('success');
      
      setTimeout(() => setSyncStatus('idle'), 2000);
    } catch (error) {
      console.error('Sync error:', error);
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
