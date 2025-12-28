import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ScrollView } from 'react-native';
import {
  Portal,
  Dialog,
  TextInput,
  Button,
  Text,
  Menu,
} from 'react-native-paper';
import axios from 'axios';
import { format } from 'date-fns';

import { API_URL } from '../config/api';

interface Vehiculo {
  id: string;
  matricula: string;
  marca: string;
  modelo: string;
}

interface IniciarTurnoModalProps {
  visible: boolean;
  userId: string;
  userName: string;
  token: string;
  onTurnoIniciado: () => void;
  onCancel?: () => void;
}

export default function IniciarTurnoModal({
  visible,
  userId,
  userName,
  token,
  onTurnoIniciado,
  onCancel,
}: IniciarTurnoModalProps) {
  const [vehiculos, setVehiculos] = useState<Vehiculo[]>([]);
  const [vehiculoMenuVisible, setVehiculoMenuVisible] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [fechaInicio, setFechaInicio] = useState(format(new Date(), 'dd/MM/yyyy'));
  // PR2: Hora se toma del servidor, no editable
  const [kmInicio, setKmInicio] = useState('');
  const [vehiculoId, setVehiculoId] = useState('');
  const [vehiculoMatricula, setVehiculoMatricula] = useState('');

  useEffect(() => {
    if (visible) {
      loadVehiculos();
      // Actualizar fecha al abrir el modal
      setFechaInicio(format(new Date(), 'dd/MM/yyyy'));
    }
  }, [visible]);

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

  const handleIniciarTurno = async () => {
    if (!kmInicio || !vehiculoId) {
      setError('Por favor, completa todos los campos');
      return;
    }

    const kmNum = parseInt(kmInicio);
    if (isNaN(kmNum) || kmNum < 0) {
      setError('Los kilómetros deben ser un número válido');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // PR2: NO enviar hora_inicio - el servidor usa su propia hora
      await axios.post(
        `${API_URL}/turnos`,
        {
          taxista_id: userId,
          taxista_nombre: userName,
          vehiculo_id: vehiculoId,
          vehiculo_matricula: vehiculoMatricula,
          fecha_inicio: fechaInicio,
          hora_inicio: "00:00", // El servidor lo ignora y usa su hora
          km_inicio: kmNum,
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      onTurnoIniciado();
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Error al iniciar turno';
      setError(errorMsg);
      setLoading(false);
    }
  };

  const handleCancel = () => {
    if (onCancel) {
      onCancel();
    }
  };

  return (
    <Portal>
      <Dialog visible={visible} onDismiss={handleCancel} dismissable={true}>
        <Dialog.Title>Iniciar Turno</Dialog.Title>
        <Dialog.ScrollArea>
          <ScrollView>
            <View style={styles.content}>
              <Text variant="bodyMedium" style={styles.subtitle}>
                Completa los datos para iniciar tu turno
              </Text>

              <TextInput
                label="Fecha de inicio"
                value={fechaInicio}
                onChangeText={setFechaInicio}
                mode="outlined"
                style={styles.input}
                placeholder="dd/mm/yyyy"
              />

              {/* PR2: Hora tomada del servidor - mostrar info */}
              <View style={styles.serverTimeInfo}>
                <Text variant="bodySmall" style={styles.serverTimeText}>
                  ⏰ La hora de inicio se registrará automáticamente del servidor
                </Text>
              </View>

              <Menu
                visible={vehiculoMenuVisible}
                onDismiss={() => setVehiculoMenuVisible(false)}
                anchor={
                  <Button
                    mode="outlined"
                    onPress={() => setVehiculoMenuVisible(true)}
                    icon="car"
                    style={styles.input}
                  >
                    {vehiculoMatricula || 'Seleccionar vehículo *'}
                  </Button>
                }
              >
                {vehiculos.map((vehiculo) => (
                  <Menu.Item
                    key={vehiculo.id}
                    onPress={() => {
                      setVehiculoId(vehiculo.id);
                      setVehiculoMatricula(vehiculo.matricula);
                      setVehiculoMenuVisible(false);
                    }}
                    title={`${vehiculo.matricula} - ${vehiculo.marca} ${vehiculo.modelo}`}
                  />
                ))}
              </Menu>

              <TextInput
                label="Kilómetros iniciales *"
                value={kmInicio}
                onChangeText={setKmInicio}
                mode="outlined"
                keyboardType="number-pad"
                style={styles.input}
                placeholder="0"
              />

              {error ? (
                <Text variant="bodySmall" style={styles.error}>
                  {error}
                </Text>
              ) : null}
            </View>
          </ScrollView>
        </Dialog.ScrollArea>
        <Dialog.Actions>
          <Button
            onPress={handleCancel}
            disabled={loading}
          >
            Cancelar
          </Button>
          <Button
            onPress={handleIniciarTurno}
            loading={loading}
            disabled={loading}
            mode="contained"
          >
            Iniciar Turno
          </Button>
        </Dialog.Actions>
      </Dialog>
    </Portal>
  );
}

const styles = StyleSheet.create({
  content: {
    paddingHorizontal: 24,
  },
  subtitle: {
    marginBottom: 16,
    color: '#666',
  },
  input: {
    marginBottom: 12,
  },
  error: {
    color: '#D32F2F',
    marginTop: 8,
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
