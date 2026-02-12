import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ScrollView, RefreshControl, TouchableOpacity, Platform } from 'react-native';
import {
  Text,
  Card,
  Button,
  Portal,
  Dialog,
  TextInput,
  Chip,
  Snackbar,
  Menu,
  FAB,
  Divider,
  SegmentedButtons,
  DataTable,
} from 'react-native-paper';
import { useAuth } from '../../contexts/AuthContext';
import { useFocusEffect } from 'expo-router';
import axios from 'axios';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import * as FileSystem from 'expo-file-system/legacy';
import * as Sharing from 'expo-sharing';
import { encode as base64Encode } from 'base-64';

import { API_URL } from '../../config/api';

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
  cobrado?: boolean;
  facturar?: boolean;
  vehiculo_matricula?: string;
  metodo_pago?: string;
}

interface Turno {
  id: string;
  taxista_id: string;
  taxista_nombre: string;
  vehiculo_matricula: string;
  fecha_inicio: string;
  hora_inicio: string;
  km_inicio: number;
  fecha_fin?: string;
  hora_fin?: string;
  km_fin?: number;
  cerrado: boolean;
  liquidado: boolean;
  total_importe_clientes: number;
  total_importe_particulares: number;
  total_kilometros: number;
  cantidad_servicios: number;
  // Combustible/Repostaje
  combustible?: {
    repostado: boolean;
    litros?: number;
    vehiculo_id?: string;
    vehiculo_matricula?: string;
    km_vehiculo?: number;
    fecha?: string;
    hora?: string;
  };
}

interface Taxista {
  id: string;
  nombre: string;
  username: string;
}

interface Vehiculo {
  id: string;
  matricula: string;
  marca: string;
  modelo: string;
}

interface Estadisticas {
  total_turnos: number;
  turnos_activos: number;
  turnos_cerrados: number;
  turnos_liquidados: number;
  turnos_pendiente_liquidacion: number;
  total_importe: number;
  total_kilometros: number;
  total_servicios: number;
  promedio_importe_por_turno: number;
  promedio_servicios_por_turno: number;
}

