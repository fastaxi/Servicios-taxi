import React from 'react';
import { View, StyleSheet, ScrollView, Image } from 'react-native';
import { Text, Card, Button, Divider, Chip } from 'react-native-paper';
import { useAuth } from '../../contexts/AuthContext';
import { useSync } from '../../contexts/SyncContext';
import { useOrganization } from '../../contexts/OrganizationContext';
import { useRouter } from 'expo-router';

export default function ProfileScreen() {
  const { user, logout } = useAuth();
  const { pendingServices } = useSync();
  const { organization } = useOrganization();
  const router = useRouter();

  const handleLogout = async () => {
    await logout();
    router.replace('/');
  };

  return (
    <ScrollView style={styles.container}>
      <View style={[styles.header, { backgroundColor: organization.color_primario || '#0066CC' }]}>
        {organization.logo_base64 ? (
          <Image
            source={{ uri: organization.logo_base64 }}
            style={styles.logo}
            resizeMode="contain"
          />
        ) : (
          <View style={styles.orgNameContainer}>
            <Text variant="headlineMedium" style={styles.orgName}>
              {organization.nombre}
            </Text>
          </View>
        )}
      </View>

      <Card style={styles.card}>
        <Card.Content>
          <Text variant="titleLarge" style={styles.name}>
            {user?.nombre}
          </Text>
          <Text variant="bodyMedium" style={styles.username}>
            @{user?.username}
          </Text>
          <Divider style={styles.divider} />
          <View style={styles.infoRow}>
            <Text variant="bodyMedium" style={styles.label}>Rol:</Text>
            <Text variant="bodyMedium">{user?.role === 'admin' ? 'Administrador' : 'Taxista'}</Text>
          </View>
        </Card.Content>
      </Card>

      <Card style={styles.card}>
        <Card.Content>
          <Text variant="titleMedium" style={styles.sectionTitle}>
            Sincronizacion
          </Text>
          <View style={styles.infoRow}>
            <Text variant="bodyMedium" style={styles.label}>Servicios pendientes:</Text>
            <Text variant="bodyMedium" style={pendingServices > 0 ? styles.pending : styles.synced}>
              {pendingServices}
            </Text>
          </View>
        </Card.Content>
      </Card>

      <Card style={styles.card}>
        <Card.Content>
          <Text variant="titleMedium" style={styles.sectionTitle}>
            Mi Organizacion
          </Text>
          <Text variant="bodyLarge" style={[styles.orgTitle, { color: organization.color_primario }]}>
            {organization.nombre}
          </Text>
          {organization.localidad && (
            <Text variant="bodyMedium" style={styles.contact}>
              📍 {organization.localidad}{organization.provincia ? `, ${organization.provincia}` : ''}
            </Text>
          )}
          {organization.telefono && (
            <Text variant="bodyMedium" style={styles.contact}>
              📞 {organization.telefono}
            </Text>
          )}
          {organization.email && (
            <Text variant="bodyMedium" style={styles.contact}>
              ✉️ {organization.email}
            </Text>
          )}
          {organization.web && (
            <Text variant="bodyMedium" style={styles.contact}>
              🌐 {organization.web}
            </Text>
          )}
        </Card.Content>
      </Card>

      <Button
        mode="contained"
        onPress={handleLogout}
        style={styles.logoutButton}
        buttonColor="#D32F2F"
      >
        Cerrar Sesion
      </Button>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  header: {
    backgroundColor: '#0066CC',
    padding: 24,
    alignItems: 'center',
  },
  logo: {
    width: 150,
    height: 100,
  },
  orgNameContainer: {
    padding: 16,
  },
  orgName: {
    color: '#fff',
    fontWeight: 'bold',
    textAlign: 'center',
  },
  orgTitle: {
    fontWeight: 'bold',
    marginBottom: 8,
  },
  card: {
    margin: 16,
    backgroundColor: 'white',
    elevation: 2,
  },
  name: {
    fontWeight: 'bold',
    color: '#0066CC',
    marginBottom: 4,
  },
  username: {
    color: '#666',
  },
  divider: {
    marginVertical: 16,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 8,
  },
  label: {
    fontWeight: '600',
    color: '#666',
  },
  sectionTitle: {
    marginBottom: 8,
    color: '#333',
  },
  pending: {
    color: '#FFD700',
    fontWeight: 'bold',
  },
  synced: {
    color: '#4CAF50',
    fontWeight: 'bold',
  },
  contact: {
    marginTop: 4,
    color: '#0066CC',
  },
  logoutButton: {
    margin: 16,
    paddingVertical: 8,
  },
});
