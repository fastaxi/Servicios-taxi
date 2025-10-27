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
import NetInfo from '@react-native-community/netinfo';
import axios from 'axios';
import { format } from 'date-fns';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL + '/api';

interface Company {
  id: string;
  nombre: string;
}

export default function NewServiceScreen() {
  const { token } = useAuth();
  const { addPendingService } = useSync();

  const [fecha, setFecha] = useState(format(new Date(), 'dd/MM/yyyy'));
  const [hora, setHora] = useState(format(new Date(), 'HH:mm'));
  const [origen, setOrigen] = useState('');
  const [destino, setDestino] = useState('');
  const [importe, setImporte] = useState('');
  const [importeEspera, setImporteEspera] = useState('');
  const [importeTotal, setImporteTotal] = useState('0,00');
  const [kilometros, setKilometros] = useState('');
  const [tipo, setTipo] = useState('particular');
  const [empresaId, setEmpresaId] = useState('');
  const [empresaNombre, setEmpresaNombre] = useState('');
  
  const [companies, setCompanies] = useState<Company[]>([]);
  const [menuVisible, setMenuVisible] = useState(false);
  const [loading, setLoading] = useState(false);
  const [snackbar, setSnackbar] = useState({ visible: false, message: '' });

  // Calcular importe total automáticamente
  useEffect(() => {
    const calcularTotal = () => {
      const importeNum = importe ? parseEuroNumber(importe) : 0;
      const esperaNum = importeEspera ? parseEuroNumber(importeEspera) : 0;
      const total = importeNum + esperaNum;
      setImporteTotal(total.toFixed(2).replace('.', ','));
    };
    calcularTotal();
  }, [importe, importeEspera]);

  useEffect(() => {
    loadCompanies();
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

  const parseEuroNumber = (value: string): number => {
    // Convierte formato europeo (1.234,56) a formato JS (1234.56)
    return parseFloat(value.replace(/\./g, '').replace(',', '.'));
  };

  const validateForm = () => {
    if (!fecha || !hora || !origen || !destino || !importe || !kilometros) {
      setSnackbar({ visible: true, message: 'Por favor, completa todos los campos obligatorios' });
      return false;
    }

    // Validar formato de fecha dd/mm/yyyy
    const dateRegex = /^\d{2}\/\d{2}\/\d{4}$/;
    if (!dateRegex.test(fecha)) {
      setSnackbar({ visible: true, message: 'Formato de fecha incorrecto. Usa dd/mm/yyyy' });
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
      const netInfo = await NetInfo.fetch();

      if (netInfo.isConnected) {
        // Online: save directly to API
        await axios.post(`${API_URL}/services`, serviceData, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setSnackbar({ visible: true, message: 'Servicio guardado correctamente' });
      } else {
        // Offline: save to local storage
        await addPendingService(serviceData);
        setSnackbar({
          visible: true,
          message: 'Servicio guardado localmente. Se sincronizará cuando haya conexión',
        });
      }

      // Reset form
      resetForm();
    } catch (error: any) {
      console.error('Error saving service:', error);
      setSnackbar({
        visible: true,
        message: error.response?.data?.detail || 'Error al guardar el servicio',
      });
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFecha(format(new Date(), 'dd/MM/yyyy'));
    setHora(format(new Date(), 'HH:mm'));
    setOrigen('');
    setDestino('');
    setImporte('');
    setImporteEspera('');
    setKilometros('');
    setTipo('particular');
    setEmpresaId('');
    setEmpresaNombre('');
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
            Registrar Nuevo Servicio
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
            Guardar Servicio
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
});
