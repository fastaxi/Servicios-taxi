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

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL + '/api';

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
  const [horaInicio, setHoraInicio] = useState(format(new Date(), 'HH:mm'));
  const [kmInicio, setKmInicio] = useState('');
  const [vehiculoId, setVehiculoId] = useState('');
  const [vehiculoMatricula, setVehiculoMatricula] = useState('');

  useEffect(() => {
    if (visible) {
      loadVehiculos();
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
      await axios.post(
        `${API_URL}/turnos`,
        {
          taxista_id: userId,
          taxista_nombre: userName,
          vehiculo_id: vehiculoId,
          vehiculo_matricula: vehiculoMatricula,
          fecha_inicio: fechaInicio,
          hora_inicio: horaInicio,
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

  return (
    <Portal>
      <Dialog visible={visible} dismissable={false}>
        <Dialog.Title>Iniciar Turno</Dialog.Title>
        <Dialog.ScrollArea>
          <ScrollView>
            <View style={styles.content}>
              <Text variant="bodyMedium" style={styles.subtitle}>
                Debes iniciar un turno antes de registrar servicios
              </Text>

              <TextInput
                label="Fecha de inicio"
                value={fechaInicio}
                onChangeText={setFechaInicio}
                mode="outlined"
                style={styles.input}
                placeholder="dd/mm/yyyy"
              />

              <TextInput
                label="Hora de inicio"
                value={horaInicio}
                onChangeText={setHoraInicio}
                mode="outlined"
                style={styles.input}
                placeholder="HH:mm"
              />

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
});
