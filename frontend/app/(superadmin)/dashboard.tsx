import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ScrollView, RefreshControl, Dimensions } from 'react-native';
import { Text, Card, useTheme, ActivityIndicator, Button } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_URL } from '../../config/api';

interface Organization {
  id: string;
  nombre: string;
  slug: string;
  activa: boolean;
  total_taxistas: number;
  total_vehiculos: number;
  total_clientes: number;
  created_at: string;
}

interface Stats {
  totalOrganizations: number;
  activeOrganizations: number;
  totalTaxistas: number;
  totalVehiculos: number;
  totalClientes: number;
}

export default function SuperAdminDashboard() {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [stats, setStats] = useState<Stats>({
    totalOrganizations: 0,
    activeOrganizations: 0,
    totalTaxistas: 0,
    totalVehiculos: 0,
    totalClientes: 0,
  });
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const router = useRouter();
  const theme = useTheme();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const token = await AsyncStorage.getItem('token');
      const response = await axios.get(`${API_URL}/organizations`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const orgs = response.data;
      setOrganizations(orgs);
      
      // Calculate stats
      const totalTaxistas = orgs.reduce((sum: number, org: Organization) => sum + org.total_taxistas, 0);
      const totalVehiculos = orgs.reduce((sum: number, org: Organization) => sum + org.total_vehiculos, 0);
      const totalClientes = orgs.reduce((sum: number, org: Organization) => sum + org.total_clientes, 0);
      const activeOrgs = orgs.filter((org: Organization) => org.activa).length;
      
      setStats({
        totalOrganizations: orgs.length,
        activeOrganizations: activeOrgs,
        totalTaxistas,
        totalVehiculos,
        totalClientes,
      });
    } catch (error) {
      console.error('Error loading organizations:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" />
        <Text style={{ marginTop: 16 }}>Cargando datos...</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      <View style={styles.header}>
        <Text variant="headlineMedium" style={styles.title}>🏢 Panel Super Admin</Text>
        <Text variant="bodyMedium" style={styles.subtitle}>Gestión de organizaciones TaxiFast</Text>
      </View>

      {/* Stats Cards */}
      <View style={styles.statsContainer}>
        <Card style={[styles.statCard, { backgroundColor: '#e3f2fd' }]}>
          <Card.Content style={styles.statContent}>
            <MaterialCommunityIcons name="domain" size={32} color="#1976d2" />
            <Text variant="headlineLarge" style={styles.statNumber}>{stats.totalOrganizations}</Text>
            <Text variant="bodyMedium">Organizaciones</Text>
            <Text variant="bodySmall" style={styles.statSubtext}>{stats.activeOrganizations} activas</Text>
          </Card.Content>
        </Card>

        <Card style={[styles.statCard, { backgroundColor: '#e8f5e9' }]}>
          <Card.Content style={styles.statContent}>
            <MaterialCommunityIcons name="account-group" size={32} color="#388e3c" />
            <Text variant="headlineLarge" style={styles.statNumber}>{stats.totalTaxistas}</Text>
            <Text variant="bodyMedium">Taxistas</Text>
            <Text variant="bodySmall" style={styles.statSubtext}>Total en plataforma</Text>
          </Card.Content>
        </Card>

        <Card style={[styles.statCard, { backgroundColor: '#fff3e0' }]}>
          <Card.Content style={styles.statContent}>
            <MaterialCommunityIcons name="car" size={32} color="#f57c00" />
            <Text variant="headlineLarge" style={styles.statNumber}>{stats.totalVehiculos}</Text>
            <Text variant="bodyMedium">Vehículos</Text>
            <Text variant="bodySmall" style={styles.statSubtext}>Registrados</Text>
          </Card.Content>
        </Card>

        <Card style={[styles.statCard, { backgroundColor: '#fce4ec' }]}>
          <Card.Content style={styles.statContent}>
            <MaterialCommunityIcons name="briefcase" size={32} color="#c2185b" />
            <Text variant="headlineLarge" style={styles.statNumber}>{stats.totalClientes}</Text>
            <Text variant="bodyMedium">Empresas Cliente</Text>
            <Text variant="bodySmall" style={styles.statSubtext}>Total registradas</Text>
          </Card.Content>
        </Card>
      </View>

      {/* Recent Organizations */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text variant="titleLarge">Organizaciones Recientes</Text>
          <Button mode="contained" onPress={() => router.push('/(superadmin)/organizations' as any)}>
            Ver Todas
          </Button>
        </View>
        
        {/* Quick Action: Unassigned Users */}
        <Card style={[styles.actionCard, { marginBottom: 16 }]}>
          <Card.Content style={styles.actionContent}>
            <View style={styles.actionInfo}>
              <MaterialCommunityIcons name="account-alert" size={32} color="#FF9800" />
              <View style={{ marginLeft: 16, flex: 1 }}>
                <Text variant="titleMedium">Usuarios Sin Asignar</Text>
                <Text variant="bodySmall" style={{ color: '#666' }}>
                  Usuarios creados antes del sistema multi-tenant
                </Text>
              </View>
            </View>
            <Button 
              mode="outlined" 
              onPress={() => router.push('/(superadmin)/users' as any)}
              icon="arrow-right"
            >
              Gestionar
            </Button>
          </Card.Content>
        </Card>
        
        {organizations.slice(0, 5).map((org) => (
          <Card key={org.id} style={styles.orgCard}>
            <Card.Content style={styles.orgContent}>
              <View style={styles.orgInfo}>
                <View style={[styles.statusDot, { backgroundColor: org.activa ? '#4caf50' : '#f44336' }]} />
                <View style={{ flex: 1 }}>
                  <Text variant="titleMedium">{org.nombre}</Text>
                  <Text variant="bodySmall" style={styles.slugText}>/{org.slug}</Text>
                </View>
              </View>
              <View style={styles.orgStats}>
                <View style={styles.orgStatItem}>
                  <MaterialCommunityIcons name="account" size={16} color="#666" />
                  <Text variant="bodySmall" style={styles.orgStatText}>{org.total_taxistas}</Text>
                </View>
                <View style={styles.orgStatItem}>
                  <MaterialCommunityIcons name="car" size={16} color="#666" />
                  <Text variant="bodySmall" style={styles.orgStatText}>{org.total_vehiculos}</Text>
                </View>
                <View style={styles.orgStatItem}>
                  <MaterialCommunityIcons name="briefcase" size={16} color="#666" />
                  <Text variant="bodySmall" style={styles.orgStatText}>{org.total_clientes}</Text>
                </View>
              </View>
            </Card.Content>
          </Card>
        ))}
        
        {organizations.length === 0 && (
          <Card style={styles.emptyCard}>
            <Card.Content style={styles.emptyContent}>
              <MaterialCommunityIcons name="domain-plus" size={48} color="#ccc" />
              <Text variant="bodyLarge" style={styles.emptyText}>No hay organizaciones</Text>
              <Button mode="contained" onPress={() => router.push('/(superadmin)/organizations' as any)} style={{ marginTop: 16 }}>
                Crear Primera Organización
              </Button>
            </Card.Content>
          </Card>
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    padding: 24,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  title: {
    fontWeight: 'bold',
    color: '#333',
  },
  subtitle: {
    color: '#666',
    marginTop: 4,
  },
  statsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 16,
    gap: 16,
  },
  statCard: {
    flex: 1,
    minWidth: 200,
    borderRadius: 12,
  },
  statContent: {
    alignItems: 'center',
    padding: 16,
  },
  statNumber: {
    fontWeight: 'bold',
    marginTop: 8,
  },
  statSubtext: {
    color: '#666',
    marginTop: 4,
  },
  section: {
    padding: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  orgCard: {
    marginBottom: 12,
    borderRadius: 8,
  },
  orgContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  orgInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  statusDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 12,
  },
  slugText: {
    color: '#666',
  },
  orgStats: {
    flexDirection: 'row',
    gap: 16,
  },
  orgStatItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  orgStatText: {
    color: '#666',
  },
  emptyCard: {
    borderRadius: 12,
  },
  emptyContent: {
    alignItems: 'center',
    padding: 32,
  },
  emptyText: {
    color: '#999',
    marginTop: 16,
  },
  actionCard: {
    borderRadius: 12,
    backgroundColor: '#FFF3E0',
  },
  actionContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  actionInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
});
