import React, { createContext, useState, useContext, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';
import { API_URL } from '../config/api';
import { useAuth } from './AuthContext';

interface OrganizationFeatures {
  taxitur_origen?: boolean;
  [key: string]: boolean | undefined;
}

interface OrganizationSettings {
  display_name?: string;
  logo_url?: string;
  footer_name?: string;
  footer_cif?: string;
  footer_extra?: string;
  primary_color?: string;
  support_email?: string;
  support_phone?: string;
  [key: string]: string | boolean | undefined;
}

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
  cif: string;
  features: OrganizationFeatures;
  settings: OrganizationSettings;
}

interface OrganizationContextType {
  organization: OrganizationBranding;
  loading: boolean;
  refreshOrganization: () => Promise<void>;
  hasFeature: (featureName: string) => boolean;
  getSetting: <T extends string | boolean | undefined>(key: string, defaultValue: T) => T;
  updateSettings: (settings: Partial<OrganizationSettings>) => Promise<boolean>;
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
  cif: '',
  features: {},
  settings: {},
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

      // Asegurar que features y settings existen
      const orgData = {
        ...response.data,
        features: response.data.features || {},
        settings: response.data.settings || {},
        cif: response.data.cif || '',
      };

      setOrganization(orgData);
      
      // Cache the organization data
      await AsyncStorage.setItem('organization', JSON.stringify(orgData));
    } catch (error) {
      console.error('[OrganizationContext] Error loading organization:', error);
      
      // Try to load from cache
      try {
        const cached = await AsyncStorage.getItem('organization');
        if (cached) {
          const cachedData = JSON.parse(cached);
          setOrganization({
            ...cachedData,
            features: cachedData.features || {},
            settings: cachedData.settings || {},
          });
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

  // Helper function to check if a feature is enabled
  const hasFeature = (featureName: string): boolean => {
    return organization.features?.[featureName] === true;
  };

  // Helper function to get a setting value with fallback
  const getSetting = <T extends string | boolean | undefined>(key: string, defaultValue: T): T => {
    const value = organization.settings?.[key];
    if (value === undefined || value === null) {
      return defaultValue;
    }
    return value as T;
  };

  // Function to update organization settings via API
  const updateSettings = async (settings: Partial<OrganizationSettings>): Promise<boolean> => {
    try {
      const storedToken = await AsyncStorage.getItem('token');
      if (!storedToken) return false;

      await axios.put(
        `${API_URL}/my-organization/settings`,
        settings,
        { headers: { Authorization: `Bearer ${storedToken}` } }
      );

      // Refresh organization data after update
      await refreshOrganization();
      return true;
    } catch (error) {
      console.error('[OrganizationContext] Error updating settings:', error);
      return false;
    }
  };

  return (
    <OrganizationContext.Provider value={{ 
      organization, 
      loading, 
      refreshOrganization, 
      hasFeature, 
      getSetting,
      updateSettings 
    }}>
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
