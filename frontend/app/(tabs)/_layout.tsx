import React, { useState, useEffect } from 'react';
import { Tabs } from 'expo-router';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { useAuth } from '../../contexts/AuthContext';
import IniciarTurnoModal from '../../components/IniciarTurnoModal';
import axios from 'axios';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL + '/api';

export default function TabsLayout() {
  const { user, token } = useAuth();
  const [turnoActivo, setTurnoActivo] = useState<any>(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [loading, setLoading] = useState(true);

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
      } else {
        setModalVisible(true);
      }
    } catch (error) {
      console.error('Error checking turno activo:', error);
      setModalVisible(true);
    } finally {
      setLoading(false);
    }
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

      <IniciarTurnoModal
        visible={modalVisible}
        userId={user?._id || ''}
        userName={user?.nombre || ''}
        token={token || ''}
        onTurnoIniciado={handleTurnoIniciado}
      />
    </>
  );
}
