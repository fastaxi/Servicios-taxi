import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ScrollView, Alert } from 'react-native';
import {
  TextInput,
  Button,
  Text,
  FAB,
  Dialog,
  Portal,
  Snackbar,
  Card,
  IconButton,
  Chip,
} from 'react-native-paper';
import { useAuth } from '../../contexts/AuthContext';
import axios from 'axios';
import Constants from 'expo-constants';

const API_URL = Constants.expoConfig?.extra?.EXPO_BACKEND_URL || 'http://localhost:8001/api';

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

  const handleDelete = (vehiculo: Vehiculo) => {
    Alert.alert(
      'Eliminar Vehículo',
      `¿Estás seguro de que deseas eliminar el vehículo ${vehiculo.matricula}?`,
      [
        { text: 'Cancelar', style: 'cancel' },
        {
          text: 'Eliminar',
          style: 'destructive',
          onPress: async () => {
            try {
              await axios.delete(`${API_URL}/vehiculos/${vehiculo.id}`, {
                headers: { Authorization: `Bearer ${token}` },
              });
              setSnackbar({ visible: true, message: 'Vehículo eliminado correctamente' });
              loadVehiculos();
            } catch (error) {
              setSnackbar({ visible: true, message: 'Error al eliminar el vehículo' });
            }
          },
        },
      ]
    );
  };

  return (
    <View style={styles.container}>
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

      <FAB
        icon="plus"
        style={styles.fab}
        onPress={() => openModal()}
      />

      <Portal>
        <Dialog visible={modalVisible} onDismiss={() => setModalVisible(false)}>
          <Dialog.Title>
            {editingVehiculo ? 'Editar Vehículo' : 'Nuevo Vehículo'}
          </Dialog.Title>
          <Dialog.ScrollArea>
            <ScrollView>
              <TextInput
                label="Matrícula *"
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
            </ScrollView>
          </Dialog.ScrollArea>
          <Dialog.Actions>
            <Button onPress={() => setModalVisible(false)}>Cancelar</Button>
            <Button onPress={handleSubmit}>Guardar</Button>
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
  input: {
    marginBottom: 12,
  },
});
