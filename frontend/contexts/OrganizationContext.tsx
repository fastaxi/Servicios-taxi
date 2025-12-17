import React, { createContext, useState, useContext, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';
import { API_URL } from '../config/api';
import { useAuth } from './AuthContext';

interface OrganizationBranding {
  id: string | null;
  nombre: string;
  slug: string;
  logo_base64: string | null;
  color_primario: string;
  color_secundario: string;
  telefono: string;
  email: string;
  web: string;
  direccion: string;
  localidad: string;
  provincia: string;
}

interface OrganizationContextType {
  organization: OrganizationBranding;
  loading: boolean;
  refreshOrganization: () => Promise<void>;
}

const defaultOrganization: OrganizationBranding = {
  id: null,
  nombre: 'TaxiFast',
  slug: 'taxifast',
  logo_base64: null,
  color_primario: '#0066CC',
  color_secundario: '#FFD700',
  telefono: '',
  email: '',
  web: 'www.taxifast.com',
  direccion: '',
  localidad: '',
  provincia: '',
};

const OrganizationContext = createContext<OrganizationContextType | undefined>(undefined);

export function OrganizationProvider({ children }: { children: React.ReactNode }) {
  const [organization, setOrganization] = useState<OrganizationBranding>(defaultOrganization);
  const [loading, setLoading] = useState(true);
  const { user, token } = useAuth();

  useEffect(() => {
    if (user && token) {
      loadOrganization();
    } else {
      setOrganization(defaultOrganization);
      setLoading(false);
    }
  }, [user, token]);

  const loadOrganization = async () => {
    try {
      setLoading(true);
      const storedToken = await AsyncStorage.getItem('token');
      
      if (!storedToken) {
        setOrganization(defaultOrganization);
        return;
      }

      const response = await axios.get(`${API_URL}/my-organization`, {
        headers: { Authorization: `Bearer ${storedToken}` }
      });

      setOrganization(response.data);
      
      // Cache the organization data
      await AsyncStorage.setItem('organization', JSON.stringify(response.data));
    } catch (error) {
      console.error('[OrganizationContext] Error loading organization:', error);
      
      // Try to load from cache
      try {
        const cached = await AsyncStorage.getItem('organization');
        if (cached) {
          setOrganization(JSON.parse(cached));
        } else {
          setOrganization(defaultOrganization);
        }
      } catch (e) {
        setOrganization(defaultOrganization);
      }
    } finally {
      setLoading(false);
    }
  };

  const refreshOrganization = async () => {
    await loadOrganization();
  };

  return (
    <OrganizationContext.Provider value={{ organization, loading, refreshOrganization }}>
      {children}
    </OrganizationContext.Provider>
  );
}

export function useOrganization() {
  const context = useContext(OrganizationContext);
  if (context === undefined) {
    throw new Error('useOrganization must be used within an OrganizationProvider');
  }
  return context;
}
