import React from 'react';
import { View, StyleSheet, useWindowDimensions, Platform } from 'react-native';
import { Tabs, Slot } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import AdminSidebar from '../../components/AdminSidebar';
import OrganizationBranding from '../../components/OrganizationBranding';

export default function AdminLayout() {
  const { width } = useWindowDimensions();
  const isDesktop = Platform.OS === 'web' && width >= 1024;

  // Si es desktop (web + pantalla grande), mostrar sidebar + contenido
  if (isDesktop) {
    return (
      <View style={styles.desktopContainer}>
        <View style={styles.sidebar}>
          <AdminSidebar />
        </View>
        <View style={styles.content}>
          <Slot />
        </View>
      </View>
    );
  }

  // Si es movil o tablet, mostrar tabs como antes
  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: '#0066CC',
        tabBarInactiveTintColor: '#666',
        headerStyle: {
          backgroundColor: '#0066CC',
        },
        headerTintColor: '#fff',
        headerRight: () => <OrganizationBranding variant="header" />,
        headerRightContainerStyle: { paddingRight: 16 },
        tabBarStyle: {
          backgroundColor: '#FFFFFF',
          borderTopWidth: 1,
          borderTopColor: '#E0E0E0',
        },
      }}
    >
      <Tabs.Screen
        name="dashboard"
        options={{
          title: 'Panel',
          tabBarIcon: ({ color, size }) => (
            <MaterialCommunityIcons name="view-dashboard" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="companies"
        options={{
          title: 'Clientes',
          tabBarIcon: ({ color, size }) => (
            <MaterialCommunityIcons name="office-building" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="users"
        options={{
          title: 'Taxistas/Vehiculos',
          tabBarIcon: ({ color, size }) => (
            <MaterialCommunityIcons name="car-multiple" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="turnos"
        options={{
          title: 'Turnos',
          tabBarIcon: ({ color, size }) => (
            <MaterialCommunityIcons name="clock-outline" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="config"
        options={{
          href: null,
          title: 'Configuracion',
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'Perfil',
          tabBarIcon: ({ color, size }) => (
            <MaterialCommunityIcons name="account" size={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="vehiculos"
        options={{
          href: null,
          title: 'Vehiculos',
        }}
      />
      <Tabs.Screen
        name="edit-service"
        options={{
          href: null,
          title: 'Editar Servicio',
        }}
      />
    </Tabs>
  );
}

const styles = StyleSheet.create({
  desktopContainer: {
    flex: 1,
    flexDirection: 'row',
  },
  sidebar: {
    width: 280,
    height: '100%',
  },
  content: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
});
