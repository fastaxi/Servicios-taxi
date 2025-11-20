import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';

import { API_URL } from '../config/api';

interface ConfigType {
  nombre_radio_taxi: string;
  telefono: string;
  web: string;
  direccion: string;
  email: string;
  logo_base64: string | null;
}

interface ConfigContextType {
  config: ConfigType;
  loading: boolean;
  reloadConfig: () => Promise<void>;
}

const defaultConfig: ConfigType = {
  nombre_radio_taxi: 'Taxi Tineo',
  telefono: '985 80 15 15',
  web: 'www.taxitineo.com',
  direccion: 'Tineo, Asturias',
  email: '',
  logo_base64: null,
};

const ConfigContext = createContext<ConfigContextType | undefined>(undefined);

export function ConfigProvider({ children }: { children: React.ReactNode }) {
  const [config, setConfig] = useState<ConfigType>(defaultConfig);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const response = await axios.get(`${API_URL}/config`);
      setConfig(response.data);
    } catch (error) {
      console.error('Error loading config:', error);
      // Si falla, usar la configuración por defecto
      setConfig(defaultConfig);
    } finally {
      setLoading(false);
    }
  };

  const reloadConfig = async () => {
    await loadConfig();
  };

  return (
    <ConfigContext.Provider value={{ config, loading, reloadConfig }}>
      {children}
    </ConfigContext.Provider>
  );
}

export function useConfig() {
  const context = useContext(ConfigContext);
  if (context === undefined) {
    throw new Error('useConfig must be used within a ConfigProvider');
  }
  return context;
}
