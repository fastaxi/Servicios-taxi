import React, { useState, useEffect } from 'react';
import { View, StyleSheet, FlatList, RefreshControl, ScrollView } from 'react-native';
import { Text, Card, Chip, IconButton, Button, List } from 'react-native-paper';
import { useAuth } from '../../contexts/AuthContext';
import { useSync, QueuedService } from '../../contexts/SyncContext';
import { useRouter, useFocusEffect } from 'expo-router';
import axios from 'axios';

import { API_URL } from '../../config/api';

interface Service {
  id: string;
  fecha: string;
  hora: string;
  origen: string;
  destino: string;
  importe: number;
  importe_espera: number;
  importe_total: number;
  kilometros: number;
  tipo: string;
  empresa_nombre?: string;
  cobrado?: boolean;
  facturar?: boolean;
  turno_id?: string;
}

export default function ServicesScreen() {
  const [services, setServices] = useState<Service[]>([]);
  const [turnoActivo, setTurnoActivo] = useState<any>(null);
  const [mostrarHistorial, setMostrarHistorial] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [expandedDates, setExpandedDates] = useState<{ [key: string]: boolean }>({});
  const [showPendingList, setShowPendingList] = useState(false);
  const { token } = useAuth();
  const { pendingCount, pendingServices, syncStatus, syncQueue } = useSync();
  const router = useRouter();

  useEffect(() => {
    loadServices();
  }, []);

  useFocusEffect(
    React.useCallback(() => {
      loadServices();
    }, [])
  );

  useEffect(() => {
    if (syncStatus === 'success') {
      loadServices();
    }
  }, [syncStatus]);

  const loadServices = async () => {
    try {
      try {
        const turnoResponse = await axios.get(`${API_URL}/turnos/activo`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setTurnoActivo(turnoResponse.data);
      } catch (error: any) {
        if (error.response?.status !== 404) {
          console.error('Error cargando turno activo:', error);
        }
        setTurnoActivo(null);
      }
      
      const response = await axios.get(`${API_URL}/services`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setServices(response.data);
    } catch (error) {
      console.error('Error loading services:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await syncQueue();
    await loadServices();
    setRefreshing(false);
  };

  const formatEuro = (amount: number) => {
    return amount.toFixed(2).replace('.', ',') + ' *';
  };

  const getServiciosFiltrados = () => {
    if (!turnoActivo) return services;
    if (!mostrarHistorial) return services.filter(s => s.turno_id === turnoActivo.id);
    return services;
  };

  const serviciosTurnoActivo = turnoActivo ? services.filter(s => s.turno_id === turnoActivo.id).length : 0;
  const serviciosArchivados = services.length - serviciosTurnoActivo;

  const agruparPorFecha = (servicios: Service[]) => {
    const grupos: { [key: string]: Service[] } = {};
    servicios.forEach(servicio => {
      if (!grupos[servicio.fecha]) {
        grupos[servicio.fecha] = [];
      }
      grupos[servicio.fecha].push(servicio);
    });
    
    const fechasOrdenadas = Object.keys(grupos).sort((a, b) => {
      const [diaA, mesA, anoA] = a.split('/').map(Number);
      const [diaB, mesB, anoB] = b.split('/').map(Number);
      const fechaA = new Date(anoA, mesA - 1, diaA);
      const fechaB = new Date(anoB, mesB - 1, diaB);
      return fechaB.getTime() - fechaA.getTime();
    });
    
    return fechasOrdenadas.map(fecha => ({
      fecha,
      servicios: grupos[fecha].sort((a, b) => b.hora.localeCompare(a.hora))
    }));
  };

  const renderPendingItem = (item: QueuedService) => (
    <Card key={item.client_uuid} style={styles.pendingCard}>
      <Card.Content>
        <View style={styles.pendingRow}>
          <Text variant="bodyMedium" style={styles.pendingRoute}>
            {item.payload.origen || '?'} - {item.payload.destino || '?'}
          </Text>
          <Chip
            mode="flat"
            compact
            style={item.status === 'failed' ? styles.chipFailed : styles.chipPending}
            textStyle={styles.chipTextWhite}
          >
            {item.status === 'failed' ? 'Error' : 'Pendiente'}
          </Chip>
        </View>
        <Text variant="bodySmall" style={styles.pendingMeta}>
          {item.payload.fecha} {item.payload.hora} | {(item.payload.importe || 0).toFixed(2).replace('.', ',')} *
        </Text>
        {item.error && (
          <Text variant="bodySmall" style={styles.pendingError}>{item.error}</Text>
        )}
      </Card.Content>
    </Card>
  );

  const renderService = ({ item }: { item: Service }) => (
    <Card style={styles.card}>
      <Card.Content>
        <View style={styles.cardHeader}>
          <View style={styles.cardTitleContainer}>
            <Text variant="titleMedium" style={styles.cardTitle}>
              {item.origen} - {item.destino}
            </Text>
            <Chip mode="flat" style={styles.chip}>
              {formatEuro(item.importe_total || item.importe)}
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
          <Text variant="bodyMedium" style={styles.label}>Kilometros:</Text>
          <Text variant="bodyMedium">{item.kilometros} km</Text>
        </View>

        <View style={styles.detailRow}>
          <Text variant="bodyMedium" style={styles.label}>Importe del servicio:</Text>
          <Text variant="bodyMedium">{formatEuro(item.importe)}</Text>
        </View>

        {item.importe_espera > 0 && (
          <View style={styles.detailRow}>
            <Text variant="bodyMedium" style={styles.label}>Importe de espera:</Text>
            <Text variant="bodyMedium">{formatEuro(item.importe_espera)}</Text>
          </View>
        )}

        <View style={styles.detailRow}>
          <Text variant="bodyMedium" style={styles.label}>Tipo:</Text>
          <Chip mode="outlined" compact>
            {item.tipo === 'empresa' ? item.empresa_nombre : 'Particular'}
          </Chip>
        </View>

        <View style={styles.statusChipsContainer}>
          {item.cobrado && (
            <Chip 
              mode="flat" 
              compact 
              icon="cash-check"
              style={styles.chipCobrado}
              textStyle={styles.chipText}
            >
              Cobrado
            </Chip>
          )}
          {item.facturar && (
            <Chip 
              mode="flat" 
              compact 
              icon="file-document"
              style={styles.chipFacturar}
              textStyle={styles.chipText}
            >
              Facturar
            </Chip>
          )}
        </View>
      </Card.Content>
    </Card>
  );

  return (
    <View style={styles.container}>
      {/* Paso 5B: Sync banner with pending count and optional detail list */}
      {pendingCount > 0 && (
        <View>
          <View style={styles.syncBanner}>
            <View style={styles.syncBannerContent}>
              <Text style={styles.syncText}>
                {syncStatus === 'syncing'
                  ? 'Sincronizando servicios...'
                  : `Pendientes de sincronizar: ${pendingCount}`}
              </Text>
              <View style={styles.syncActions}>
                <Button
                  mode="text"
                  compact
                  textColor="#333"
                  onPress={() => setShowPendingList(!showPendingList)}
                  icon={showPendingList ? 'chevron-up' : 'chevron-down'}
                >
                  {showPendingList ? 'Ocultar' : 'Ver'}
                </Button>
                {syncStatus !== 'syncing' && (
                  <Button
                    mode="text"
                    compact
                    textColor="#0066CC"
                    onPress={() => syncQueue()}
                    icon="sync"
                  >
                    Reintentar
                  </Button>
                )}
              </View>
            </View>
          </View>
          {showPendingList && pendingServices.length > 0 && (
            <View style={styles.pendingListContainer}>
              {pendingServices.map(renderPendingItem)}
            </View>
          )}
        </View>
      )}

      {/* Banner informativo del turno activo */}
      {turnoActivo && !mostrarHistorial && (
        <View style={styles.turnoInfoBanner}>
          <Text style={styles.turnoInfoText}>
            Turno activo: {serviciosTurnoActivo} servicio(s) en este turno
          </Text>
          {serviciosArchivados > 0 && (
            <Text style={styles.turnoInfoSubtext}>
              {serviciosArchivados} servicio(s) archivados
            </Text>
          )}
        </View>
      )}

      {/* Boton para ver/ocultar historial */}
      {turnoActivo && serviciosArchivados > 0 && (
        <View style={styles.historialButtonContainer}>
          <Button
            mode={mostrarHistorial ? "contained" : "outlined"}
            onPress={() => setMostrarHistorial(!mostrarHistorial)}
            icon={mostrarHistorial ? "eye-off" : "history"}
            style={styles.historialButton}
          >
            {mostrarHistorial ? 'Ocultar historial' : `Ver historial (${serviciosArchivados})`}
          </Button>
        </View>
      )}

      {/* Vista normal: solo servicios del turno activo en FlatList */}
      {turnoActivo && !mostrarHistorial ? (
        <FlatList
          data={getServiciosFiltrados()}
          renderItem={renderService}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.list}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={['#0066CC']} />
          }
          ListEmptyComponent={
            <View style={styles.emptyContainer}>
              <Text variant="bodyLarge" style={styles.emptyText}>
                No hay servicios en este turno
              </Text>
            </View>
          }
        />
      ) : (
        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={['#0066CC']} />
          }
        >
          {getServiciosFiltrados().length === 0 ? (
            <View style={styles.emptyContainer}>
              <Text variant="bodyLarge" style={styles.emptyText}>
                {mostrarHistorial 
                  ? 'No hay servicios en el historial' 
                  : 'No hay servicios registrados'}
              </Text>
            </View>
          ) : (
            agruparPorFecha(getServiciosFiltrados()).map((grupo) => (
              <List.Accordion
                key={grupo.fecha}
                title={grupo.fecha}
                description={`${grupo.servicios.length} servicio(s)`}
                left={props => <List.Icon {...props} icon="calendar" />}
                expanded={expandedDates[grupo.fecha] || false}
                onPress={() => setExpandedDates({
                  ...expandedDates,
                  [grupo.fecha]: !expandedDates[grupo.fecha]
                })}
                style={styles.accordion}
              >
                {grupo.servicios.map((servicio) => (
                  <View key={servicio.id}>
                    {renderService({ item: servicio })}
                  </View>
                ))}
              </List.Accordion>
            ))
          )}
        </ScrollView>
      )}
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
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  syncBannerContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  syncText: {
    color: '#333',
    fontWeight: '600',
    flex: 1,
  },
  syncActions: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  pendingListContainer: {
    backgroundColor: '#FFF8E1',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#FFD700',
  },
  pendingCard: {
    marginBottom: 8,
    backgroundColor: '#FFFFFF',
    elevation: 1,
  },
  pendingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  pendingRoute: {
    fontWeight: '600',
    flex: 1,
  },
  pendingMeta: {
    color: '#666',
  },
  pendingError: {
    color: '#D32F2F',
    marginTop: 4,
  },
  chipPending: {
    backgroundColor: '#FF9800',
  },
  chipFailed: {
    backgroundColor: '#D32F2F',
  },
  chipTextWhite: {
    color: '#FFFFFF',
    fontSize: 11,
  },
  turnoInfoBanner: {
    backgroundColor: '#E3F2FD',
    padding: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#0066CC',
  },
  turnoInfoText: {
    color: '#0066CC',
    fontWeight: '600',
    fontSize: 14,
  },
  turnoInfoSubtext: {
    color: '#666',
    fontSize: 12,
    marginTop: 4,
  },
  historialButtonContainer: {
    padding: 12,
    backgroundColor: '#F5F5F5',
  },
  historialButton: {
    borderColor: '#0066CC',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 80,
  },
  accordion: {
    backgroundColor: 'white',
    marginBottom: 1,
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
  statusChipsContainer: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 12,
    flexWrap: 'wrap',
  },
  chipCobrado: {
    backgroundColor: '#4CAF50',
  },
  chipFacturar: {
    backgroundColor: '#FF9800',
  },
  chipText: {
    color: '#FFFFFF',
    fontWeight: '600',
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
