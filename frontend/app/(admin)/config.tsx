import React, { useState, useEffect } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  Image,
  TouchableOpacity,
} from 'react-native';
import {
  Text,
  TextInput,
  Button,
  Card,
  Snackbar,
} from 'react-native-paper';
import { useAuth } from '../../contexts/AuthContext';
import { useConfig } from '../../contexts/ConfigContext';
import axios from 'axios';
import * as ImagePicker from 'expo-image-picker';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL + '/api';

interface Config {
  nombre_radio_taxi: string;
  telefono: string;
  web: string;
  direccion: string;
  email: string;
  logo_base64: string | null;
}

export default function ConfigScreen() {
  const { token } = useAuth();
  const { reloadConfig } = useConfig();
  const [loading, setLoading] = useState(false);
  const [snackbar, setSnackbar] = useState({ visible: false, message: '' });
  
  const [formData, setFormData] = useState<Config>({
    nombre_radio_taxi: '',
    telefono: '',
    web: '',
    direccion: '',
    email: '',
    logo_base64: null,
  });

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const response = await axios.get(`${API_URL}/config`);
      setFormData(response.data);
    } catch (error) {
      console.error('Error loading config:', error);
    }
  };

  const pickImage = async () => {
    try {
      const permissionResult = await ImagePicker.requestMediaLibraryPermissionsAsync();
      
      if (permissionResult.granted === false) {
        setSnackbar({ visible: true, message: 'Se necesita permiso para acceder a las imágenes' });
        return;
      }

      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        aspect: [4, 3],
        quality: 0.7,
        base64: true,
      });

      if (!result.canceled && result.assets[0].base64) {
        setFormData({
          ...formData,
          logo_base64: `data:image/jpeg;base64,${result.assets[0].base64}`,
        });
      }
    } catch (error) {
      console.error('Error picking image:', error);
      setSnackbar({ visible: true, message: 'Error al seleccionar imagen' });
    }
  };

  const handleSubmit = async () => {
    if (!formData.nombre_radio_taxi || !formData.telefono || !formData.web) {
      setSnackbar({ visible: true, message: 'Por favor, completa los campos obligatorios' });
      return;
    }

    setLoading(true);

    try {
      await axios.put(
        `${API_URL}/config`,
        formData,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      setSnackbar({ visible: true, message: 'Configuración guardada correctamente' });
    } catch (error: any) {
      console.error('Error saving config:', error);
      setSnackbar({
        visible: true,
        message: error.response?.data?.detail || 'Error al guardar configuración',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
      >
        <Card style={styles.card}>
          <Card.Content>
            <Text variant="titleLarge" style={styles.title}>
              Configuración del Radio Taxi
            </Text>

            <Text variant="titleMedium" style={styles.sectionTitle}>
              Logo
            </Text>
            <TouchableOpacity onPress={pickImage} style={styles.logoContainer}>
              {formData.logo_base64 ? (
                <Image
                  source={{ uri: formData.logo_base64 }}
                  style={styles.logo}
                  resizeMode="contain"
                />
              ) : (
                <View style={styles.logoPlaceholder}>
                  <Text style={styles.logoPlaceholderText}>
                    Toca para seleccionar logo
                  </Text>
                </View>
              )}
            </TouchableOpacity>
            <Text variant="bodySmall" style={styles.helperText}>
              Se recomienda una imagen cuadrada o rectangular
            </Text>

            <Text variant="titleMedium" style={styles.sectionTitle}>
              Información General
            </Text>

            <TextInput
              label="Nombre del Radio Taxi *"
              value={formData.nombre_radio_taxi}
              onChangeText={(text) => setFormData({ ...formData, nombre_radio_taxi: text })}
              mode="outlined"
              style={styles.input}
            />

            <TextInput
              label="Teléfono *"
              value={formData.telefono}
              onChangeText={(text) => setFormData({ ...formData, telefono: text })}
              mode="outlined"
              keyboardType="phone-pad"
              style={styles.input}
            />

            <TextInput
              label="Página Web *"
              value={formData.web}
              onChangeText={(text) => setFormData({ ...formData, web: text })}
              mode="outlined"
              keyboardType="url"
              autoCapitalize="none"
              style={styles.input}
            />

            <TextInput
              label="Email"
              value={formData.email}
              onChangeText={(text) => setFormData({ ...formData, email: text })}
              mode="outlined"
              keyboardType="email-address"
              autoCapitalize="none"
              style={styles.input}
            />

            <TextInput
              label="Dirección"
              value={formData.direccion}
              onChangeText={(text) => setFormData({ ...formData, direccion: text })}
              mode="outlined"
              multiline
              numberOfLines={3}
              style={styles.input}
            />

            <Button
              mode="contained"
              onPress={handleSubmit}
              style={styles.submitButton}
              loading={loading}
              disabled={loading}
            >
              Guardar Configuración
            </Button>
          </Card.Content>
        </Card>
      </ScrollView>

      <Snackbar
        visible={snackbar.visible}
        onDismiss={() => setSnackbar({ ...snackbar, visible: false })}
        duration={3000}
      >
        {snackbar.message}
      </Snackbar>
    </KeyboardAvoidingView>
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
  scrollContent: {
    padding: 16,
  },
  card: {
    backgroundColor: 'white',
    elevation: 2,
  },
  title: {
    marginBottom: 24,
    color: '#0066CC',
    fontWeight: 'bold',
  },
  sectionTitle: {
    marginTop: 16,
    marginBottom: 12,
    color: '#333',
  },
  logoContainer: {
    width: '100%',
    height: 200,
    backgroundColor: '#F5F5F5',
    borderRadius: 8,
    overflow: 'hidden',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#E0E0E0',
    borderStyle: 'dashed',
  },
  logo: {
    width: '100%',
    height: '100%',
  },
  logoPlaceholder: {
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  logoPlaceholderText: {
    color: '#666',
    textAlign: 'center',
  },
  helperText: {
    color: '#666',
    fontStyle: 'italic',
    marginTop: 8,
    marginBottom: 16,
  },
  input: {
    marginBottom: 16,
  },
  submitButton: {
    marginTop: 24,
    paddingVertical: 8,
  },
});