export default function AdminTurnosScreen() {
  const { token } = useAuth();
  const [turnos, setTurnos] = useState<Turno[]>([]);
  const [taxistas, setTaxistas] = useState<Taxista[]>([]);
  const [vehiculos, setVehiculos] = useState<Vehiculo[]>([]);
  const [estadisticas, setEstadisticas] = useState<Estadisticas | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [vistaActual, setVistaActual] = useState('lista'); // 'lista', 'tabla', 'estadisticas'
  
  // Filtros
  const [filtroTaxista, setFiltroTaxista] = useState('');
  const [filtroTaxistaNombre, setFiltroTaxistaNombre] = useState('Todos');
  const [filtroVehiculo, setFiltroVehiculo] = useState('');
  const [filtroEstado, setFiltroEstado] = useState('todos'); // 'todos', 'activos', 'cerrados', 'liquidados'
  
  // Modales
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [finalizarModalVisible, setFinalizarModalVisible] = useState(false);
  const [exportMenuVisible, setExportMenuVisible] = useState(false);
  const [deleteConfirmVisible, setDeleteConfirmVisible] = useState(false);
  const [turnoSeleccionado, setTurnoSeleccionado] = useState<Turno | null>(null);
  
  // Estados expandibles
  const [expandedTurnos, setExpandedTurnos] = useState<{ [key: string]: boolean }>({});
  const [serviciosPorTurno, setServiciosPorTurno] = useState<{ [key: string]: Servicio[] }>({});
  
  // Form states
  const [editForm, setEditForm] = useState({
    fecha_inicio: '',
    hora_inicio: '',
    km_inicio: '',
    fecha_fin: '',
    hora_fin: '',
    km_fin: '',
    cerrado: false,
    liquidado: false,
  });
  const [kmFin, setKmFin] = useState('');
  const [horaFin, setHoraFin] = useState('');
  
  // Menus
  const [taxistaMenuVisible, setTaxistaMenuVisible] = useState(false);
  
  const [snackbar, setSnackbar] = useState({ visible: false, message: '' });

  useEffect(() => {
    if (token) {
      loadData();
    }
  }, [token]);

  useFocusEffect(
    React.useCallback(() => {
      if (token) {
        loadData();
      }
    }, [token])
  );

  const loadData = async () => {
    await Promise.all([
      loadTurnos(),
      loadTaxistas(),
      loadVehiculos(),
      loadEstadisticas(),
    ]);
  };

  const loadTurnos = async () => {
    try {
      const params: any = {};
      if (filtroTaxista) params.taxista_id = filtroTaxista;
      
      // Filtros por estado
      if (filtroEstado === 'activos') {
        params.cerrado = false;
      } else if (filtroEstado === 'cerrados') {
        params.cerrado = true;
        params.liquidado = false;  // Solo cerrados pero no liquidados
      } else if (filtroEstado === 'liquidados') {
        params.cerrado = true;
        params.liquidado = true;
      }
      // Si filtroEstado === 'todos', no agregar ningún filtro de estado
      
      const response = await axios.get(`${API_URL}/turnos`, {
        headers: { Authorization: `Bearer ${token}` },
        params,
      });
      
      // Ordenar del mas reciente al mas antiguo
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

  const loadTaxistas = async () => {
    try {
      const response = await axios.get(`${API_URL}/users`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setTaxistas(response.data);
    } catch (error) {
      console.error('Error loading taxistas:', error);
    }
  };

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

  const loadEstadisticas = async () => {
    try {
      const response = await axios.get(`${API_URL}/turnos/estadisticas`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setEstadisticas(response.data);
    } catch (error) {
      console.error('Error loading estadisticas:', error);
    }
  };

  const loadServiciosTurno = async (turnoId: string) => {
    try {
      console.log('Cargando servicios para turno:', turnoId);
      
      // Primero intentar con turno_id
      let response = await axios.get(`${API_URL}/services?turno_id=${turnoId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      console.log('Servicios con turno_id:', response.data.length);
      
      // Si no hay servicios con turno_id, buscar por taxista y fecha
      if (response.data.length === 0) {
        const turno = turnos.find(t => t.id === turnoId);
        if (turno) {
          console.log('Buscando servicios por taxista y fecha:', turno.taxista_id, turno.fecha_inicio);
          response = await axios.get(
            `${API_URL}/services?taxista_id=${turno.taxista_id}`, 
            { headers: { Authorization: `Bearer ${token}` } }
          );
          
          // Filtrar manualmente por fecha del turno
          const serviciosFiltrados = response.data.filter((s: Servicio) => {
            return s.fecha === turno.fecha_inicio;
          });
          
          console.log('Servicios filtrados por fecha:', serviciosFiltrados.length);
          setServiciosPorTurno(prev => ({ ...prev, [turnoId]: serviciosFiltrados }));
          return;
        }
      }
      
      setServiciosPorTurno(prev => ({ ...prev, [turnoId]: response.data }));
    } catch (error) {
      console.error('Error loading servicios:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const toggleTurnoExpanded = (turnoId: string) => {
    const isExpanding = !expandedTurnos[turnoId];
    setExpandedTurnos(prev => ({ ...prev, [turnoId]: isExpanding }));
    
    if (isExpanding && !serviciosPorTurno[turnoId]) {
      loadServiciosTurno(turnoId);
    }
  };

  const handleEditTurno = (turno: Turno) => {
    setTurnoSeleccionado(turno);
    setEditForm({
      fecha_inicio: turno.fecha_inicio,
      hora_inicio: turno.hora_inicio,
      km_inicio: turno.km_inicio.toString(),
      fecha_fin: turno.fecha_fin || '',
      hora_fin: turno.hora_fin || '',
      km_fin: turno.km_fin?.toString() || '',
      cerrado: turno.cerrado,
      liquidado: turno.liquidado,
    });
    setEditModalVisible(true);
  };

  const handleFinalizarTurno = (turno: Turno) => {
    setTurnoSeleccionado(turno);
    setKmFin('');
    setHoraFin('');
    setFinalizarModalVisible(true);
  };

  const submitEditTurno = async () => {
    if (!turnoSeleccionado) return;
    
    try {
      const updateData: any = {
        fecha_inicio: editForm.fecha_inicio,
        hora_inicio: editForm.hora_inicio,
        km_inicio: parseInt(editForm.km_inicio),
        cerrado: editForm.cerrado,
        liquidado: editForm.liquidado,
      };
      
      if (editForm.fecha_fin) updateData.fecha_fin = editForm.fecha_fin;
      if (editForm.hora_fin) updateData.hora_fin = editForm.hora_fin;
      if (editForm.km_fin) updateData.km_fin = parseInt(editForm.km_fin);
      
      await axios.put(
        `${API_URL}/turnos/${turnoSeleccionado.id}`,
        updateData,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      setEditModalVisible(false);
      setSnackbar({ visible: true, message: 'Turno actualizado correctamente' });
      loadData();
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Error al actualizar turno';
      setSnackbar({ visible: true, message: errorMsg });
    }
  };

  const handleDeleteTurno = async () => {
    if (!turnoSeleccionado) return;
    
    try {
      await axios.delete(
        `${API_URL}/turnos/${turnoSeleccionado.id}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      setEditModalVisible(false);
      setSnackbar({ visible: true, message: 'Turno y servicios asociados eliminados correctamente' });
      loadData();
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Error al eliminar turno';
      setSnackbar({ visible: true, message: errorMsg });
    }
  };

  const submitFinalizarTurno = async () => {
    if (!kmFin || !horaFin || !turnoSeleccionado) {
      setSnackbar({ visible: true, message: 'Por favor, completa todos los campos' });
      return;
    }

    const horaRegex = /^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/;
    if (!horaRegex.test(horaFin)) {
      setSnackbar({ 
        visible: true, 
        message: 'Formato de hora invalido. Usa HH:mm' 
      });
      return;
    }

    const kmNum = parseInt(kmFin);
    if (isNaN(kmNum) || kmNum < turnoSeleccionado.km_inicio) {
      setSnackbar({ 
        visible: true, 
        message: 'Los kilometros finales deben ser mayores a los iniciales' 
      });
      return;
    }

    try {
      const fechaActual = new Date();
      const fecha_fin = `${String(fechaActual.getDate()).padStart(2, '0')}/${String(fechaActual.getMonth() + 1).padStart(2, '0')}/${fechaActual.getFullYear()}`;
      
      await axios.put(
        `${API_URL}/turnos/${turnoSeleccionado.id}/finalizar`,
        {
          fecha_fin,
          hora_fin: horaFin,
          km_fin: kmNum,
          cerrado: true,
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setFinalizarModalVisible(false);
      setSnackbar({ visible: true, message: 'Turno finalizado correctamente' });
      loadData();
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Error al finalizar turno';
      setSnackbar({ visible: true, message: errorMsg });
    }
  };

  const handleToggleLiquidado = async (turno: Turno) => {
    try {
      await axios.put(
        `${API_URL}/turnos/${turno.id}`,
        { liquidado: !turno.liquidado },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setSnackbar({ 
        visible: true, 
        message: turno.liquidado ? 'Turno marcado como no liquidado' : 'Turno liquidado correctamente' 
      });
      loadData();
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Error al actualizar turno';
      setSnackbar({ visible: true, message: errorMsg });
    }
  };

  const handleExport = async (format: 'csv' | 'excel' | 'pdf') => {
    try {
      const params: any = {};
      if (filtroTaxista) params.taxista_id = filtroTaxista;
      if (filtroEstado === 'activos') params.cerrado = false;
      if (filtroEstado === 'cerrados') params.cerrado = true;
      if (filtroEstado === 'liquidados') params.liquidado = true;
      
      // En web, descargar directamente usando fetch y blob
      if (Platform.OS === 'web') {
        // Esperar a que window esté disponible si estamos en SSR
        if (typeof window === 'undefined') {
          setSnackbar({ visible: true, message: 'Por favor, espera un momento e intenta de nuevo' });
          setExportMenuVisible(false);
          return;
        }

        try {
          const response = await axios.get(`${API_URL}/turnos/export/${format}`, {
            headers: { Authorization: `Bearer ${token}` },
            params,
            responseType: 'blob',
          });

          const blob = response.data;
          const downloadUrl = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = downloadUrl;
          link.download = `turnos.${format === 'excel' ? 'xlsx' : format}`;
          link.style.display = 'none';
          document.body.appendChild(link);
          link.click();
          
          // Cleanup
          setTimeout(() => {
            document.body.removeChild(link);
            window.URL.revokeObjectURL(downloadUrl);
          }, 100);
          
          setSnackbar({ visible: true, message: `Archivo ${format.toUpperCase()} descargado correctamente` });
        } catch (err) {
          console.error('Web export error:', err);
          setSnackbar({ visible: true, message: 'Error al descargar el archivo' });
        }
        setExportMenuVisible(false);
        return;
      }

      // En móvil, usar FileSystem y Sharing
      const response = await axios.get(`${API_URL}/turnos/export/${format}`, {
        headers: { Authorization: `Bearer ${token}` },
        params,
        responseType: 'arraybuffer',
      });
      
      const uint8Array = new Uint8Array(response.data);
      let binaryString = '';
      for (let i = 0; i < uint8Array.length; i++) {
        binaryString += String.fromCharCode(uint8Array[i]);
      }
      const base64 = base64Encode(binaryString);
      
      const fileUri = `${FileSystem.documentDirectory}turnos.${format === 'excel' ? 'xlsx' : format}`;
      await FileSystem.writeAsStringAsync(fileUri, base64, {
        encoding: 'base64',
      });

      if (await Sharing.isAvailableAsync()) {
        await Sharing.shareAsync(fileUri);
        setSnackbar({ visible: true, message: `Archivo ${format.toUpperCase()} exportado correctamente` });
      }
      setExportMenuVisible(false);
    } catch (error) {
      console.error('Error exporting:', error);
      setSnackbar({ visible: true, message: 'Error al exportar' });
    }
  };

  const aplicarFiltros = () => {
    loadTurnos();
  };

  const limpiarFiltros = () => {
    setFiltroTaxista('');
    setFiltroTaxistaNombre('Todos');
    setFiltroVehiculo('');
    setFiltroEstado('todos');
    setTimeout(() => loadTurnos(), 100);
  };

  const formatEuro = (amount: number) => {
    return amount.toFixed(2).replace('.', ',') + ' €';
  };

  const renderTurnoCard = (turno: Turno) => (
    <Card key={turno.id} style={styles.card}>
      <Card.Content>
        <View style={styles.header}>
          <View>
            <Text variant="titleMedium" style={styles.taxistaNombre}>
              {turno.taxista_nombre}
            </Text>
            <Text variant="bodySmall" style={styles.vehiculo}>
              🚗 {turno.vehiculo_matricula}
            </Text>
          </View>
          <View style={styles.chipContainer}>
            {!turno.cerrado && (
              <Chip mode="flat" style={styles.chipActivo} compact>Activo</Chip>
            )}
            {turno.cerrado && !turno.liquidado && (
              <Chip mode="flat" style={styles.chipCerrado} compact>Cerrado</Chip>
            )}
            {turno.liquidado && (
              <Chip mode="flat" style={styles.chipLiquidado} compact>Liquidado</Chip>
            )}
          </View>
        </View>

        <Divider style={styles.divider} />

        <View style={styles.infoRow}>
          <Text variant="bodySmall" style={styles.label}>Inicio:</Text>
          <Text variant="bodySmall">{turno.fecha_inicio} {turno.hora_inicio}</Text>
        </View>

        {turno.cerrado && (
          <View style={styles.infoRow}>
            <Text variant="bodySmall" style={styles.label}>Fin:</Text>
            <Text variant="bodySmall">{turno.fecha_fin} {turno.hora_fin}</Text>
          </View>
        )}

        <View style={styles.infoRow}>
          <Text variant="bodySmall" style={styles.label}>KM:</Text>
          <Text variant="bodySmall">
            {turno.km_inicio} {turno.cerrado && `→ ${turno.km_fin} (${turno.km_fin! - turno.km_inicio} km)`}
          </Text>
        </View>

        <Divider style={styles.divider} />

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

        {/* Informacion de combustible/repostaje */}
        {turno.combustible?.repostado && (
          <>
            <Divider style={styles.divider} />
            <View style={styles.combustibleSection}>
              <Text variant="bodySmall" style={styles.combustibleTitle}>⛽ Repostaje</Text>
              <View style={styles.infoRow}>
                <Text variant="bodySmall" style={styles.label}>Litros:</Text>
                <Text variant="bodySmall" style={styles.combustibleValue}>{turno.combustible.litros} L</Text>
              </View>
              {turno.combustible.vehiculo_matricula && (
                <View style={styles.infoRow}>
                  <Text variant="bodySmall" style={styles.label}>Vehiculo:</Text>
                  <Text variant="bodySmall">{turno.combustible.vehiculo_matricula}</Text>
                </View>
              )}
              {turno.combustible.km_vehiculo && (
                <View style={styles.infoRow}>
                  <Text variant="bodySmall" style={styles.label}>KM:</Text>
                  <Text variant="bodySmall">{turno.combustible.km_vehiculo}</Text>
                </View>
              )}
            </View>
          </>
        )}

        {/* Botones de accion */}
        <View style={styles.actionButtons}>
          <Button
            mode="outlined"
            onPress={() => handleEditTurno(turno)}
            icon="pencil"
            compact
            style={styles.actionButton}
          >
            Editar
          </Button>
          
          {!turno.cerrado && (
            <Button
              mode="contained"
              onPress={() => handleFinalizarTurno(turno)}
              icon="check"
              compact
              style={[styles.actionButton, { backgroundColor: '#D32F2F' }]}
            >
              Cerrar
            </Button>
          )}
          
          {turno.cerrado && (
            <Button
              mode="contained"
              onPress={() => handleToggleLiquidado(turno)}
              icon={turno.liquidado ? "close-circle" : "cash"}
              compact
              style={[styles.actionButton, { backgroundColor: turno.liquidado ? '#666' : '#4CAF50' }]}
            >
              {turno.liquidado ? 'Desliqu.' : 'Liquidar'}
            </Button>
          )}
        </View>

        {/* Botón para ver servicios */}
        <Button
          mode="text"
          onPress={() => toggleTurnoExpanded(turno.id)}
          icon={expandedTurnos[turno.id] ? 'chevron-up' : 'chevron-down'}
          style={styles.expandButton}
        >
          {expandedTurnos[turno.id] ? 'Ocultar servicios' : 'Ver servicios'}
        </Button>

        {/* Servicios expandibles */}
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
                    {servicio.vehiculo_matricula && (
                      <Text variant="bodySmall" style={styles.servicioVehiculo}>
                        🚗 {servicio.vehiculo_matricula}
                      </Text>
                    )}
                    <Text variant="bodySmall" style={styles.servicioDetalle}>
                      📍 {servicio.origen} → {servicio.destino}
                    </Text>
                    <Text variant="bodySmall" style={styles.servicioDetalle}>
                      🚗 {servicio.kilometros} km
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
                    
                    {/* Chips de estado del servicio */}
                    {(servicio.cobrado || servicio.facturar) && (
                      <View style={styles.servicioEstadoChips}>
                        {servicio.cobrado && (
                          <Chip 
                            mode="flat" 
                            compact 
                            icon="cash-check"
                            style={styles.servicioChipCobrado}
                            textStyle={styles.servicioChipText}
                          >
                            Cobrado
                          </Chip>
                        )}
                        {servicio.facturar && (
                          <Chip 
                            mode="flat" 
                            compact 
                            icon="file-document"
                            style={styles.servicioChipFacturar}
                            textStyle={styles.servicioChipText}
                          >
                            Facturar
                          </Chip>
                        )}
                      </View>
                    )}
                    
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
  );

  const renderTablaView = () => (
    <ScrollView horizontal>
      <DataTable>
        <DataTable.Header>
          <DataTable.Title style={{ width: 100 }}>Taxista</DataTable.Title>
          <DataTable.Title style={{ width: 100 }}>Vehiculo</DataTable.Title>
          <DataTable.Title style={{ width: 90 }}>Fecha</DataTable.Title>
          <DataTable.Title style={{ width: 50 }}>KM</DataTable.Title>
          <DataTable.Title numeric style={{ width: 50 }}>Servs.</DataTable.Title>
          <DataTable.Title numeric style={{ width: 90, paddingRight: 15 }}>Total €</DataTable.Title>
          <DataTable.Title style={{ width: 80, paddingLeft: 10 }}>⛽ Litros</DataTable.Title>
          <DataTable.Title style={{ width: 75, paddingLeft: 10 }}>Estado</DataTable.Title>
        </DataTable.Header>

        {turnos.map((turno) => (
          <DataTable.Row key={turno.id}>
            <DataTable.Cell style={styles.tableCellTaxista}>
              <TouchableOpacity onPress={() => handleEditTurno(turno)} style={styles.taxistaTouchable}>
                <Text style={styles.clickableText} numberOfLines={1} ellipsizeMode="tail">
                  {turno.taxista_nombre}
                </Text>
              </TouchableOpacity>
            </DataTable.Cell>
            <DataTable.Cell style={styles.tableCellVehiculo}>
              <Text numberOfLines={1} ellipsizeMode="tail" style={styles.vehiculoText}>
                {turno.vehiculo_matricula}
              </Text>
            </DataTable.Cell>
            <DataTable.Cell style={styles.tableCellFecha}>
              <Text numberOfLines={1} style={styles.fechaText}>{turno.fecha_inicio}</Text>
            </DataTable.Cell>
            <DataTable.Cell style={styles.tableCellKm}>
              <Text style={styles.kmText}>
                {turno.cerrado ? turno.km_fin! - turno.km_inicio : '-'}
              </Text>
            </DataTable.Cell>
            <DataTable.Cell numeric style={styles.tableCellServicios}>
              {turno.cantidad_servicios}
            </DataTable.Cell>
            <DataTable.Cell numeric style={[styles.tableCellTotal, { paddingRight: 15 }]}>
              <Text numberOfLines={1} style={styles.totalText}>
                {formatEuro(turno.total_importe_clientes + turno.total_importe_particulares)}
              </Text>
            </DataTable.Cell>
            <DataTable.Cell style={[styles.tableCellCombustible, { paddingLeft: 10 }]}>
              <Text style={turno.combustible?.repostado ? styles.combustibleSi : styles.combustibleNo}>
                {turno.combustible?.repostado ? `${turno.combustible.litros}L` : '-'}
              </Text>
            </DataTable.Cell>
            <DataTable.Cell style={[styles.tableCellEstado, { paddingLeft: 10 }]}>
              <Text style={styles.estadoText}>
                {turno.liquidado ? 'Liquid.' : turno.cerrado ? 'Cerrado' : 'Activo'}
              </Text>
            </DataTable.Cell>
          </DataTable.Row>
        ))}
      </DataTable>
    </ScrollView>
  );

  const renderEstadisticasView = () => (
    <View style={styles.estadisticasContainer}>
      <Card style={styles.estadCard}>
        <Card.Content>
          <Text variant="titleLarge" style={styles.estadTitle}>📊 Resumen Global</Text>
          
          <View style={styles.estadRow}>
            <Text variant="bodyLarge">Total Turnos:</Text>
            <Text variant="bodyLarge" style={styles.estadValue}>
              {estadisticas?.total_turnos || 0}
            </Text>
          </View>
          
          <View style={styles.estadRow}>
            <Text variant="bodyMedium">Activos:</Text>
            <Text variant="bodyMedium" style={styles.estadValueActivo}>
              {estadisticas?.turnos_activos || 0}
            </Text>
          </View>
          
          <View style={styles.estadRow}>
            <Text variant="bodyMedium">Cerrados:</Text>
            <Text variant="bodyMedium" style={styles.estadValueCerrado}>
              {estadisticas?.turnos_cerrados || 0}
            </Text>
          </View>
          
          <View style={styles.estadRow}>
            <Text variant="bodyMedium">Liquidados:</Text>
            <Text variant="bodyMedium" style={styles.estadValueLiquidado}>
              {estadisticas?.turnos_liquidados || 0}
            </Text>
          </View>
          
          <View style={styles.estadRow}>
            <Text variant="bodyMedium">Pendiente liquidación:</Text>
            <Text variant="bodyMedium" style={styles.estadValuePendiente}>
              {estadisticas?.turnos_pendiente_liquidacion || 0}
            </Text>
          </View>
        </Card.Content>
      </Card>

      <Card style={styles.estadCard}>
        <Card.Content>
          <Text variant="titleLarge" style={styles.estadTitle}>💰 Totales</Text>
          
          <View style={styles.estadRow}>
            <Text variant="bodyLarge">Importe Total:</Text>
            <Text variant="bodyLarge" style={styles.estadValueImporte}>
              {formatEuro(estadisticas?.total_importe || 0)}
            </Text>
          </View>
          
          <View style={styles.estadRow}>
            <Text variant="bodyMedium">Kilometros:</Text>
            <Text variant="bodyMedium">{estadisticas?.total_kilometros || 0} km</Text>
          </View>
          
          <View style={styles.estadRow}>
            <Text variant="bodyMedium">Servicios:</Text>
            <Text variant="bodyMedium">{estadisticas?.total_servicios || 0}</Text>
          </View>
        </Card.Content>
      </Card>

      <Card style={styles.estadCard}>
        <Card.Content>
          <Text variant="titleLarge" style={styles.estadTitle}>📈 Promedios</Text>
          
          <View style={styles.estadRow}>
            <Text variant="bodyMedium">€ por turno:</Text>
            <Text variant="bodyMedium" style={styles.estadValueImporte}>
              {formatEuro(estadisticas?.promedio_importe_por_turno || 0)}
            </Text>
          </View>
          
          <View style={styles.estadRow}>
            <Text variant="bodyMedium">Servicios por turno:</Text>
            <Text variant="bodyMedium">
              {estadisticas?.promedio_servicios_por_turno?.toFixed(1) || 0}
            </Text>
          </View>
        </Card.Content>
      </Card>
    </View>
  );

  return (
    <View style={styles.container}>
      {/* Barra de filtros */}
      <View style={styles.filtrosContainer}>
        <Text variant="titleSmall" style={styles.filtrosTitle}>Filtros</Text>
        
        <Menu
          visible={taxistaMenuVisible}
          onDismiss={() => setTaxistaMenuVisible(false)}
          anchor={
            <Button
              mode="outlined"
              onPress={() => setTaxistaMenuVisible(true)}
              icon="account"
              style={styles.filtroButton}
            >
              {filtroTaxistaNombre}
            </Button>
          }
        >
          <Menu.Item
            onPress={() => {
              setFiltroTaxista('');
              setFiltroTaxistaNombre('Todos');
              setTaxistaMenuVisible(false);
            }}
            title="Todos los taxistas"
          />
          {taxistas.map((taxista) => (
            <Menu.Item
              key={taxista.id}
              onPress={() => {
                setFiltroTaxista(taxista.id);
                setFiltroTaxistaNombre(taxista.nombre);
                setTaxistaMenuVisible(false);
              }}
              title={taxista.nombre}
            />
          ))}
        </Menu>

        <SegmentedButtons
          value={filtroEstado}
          onValueChange={setFiltroEstado}
          buttons={[
            { value: 'todos', label: 'Todos' },
            { value: 'activos', label: 'Activos' },
            { value: 'cerrados', label: 'Cerrados' },
            { value: 'liquidados', label: 'Liquid.' },
          ]}
          style={styles.segmentedButtons}
        />

        <View style={styles.filtroActions}>
          <Button mode="contained" onPress={aplicarFiltros} icon="filter">
            Aplicar
          </Button>
          <Button mode="outlined" onPress={limpiarFiltros} icon="filter-remove">
            Limpiar
          </Button>
        </View>
      </View>

      {/* Selector de vista */}
      <SegmentedButtons
        value={vistaActual}
        onValueChange={setVistaActual}
        buttons={[
          { value: 'lista', label: 'Lista', icon: 'view-list' },
          { value: 'tabla', label: 'Tabla', icon: 'table' },
          { value: 'estadisticas', label: 'Estadísticas', icon: 'chart-bar' },
        ]}
        style={styles.vistaButtons}
      />

      {/* Contenido según vista */}
      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={['#0066CC']} />
        }
      >
        {vistaActual === 'lista' && turnos.map(renderTurnoCard)}
        {vistaActual === 'tabla' && renderTablaView()}
        {vistaActual === 'estadisticas' && renderEstadisticasView()}
        
        {vistaActual === 'lista' && turnos.length === 0 && (
          <View style={styles.emptyContainer}>
            <Text variant="bodyLarge" style={styles.emptyText}>
              No hay turnos para mostrar
            </Text>
          </View>
        )}
      </ScrollView>

      {/* FAB de exportación */}
      <FAB
        icon="download"
        style={styles.fab}
        onPress={() => setExportMenuVisible(true)}
      />

      {/* Modal de edición */}
      <Portal>
        <Dialog visible={editModalVisible} onDismiss={() => setEditModalVisible(false)}>
          <Dialog.Title>Editar Turno</Dialog.Title>
          <Dialog.ScrollArea>
            <ScrollView>
              <View style={styles.dialogContent}>
                <TextInput
                  label="Fecha inicio"
                  value={editForm.fecha_inicio}
                  onChangeText={(text) => setEditForm({ ...editForm, fecha_inicio: text })}
                  mode="outlined"
                  style={styles.input}
                />
                <TextInput
                  label="Hora inicio"
                  value={editForm.hora_inicio}
                  onChangeText={(text) => setEditForm({ ...editForm, hora_inicio: text })}
                  mode="outlined"
                  style={styles.input}
                />
                <TextInput
                  label="KM inicial"
                  value={editForm.km_inicio}
                  onChangeText={(text) => setEditForm({ ...editForm, km_inicio: text })}
                  mode="outlined"
                  keyboardType="number-pad"
                  style={styles.input}
                />
                <TextInput
                  label="Fecha fin"
                  value={editForm.fecha_fin}
                  onChangeText={(text) => setEditForm({ ...editForm, fecha_fin: text })}
                  mode="outlined"
                  style={styles.input}
                />
                <TextInput
                  label="Hora fin"
                  value={editForm.hora_fin}
                  onChangeText={(text) => setEditForm({ ...editForm, hora_fin: text })}
                  mode="outlined"
                  style={styles.input}
                />
                <TextInput
                  label="KM final"
                  value={editForm.km_fin}
                  onChangeText={(text) => setEditForm({ ...editForm, km_fin: text })}
                  mode="outlined"
                  keyboardType="number-pad"
                  style={styles.input}
                />
                
                <View style={styles.checkboxRow}>
                  <Button
                    mode={editForm.cerrado ? "contained" : "outlined"}
                    onPress={() => setEditForm({ ...editForm, cerrado: !editForm.cerrado })}
                    icon={editForm.cerrado ? "check-circle" : "circle-outline"}
                  >
                    Cerrado
                  </Button>
                  <Button
                    mode={editForm.liquidado ? "contained" : "outlined"}
                    onPress={() => setEditForm({ ...editForm, liquidado: !editForm.liquidado })}
                    icon={editForm.liquidado ? "check-circle" : "circle-outline"}
                  >
                    Liquidado
                  </Button>
                </View>
              </View>
            </ScrollView>
          </Dialog.ScrollArea>
          <Dialog.Actions>
            <Button 
              onPress={() => setDeleteConfirmVisible(true)} 
              textColor="#D32F2F"
              icon="delete"
            >
              Eliminar
            </Button>
            <View style={{ flex: 1 }} />
            <Button onPress={() => setEditModalVisible(false)}>Cancelar</Button>
            <Button onPress={submitEditTurno}>Guardar</Button>
          </Dialog.Actions>
        </Dialog>
      </Portal>

      {/* Modal de confirmación de eliminación */}
      <Portal>
        <Dialog visible={deleteConfirmVisible} onDismiss={() => setDeleteConfirmVisible(false)}>
          <Dialog.Title>Confirmar Eliminación</Dialog.Title>
          <Dialog.Content>
            <Text variant="bodyMedium">
              ¿Estas seguro de que deseas eliminar este turno? 
            </Text>
            <Text variant="bodyMedium" style={{ marginTop: 8, color: '#D32F2F' }}>
              Esta accion tambien eliminará todos los servicios asociados y no se puede deshacer.
            </Text>
          </Dialog.Content>
          <Dialog.Actions>
            <Button onPress={() => setDeleteConfirmVisible(false)}>Cancelar</Button>
            <Button 
              onPress={() => {
                setDeleteConfirmVisible(false);
                handleDeleteTurno();
              }}
              textColor="#D32F2F"
            >
              Eliminar
            </Button>
          </Dialog.Actions>
        </Dialog>
      </Portal>

      {/* Modal de finalizar */}
      <Portal>
        <Dialog visible={finalizarModalVisible} onDismiss={() => setFinalizarModalVisible(false)}>
          <Dialog.Title>Finalizar Turno</Dialog.Title>
          <Dialog.Content>
            <Text variant="bodyMedium" style={styles.dialogText}>
              Ingresa la hora de finalización y los kilometros finales
            </Text>
            <TextInput
              label="Hora de finalización (HH:mm) *"
              value={horaFin}
              onChangeText={setHoraFin}
              mode="outlined"
              placeholder="Ejemplo: 14:30"
              style={styles.input}
            />
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
            <Button onPress={submitFinalizarTurno}>Finalizar</Button>
          </Dialog.Actions>
        </Dialog>
      </Portal>

      {/* Menu de exportación */}
      <Portal>
        <Dialog visible={exportMenuVisible} onDismiss={() => setExportMenuVisible(false)}>
          <Dialog.Title>Exportar Turnos</Dialog.Title>
          <Dialog.Content>
            <Button
              mode="outlined"
              onPress={() => handleExport('csv')}
              icon="file-delimited"
              style={styles.exportButton}
            >
              Exportar a CSV
            </Button>
            <Button
              mode="outlined"
              onPress={() => handleExport('excel')}
              icon="file-excel"
              style={styles.exportButton}
            >
              Exportar a Excel
            </Button>
            <Button
              mode="outlined"
              onPress={() => handleExport('pdf')}
              icon="file-pdf-box"
              style={styles.exportButton}
            >
              Exportar a PDF
            </Button>
          </Dialog.Content>
          <Dialog.Actions>
            <Button onPress={() => setExportMenuVisible(false)}>Cerrar</Button>
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
  filtrosContainer: {
    backgroundColor: 'white',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  filtrosTitle: {
    fontWeight: 'bold',
    marginBottom: 8,
    color: '#0066CC',
  },
  filtroButton: {
    marginBottom: 8,
  },
  segmentedButtons: {
    marginBottom: 8,
  },
  filtroActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 8,
  },
  vistaButtons: {
    margin: 8,
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
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  taxistaNombre: {
    fontWeight: 'bold',
    color: '#0066CC',
  },
  vehiculo: {
    color: '#666',
    marginTop: 4,
  },
  chipContainer: {
    flexDirection: 'column',
    gap: 4,
  },
  chipActivo: {
    backgroundColor: '#4CAF50',
  },
  chipCerrado: {
    backgroundColor: '#FF9800',
  },
  chipLiquidado: {
    backgroundColor: '#2196F3',
  },
  chipEmpresa: {
    backgroundColor: '#E3F2FD',
  },
  chipParticular: {
    backgroundColor: '#FFF9C4',
  },
  divider: {
    marginVertical: 12,
    backgroundColor: '#E0E0E0',
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
  importeText: {
    color: '#0066CC',
    fontWeight: '600',
  },
  totalText: {
    color: '#4CAF50',
    fontWeight: 'bold',
    fontSize: 16,
  },
  actionButtons: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 16,
    flexWrap: 'wrap',
  },
  actionButton: {
    flex: 1,
    minWidth: 100,
  },
  expandButton: {
    marginTop: 8,
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
  servicioEstadoChips: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 8,
    flexWrap: 'wrap',
  },
  servicioChipCobrado: {
    backgroundColor: '#4CAF50',
  },
  servicioChipFacturar: {
    backgroundColor: '#FF9800',
  },
  servicioChipText: {
    color: '#FFFFFF',
    fontWeight: '600',
    fontSize: 12,
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
  emptyContainer: {
    padding: 32,
    alignItems: 'center',
  },
  emptyText: {
    color: '#999',
    textAlign: 'center',
  },
  estadisticasContainer: {
    padding: 16,
  },
  estadCard: {
    marginBottom: 16,
    backgroundColor: 'white',
    elevation: 2,
  },
  estadTitle: {
    fontWeight: 'bold',
    marginBottom: 16,
    color: '#0066CC',
  },
  estadRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 12,
  },
  estadValue: {
    fontWeight: 'bold',
    color: '#0066CC',
  },
  estadValueActivo: {
    fontWeight: 'bold',
    color: '#4CAF50',
  },
  estadValueCerrado: {
    fontWeight: 'bold',
    color: '#FF9800',
  },
  estadValueLiquidado: {
    fontWeight: 'bold',
    color: '#2196F3',
  },
  estadValuePendiente: {
    fontWeight: 'bold',
    color: '#F44336',
  },
  estadValueImporte: {
    fontWeight: 'bold',
    color: '#4CAF50',
  },
  fab: {
    position: 'absolute',
    margin: 16,
    right: 0,
    bottom: 0,
    backgroundColor: '#0066CC',
  },
  dialogContent: {
    paddingHorizontal: 24,
  },
  dialogText: {
    marginBottom: 16,
  },
  input: {
    marginBottom: 12,
  },
  checkboxRow: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 8,
  },
  exportButton: {
    marginBottom: 8,
  },
  clickableText: {
    color: '#0066CC',
    textDecorationLine: 'underline',
  },
  // Estilos para tabla
  tableCellTaxista: {
    width: 100,
    paddingRight: 4,
  },
  taxistaTouchable: {
    maxWidth: 95,
  },
  tableCellVehiculo: {
    width: 100,
    paddingRight: 4,
  },
  vehiculoText: {
    maxWidth: 95,
  },
  tableCellFecha: {
    width: 90,
  },
  fechaText: {
    fontSize: 12,
  },
  tableCellKm: {
    width: 50,
  },
  kmText: {
    fontSize: 12,
  },
  tableCellServicios: {
    width: 50,
  },
  tableCellTotal: {
    width: 90,
    paddingRight: 15,
  },
  totalText: {
    fontSize: 12,
    fontWeight: 'bold',
  },
  tableCellCombustible: {
    width: 80,
    paddingLeft: 10,
  },
  tableCellEstado: {
    width: 75,
    paddingLeft: 10,
  },
  estadoText: {
    fontSize: 12,
  },
  // Estilos para combustible
  tableCellCombustible: {
    width: 65,
  },
  combustibleSi: {
    fontSize: 12,
    color: '#4CAF50',
    fontWeight: 'bold',
  },
  combustibleNo: {
    fontSize: 12,
    color: '#999',
  },
  combustibleSection: {
    backgroundColor: '#FFF8E1',
    borderRadius: 8,
    padding: 12,
    marginTop: 8,
  },
  combustibleTitle: {
    fontWeight: 'bold',
    color: '#FF9800',
    marginBottom: 8,
  },
  combustibleValue: {
    color: '#FF9800',
    fontWeight: 'bold',
  },
  servicioVehiculo: {
    marginTop: 4,
    color: '#0066CC',
    fontWeight: '600',
  },
});
