import React, { useState, useEffect } from 'react';
import { View, StyleSheet, Image } from 'react-native';
import { Text, Avatar } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_URL } from '../config/api';

interface Organization {
  id: string;
  nombre: string;
  logo_url?: string;
  logo_base64?: string;
  color_primario?: string;
  color_secundario?: string;
  settings?: {
    display_name?: string;
    logo_url?: string;
    primary_color?: string;
    [key: string]: string | undefined;
  };
}

interface OrganizationBrandingProps {
  variant?: 'header' | 'sidebar' | 'compact';
}

export default function OrganizationBranding({ variant = 'header' }: OrganizationBrandingProps) {
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadOrganization();
  }, []);

  const loadOrganization = async () => {
    try {
      const token = await AsyncStorage.getItem('token');
      if (!token) return;
      
      const response = await axios.get(`${API_URL}/my-organization`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setOrganization(response.data);
    } catch (error) {
      console.log('No organization found or not applicable');
    } finally {
      setLoading(false);
    }
  };

  if (loading || !organization) {
    return null;
  }

  // Priorizar settings sobre campos base
  const displayName = organization.settings?.display_name || organization.nombre;
  const primaryColor = organization.settings?.primary_color || organization.color_primario || '#0066CC';
  const logoSource = organization.settings?.logo_url || organization.logo_base64 || organization.logo_url;

  if (variant === 'compact') {
    return (
      <View style={styles.compactContainer}>
        {logoSource ? (
          <Image 
            source={{ uri: logoSource }} 
            style={styles.compactLogo}
            resizeMode="contain"
          />
        ) : (
          <View style={[styles.compactIconContainer, { backgroundColor: primaryColor }]}>
            <MaterialCommunityIcons name="office-building" size={16} color="#FFF" />
          </View>
        )}
        <Text variant="labelMedium" style={styles.compactName} numberOfLines={1}>
          {displayName}
        </Text>
      </View>
    );
  }

  if (variant === 'sidebar') {
    return (
      <View style={styles.sidebarContainer}>
        {logoSource ? (
          <Image 
            source={{ uri: logoSource }} 
            style={styles.sidebarLogo}
            resizeMode="contain"
          />
        ) : (
          <View style={[styles.sidebarIconContainer, { backgroundColor: primaryColor }]}>
            <MaterialCommunityIcons name="office-building" size={28} color="#FFF" />
          </View>
        )}
        <View style={styles.sidebarTextContainer}>
          <Text variant="titleMedium" style={styles.sidebarName} numberOfLines={2}>
            {displayName}
          </Text>
        </View>
      </View>
    );
  }

  // Default: header variant
  return (
    <View style={styles.headerContainer}>
      {logoSource ? (
        <Image 
          source={{ uri: logoSource }} 
          style={styles.headerLogo}
          resizeMode="contain"
        />
      ) : (
        <View style={[styles.headerIconContainer, { backgroundColor: primaryColor }]}>
          <MaterialCommunityIcons name="office-building" size={20} color="#FFF" />
        </View>
      )}
      <Text variant="labelLarge" style={styles.headerName} numberOfLines={1}>
        {organization.nombre}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  // Header variant (top right)
  headerContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.15)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    gap: 8,
  },
  headerLogo: {
    width: 28,
    height: 28,
    borderRadius: 14,
  },
  headerIconContainer: {
    width: 28,
    height: 28,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerName: {
    color: '#FFF',
    fontWeight: '600',
    maxWidth: 150,
  },

  // Sidebar variant
  sidebarContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#F5F5F5',
    borderRadius: 12,
    marginHorizontal: 16,
    marginVertical: 8,
    gap: 12,
  },
  sidebarLogo: {
    width: 48,
    height: 48,
    borderRadius: 8,
  },
  sidebarIconContainer: {
    width: 48,
    height: 48,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sidebarTextContainer: {
    flex: 1,
  },
  sidebarName: {
    fontWeight: '600',
    color: '#333',
  },

  // Compact variant
  compactContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  compactLogo: {
    width: 20,
    height: 20,
    borderRadius: 4,
  },
  compactIconContainer: {
    width: 20,
    height: 20,
    borderRadius: 4,
    alignItems: 'center',
    justifyContent: 'center',
  },
  compactName: {
    color: '#666',
    maxWidth: 100,
  },
});
