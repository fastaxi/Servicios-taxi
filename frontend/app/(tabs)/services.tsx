import React, { useState, useEffect } from 'react';
import { View, StyleSheet, FlatList, RefreshControl } from 'react-native';
import { Text, Card, Chip, FAB, IconButton } from 'react-native-paper';
import { useAuth } from '../../contexts/AuthContext';
import { useSync } from '../../contexts/SyncContext';
import { useRouter } from 'expo-router';
import axios from 'axios';
import { format } from 'date-fns';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL + '/api';

interface Service {
  id: string;
  fecha: string;
  hora: string;
  origen: string;
  destino: string;
  importe: number;
  importe_espera: number;
  kilometros: number;
  tipo: string;
  empresa_nombre?: string;
}

export default function ServicesScreen() {
  const [services, setServices] = useState<Service[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const { token } = useAuth();
  const { pendingServices, syncStatus, syncServices } = useSync();
  const router = useRouter();

  useEffect(() => {
    loadServices();
  }, []);

  useEffect(() => {
    if (syncStatus === 'success') {
      loadServices();
    }
  }, [syncStatus]);

  const loadServices = async () => {
    try {
      console.log('=== Cargando servicios del taxista ===');
      console.log('Token:', token ? 'Presente' : 'Ausente');
      const response = await axios.get(`${API_URL}/services`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      console.log('Servicios recibidos:', response.data.length);
      setServices(response.data);
    } catch (error) {
      console.error('Error loading services:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await syncServices();
    await loadServices();
    setRefreshing(false);
  };

  const renderService = ({ item }: { item: Service }) => (
    <Card style={styles.card}>
      <Card.Content>
        <View style={styles.cardHeader}>
          <View style={styles.cardTitleContainer}>
            <Text variant="titleMedium" style={styles.cardTitle}>
              {item.origen} → {item.destino}
            </Text>
            <Chip mode="flat" style={styles.chip}>
              {item.importe}€
            </Chip>
          </View>
          <IconButton
            icon="pencil"
            size={20}
            onPress={() => router.push(`/edit-service?id=${item.id}`)}
            iconColor="#0066CC"
          />
        </View>

        <View style={styles.detailRow}>
          <Text variant="bodyMedium" style={styles.label}>Fecha:</Text>
          <Text variant="bodyMedium">{item.fecha} {item.hora}</Text>
        </View>

        <View style={styles.detailRow}>
          <Text variant="bodyMedium" style={styles.label}>Kilómetros:</Text>
          <Text variant="bodyMedium">{item.kilometros} km</Text>
        </View>

        {item.importe_espera > 0 && (
          <View style={styles.detailRow}>
            <Text variant="bodyMedium" style={styles.label}>Importe espera:</Text>
            <Text variant="bodyMedium">{item.importe_espera}€</Text>
          </View>
        )}

        <View style={styles.detailRow}>
          <Text variant="bodyMedium" style={styles.label}>Tipo:</Text>
          <Chip mode="outlined" compact>
            {item.tipo === 'empresa' ? item.empresa_nombre : 'Particular'}
          </Chip>
        </View>
      </Card.Content>
    </Card>
  );

  return (
    <View style={styles.container}>
      {pendingServices > 0 && (
        <View style={styles.syncBanner}>
          <Text style={styles.syncText}>
            {syncStatus === 'syncing'
              ? 'Sincronizando servicios...'
              : `${pendingServices} servicio(s) pendiente(s) de sincronizar`}
          </Text>
        </View>
      )}

      <FlatList
        data={services}
        renderItem={renderService}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={['#0066CC']} />
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text variant="bodyLarge" style={styles.emptyText}>
              No hay servicios registrados
            </Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  syncBanner: {
    backgroundColor: '#FFD700',
    padding: 12,
    alignItems: 'center',
  },
  syncText: {
    color: '#333',
    fontWeight: '600',
  },
  list: {
    padding: 16,
  },
  card: {
    marginBottom: 16,
    backgroundColor: 'white',
    elevation: 2,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  cardTitleContainer: {
    flex: 1,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  cardTitle: {
    flex: 1,
    fontWeight: 'bold',
    color: '#0066CC',
  },
  chip: {
    backgroundColor: '#0066CC',
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 8,
  },
  label: {
    fontWeight: '600',
    color: '#666',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 100,
  },
  emptyText: {
    color: '#999',
  },
});
