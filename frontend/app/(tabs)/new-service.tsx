import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import {
  TextInput,
  Button,
  Text,
  SegmentedButtons,
  Menu,
  Snackbar,
  Checkbox,
} from 'react-native-paper';
import { useAuth } from '../../contexts/AuthContext';
import { useSync } from '../../contexts/SyncContext';
import { useOrganization } from '../../contexts/OrganizationContext';
import { generateClientUUID } from '../../utils/uuid';
import NetInfo from '@react-native-community/netinfo';
import axios from 'axios';
import { format } from 'date-fns';
import { useRouter } from 'expo-router';

import { API_URL } from '../../config/api';

interface Company {
  id: string;
  nombre: string;
}

interface Vehiculo {
  id: string;
  matricula: string;
  marca: string;
  modelo: string;
}

interface TurnoActivo {
  id: string;
  vehiculo_id: string;
  vehiculo_matricula: string;
}

export default function NewServiceScreen() {
  const { token, user } = useAuth();
  const { addToQueue } = useSync();
  const { hasFeature } = useOrganization();
  const router = useRouter();

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
  const [cobrado, setCobrado] = useState(false);
  const [facturar, setFacturar] = useState(false);
  
  const [metodoPago, setMetodoPago] = useState('efectivo');
  const [origenTaxitur, setOrigenTaxitur] = useState('');
  const [vehiculoId, setVehiculoId] = useState('');
  const [vehiculoMatricula, setVehiculoMatricula] = useState('');
  const [kmInicioVehiculo, setKmInicioVehiculo] = useState('');
  const [kmFinVehiculo, setKmFinVehiculo] = useState('');
  
  const [companies, setCompanies] = useState<Company[]>([]);
  const [vehiculos, setVehiculos] = useState<Vehiculo[]>([]);
  const [turnoActivo, setTurnoActivo] = useState<TurnoActivo | null>(null);
  const [menuVisible, setMenuVisible] = useState(false);
  const [vehiculoMenuVisible, setVehiculoMenuVisible] = useState(false);
  const [loading, setLoading] = useState(false);
  const [snackbar, setSnackbar] = useState({ visible: false, message: '' });

  // Paso 5B: Stable client_uuid per submit attempt.
  // Generated once when user presses "Guardar" and reused if queued.
  const currentUUIDRef = useRef<string | null>(null);

  const hasTaxiturOrigenFeature = hasFeature('taxitur_origen');

  const vehiculoDefaultId = turnoActivo?.vehiculo_id || '';
  const vehiculoCambiado = vehiculoDefaultId && vehiculoId && vehiculoId !== vehiculoDefaultId;

  const parseEuroNumber = (value: string): number => {
    if (!value) return 0;
    return parseFloat(value.replace(/\./g, '').replace(',', '.'));
  };

  useEffect(() => {
    const importeNum = importe ? parseEuroNumber(importe) : 0;
    const esperaNum = importeEspera ? parseEuroNumber(importeEspera) : 0;
    setImporteTotal((importeNum + esperaNum).toFixed(2).replace('.', ','));
  }, [importe, importeEspera]);

  useEffect(() => {
    loadCompanies();
    loadVehiculos();
    loadTurnoActivo();
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

  const loadTurnoActivo = async () => {
    try {
      const response = await axios.get(`${API_URL}/turnos?cerrado=false&limit=1`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.data.length > 0) {
        const turno = response.data[0];
        setTurnoActivo({
          id: turno.id,
          vehiculo_id: turno.vehiculo_id,
          vehiculo_matricula: turno.vehiculo_matricula,
        });
        setVehiculoId(turno.vehiculo_id);
        setVehiculoMatricula(turno.vehiculo_matricula);
      }
    } catch (error) {
      console.error('Error loading turno activo:', error);
    }
  };

  const validateForm = () => {
    if (!fecha || !hora || !origen || !destino || !importe) {
      setSnackbar({ visible: true, message: 'Por favor, completa los campos obligatorios (fecha, hora, origen, destino, importe)' });
      return false;
    }

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
    if (isNaN(importeNum) || importeNum <= 0) {
      setSnackbar({ visible: true, message: 'El importe debe ser un numero valido mayor que 0' });
      return false;
    }

    if (kilometros) {
      const kmNum = parseEuroNumber(kilometros);
      if (isNaN(kmNum) || kmNum < 0) {
        setSnackbar({ visible: true, message: 'Los kilometros deben ser un numero valido >= 0' });
        return false;
      }
    }

    if (importeEspera) {
      const importeEsperaNum = parseEuroNumber(importeEspera);
      if (isNaN(importeEsperaNum) || importeEsperaNum < 0) {
        setSnackbar({ visible: true, message: 'El importe de espera debe ser un numero valido' });
        return false;
      }
    }

    if (hasTaxiturOrigenFeature && !origenTaxitur) {
      setSnackbar({ visible: true, message: 'Debes seleccionar el origen (Parada o Lagos)' });
      return false;
    }

    if (vehiculoCambiado) {
      const kmInicio = parseInt(kmInicioVehiculo);
      const kmFin = parseInt(kmFinVehiculo);
      
      if (!kmInicioVehiculo || isNaN(kmInicio) || kmInicio < 0) {
        setSnackbar({ visible: true, message: 'Al cambiar de vehiculo, debes indicar los km de inicio (>= 0)' });
        return false;
      }
      if (!kmFinVehiculo || isNaN(kmFin)) {
        setSnackbar({ visible: true, message: 'Al cambiar de vehiculo, debes indicar los km de fin' });
        return false;
      }
      if (kmFin < kmInicio) {
        setSnackbar({ visible: true, message: 'Los km de fin deben ser >= km de inicio' });
        return false;
      }
    }

    return true;
  };

  const handleSubmit = async () => {
    if (!validateForm() || loading) return;

    setLoading(true);

    // Paso 5B: Generate stable client_uuid ONCE per submit.
    // If user retaps "Guardar" while loading, the same UUID is reused.
    if (!currentUUIDRef.current) {
      currentUUIDRef.current = generateClientUUID();
    }
    const clientUUID = currentUUIDRef.current;

    const serviceData: Record<string, any> = {
      fecha,
      hora,
      origen,
      destino,
      importe: parseEuroNumber(importe),
      importe_espera: importeEspera ? parseEuroNumber(importeEspera) : 0,
      kilometros: kilometros ? parseEuroNumber(kilometros) : null,
      tipo,
      empresa_id: tipo === 'empresa' ? empresaId : null,
      empresa_nombre: tipo === 'empresa' ? empresaNombre : null,
      cobrado,
      facturar,
      metodo_pago: metodoPago,
      vehiculo_id: vehiculoId || null,
    };

    if (hasTaxiturOrigenFeature) {
      serviceData.origen_taxitur = origenTaxitur;
    }

    if (vehiculoCambiado) {
      serviceData.km_inicio_vehiculo = parseInt(kmInicioVehiculo);
      serviceData.km_fin_vehiculo = parseInt(kmFinVehiculo);
    }

    try {
      const netInfo = await NetInfo.fetch();

      if (netInfo.isConnected) {
        // Try online first, include client_uuid in payload
        await axios.post(`${API_URL}/services`, { ...serviceData, client_uuid: clientUUID }, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setSnackbar({ visible: true, message: 'Servicio guardado correctamente' });
      } else {
        // Offline: queue directly
        await addToQueue(serviceData, clientUUID);
        setSnackbar({
          visible: true,
          message: 'Sin conexion. Servicio guardado en cola, se sincronizara automaticamente',
        });
      }

      // Success path: reset UUID and form
      currentUUIDRef.current = null;
      resetForm();
      setTimeout(() => router.push('/services'), 500);
    } catch (error: any) {
      console.error('Error saving service:', error);

      // Paso 5B: On ANY API failure, queue the service for later sync
      // The same client_uuid ensures no duplicates when retried
      await addToQueue(serviceData, clientUUID);
      currentUUIDRef.current = null;
      resetForm();

      setSnackbar({
        visible: true,
        message: 'Error de red. Servicio guardado en cola, se sincronizara automaticamente',
      });

      setTimeout(() => router.push('/services'), 500);
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
    setCobrado(false);
    setFacturar(false);
    setMetodoPago('efectivo');
    setOrigenTaxitur('');
    setKmInicioVehiculo('');
    setKmFinVehiculo('');
    currentUUIDRef.current = null;
    if (turnoActivo) {
      setVehiculoId(turnoActivo.vehiculo_id);
      setVehiculoMatricula(turnoActivo.vehiculo_matricula);
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
              label="Importe (*) *"
              value={importe}
              onChangeText={setImporte}
              mode="outlined"
              keyboardType="default"
              style={styles.halfInput}
            />
            <TextInput
              label="Kilometros"
              value={kilometros}
              onChangeText={setKilometros}
              mode="outlined"
              keyboardType="default"
              style={styles.halfInput}
            />
          </View>

          <TextInput
            label="Importe de espera (*)"
            value={importeEspera}
            onChangeText={setImporteEspera}
            mode="outlined"
            keyboardType="default"
            style={styles.input}
            placeholder="0,00"
          />

          <TextInput
            label="Importe Total (*)"
            value={importeTotal}
            mode="outlined"
            editable={false}
            style={[styles.input, styles.totalInput]}
            right={<TextInput.Icon icon="calculator" />}
          />

          {/* Selector de vehiculo */}
          <Text variant="titleMedium" style={styles.sectionTitle}>
            Vehiculo
          </Text>
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
                {vehiculoMatricula || 'Seleccionar vehiculo'}
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
                leadingIcon={vehiculo.id === vehiculoDefaultId ? 'star' : undefined}
              />
            ))}
          </Menu>

          {/* Campos de km si cambio de vehiculo */}
          {vehiculoCambiado && (
            <View style={styles.kmCambioContainer}>
              <Text variant="bodySmall" style={styles.kmCambioWarning}>
                Has cambiado de vehiculo. Debes indicar los kilometros:
              </Text>
              <View style={styles.row}>
                <TextInput
                  label="KM inicio vehiculo *"
                  value={kmInicioVehiculo}
                  onChangeText={setKmInicioVehiculo}
                  mode="outlined"
                  keyboardType="number-pad"
                  style={styles.halfInput}
                />
                <TextInput
                  label="KM fin vehiculo *"
                  value={kmFinVehiculo}
                  onChangeText={setKmFinVehiculo}
                  mode="outlined"
                  keyboardType="number-pad"
                  style={styles.halfInput}
                />
              </View>
            </View>
          )}

          {/* Metodo de pago */}
          <Text variant="titleMedium" style={styles.sectionTitle}>
            Metodo de Pago
          </Text>
          <SegmentedButtons
            value={metodoPago}
            onValueChange={setMetodoPago}
            buttons={[
              { value: 'efectivo', label: 'Efectivo', icon: 'cash' },
              { value: 'tpv', label: 'TPV', icon: 'credit-card' },
            ]}
            style={styles.segmented}
          />

          {/* Origen Taxitur (solo si la org tiene el feature activo) */}
          {hasTaxiturOrigenFeature && (
            <>
              <Text variant="titleMedium" style={styles.sectionTitle}>
                Origen Taxitur *
              </Text>
              <SegmentedButtons
                value={origenTaxitur}
                onValueChange={setOrigenTaxitur}
                buttons={[
                  { value: 'parada', label: 'Parada' },
                  { value: 'lagos', label: 'Lagos' },
                ]}
                style={styles.segmented}
              />
            </>
          )}

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

          <View style={styles.checkboxContainer}>
            <Checkbox.Item
              label="Cobrado"
              status={cobrado ? 'checked' : 'unchecked'}
              onPress={() => setCobrado(!cobrado)}
              position="leading"
              labelStyle={styles.checkboxLabel}
            />
            <Checkbox.Item
              label="Facturar"
              status={facturar ? 'checked' : 'unchecked'}
              onPress={() => setFacturar(!facturar)}
              position="leading"
              labelStyle={styles.checkboxLabel}
            />
          </View>

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
  totalInput: {
    backgroundColor: '#E3F2FD',
  },
  checkboxContainer: {
    marginTop: 16,
    marginBottom: 8,
    backgroundColor: '#F9F9F9',
    borderRadius: 8,
    padding: 4,
  },
  checkboxLabel: {
    fontSize: 16,
  },
  submitButton: {
    marginTop: 24,
    paddingVertical: 8,
  },
  kmCambioContainer: {
    backgroundColor: '#FFF3E0',
    padding: 12,
    borderRadius: 8,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#FF9800',
  },
  kmCambioWarning: {
    color: '#E65100',
    marginBottom: 12,
    fontWeight: '600',
  },
});
