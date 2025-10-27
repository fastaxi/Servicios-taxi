import React, { useState, useEffect } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  Alert,
} from 'react-native';
import {
  TextInput,
  Button,
  Text,
  SegmentedButtons,
  Menu,
  Snackbar,
} from 'react-native-paper';
import { useAuth } from '../../contexts/AuthContext';
import { useSync } from '../../contexts/SyncContext';
import { useLocalSearchParams, useRouter } from 'expo-router';
import axios from 'axios';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL + '/api';

interface Company {
  id: string;
  nombre: string;
}

export default function EditServiceScreen() {
  const { token } = useAuth();
  const { syncServices } = useSync();
  const router = useRouter();
  const params = useLocalSearchParams();
  
  const serviceId = params.id as string;

  const [fecha, setFecha] = useState('');
  const [hora, setHora] = useState('');
  const [origen, setOrigen] = useState('');
  const [destino, setDestino] = useState('');
  const [importe, setImporte] = useState('');
  const [importeEspera, setImporteEspera] = useState('');
  const [kilometros, setKilometros] = useState('');
  const [tipo, setTipo] = useState('particular');
  const [empresaId, setEmpresaId] = useState('');
  const [empresaNombre, setEmpresaNombre] = useState('');
  
  const [companies, setCompanies] = useState<Company[]>([]);
  const [menuVisible, setMenuVisible] = useState(false);
  const [loading, setLoading] = useState(false);
  const [snackbar, setSnackbar] = useState({ visible: false, message: '' });

  useEffect(() => {
    loadCompanies();
    loadService();
  }, []);

  const loadCompanies = async () => {
    try {
      const response = await axios.get(`${API_URL}/companies`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setCompanies(response.data);
    } catch (error) {
      console.error('Error loading companies:', error);
    }
  };

  const formatNumberToEuro = (num: number): string => {
    // Convierte número a formato europeo (123.45 → "123,45")
    return num.toString().replace('.', ',');
  };

  const loadService = async () => {
    try {
      const response = await axios.get(`${API_URL}/services`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      const service = response.data.find((s: any) => s.id === serviceId);
      
      if (service) {
        setFecha(service.fecha);
        setHora(service.hora);
        setOrigen(service.origen);
        setDestino(service.destino);
        setImporte(formatNumberToEuro(service.importe));
        setImporteEspera(service.importe_espera ? formatNumberToEuro(service.importe_espera) : '');
        setKilometros(formatNumberToEuro(service.kilometros));
        setTipo(service.tipo);
        setEmpresaId(service.empresa_id || '');
        setEmpresaNombre(service.empresa_nombre || '');
      }
    } catch (error) {
      console.error('Error loading service:', error);
      setSnackbar({ visible: true, message: 'Error al cargar el servicio' });
    }
  };

  const parseEuroNumber = (value: string): number => {
    // Convierte formato europeo (1.234,56) a formato JS (1234.56)
    return parseFloat(value.replace(/\./g, '').replace(',', '.'));
  };

  const validateForm = () => {
    if (!fecha || !hora || !origen || !destino || !importe || !kilometros) {
      setSnackbar({ visible: true, message: 'Por favor, completa todos los campos obligatorios' });
      return false;
    }

    const dateRegex = /^\d{2}\/\d{2}\/\d{4}$/;
    if (!dateRegex.test(fecha)) {
      setSnackbar({ visible: true, message: 'Formato de fecha incorrecto. Usa dd/mm/aaaa' });
      return false;
    }

    if (tipo === 'empresa' && !empresaId) {
      setSnackbar({ visible: true, message: 'Por favor, selecciona una empresa' });
      return false;
    }

    const importeNum = parseEuroNumber(importe);
    const kmNum = parseEuroNumber(kilometros);

    if (isNaN(importeNum) || importeNum <= 0) {
      setSnackbar({ visible: true, message: 'El importe debe ser un número válido mayor que 0' });
      return false;
    }

    if (isNaN(kmNum) || kmNum <= 0) {
      setSnackbar({ visible: true, message: 'Los kilómetros deben ser un número válido mayor que 0' });
      return false;
    }

    if (importeEspera) {
      const importeEsperaNum = parseEuroNumber(importeEspera);
      if (isNaN(importeEsperaNum) || importeEsperaNum < 0) {
        setSnackbar({ visible: true, message: 'El importe de espera debe ser un número válido' });
        return false;
      }
    }

    return true;
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;

    setLoading(true);

    const serviceData = {
      fecha,
      hora,
      origen,
      destino,
      importe: parseEuroNumber(importe),
      importe_espera: importeEspera ? parseEuroNumber(importeEspera) : 0,
      kilometros: parseEuroNumber(kilometros),
      tipo,
      empresa_id: tipo === 'empresa' ? empresaId : null,
      empresa_nombre: tipo === 'empresa' ? empresaNombre : null,
    };

    try {
      await axios.put(`${API_URL}/services/${serviceId}`, serviceData, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      setSnackbar({ visible: true, message: 'Servicio actualizado correctamente' });
      
      // Esperar un momento y volver a la lista
      setTimeout(() => {
        router.back();
      }, 1000);
    } catch (error: any) {
      console.error('Error updating service:', error);
      setSnackbar({
        visible: true,
        message: error.response?.data?.detail || 'Error al actualizar el servicio',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = () => {
    Alert.alert(
      'Eliminar Servicio',
      '¿Estás seguro de que deseas eliminar este servicio?',
      [
        { text: 'Cancelar', style: 'cancel' },
        {
          text: 'Eliminar',
          style: 'destructive',
          onPress: async () => {
            try {
              await axios.delete(`${API_URL}/services/${serviceId}`, {
                headers: { Authorization: `Bearer ${token}` },
              });
              setSnackbar({ visible: true, message: 'Servicio eliminado correctamente' });
              setTimeout(() => {
                router.back();
              }, 1000);
            } catch (error) {
              console.error('Error deleting service:', error);
              setSnackbar({ visible: true, message: 'Error al eliminar el servicio' });
            }
          },
        },
      ]
    );
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
        <View style={styles.formContainer}>
          <Text variant="titleLarge" style={styles.title}>
            Editar Servicio
          </Text>

          <View style={styles.dateRow}>
            <TextInput
              label="Fecha (dd/mm/aaaa)"
              value={fecha}
              onChangeText={setFecha}
              mode="outlined"
              style={styles.dateInput}
              placeholder="dd/mm/aaaa"
            />
            <TextInput
              label="Hora"
              value={hora}
              onChangeText={setHora}
              mode="outlined"
              style={styles.timeInput}
              placeholder="HH:mm"
            />
          </View>

          <TextInput
            label="Origen *"
            value={origen}
            onChangeText={setOrigen}
            mode="outlined"
            style={styles.input}
          />

          <TextInput
            label="Destino *"
            value={destino}
            onChangeText={setDestino}
            mode="outlined"
            style={styles.input}
          />

          <View style={styles.row}>
            <TextInput
              label="Importe (€) *"
              value={importe}
              onChangeText={setImporte}
              mode="outlined"
              keyboardType="default"
              style={styles.halfInput}
            />
            <TextInput
              label="Kilómetros *"
              value={kilometros}
              onChangeText={setKilometros}
              mode="outlined"
              keyboardType="default"
              style={styles.halfInput}
            />
          </View>

          <TextInput
            label="Importe de espera (€)"
            value={importeEspera}
            onChangeText={setImporteEspera}
            mode="outlined"
            keyboardType="default"
            style={styles.input}
            placeholder="0,00"
          />

          <Text variant="titleMedium" style={styles.sectionTitle}>
            Tipo de Servicio
          </Text>
          <SegmentedButtons
            value={tipo}
            onValueChange={setTipo}
            buttons={[
              { value: 'particular', label: 'Particular' },
              { value: 'empresa', label: 'Empresa' },
            ]}
            style={styles.segmented}
          />

          {tipo === 'empresa' && (
            <Menu
              visible={menuVisible}
              onDismiss={() => setMenuVisible(false)}
              anchor={
                <Button
                  mode="outlined"
                  onPress={() => setMenuVisible(true)}
                  style={styles.input}
                >
                  {empresaNombre || 'Seleccionar Empresa'}
                </Button>
              }
            >
              {companies.map((company) => (
                <Menu.Item
                  key={company.id}
                  onPress={() => {
                    setEmpresaId(company.id);
                    setEmpresaNombre(company.nombre);
                    setMenuVisible(false);
                  }}
                  title={company.nombre}
                />
              ))}
            </Menu>
          )}

          <Button
            mode="contained"
            onPress={handleSubmit}
            style={styles.submitButton}
            loading={loading}
            disabled={loading}
          >
            Guardar Cambios
          </Button>

          <Button
            mode="outlined"
            onPress={handleDelete}
            style={styles.deleteButton}
            buttonColor="#FFFFFF"
            textColor="#D32F2F"
          >
            Eliminar Servicio
          </Button>
        </View>
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
  formContainer: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    elevation: 2,
  },
  title: {
    marginBottom: 16,
    color: '#0066CC',
    fontWeight: 'bold',
  },
  sectionTitle: {
    marginTop: 16,
    marginBottom: 8,
    color: '#333',
  },
  input: {
    marginBottom: 16,
  },
  dateRow: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 16,
  },
  dateInput: {
    flex: 2,
  },
  timeInput: {
    flex: 1,
  },
  row: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 16,
  },
  halfInput: {
    flex: 1,
  },
  segmented: {
    marginBottom: 16,
  },
  submitButton: {
    marginTop: 24,
    paddingVertical: 8,
  },
  deleteButton: {
    marginTop: 12,
    paddingVertical: 8,
    borderColor: '#D32F2F',
  },
});
