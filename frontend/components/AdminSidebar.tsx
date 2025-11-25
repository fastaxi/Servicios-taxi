import React from 'react';
import { View, StyleSheet, TouchableOpacity, ScrollView, Platform } from 'react-native';
import { Text, Divider, Avatar } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useRouter, usePathname } from 'expo-router';
import { useAuth } from '../contexts/AuthContext';

interface MenuItem {
  icon: string;
  label: string;
  route: string;
}

const menuItems: MenuItem[] = [
  { icon: 'view-dashboard', label: 'Dashboard', route: '/dashboard' },
  { icon: 'car-multiple', label: 'Servicios', route: '/dashboard' }, // Será la vista principal
  { icon: 'office-building', label: 'Empresas', route: '/companies' },
  { icon: 'account-group', label: 'Taxistas', route: '/users' },
  { icon: 'car', label: 'Vehículos', route: '/vehiculos' },
  { icon: 'clock-outline', label: 'Turnos', route: '/turnos' },
  { icon: 'cog', label: 'Configuración', route: '/config' },
];

export default function AdminSidebar() {
  const router = useRouter();
  const pathname = usePathname();
  const { user, logout } = useAuth();

  const handleNavigation = (route: string) => {
    router.push(route);
  };

  const handleLogout = () => {
    logout();
    router.replace('/');
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.logoContainer}>
          <MaterialCommunityIcons name="taxi" size={32} color="#0066CC" />
          <Text variant="headlineSmall" style={styles.title}>Taxi Tineo</Text>
        </View>
        <Text variant="bodySmall" style={styles.subtitle}>Panel de Administración</Text>
      </View>

      <Divider />

      {/* User Info */}
      <View style={styles.userInfo}>
        <Avatar.Icon size={48} icon="account" style={styles.avatar} />
        <Text variant="titleMedium" style={styles.userName}>{user?.nombre || 'Admin'}</Text>
        <Text variant="bodySmall" style={styles.userRole}>Administrador</Text>
      </View>

      <Divider />

      {/* Menu Items */}
      <ScrollView style={styles.menuContainer} showsVerticalScrollIndicator={false}>
        {menuItems.map((item) => {
          const isActive = pathname.includes(item.route);
          return (
            <TouchableOpacity
              key={item.route}
              style={[styles.menuItem, isActive && styles.menuItemActive]}
              onPress={() => handleNavigation(item.route)}
            >
              <MaterialCommunityIcons
                name={item.icon as any}
                size={24}
                color={isActive ? '#0066CC' : '#666'}
              />
              <Text
                variant="bodyLarge"
                style={[styles.menuLabel, isActive && styles.menuLabelActive]}
              >
                {item.label}
              </Text>
            </TouchableOpacity>
          );
        })}
      </ScrollView>

      <Divider />

      {/* Logout */}
      <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
        <MaterialCommunityIcons name="logout" size={24} color="#D32F2F" />
        <Text variant="bodyLarge" style={styles.logoutText}>Cerrar Sesión</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    borderRightWidth: 1,
    borderRightColor: '#E0E0E0',
  },
  header: {
    padding: 24,
    paddingBottom: 16,
  },
  logoContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 4,
  },
  title: {
    fontWeight: 'bold',
    color: '#0066CC',
  },
  subtitle: {
    color: '#666',
    marginTop: 4,
  },
  userInfo: {
    padding: 20,
    alignItems: 'center',
  },
  avatar: {
    backgroundColor: '#0066CC',
    marginBottom: 8,
  },
  userName: {
    fontWeight: '600',
    marginBottom: 4,
  },
  userRole: {
    color: '#666',
  },
  menuContainer: {
    flex: 1,
    padding: 8,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderRadius: 8,
    marginBottom: 4,
    gap: 16,
  },
  menuItemActive: {
    backgroundColor: '#E3F2FD',
  },
  menuLabel: {
    color: '#666',
    fontWeight: '500',
  },
  menuLabelActive: {
    color: '#0066CC',
    fontWeight: '600',
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 20,
    gap: 16,
  },
  logoutText: {
    color: '#D32F2F',
    fontWeight: '600',
  },
});
