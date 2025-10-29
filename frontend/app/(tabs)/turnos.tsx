import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ScrollView, RefreshControl } from 'react-native';
import {
  Text,
  Card,
  Button,
  Portal,
  Dialog,
  TextInput,
  Chip,
  Snackbar,
  List,
  Divider,
} from 'react-native-paper';
import { useAuth } from '../../contexts/AuthContext';
import { useFocusEffect } from 'expo-router';
import axios from 'axios';
import { format } from 'date-fns';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL + '/api';

interface Servicio {
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
}

interface Turno {
  id: string;
  taxista_nombre: string;
  vehiculo_matricula: string;
  fecha_inicio: string;
  hora_inicio: string;
  km_inicio: number;
  fecha_fin?: string;
  hora_fin?: string;
  km_fin?: number;
  cerrado: boolean;
  total_importe_clientes: number;
  total_importe_particulares: number;
  total_kilometros: number;
  cantidad_servicios: number;
}

export default function TurnosScreen() {
  const { token } = useAuth();
  const [turnos, setTurnos] = useState<Turno[]>([]);
  const [turnoActivo, setTurnoActivo] = useState<Turno | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [finalizarModalVisible, setFinalizarModalVisible] = useState(false);
  const [kmFin, setKmFin] = useState('');
  const [horaFin, setHoraFin] = useState('');
  const [expandedTurnos, setExpandedTurnos] = useState<{ [key: string]: boolean }>({});
  const [serviciosPorTurno, setServiciosPorTurno] = useState<{ [key: string]: Servicio[] }>({});
  const [snackbar, setSnackbar] = useState({ visible: false, message: '' });

  useEffect(() => {
    loadTurnos();
  }, []);

  useFocusEffect(
    React.useCallback(() => {
      loadTurnos();
    }, [])
  );

  const loadTurnos = async () => {
    try {
      const response = await axios.get(`${API_URL}/turnos`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      const activo = response.data.find((t: Turno) => !t.cerrado);
      setTurnoActivo(activo || null);
      setTurnos(response.data);
    } catch (error) {
      console.error('Error loading turnos:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadTurnos();
    setRefreshing(false);
  };

  const handleFinalizarTurno = async () => {
    if (!kmFin || !turnoActivo) {
      setSnackbar({ visible: true, message: 'Por favor, ingresa los kilómetros finales' });
      return;
    }

    const kmNum = parseInt(kmFin);
    if (isNaN(kmNum) || kmNum < turnoActivo.km_inicio) {
      setSnackbar({ 
        visible: true, 
        message: 'Los kilómetros finales deben ser mayores a los iniciales' 
      });
      return;
    }

    try {
      await axios.put(
        `${API_URL}/turnos/${turnoActivo.id}/finalizar`,
        {
          fecha_fin: format(new Date(), 'dd/MM/yyyy'),
          hora_fin: format(new Date(), 'HH:mm'),
          km_fin: kmNum,
          cerrado: true,
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setFinalizarModalVisible(false);
      setKmFin('');
      setSnackbar({ visible: true, message: 'Turno finalizado correctamente' });
      loadTurnos();
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Error al finalizar turno';
      setSnackbar({ visible: true, message: errorMsg });
    }
  };

  const formatEuro = (amount: number) => {
    return amount.toFixed(2).replace('.', ',') + ' €';
  };

  return (
    <View style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={['#0066CC']} />
        }
      >
        {turnoActivo && (
          <Card style={[styles.card, styles.turnoActivoCard]}>
            <Card.Content>
              <View style={styles.header}>
                <Text variant="titleLarge" style={styles.turnoActivoTitle}>
                  Turno Activo
                </Text>
                <Chip mode="flat" style={styles.activoChip}>
                  En curso
                </Chip>
              </View>

              <View style={styles.infoRow}>
                <Text variant="bodyMedium" style={styles.label}>Vehículo:</Text>
                <Text variant="bodyMedium">🚗 {turnoActivo.vehiculo_matricula}</Text>
              </View>

              <View style={styles.infoRow}>
                <Text variant="bodyMedium" style={styles.label}>Inicio:</Text>
                <Text variant="bodyMedium">
                  {turnoActivo.fecha_inicio} {turnoActivo.hora_inicio}
                </Text>
              </View>

              <View style={styles.infoRow}>
                <Text variant="bodyMedium" style={styles.label}>KM Inicial:</Text>
                <Text variant="bodyMedium">{turnoActivo.km_inicio} km</Text>
              </View>

              <View style={styles.divider} />

              <View style={styles.infoRow}>
                <Text variant="bodyMedium" style={styles.label}>Servicios:</Text>
                <Text variant="bodyMedium">{turnoActivo.cantidad_servicios}</Text>
              </View>

              <View style={styles.infoRow}>
                <Text variant="bodyMedium" style={styles.label}>Importe Clientes:</Text>
                <Text variant="bodyMedium">{formatEuro(turnoActivo.total_importe_clientes)}</Text>
              </View>

              <View style={styles.infoRow}>
                <Text variant="bodyMedium" style={styles.label}>Importe Particulares:</Text>
                <Text variant="bodyMedium">{formatEuro(turnoActivo.total_importe_particulares)}</Text>
              </View>

              <View style={styles.infoRow}>
                <Text variant="bodyMedium" style={styles.label}>KM del Turno:</Text>
                <Text variant="bodyMedium">{turnoActivo.total_kilometros} km</Text>
              </View>

              <Button
                mode="contained"
                onPress={() => setFinalizarModalVisible(true)}
                style={styles.finalizarButton}
                buttonColor="#D32F2F"
              >
                Finalizar Turno
              </Button>
            </Card.Content>
          </Card>
        )}

        <Text variant="titleMedium" style={styles.sectionTitle}>
          Historial de Turnos
        </Text>

        {turnos.filter(t => t.cerrado).length === 0 ? (
          <View style={styles.emptyContainer}>
            <Text variant="bodyLarge" style={styles.emptyText}>
              No hay turnos finalizados
            </Text>
          </View>
        ) : (
          turnos
            .filter(t => t.cerrado)
            .map((turno) => (
              <Card key={turno.id} style={styles.card}>
                <Card.Content>
                  <View style={styles.header}>
                    <Text variant="titleMedium">
                      🚗 {turno.vehiculo_matricula}
                    </Text>
                    <Chip mode="outlined" compact>Cerrado</Chip>
                  </View>

                  <View style={styles.infoRow}>
                    <Text variant="bodySmall" style={styles.label}>Inicio:</Text>
                    <Text variant="bodySmall">
                      {turno.fecha_inicio} {turno.hora_inicio}
                    </Text>
                  </View>

                  <View style={styles.infoRow}>
                    <Text variant="bodySmall" style={styles.label}>Fin:</Text>
                    <Text variant="bodySmall">
                      {turno.fecha_fin} {turno.hora_fin}
                    </Text>
                  </View>

                  <View style={styles.infoRow}>
                    <Text variant="bodySmall" style={styles.label}>KM:</Text>
                    <Text variant="bodySmall">
                      {turno.km_inicio} → {turno.km_fin} ({turno.km_fin! - turno.km_inicio} km)
                    </Text>
                  </View>

                  <View style={styles.divider} />

                  <View style={styles.infoRow}>
                    <Text variant="bodySmall" style={styles.label}>Servicios:</Text>
                    <Text variant="bodySmall">{turno.cantidad_servicios}</Text>
                  </View>

                  <View style={styles.infoRow}>
                    <Text variant="bodySmall" style={styles.label}>Clientes:</Text>
                    <Text variant="bodySmall" style={styles.importeText}>
                      {formatEuro(turno.total_importe_clientes)}
                    </Text>
                  </View>

                  <View style={styles.infoRow}>
                    <Text variant="bodySmall" style={styles.label}>Particulares:</Text>
                    <Text variant="bodySmall" style={styles.importeText}>
                      {formatEuro(turno.total_importe_particulares)}
                    </Text>
                  </View>

                  <View style={styles.infoRow}>
                    <Text variant="bodySmall" style={styles.label}>Total:</Text>
                    <Text variant="bodyMedium" style={styles.totalText}>
                      {formatEuro(turno.total_importe_clientes + turno.total_importe_particulares)}
                    </Text>
                  </View>
                </Card.Content>
              </Card>
            ))
        )}
      </ScrollView>

      <Portal>
        <Dialog visible={finalizarModalVisible} onDismiss={() => setFinalizarModalVisible(false)}>
          <Dialog.Title>Finalizar Turno</Dialog.Title>
          <Dialog.Content>
            <Text variant="bodyMedium" style={styles.dialogText}>
              Ingresa los kilómetros finales del vehículo
            </Text>
            <TextInput
              label="Kilómetros finales *"
              value={kmFin}
              onChangeText={setKmFin}
              mode="outlined"
              keyboardType="number-pad"
              style={styles.input}
            />
          </Dialog.Content>
          <Dialog.Actions>
            <Button onPress={() => setFinalizarModalVisible(false)}>Cancelar</Button>
            <Button onPress={handleFinalizarTurno}>Finalizar</Button>
          </Dialog.Actions>
        </Dialog>
      </Portal>

      <Snackbar
        visible={snackbar.visible}
        onDismiss={() => setSnackbar({ ...snackbar, visible: false })}
        duration={3000}
      >
        {snackbar.message}
      </Snackbar>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  scrollView: {
    flex: 1,
  },
  card: {
    margin: 8,
    marginHorizontal: 16,
    backgroundColor: 'white',
    elevation: 2,
  },
  turnoActivoCard: {
    backgroundColor: '#E3F2FD',
    borderWidth: 2,
    borderColor: '#0066CC',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  turnoActivoTitle: {
    color: '#0066CC',
    fontWeight: 'bold',
  },
  activoChip: {
    backgroundColor: '#4CAF50',
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
  divider: {
    height: 1,
    backgroundColor: '#E0E0E0',
    marginVertical: 12,
  },
  finalizarButton: {
    marginTop: 16,
  },
  sectionTitle: {
    marginTop: 16,
    marginBottom: 8,
    marginHorizontal: 16,
    fontWeight: 'bold',
  },
  emptyContainer: {
    padding: 32,
    alignItems: 'center',
  },
  emptyText: {
    color: '#999',
    textAlign: 'center',
  },
  dialogText: {
    marginBottom: 16,
  },
  input: {
    marginTop: 8,
  },
  importeText: {
    color: '#0066CC',
    fontWeight: '600',
  },
  totalText: {
    color: '#4CAF50',
    fontWeight: 'bold',
    fontSize: 16,
  },
});
