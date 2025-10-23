import React from 'react';
import { View, StyleSheet, ScrollView, Image } from 'react-native';
import { Text, Card, Button, Divider } from 'react-native-paper';
import { useAuth } from '../../contexts/AuthContext';
import { useConfig } from '../../contexts/ConfigContext';
import { useRouter } from 'expo-router';

export default function AdminProfileScreen() {
  const { user, logout } = useAuth();
  const { config } = useConfig();
  const router = useRouter();

  const handleLogout = async () => {
    await logout();
    router.replace('/');
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Image
          source={require('../../assets/images/logo-taxi-tineo.png')}
          style={styles.logo}
          resizeMode="contain"
        />
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
            <Text variant="bodyMedium" style={styles.adminRole}>Administrador</Text>
          </View>
        </Card.Content>
      </Card>

      <Card style={styles.card}>
        <Card.Content>
          <Text variant="titleMedium" style={styles.sectionTitle}>
            Información del Sistema
          </Text>
          <Text variant="bodyMedium" style={styles.infoText}>
            Como administrador, puedes:
          </Text>
          <Text variant="bodySmall" style={styles.bulletPoint}>
            • Ver y gestionar todos los servicios de taxi
          </Text>
          <Text variant="bodySmall" style={styles.bulletPoint}>
            • Crear y gestionar empresas
          </Text>
          <Text variant="bodySmall" style={styles.bulletPoint}>
            • Crear y gestionar taxistas
          </Text>
          <Text variant="bodySmall" style={styles.bulletPoint}>
            • Exportar datos en CSV, Excel o PDF
          </Text>
          <Text variant="bodySmall" style={styles.bulletPoint}>
            • Aplicar filtros por tipo y empresa
          </Text>
        </Card.Content>
      </Card>

      <Card style={styles.card}>
        <Card.Content>
          <Text variant="titleMedium" style={styles.sectionTitle}>
            Contacto
          </Text>
          <Text variant="bodyMedium" style={styles.contact}>
            www.taxitineo.com
          </Text>
          <Text variant="bodyMedium" style={styles.contact}>
            985 80 15 15
          </Text>
        </Card.Content>
      </Card>

      <Button
        mode="contained"
        onPress={handleLogout}
        style={styles.logoutButton}
        buttonColor="#D32F2F"
      >
        Cerrar Sesión
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
  },
  label: {
    fontWeight: '600',
    color: '#666',
  },
  adminRole: {
    color: '#FFD700',
    fontWeight: 'bold',
  },
  sectionTitle: {
    marginBottom: 12,
    color: '#333',
  },
  infoText: {
    marginBottom: 8,
    color: '#666',
  },
  bulletPoint: {
    marginLeft: 8,
    marginTop: 4,
    color: '#666',
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
