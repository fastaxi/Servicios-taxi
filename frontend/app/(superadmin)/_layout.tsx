import React from 'react';
import { View, StyleSheet, ScrollView, Platform, Pressable } from 'react-native';
import { Slot, useRouter, usePathname } from 'expo-router';
import { Text, useTheme, IconButton, Divider } from 'react-native-paper';
import { useAuth } from '../../contexts/AuthContext';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

const menuItems = [
  { path: '/(superadmin)/dashboard', label: 'Dashboard', icon: 'view-dashboard' },
  { path: '/(superadmin)/organizations', label: 'Organizaciones', icon: 'domain' },
];

export default function SuperAdminLayout() {
  const { user, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const isWeb = Platform.OS === 'web';

  // Redirect if not superadmin
  React.useEffect(() => {
    if (user && user.role !== 'superadmin') {
      if (user.role === 'admin') {
        router.replace('/(admin)/dashboard');
      } else {
        router.replace('/(tabs)/services');
      }
    }
  }, [user]);

  const handleLogout = async () => {
    await logout();
    router.replace('/');
  };

  const isActive = (path: string) => pathname === path || pathname?.startsWith(path.replace('/(superadmin)', ''));

  if (!isWeb) {
    // Mobile layout - simple stack
    return <Slot />;
  }

  // Web layout with sidebar
  return (
    <View style={styles.container}>
      {/* Sidebar */}
      <View style={[styles.sidebar, { paddingTop: insets.top }]}>
        <View style={styles.logoContainer}>
          <MaterialCommunityIcons name="shield-crown" size={32} color="#FFD700" />
          <Text variant="headlineSmall" style={styles.title}>TaxiFast</Text>
          <Text variant="labelSmall" style={styles.superadminBadge}>SUPER ADMIN</Text>
        </View>
        
        <Divider style={styles.divider} />
        
        <ScrollView style={styles.menuContainer}>
          {menuItems.map((item) => (
            <Pressable
              key={item.path}
              style={[styles.menuItem, isActive(item.path) && styles.menuItemActive]}
              onPress={() => router.push(item.path as any)}
            >
              <MaterialCommunityIcons
                name={item.icon as any}
                size={24}
                color={isActive(item.path) ? '#0066CC' : '#666'}
              />
              <Text style={[styles.menuLabel, isActive(item.path) && styles.menuLabelActive]}>
                {item.label}
              </Text>
            </Pressable>
          ))}
        </ScrollView>
        
        <View style={styles.userSection}>
          <Divider style={styles.divider} />
          <View style={styles.userInfo}>
            <MaterialCommunityIcons name="account-circle" size={40} color="#666" />
            <View style={styles.userTextContainer}>
              <Text variant="titleSmall">{user?.nombre}</Text>
              <Text variant="bodySmall" style={styles.roleText}>Super Administrador</Text>
            </View>
          </View>
          <IconButton
            icon="logout"
            size={24}
            onPress={handleLogout}
          />
        </View>
      </View>
      
      {/* Main content */}
      <View style={styles.content}>
        <Slot />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    flexDirection: 'row',
    backgroundColor: '#f5f5f5',
  },
  sidebar: {
    width: 280,
    backgroundColor: '#fff',
    borderRightWidth: 1,
    borderRightColor: '#e0e0e0',
    paddingHorizontal: 16,
  },
  logoContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 20,
    flexWrap: 'wrap',
  },
  title: {
    marginLeft: 12,
    fontWeight: 'bold',
    color: '#333',
  },
  superadminBadge: {
    marginLeft: 8,
    backgroundColor: '#FFD700',
    color: '#000',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
    fontWeight: 'bold',
  },
  divider: {
    marginVertical: 8,
  },
  menuContainer: {
    flex: 1,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    marginVertical: 2,
  },
  menuItemActive: {
    backgroundColor: '#e3f2fd',
  },
  menuLabel: {
    marginLeft: 16,
    fontSize: 16,
    color: '#666',
  },
  menuLabelActive: {
    color: '#0066CC',
    fontWeight: '600',
  },
  userSection: {
    paddingBottom: 16,
  },
  userInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
  },
  userTextContainer: {
    flex: 1,
    marginLeft: 12,
  },
  roleText: {
    color: '#666',
  },
  content: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
});
