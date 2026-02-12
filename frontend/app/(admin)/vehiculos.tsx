import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ScrollView, Alert, Modal, KeyboardAvoidingView, Platform, useWindowDimensions } from 'react-native';
import {
  TextInput,
  Button,
  Text,
  FAB,
  Snackbar,
  Card,
  IconButton,
  Chip,
  Appbar,
} from 'react-native-paper';
import { useAuth } from '../../contexts/AuthContext';
import axios from 'axios';
import { API_URL } from '../../config/api';

interface Vehiculo {
  id: string;
  matricula: string;
  plazas: number;
  marca: string;
  modelo: string;
  km_iniciales: number;
  fecha_compra: string;
  activo: boolean;
}

export default function VehiculosScreen() {
  const { token } = useAuth();
  const [vehiculos, setVehiculos] = useState<Vehiculo[]>([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [snackbar, setSnackbar] = useState({ visible: false, message: '' });
  const [editingVehiculo, setEditingVehiculo] = useState<Vehiculo | null>(null);
  const { width } = useWindowDimensions();
  const isDesktop = Platform.OS === 'web' && width >= 1024;

  // Form states
  const [matricula, setMatricula] = useState('');
  const [plazas, setPlazas] = useState('');
  const [marca, setMarca] = useState('');
  const [modelo, setModelo] = useState('');
  const [kmIniciales, setKmIniciales] = useState('');
  const [fechaCompra, setFechaCompra] = useState('');

  useEffect(() => {
    loadVehiculos();
  }, []);

  const loadVehiculos = async () => {
    try {
      const response = await axios.get(`${API_URL}/vehiculos`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setVehiculos(response.data);
    } catch (error) {
      console.error('Error loading vehiculos:', error);
      setSnackbar({ visible: true, message: 'Error al cargar vehículos' });
    }
  };

  const openModal = (vehiculo?: Vehiculo) => {
    if (vehiculo) {
      setEditingVehiculo(vehiculo);
      setMatricula(vehiculo.matricula);
      setPlazas(vehiculo.plazas.toString());
      setMarca(vehiculo.marca);
      setModelo(vehiculo.modelo);
      setKmIniciales(vehiculo.km_iniciales.toString());
      setFechaCompra(vehiculo.fecha_compra);
    } else {
      resetForm();
    }
    setModalVisible(true);
  };

  const resetForm = () => {
    setEditingVehiculo(null);
    setMatricula('');
    setPlazas('');
    setMarca('');
    setModelo('');
    setKmIniciales('');
    setFechaCompra('');
  };

  const handleSubmit = async () => {
    if (!matricula || !plazas || !marca || !modelo || !kmIniciales || !fechaCompra) {
      setSnackbar({ visible: true, message: 'Por favor, completa todos los campos' });
      return;
    }

    const vehiculoData = {
      matricula: matricula.toUpperCase(),
      plazas: parseInt(plazas),
      marca,
      modelo,
      km_iniciales: parseInt(kmIniciales),
      fecha_compra: fechaCompra,
      activo: true,
    };

    try {
      if (editingVehiculo) {
        await axios.put(`${API_URL}/vehiculos/${editingVehiculo.id}`, vehiculoData, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setSnackbar({ visible: true, message: 'Vehículo actualizado correctamente' });
      } else {
        await axios.post(`${API_URL}/vehiculos`, vehiculoData, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setSnackbar({ visible: true, message: 'Vehículo creado correctamente' });
      }
      
      setModalVisible(false);
      resetForm();
      loadVehiculos();
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Error al guardar el vehículo';
      setSnackbar({ visible: true, message: errorMsg });
    }
  };

  const handleDelete = async (vehiculo: Vehiculo) => {
    // Confirmación compatible con web y móvil
    if (Platform.OS === 'web') {
      const confirmed = window.confirm(
        `¿Estás seguro de que deseas eliminar el vehículo ${vehiculo.matricula}?`
      );
      if (!confirmed) return;
    } else {
      // En móvil usar Alert.alert
      Alert.alert(
        'Eliminar Vehículo',
        `¿Estás seguro de que deseas eliminar el vehículo ${vehiculo.matricula}?`,
        [
          { text: 'Cancelar', style: 'cancel' },
          {
            text: 'Eliminar',
            style: 'destructive',
            onPress: async () => {
              await performDelete(vehiculo.id);
            },
          },
        ]
      );
      return;
    }

    // En web, ejecutar directamente después de la confirmación
    await performDelete(vehiculo.id);
  };

  const performDelete = async (vehiculoId: string) => {
    try {
      await axios.delete(`${API_URL}/vehiculos/${vehiculoId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setSnackbar({ visible: true, message: 'Vehículo eliminado correctamente' });
      loadVehiculos();
    } catch (error) {
      setSnackbar({ visible: true, message: 'Error al eliminar el vehículo' });
    }
  };

  const renderTableHeader = () => (
    <View style={styles.tableHeader}>
      <Text style={[styles.tableHeaderText, styles.colMatricula]}>Matricula</Text>
      <Text style={[styles.tableHeaderText, styles.colMarca]}>Marca</Text>
      <Text style={[styles.tableHeaderText, styles.colModelo]}>Modelo</Text>
      <Text style={[styles.tableHeaderText, styles.colPlazas]}>Plazas</Text>
      <Text style={[styles.tableHeaderText, styles.colKmIniciales]}>KM Iniciales</Text>
      <Text style={[styles.tableHeaderText, styles.colFechaCompra]}>Fecha Compra</Text>
      <Text style={[styles.tableHeaderText, styles.colEstado]}>Estado</Text>
      <Text style={[styles.tableHeaderText, styles.colAcciones]}>Acciones</Text>
    </View>
  );

  const renderTableRow = (vehiculo: Vehiculo) => (
    <View key={vehiculo.id} style={styles.tableRow}>
      <Text style={[styles.tableCell, styles.colMatricula, styles.matriculaText]}>{vehiculo.matricula}</Text>
      <Text style={[styles.tableCell, styles.colMarca]}>{vehiculo.marca}</Text>
      <Text style={[styles.tableCell, styles.colModelo]}>{vehiculo.modelo}</Text>
      <Text style={[styles.tableCell, styles.colPlazas, styles.centerText]}>{vehiculo.plazas}</Text>
      <Text style={[styles.tableCell, styles.colKmIniciales, styles.rightText]}>{vehiculo.km_iniciales}</Text>
      <Text style={[styles.tableCell, styles.colFechaCompra]}>{vehiculo.fecha_compra}</Text>
      <View style={[styles.tableCell, styles.colEstado]}>
        <Chip
          mode="flat"
          style={[styles.statusChip, vehiculo.activo ? styles.statusChipActive : styles.statusChipInactive]}
          textStyle={styles.statusChipText}
        >
          {vehiculo.activo ? 'Activo' : 'Inactivo'}
        </Chip>
      </View>
      <View style={[styles.tableCell, styles.colAcciones]}>
        <IconButton
          icon="pencil"
          size={18}
          onPress={() => openModal(vehiculo)}
          iconColor="#0066CC"
          style={styles.tableActionButton}
        />
        <IconButton
          icon="delete"
          size={18}
          onPress={() => handleDelete(vehiculo)}
          iconColor="#D32F2F"
          style={styles.tableActionButton}
        />
      </View>
    </View>
  );

  return (
    <>
      {isDesktop ? (
        <ScrollView style={styles.tableContainer}>
          {vehiculos.length === 0 ? (
            <View style={styles.emptyContainer}>
              <Text variant="bodyLarge" style={styles.emptyText}>
                No hay vehículos registrados
              </Text>
            </View>
          ) : (
            <>
              {renderTableHeader()}
              {vehiculos.map(renderTableRow)}
            </>
          )}
        </ScrollView>
      ) : (
        <ScrollView style={styles.scrollView}>
          {vehiculos.length === 0 ? (
            <View style={styles.emptyContainer}>
              <Text variant="bodyLarge" style={styles.emptyText}>
                No hay vehículos registrados
              </Text>
            </View>
          ) : (
            vehiculos.map((vehiculo) => (
            <Card key={vehiculo.id} style={styles.card}>
              <Card.Content>
                <View style={styles.cardHeader}>
                  <View>
                    <Text variant="titleLarge" style={styles.matricula}>
                      {vehiculo.matricula}
                    </Text>
                    <Text variant="bodyMedium" style={styles.subtitle}>
                      {vehiculo.marca} {vehiculo.modelo}
                    </Text>
                  </View>
                  <View style={styles.actions}>
                    <IconButton
                      icon="pencil"
                      size={20}
                      onPress={() => openModal(vehiculo)}
                      iconColor="#0066CC"
                    />
                    <IconButton
                      icon="delete"
                      size={20}
                      onPress={() => handleDelete(vehiculo)}
                      iconColor="#D32F2F"
                    />
                  </View>
                </View>

                <View style={styles.infoRow}>
                  <Text variant="bodySmall" style={styles.label}>Plazas:</Text>
                  <Chip compact>{vehiculo.plazas}</Chip>
                </View>

                <View style={styles.infoRow}>
                  <Text variant="bodySmall" style={styles.label}>KM Iniciales:</Text>
                  <Text variant="bodySmall">{vehiculo.km_iniciales} km</Text>
                </View>

                <View style={styles.infoRow}>
                  <Text variant="bodySmall" style={styles.label}>Fecha compra:</Text>
                  <Text variant="bodySmall">{vehiculo.fecha_compra}</Text>
                </View>
              </Card.Content>
            </Card>
          ))
          )}
        </ScrollView>
      )}

      <FAB
        icon="plus"
        style={styles.fab}
        onPress={() => openModal()}
      />

      <Modal
        visible={modalVisible}
        animationType="slide"
        onRequestClose={() => setModalVisible(false)}
      >
        <View style={styles.modalContainer}>
          <Appbar.Header>
            <Appbar.BackAction onPress={() => setModalVisible(false)} />
            <Appbar.Content title={editingVehiculo ? 'Editar Vehículo' : 'Nuevo Vehículo'} />
            <Appbar.Action icon="check" onPress={handleSubmit} />
          </Appbar.Header>
          
          <KeyboardAvoidingView
            style={styles.keyboardAvoid}
            behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
            keyboardVerticalOffset={0}
          >
            <ScrollView 
              style={styles.modalContent}
              contentContainerStyle={styles.modalScrollContent}
              keyboardShouldPersistTaps="handled"
            >
              <TextInput
                label="Matricula *"
                value={matricula}
                onChangeText={setMatricula}
                mode="outlined"
                style={styles.input}
                autoCapitalize="characters"
              />
              <TextInput
                label="Número de Plazas *"
                value={plazas}
                onChangeText={setPlazas}
                mode="outlined"
                keyboardType="number-pad"
                style={styles.input}
              />
              <TextInput
                label="Marca *"
                value={marca}
                onChangeText={setMarca}
                mode="outlined"
                style={styles.input}
              />
              <TextInput
                label="Modelo *"
                value={modelo}
                onChangeText={setModelo}
                mode="outlined"
                style={styles.input}
              />
              <TextInput
                label="Kilómetros Iniciales *"
                value={kmIniciales}
                onChangeText={setKmIniciales}
                mode="outlined"
                keyboardType="number-pad"
                style={styles.input}
              />
              <TextInput
                label="Fecha de Compra (dd/mm/yyyy) *"
                value={fechaCompra}
                onChangeText={setFechaCompra}
                mode="outlined"
                placeholder="01/01/2020"
                style={styles.input}
              />
              <View style={styles.buttonContainer}>
                <Button mode="outlined" onPress={() => setModalVisible(false)} style={styles.modalButton}>
                  Cancelar
                </Button>
                <Button mode="contained" onPress={handleSubmit} style={styles.modalButton}>
                  Guardar
                </Button>
              </View>
            </ScrollView>
          </KeyboardAvoidingView>
        </View>
      </Modal>

      <Snackbar
        visible={snackbar.visible}
        onDismiss={() => setSnackbar({ ...snackbar, visible: false })}
        duration={3000}
      >
        {snackbar.message}
      </Snackbar>
    </>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  scrollView: {
    backgroundColor: '#F5F5F5',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
    marginTop: 100,
  },
  emptyText: {
    color: '#999',
    textAlign: 'center',
  },
  card: {
    margin: 8,
    marginHorizontal: 16,
    backgroundColor: 'white',
    elevation: 2,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  matricula: {
    fontWeight: 'bold',
    color: '#0066CC',
  },
  subtitle: {
    color: '#666',
    marginTop: 4,
  },
  actions: {
    flexDirection: 'row',
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
  fab: {
    position: 'absolute',
    margin: 16,
    right: 0,
    bottom: 0,
    backgroundColor: '#0066CC',
  },
  modalContainer: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  keyboardAvoid: {
    flex: 1,
  },
  modalContent: {
    flex: 1,
  },
  modalScrollContent: {
    padding: 16,
    paddingBottom: 40,
  },
  input: {
    marginBottom: 16,
  },
  buttonContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 24,
    gap: 12,
  },
  modalButton: {
    flex: 1,
  },
  // Table styles for desktop
  tableContainer: {
    flex: 1,
    backgroundColor: '#FFF',
    margin: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  tableHeader: {
    flexDirection: 'row',
    backgroundColor: '#0066CC',
    paddingVertical: 12,
    paddingHorizontal: 8,
    borderTopLeftRadius: 8,
    borderTopRightRadius: 8,
  },
  tableHeaderText: {
    color: '#FFF',
    fontWeight: '600',
    fontSize: 13,
  },
  tableRow: {
    flexDirection: 'row',
    paddingVertical: 12,
    paddingHorizontal: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#F0F0F0',
    alignItems: 'center',
  },
  tableCell: {
    fontSize: 13,
    color: '#333',
  },
  tableActionButton: {
    margin: 0,
  },
  matriculaText: {
    fontWeight: '600',
    color: '#0066CC',
  },
  centerText: {
    textAlign: 'center',
  },
  rightText: {
    textAlign: 'right',
  },
  statusChip: {
    height: 24,
  },
  statusChipActive: {
    backgroundColor: '#E8F5E9',
  },
  statusChipInactive: {
    backgroundColor: '#FFEBEE',
  },
  statusChipText: {
    fontSize: 11,
  },
  // Column widths
  colMatricula: { width: 120, paddingRight: 8 },
  colMarca: { width: 120, paddingRight: 8 },
  colModelo: { width: 140, paddingRight: 8 },
  colPlazas: { width: 70 },
  colKmIniciales: { width: 110, paddingRight: 8 },
  colFechaCompra: { width: 110 },
  colEstado: { width: 100 },
  colAcciones: { width: 100, alignItems: 'center', justifyContent: 'center', flexDirection: 'row' },
});
