import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ScrollView, Platform } from 'react-native';
import { Text, Card, TextInput, Button, ActivityIndicator } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_URL } from '../../config/api';

interface Config {
  nombre: string;
  telefono: string;
  web: string;
  email: string;
  direccion: string;
}

export default function ConfiguracionScreen() {
  const [config, setConfig] = useState<Config>({
    nombre: '',
    telefono: '',
    web: '',
    email: '',
    direccion: ''
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState({ text: '', type: '' });

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const token = await AsyncStorage.getItem('token');
      const response = await axios.get(`${API_URL}/config`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setConfig({
        nombre: response.data.nombre || '',
        telefono: response.data.telefono || '',
        web: response.data.web || '',
        email: response.data.email || '',
        direccion: response.data.direccion || ''
      });
    } catch (error) {
      console.error('Error loading config:', error);
    } finally {
      setLoading(false);
    }
  };

  const saveConfig = async () => {
    setSaving(true);
    setMessage({ text: '', type: '' });
    try {
      const token = await AsyncStorage.getItem('token');
      await axios.put(`${API_URL}/superadmin/config`, {
        nombre_radio_taxi: config.nombre,
        telefono: config.telefono,
        web: config.web,
        email: config.email,
        direccion: config.direccion
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMessage({ text: '✅ Configuracion guardada correctamente', type: 'success' });
    } catch (error: any) {
      console.error('Error saving config:', error);
      setMessage({ text: error.response?.data?.detail || 'Error al guardar', type: 'error' });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#0066CC" />
        <Text style={{ marginTop: 16 }}>Cargando configuracion...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.content}>
        <Text variant="headlineMedium" style={styles.title}>
          Configuracion del Sistema
        </Text>
        <Text variant="bodyMedium" style={styles.subtitle}>
          Estos datos aparecen en el pie de pagina del login y otros lugares de la aplicacion.
        </Text>

        <Card style={styles.card}>
          <Card.Content>
            <View style={styles.iconHeader}>
              <MaterialCommunityIcons name="cog" size={32} color="#0066CC" />
              <Text variant="titleLarge" style={{ marginLeft: 12 }}>Datos Generales</Text>
            </View>

            <TextInput
              label="Nombre de la Organizacion"
              value={config.nombre}
              onChangeText={(v) => setConfig({...config, nombre: v})}
              mode="outlined"
              style={styles.input}
            />

            <TextInput
              label="Texto inferior izquierda (ej: Nombre de la Federacion)"
              value={config.web}
              onChangeText={(v) => setConfig({...config, web: v})}
              mode="outlined"
              style={styles.input}
              placeholder="Federacion Asturiana Sindical del Taxi"
            />

            <TextInput
              label="Texto inferior derecha (ej: CIF)"
              value={config.telefono}
              onChangeText={(v) => setConfig({...config, telefono: v})}
              mode="outlined"
              style={styles.input}
              placeholder="CIF: G33045147"
            />

            <TextInput
              label="Email de contacto"
              value={config.email}
              onChangeText={(v) => setConfig({...config, email: v})}
              mode="outlined"
              style={styles.input}
              keyboardType="email-address"
            />

            <TextInput
              label="Direccion"
              value={config.direccion}
              onChangeText={(v) => setConfig({...config, direccion: v})}
              mode="outlined"
              style={styles.input}
              multiline
            />

            {message.text ? (
              <Text style={[styles.message, { color: message.type === 'error' ? '#f44336' : '#4CAF50' }]}>
                {message.text}
              </Text>
            ) : null}

            <Button 
              mode="contained" 
              onPress={saveConfig} 
              loading={saving}
              disabled={saving}
              style={styles.saveButton}
              icon="content-save"
            >
              Guardar Configuracion
            </Button>
          </Card.Content>
        </Card>

        <Card style={[styles.card, { marginTop: 16 }]}>
          <Card.Content>
            <View style={styles.iconHeader}>
              <MaterialCommunityIcons name="information" size={32} color="#FF9800" />
              <Text variant="titleLarge" style={{ marginLeft: 12 }}>Vista Previa</Text>
            </View>
            <Text variant="bodyMedium" style={{ marginTop: 8, color: '#666' }}>
              Asi se vera en el pie de pagina del login:
            </Text>
            <View style={styles.preview}>
              <Text style={styles.previewText}>{config.web || '(vacio)'}</Text>
              <Text style={styles.previewText}>{config.telefono || '(vacio)'}</Text>
            </View>
          </Card.Content>
        </Card>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  content: {
    padding: 16,
    maxWidth: 800,
    alignSelf: 'center',
    width: '100%',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: {
    marginBottom: 8,
    color: '#333',
  },
  subtitle: {
    marginBottom: 24,
    color: '#666',
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
  },
  iconHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  input: {
    marginBottom: 16,
  },
  message: {
    marginBottom: 16,
    textAlign: 'center',
    fontSize: 16,
  },
  saveButton: {
    marginTop: 8,
    paddingVertical: 8,
  },
  preview: {
    marginTop: 16,
    padding: 16,
    backgroundColor: '#f0f0f0',
    borderRadius: 8,
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  previewText: {
    color: '#666',
    fontSize: 14,
  },
});
