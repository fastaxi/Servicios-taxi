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
  FAB,
  Switch,
  Menu,
} from 'react-native-paper';
import { useAuth } from '../../contexts/AuthContext';
import { useFocusEffect } from 'expo-router';
import axios from 'axios';
import { format } from 'date-fns';
import IniciarTurnoModal from '../../components/IniciarTurnoModal';

import { API_URL } from '../../config/api';

interface Vehiculo {
  id: string;
  matricula: string;
  marca: string;
  modelo: string;
}

interface Combustible {
  repostado: boolean;
  litros?: number;
  vehiculo_id?: string;
  vehiculo_matricula?: string;
  km_vehiculo?: number;
  timestamp?: string;
}

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
  vehiculo_id: string;
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
  combustible?: Combustible;
}

export default function TurnosScreen() {
  const { token, user } = useAuth();
  const [turnos, setTurnos] = useState<Turno[]>([]);
  const [turnoActivo, setTurnoActivo] = useState<Turno | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [finalizarModalVisible, setFinalizarModalVisible] = useState(false);
  const [iniciarTurnoModalVisible, setIniciarTurnoModalVisible] = useState(false);
  const [kmFin, setKmFin] = useState('');
  const [expandedTurnos, setExpandedTurnos] = useState<{ [key: string]: boolean }>({});
  const [serviciosPorTurno, setServiciosPorTurno] = useState<{ [key: string]: Servicio[] }>({});
  const [snackbar, setSnackbar] = useState({ visible: false, message: '' });

  // PR2: Estados para combustible
  const [combustibleRepostado, setCombustibleRepostado] = useState(false);
  const [combustibleLitros, setCombustibleLitros] = useState('');
  const [combustibleVehiculoId, setCombustibleVehiculoId] = useState('');
  const [combustibleVehiculoMatricula, setCombustibleVehiculoMatricula] = useState('');
  const [combustibleKm, setCombustibleKm] = useState('');
  const [combustibleMenuVisible, setCombustibleMenuVisible] = useState(false);
  const [vehiculos, setVehiculos] = useState<Vehiculo[]>([]);
  const [combustibleLoading, setCombustibleLoading] = useState(false);

  useEffect(() => {
    loadTurnos();
    loadVehiculos();
  }, []);

  useFocusEffect(
    React.useCallback(() => {
      loadTurnos();
    }, [])
  );

  // Cargar datos de combustible cuando hay turno activo
  useEffect(() => {
    if (turnoActivo?.combustible) {
      setCombustibleRepostado(turnoActivo.combustible.repostado || false);
      setCombustibleLitros(turnoActivo.combustible.litros?.toString() || '');
      setCombustibleVehiculoId(turnoActivo.combustible.vehiculo_id || '');
      setCombustibleVehiculoMatricula(turnoActivo.combustible.vehiculo_matricula || '');
      setCombustibleKm(turnoActivo.combustible.km_vehiculo?.toString() || '');
    } else {
      setCombustibleRepostado(false);
      setCombustibleLitros('');
      setCombustibleVehiculoId('');
      setCombustibleVehiculoMatricula('');
      setCombustibleKm('');
    }
  }, [turnoActivo]);

  const loadVehiculos = async () => {
    try {
      const response = await axios.get(`${API_URL}/vehiculos`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setVehiculos(response.data);
    } catch (error) {
      console.error('Error loading vehiculos:', error);
    }
  };

  const loadTurnos = async () => {
    try {
      const response = await axios.get(`${API_URL}/turnos`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      const activo = response.data.find((t: Turno) => !t.cerrado);
      setTurnoActivo(activo || null);
      
      // Ordenar turnos del mas reciente al mas antiguo
      const turnosOrdenados = response.data.sort((a: Turno, b: Turno) => {
        const fechaHoraA = `${a.fecha_inicio} ${a.hora_inicio}`;
        const fechaHoraB = `${b.fecha_inicio} ${b.hora_inicio}`;
        return fechaHoraB.localeCompare(fechaHoraA);
      });
      
      setTurnos(turnosOrdenados);
    } catch (error) {
      console.error('Error loading turnos:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadTurnos();
    setRefreshing(false);
  };

  const loadServiciosTurno = async (turnoId: string) => {
    try {
      const response = await axios.get(`${API_URL}/services?turno_id=${turnoId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setServiciosPorTurno(prev => ({ ...prev, [turnoId]: response.data }));
    } catch (error) {
      console.error('Error loading servicios:', error);
    }
  };

  const toggleTurnoExpanded = (turnoId: string) => {
    const isExpanding = !expandedTurnos[turnoId];
    setExpandedTurnos(prev => ({ ...prev, [turnoId]: isExpanding }));
    
    if (isExpanding && !serviciosPorTurno[turnoId]) {
      loadServiciosTurno(turnoId);
    }
  };

  // PR2: Guardar combustible
  const handleGuardarCombustible = async () => {
    if (!turnoActivo) return;

    if (combustibleRepostado) {
      const litros = parseFloat(combustibleLitros);
      const km = parseInt(combustibleKm);
      
      if (isNaN(litros) || litros <= 0) {
        setSnackbar({ visible: true, message: 'Los litros deben ser un numero mayor que 0' });
        return;
      }
      if (!combustibleVehiculoId) {
        setSnackbar({ visible: true, message: 'Selecciona un vehiculo para el repostaje' });
        return;
      }
      if (isNaN(km) || km < 0) {
        setSnackbar({ visible: true, message: 'Los kilometros deben ser un numero valido >= 0' });
        return;
      }
    }

    setCombustibleLoading(true);
    try {
      await axios.put(
        `${API_URL}/turnos/${turnoActivo.id}/combustible`,
        {
          repostado: combustibleRepostado,
          litros: combustibleRepostado ? parseFloat(combustibleLitros) : null,
          vehiculo_id: combustibleRepostado ? combustibleVehiculoId : null,
          km_vehiculo: combustibleRepostado ? parseInt(combustibleKm) : null,
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setSnackbar({ visible: true, message: 'Repostaje guardado correctamente' });
      loadTurnos();
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Error al guardar repostaje';
      setSnackbar({ visible: true, message: errorMsg });
    } finally {
      setCombustibleLoading(false);
    }
  };

  // PR2: Finalizar turno - sin enviar hora (el servidor la pone)
  const handleFinalizarTurno = async () => {
    if (!kmFin || !turnoActivo) {
      setSnackbar({ visible: true, message: 'Por favor, ingresa los kilometros finales' });
      return;
    }

    const kmNum = parseInt(kmFin);
    if (isNaN(kmNum) || kmNum < turnoActivo.km_inicio) {
      setSnackbar({ 
        visible: true, 
        message: 'Los kilometros finales deben ser mayores a los iniciales' 
      });
      return;
    }

    try {
      // PR2: NO enviar hora_fin - el servidor usa su propia hora
      await axios.put(
        `${API_URL}/turnos/${turnoActivo.id}/finalizar`,
        {
          fecha_fin: format(new Date(), 'dd/MM/yyyy'),
          hora_fin: "00:00", // El servidor lo ignora y usa su hora
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

  const handleTurnoIniciado = () => {
    setIniciarTurnoModalVisible(false);
    loadTurnos();
  };

  return (
    <View style={styles.container}>
      {/* Banner si no hay turno activo */}
      {!turnoActivo && (
        <View style={styles.sinTurnoBanner}>
          <Text variant="titleMedium" style={styles.sinTurnoText}>
            No hay turno activo
          </Text>
          <Text variant="bodySmall" style={styles.sinTurnoSubtext}>
            Inicia un turno para registrar nuevos servicios
          </Text>
          <Button
            mode="contained"
            onPress={() => setIniciarTurnoModalVisible(true)}
            icon="plus-circle"
            style={styles.iniciarTurnoButton}
          >
            Iniciar Turno
          </Button>
        </View>
      )}

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
                <Text variant="bodyMedium" style={styles.label}>Vehiculo:</Text>
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

              {/* PR2: Seccion Combustible */}
              <View style={styles.combustibleSection}>
                <Text variant="titleMedium" style={styles.combustibleTitle}>
                  ⛽ Combustible
                </Text>
                
                <View style={styles.switchRow}>
                  <Text variant="bodyMedium">He repostado</Text>
                  <Switch
                    value={combustibleRepostado}
                    onValueChange={setCombustibleRepostado}
                    color="#0066CC"
                  />
                </View>

                {combustibleRepostado && (
                  <View style={styles.combustibleForm}>
                    <TextInput
                      label="Litros *"
                      value={combustibleLitros}
                      onChangeText={setCombustibleLitros}
                      mode="outlined"
                      keyboardType="decimal-pad"
                      style={styles.combustibleInput}
                      placeholder="0.00"
                    />
                    
                    <Menu
                      visible={combustibleMenuVisible}
                      onDismiss={() => setCombustibleMenuVisible(false)}
                      anchor={
                        <Button
                          mode="outlined"
                          onPress={() => setCombustibleMenuVisible(true)}
                          icon="car"
                          style={styles.combustibleInput}
                        >
                          {combustibleVehiculoMatricula || 'Seleccionar vehiculo *'}
                        </Button>
                      }
                    >
                      {vehiculos.map((vehiculo) => (
                        <Menu.Item
                          key={vehiculo.id}
                          onPress={() => {
                            setCombustibleVehiculoId(vehiculo.id);
                            setCombustibleVehiculoMatricula(vehiculo.matricula);
                            setCombustibleMenuVisible(false);
                          }}
                          title={`${vehiculo.matricula} - ${vehiculo.marca} ${vehiculo.modelo}`}
                        />
                      ))}
                    </Menu>

                    <TextInput
                      label="KM del vehiculo *"
                      value={combustibleKm}
                      onChangeText={setCombustibleKm}
                      mode="outlined"
                      keyboardType="number-pad"
                      style={styles.combustibleInput}
                      placeholder="0"
                    />
                  </View>
                )}

                <Button
                  mode="contained-tonal"
                  onPress={handleGuardarCombustible}
                  loading={combustibleLoading}
                  disabled={combustibleLoading}
                  style={styles.combustibleButton}
                  icon="gas-station"
                >
                  Guardar Repostaje
                </Button>

                {turnoActivo.combustible?.repostado && (
                  <View style={styles.combustibleGuardado}>
                    <Text variant="bodySmall" style={styles.combustibleGuardadoText}>
                      ✅ Último repostaje: {turnoActivo.combustible.litros} L en {turnoActivo.combustible.vehiculo_matricula}
                    </Text>
                  </View>
                )}
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

                  {/* Mostrar combustible si hubo repostaje */}
                  {turno.combustible?.repostado && (
                    <View style={styles.infoRow}>
                      <Text variant="bodySmall" style={styles.label}>⛽ Repostaje:</Text>
                      <Text variant="bodySmall">
                        {turno.combustible.litros} L ({turno.combustible.vehiculo_matricula})
                      </Text>
                    </View>
                  )}

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

                  {/* Boton para expandir/contraer servicios */}
                  <Button
                    mode="text"
                    onPress={() => toggleTurnoExpanded(turno.id)}
                    icon={expandedTurnos[turno.id] ? 'chevron-up' : 'chevron-down'}
                    style={styles.expandButton}
                  >
                    {expandedTurnos[turno.id] ? 'Ocultar servicios' : 'Ver servicios'}
                  </Button>

                  {/* Lista de servicios expandible */}
                  {expandedTurnos[turno.id] && (
                    <View style={styles.serviciosContainer}>
                      <Divider style={styles.serviciosDivider} />
                      <Text variant="titleSmall" style={styles.serviciosTitle}>
                        Servicios del turno
                      </Text>
                      
                      {serviciosPorTurno[turno.id] ? (
                        serviciosPorTurno[turno.id].length > 0 ? (
                          serviciosPorTurno[turno.id].map((servicio, index) => (
                            <View key={servicio.id} style={styles.servicioItem}>
                              <View style={styles.servicioHeader}>
                                <Text variant="bodySmall" style={styles.servicioNumero}>
                                  Servicio #{index + 1}
                                </Text>
                                <Chip 
                                  mode="flat" 
                                  compact 
                                  style={servicio.tipo === 'empresa' ? styles.chipEmpresa : styles.chipParticular}
                                >
                                  {servicio.tipo === 'empresa' ? 'Cliente' : 'Particular'}
                                </Chip>
                              </View>
                              
                              <Text variant="bodySmall" style={styles.servicioDetalle}>
                                📅 {servicio.fecha} {servicio.hora}
                              </Text>
                              <Text variant="bodySmall" style={styles.servicioDetalle}>
                                📍 {servicio.origen} → {servicio.destino}
                              </Text>
                              <Text variant="bodySmall" style={styles.servicioDetalle}>
                                🚗 {servicio.kilometros || 'N/A'} km
                              </Text>
                              {servicio.empresa_nombre && (
                                <Text variant="bodySmall" style={styles.servicioDetalle}>
                                  🏢 {servicio.empresa_nombre}
                                </Text>
                              )}
                              <View style={styles.servicioImportes}>
                                <Text variant="bodySmall">Servicio: {formatEuro(servicio.importe)}</Text>
                                {servicio.importe_espera > 0 && (
                                  <Text variant="bodySmall">Espera: {formatEuro(servicio.importe_espera)}</Text>
                                )}
                                <Text variant="bodyMedium" style={styles.servicioTotal}>
                                  Total: {formatEuro(servicio.importe_total)}
                                </Text>
                              </View>
                              
                              {index < serviciosPorTurno[turno.id].length - 1 && (
                                <Divider style={styles.servicioItemDivider} />
                              )}
                            </View>
                          ))
                        ) : (
                          <Text variant="bodySmall" style={styles.emptyServiciosText}>
                            No hay servicios en este turno
                          </Text>
                        )
                      ) : (
                        <Text variant="bodySmall" style={styles.loadingText}>
                          Cargando servicios...
                        </Text>
                      )}
                    </View>
                  )}
                </Card.Content>
              </Card>
            ))
        )}
      </ScrollView>

      {/* PR2: Modal finalizar turno - sin campo de hora */}
      <Portal>
        <Dialog visible={finalizarModalVisible} onDismiss={() => setFinalizarModalVisible(false)}>
          <Dialog.Title>Finalizar Turno</Dialog.Title>
          <Dialog.Content>
            <Text variant="bodyMedium" style={styles.dialogText}>
              Ingresa los kilometros finales del vehiculo
            </Text>
            
            {/* PR2: Info sobre hora automatica */}
            <View style={styles.serverTimeInfo}>
              <Text variant="bodySmall" style={styles.serverTimeText}>
                ⏰ La hora de finalizacion se registrará automaticamente del servidor
              </Text>
            </View>

            <TextInput
              label="Kilometros finales *"
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

      {/* Modal de iniciar turno */}
      <IniciarTurnoModal
        visible={iniciarTurnoModalVisible}
        userId={user?.id || ''}
        userName={user?.nombre || ''}
        token={token || ''}
        onTurnoIniciado={handleTurnoIniciado}
        onCancel={() => setIniciarTurnoModalVisible(false)}
      />

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
  sinTurnoBanner: {
    backgroundColor: '#FFF3E0',
    padding: 20,
    alignItems: 'center',
    borderBottomWidth: 2,
    borderBottomColor: '#FF9800',
  },
  sinTurnoText: {
    color: '#E65100',
    fontWeight: 'bold',
    marginBottom: 4,
  },
  sinTurnoSubtext: {
    color: '#666',
    marginBottom: 12,
    textAlign: 'center',
  },
  iniciarTurnoButton: {
    marginTop: 8,
    backgroundColor: '#FF9800',
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
  expandButton: {
    marginTop: 12,
  },
  serviciosContainer: {
    marginTop: 8,
    backgroundColor: '#F9F9F9',
    borderRadius: 8,
    padding: 12,
  },
  serviciosDivider: {
    marginBottom: 12,
    backgroundColor: '#0066CC',
    height: 2,
  },
  serviciosTitle: {
    fontWeight: 'bold',
    marginBottom: 12,
    color: '#0066CC',
  },
  servicioItem: {
    marginBottom: 8,
  },
  servicioHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  servicioNumero: {
    fontWeight: 'bold',
    color: '#333',
  },
  chipEmpresa: {
    backgroundColor: '#E3F2FD',
  },
  chipParticular: {
    backgroundColor: '#FFF9C4',
  },
  servicioDetalle: {
    marginTop: 4,
    color: '#666',
  },
  servicioImportes: {
    marginTop: 8,
    padding: 8,
    backgroundColor: '#FFFFFF',
    borderRadius: 4,
    borderLeftWidth: 3,
    borderLeftColor: '#0066CC',
  },
  servicioTotal: {
    fontWeight: 'bold',
    color: '#4CAF50',
    marginTop: 4,
  },
  servicioItemDivider: {
    marginTop: 12,
    marginBottom: 8,
    backgroundColor: '#E0E0E0',
  },
  emptyServiciosText: {
    textAlign: 'center',
    color: '#999',
    padding: 16,
  },
  loadingText: {
    textAlign: 'center',
    color: '#666',
    padding: 16,
  },
  // PR2: Estilos para combustible
  combustibleSection: {
    marginTop: 16,
    padding: 12,
    backgroundColor: '#FFF8E1',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#FFB300',
  },
  combustibleTitle: {
    color: '#FF8F00',
    fontWeight: 'bold',
    marginBottom: 12,
  },
  switchRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  combustibleForm: {
    marginBottom: 8,
  },
  combustibleInput: {
    marginBottom: 8,
    backgroundColor: 'white',
  },
  combustibleButton: {
    marginTop: 8,
  },
  combustibleGuardado: {
    marginTop: 8,
    padding: 8,
    backgroundColor: '#E8F5E9',
    borderRadius: 4,
  },
  combustibleGuardadoText: {
    color: '#2E7D32',
    textAlign: 'center',
  },
  serverTimeInfo: {
    backgroundColor: '#E3F2FD',
    padding: 12,
    borderRadius: 8,
    marginBottom: 12,
  },
  serverTimeText: {
    color: '#0066CC',
    textAlign: 'center',
  },
});
