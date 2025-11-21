import React, { useState, useEffect } from 'react';
import { Tabs } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { Portal, Dialog, Button, Text } from 'react-native-paper';
import { useAuth } from '../../contexts/AuthContext';
import IniciarTurnoModal from '../../components/IniciarTurnoModal';
import axios from 'axios';

import { API_URL } from '../../config/api';

export default function TabsLayout() {
  const { user, token } = useAuth();
  const [turnoActivo, setTurnoActivo] = useState<any>(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [confirmarTurnoVisible, setConfirmarTurnoVisible] = useState(false);
  const [loading, setLoading] = useState(true);
  const [yaPreguntoIniciarTurno, setYaPreguntoIniciarTurno] = useState(false);

  useEffect(() => {
    checkTurnoActivo();
  }, []);

  const checkTurnoActivo = async () => {
    try {
      const response = await axios.get(`${API_URL}/turnos/activo`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      if (response.data) {
        setTurnoActivo(response.data);
        setModalVisible(false);
        setConfirmarTurnoVisible(false);
      } else {
        // No hay turno activo, preguntar si quiere iniciar
        if (!yaPreguntoIniciarTurno) {
          setConfirmarTurnoVisible(true);
          setYaPreguntoIniciarTurno(true);
        }
      }
    } catch (error) {
      console.error('Error checking turno activo:', error);
      if (!yaPreguntoIniciarTurno) {
        setConfirmarTurnoVisible(true);
        setYaPreguntoIniciarTurno(true);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleIniciarTurnoSi = () => {
    setConfirmarTurnoVisible(false);
    setModalVisible(true);
  };

  const handleIniciarTurnoNo = () => {
    setConfirmarTurnoVisible(false);
    setModalVisible(false);
  };

  const handleTurnoIniciado = () => {
    setModalVisible(false);
    checkTurnoActivo();
  };

  if (loading) {
    return null; // O un spinner de carga
  }

  return (
    <>
      <Tabs
        screenOptions={{
          tabBarActiveTintColor: '#0066CC',
          tabBarInactiveTintColor: '#666',
          headerStyle: {
            backgroundColor: '#0066CC',
          },
          headerTintColor: '#fff',
          tabBarStyle: {
            backgroundColor: '#FFFFFF',
            borderTopWidth: 1,
            borderTopColor: '#E0E0E0',
          },
        }}
      >
        <Tabs.Screen
          name="services"
          options={{
            title: 'Mis Servicios',
            tabBarIcon: ({ color, size }) => (
              <MaterialCommunityIcons name="clipboard-text" size={size} color={color} />
            ),
          }}
        />
        <Tabs.Screen
          name="new-service"
          options={{
            title: 'Nuevo Servicio',
            tabBarIcon: ({ color, size }) => (
              <MaterialCommunityIcons name="plus-circle" size={size} color={color} />
            ),
          }}
        />
        <Tabs.Screen
          name="turnos"
          options={{
            title: 'Turnos',
            tabBarIcon: ({ color, size }) => (
              <MaterialCommunityIcons name="clock-outline" size={size} color={color} />
            ),
          }}
        />
        <Tabs.Screen
          name="profile"
          options={{
            title: 'Perfil',
            tabBarIcon: ({ color, size }) => (
              <MaterialCommunityIcons name="account" size={size} color={color} />
            ),
          }}
        />
      </Tabs>

      {/* Diálogo de confirmación para iniciar turno */}
      <Portal>
        <Dialog visible={confirmarTurnoVisible} dismissable={false}>
          <Dialog.Title>Iniciar Turno</Dialog.Title>
          <Dialog.Content>
            <Text variant="bodyLarge">¿Desea iniciar un turno ahora?</Text>
            <Text variant="bodySmall" style={{ marginTop: 8, color: '#666' }}>
              Si selecciona "No", podrá consultar y editar servicios, pero deberá iniciar un turno desde la sección "Turnos" para registrar nuevos servicios.
            </Text>
          </Dialog.Content>
          <Dialog.Actions>
            <Button onPress={handleIniciarTurnoNo}>No</Button>
            <Button onPress={handleIniciarTurnoSi} mode="contained">Sí</Button>
          </Dialog.Actions>
        </Dialog>
      </Portal>

      <IniciarTurnoModal
        visible={modalVisible}
        userId={user?._id || ''}
        userName={user?.nombre || ''}
        token={token || ''}
        onTurnoIniciado={handleTurnoIniciado}
        onCancel={handleIniciarTurnoNo}
      />
    </>
  );
}
