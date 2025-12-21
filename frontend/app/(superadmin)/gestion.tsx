import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ScrollView, RefreshControl, Platform } from 'react-native';
import { Text, Card, Button, Portal, Modal, TextInput, ActivityIndicator, Chip, Divider, SegmentedButtons, IconButton, FAB, Menu } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_URL } from '../../config/api';

interface Organization {
  id: string;
  nombre: string;
}

interface Taxista {
  id: string;
  username: string;
  nombre: string;
  telefono?: string;
  organization_id?: string;
  organization_nombre?: string;
  created_at?: string;
}

interface Vehiculo {
  id: string;
  matricula: string;
  marca: string;
  modelo: string;
  licencia?: string;
  organization_id?: string;
  organization_nombre?: string;
}

export default function GestionScreen() {
  const [activeTab, setActiveTab] = useState('taxistas');
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [taxistas, setTaxistas] = useState<Taxista[]>([]);
  const [vehiculos, setVehiculos] = useState<Vehiculo[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedOrg, setSelectedOrg] = useState<string>('all');
  
  // Modals
  const [taxistaModalVisible, setTaxistaModalVisible] = useState(false);
  const [vehiculoModalVisible, setVehiculoModalVisible] = useState(false);
  const [editingTaxista, setEditingTaxista] = useState<Taxista | null>(null);
  const [editingVehiculo, setEditingVehiculo] = useState<Vehiculo | null>(null);
  const [saving, setSaving] = useState(false);

  // Form data
  const [taxistaForm, setTaxistaForm] = useState({
    username: '',
    password: '',
    nombre: '',
    telefono: '',
    organization_id: ''
  });
  
  const [vehiculoForm, setVehiculoForm] = useState({
    matricula: '',
    marca: '',
    modelo: '',
    licencia: '',
    organization_id: ''
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const token = await AsyncStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };
      
      const [orgsRes, taxistasRes, vehiculosRes] = await Promise.all([
        axios.get(`${API_URL}/organizations`, { headers }),
        axios.get(`${API_URL}/superadmin/taxistas`, { headers }),
        axios.get(`${API_URL}/superadmin/vehiculos`, { headers })
      ]);
      
      setOrganizations(orgsRes.data);
      setTaxistas(taxistasRes.data);
      setVehiculos(vehiculosRes.data);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  // Filter by organization
  const filteredTaxistas = selectedOrg === 'all' 
    ? taxistas 
    : taxistas.filter(t => t.organization_id === selectedOrg);
  
  const filteredVehiculos = selectedOrg === 'all'
    ? vehiculos
    : vehiculos.filter(v => v.organization_id === selectedOrg);

  // TAXISTA CRUD
  const openTaxistaModal = (taxista?: Taxista) => {
    if (taxista) {
      setEditingTaxista(taxista);
      setTaxistaForm({
        username: taxista.username,
        password: '',
        nombre: taxista.nombre,
        telefono: taxista.telefono || '',
        organization_id: taxista.organization_id || ''
      });
    } else {
      setEditingTaxista(null);
      setTaxistaForm({
        username: '',
        password: '',
        nombre: '',
        telefono: '',
        organization_id: organizations[0]?.id || ''
      });
    }
    setTaxistaModalVisible(true);
  };

  const saveTaxista = async () => {
    if (!taxistaForm.nombre || !taxistaForm.organization_id) {
      alert('Nombre y organización son obligatorios');
      return;
    }
    if (!editingTaxista && (!taxistaForm.username || !taxistaForm.password)) {
      alert('Usuario y contraseña son obligatorios para nuevo taxista');
      return;
    }

    setSaving(true);
    try {
      const token = await AsyncStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      if (editingTaxista) {
        await axios.put(`${API_URL}/superadmin/taxistas/${editingTaxista.id}`, {
          nombre: taxistaForm.nombre,
          telefono: taxistaForm.telefono,
          organization_id: taxistaForm.organization_id,
          ...(taxistaForm.password && { password: taxistaForm.password })
        }, { headers });
      } else {
        await axios.post(`${API_URL}/superadmin/taxistas`, taxistaForm, { headers });
      }

      setTaxistaModalVisible(false);
      loadData();
      alert(editingTaxista ? 'Taxista actualizado' : 'Taxista creado');
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error al guardar taxista');
    } finally {
      setSaving(false);
    }
  };

  const deleteTaxista = async (taxista: Taxista) => {
    if (Platform.OS === 'web') {
      if (!window.confirm(`¿Eliminar taxista "${taxista.nombre}"?`)) return;
    }

    try {
      const token = await AsyncStorage.getItem('token');
      await axios.delete(`${API_URL}/superadmin/taxistas/${taxista.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      loadData();
      alert('Taxista eliminado');
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error al eliminar');
    }
  };

  // VEHICULO CRUD
  const openVehiculoModal = (vehiculo?: Vehiculo) => {
    if (vehiculo) {
      setEditingVehiculo(vehiculo);
      setVehiculoForm({
        matricula: vehiculo.matricula,
        marca: vehiculo.marca,
        modelo: vehiculo.modelo,
        licencia: vehiculo.licencia || '',
        organization_id: vehiculo.organization_id || ''
      });
    } else {
      setEditingVehiculo(null);
      setVehiculoForm({
        matricula: '',
        marca: '',
        modelo: '',
        licencia: '',
        organization_id: organizations[0]?.id || ''
      });
    }
    setVehiculoModalVisible(true);
  };

  const saveVehiculo = async () => {
    if (!vehiculoForm.matricula || !vehiculoForm.organization_id) {
      alert('Matrícula y organización son obligatorios');
      return;
    }

    setSaving(true);
    try {
      const token = await AsyncStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      if (editingVehiculo) {
        await axios.put(`${API_URL}/superadmin/vehiculos/${editingVehiculo.id}`, vehiculoForm, { headers });
      } else {
        await axios.post(`${API_URL}/superadmin/vehiculos`, vehiculoForm, { headers });
      }

      setVehiculoModalVisible(false);
      loadData();
      alert(editingVehiculo ? 'Vehículo actualizado' : 'Vehículo creado');
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error al guardar vehículo');
    } finally {
      setSaving(false);
    }
  };

  const deleteVehiculo = async (vehiculo: Vehiculo) => {
    if (Platform.OS === 'web') {
      if (!window.confirm(`¿Eliminar vehículo "${vehiculo.matricula}"?`)) return;
    }

    try {
      const token = await AsyncStorage.getItem('token');
      await axios.delete(`${API_URL}/superadmin/vehiculos/${vehiculo.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      loadData();
      alert('Vehículo eliminado');
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error al eliminar');
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" />
        <Text style={{ marginTop: 16 }}>Cargando...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      >
        <View style={styles.header}>
          <Text variant="headlineMedium" style={styles.title}>⚙️ Gestión Global</Text>
          <Text variant="bodyMedium" style={styles.subtitle}>
            Administra taxistas y vehículos de todas las organizaciones
          </Text>
        </View>

        {/* Tabs */}
        <View style={styles.tabContainer}>
          <SegmentedButtons
            value={activeTab}
            onValueChange={setActiveTab}
            buttons={[
              { value: 'taxistas', label: `Taxistas (${taxistas.length})`, icon: 'account-group' },
              { value: 'vehiculos', label: `Vehículos (${vehiculos.length})`, icon: 'car' },
            ]}
          />
        </View>

        {/* Filter by Organization */}
        <View style={styles.filterContainer}>
          <Text variant="labelLarge" style={styles.filterLabel}>Filtrar por organización:</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            <Chip
              selected={selectedOrg === 'all'}
              onPress={() => setSelectedOrg('all')}
              style={styles.filterChip}
            >
              Todas
            </Chip>
            {organizations.map(org => (
              <Chip
                key={org.id}
                selected={selectedOrg === org.id}
                onPress={() => setSelectedOrg(org.id)}
                style={styles.filterChip}
              >
                {org.nombre}
              </Chip>
            ))}
          </ScrollView>
        </View>

        <View style={styles.content}>
          {/* TAXISTAS TAB */}
          {activeTab === 'taxistas' && (
            <>
              {filteredTaxistas.length === 0 ? (
                <Card style={styles.emptyCard}>
                  <Card.Content style={styles.emptyContent}>
                    <MaterialCommunityIcons name="account-off" size={64} color="#ccc" />
                    <Text variant="titleMedium" style={styles.emptyText}>No hay taxistas</Text>
                    <Button mode="contained" onPress={() => openTaxistaModal()} style={{ marginTop: 16 }}>
                      Crear Primer Taxista
                    </Button>
                  </Card.Content>
                </Card>
              ) : (
                filteredTaxistas.map(taxista => (
                  <Card key={taxista.id} style={styles.itemCard}>
                    <Card.Content>
                      <View style={styles.itemHeader}>
                        <View style={styles.itemInfo}>
                          <MaterialCommunityIcons name="account" size={40} color="#4CAF50" />
                          <View style={{ marginLeft: 12, flex: 1 }}>
                            <Text variant="titleMedium">{taxista.nombre}</Text>
                            <Text variant="bodySmall" style={styles.subText}>@{taxista.username}</Text>
                            {taxista.telefono && (
                              <Text variant="bodySmall" style={styles.subText}>📞 {taxista.telefono}</Text>
                            )}
                          </View>
                        </View>
                        <Chip style={styles.orgChip}>{taxista.organization_nombre || 'Sin asignar'}</Chip>
                      </View>
                    </Card.Content>
                    <Card.Actions>
                      <Button onPress={() => openTaxistaModal(taxista)} icon="pencil">Editar</Button>
                      <Button onPress={() => deleteTaxista(taxista)} icon="delete" textColor="#f44336">Eliminar</Button>
                    </Card.Actions>
                  </Card>
                ))
              )}
            </>
          )}

          {/* VEHICULOS TAB */}
          {activeTab === 'vehiculos' && (
            <>
              {filteredVehiculos.length === 0 ? (
                <Card style={styles.emptyCard}>
                  <Card.Content style={styles.emptyContent}>
                    <MaterialCommunityIcons name="car-off" size={64} color="#ccc" />
                    <Text variant="titleMedium" style={styles.emptyText}>No hay vehículos</Text>
                    <Button mode="contained" onPress={() => openVehiculoModal()} style={{ marginTop: 16 }}>
                      Crear Primer Vehículo
                    </Button>
                  </Card.Content>
                </Card>
              ) : (
                filteredVehiculos.map(vehiculo => (
                  <Card key={vehiculo.id} style={styles.itemCard}>
                    <Card.Content>
                      <View style={styles.itemHeader}>
                        <View style={styles.itemInfo}>
                          <MaterialCommunityIcons name="car" size={40} color="#2196F3" />
                          <View style={{ marginLeft: 12, flex: 1 }}>
                            <Text variant="titleMedium">{vehiculo.matricula}</Text>
                            <Text variant="bodySmall" style={styles.subText}>
                              {vehiculo.marca} {vehiculo.modelo}
                            </Text>
                            {vehiculo.licencia && (
                              <Text variant="bodySmall" style={styles.subText}>Licencia: {vehiculo.licencia}</Text>
                            )}
                          </View>
                        </View>
                        <Chip style={styles.orgChip}>{vehiculo.organization_nombre || 'Sin asignar'}</Chip>
                      </View>
                    </Card.Content>
                    <Card.Actions>
                      <Button onPress={() => openVehiculoModal(vehiculo)} icon="pencil">Editar</Button>
                      <Button onPress={() => deleteVehiculo(vehiculo)} icon="delete" textColor="#f44336">Eliminar</Button>
                    </Card.Actions>
                  </Card>
                ))
              )}
            </>
          )}
        </View>
      </ScrollView>

      {/* FAB */}
      <FAB
        icon="plus"
        style={styles.fab}
        onPress={() => activeTab === 'taxistas' ? openTaxistaModal() : openVehiculoModal()}
        label={activeTab === 'taxistas' ? 'Nuevo Taxista' : 'Nuevo Vehículo'}
        disabled={organizations.length === 0}
      />

      {/* Modal Taxista */}
      <Portal>
        <Modal visible={taxistaModalVisible} onDismiss={() => setTaxistaModalVisible(false)} contentContainerStyle={styles.modal}>
          <ScrollView>
            <Text variant="headlineSmall" style={styles.modalTitle}>
              {editingTaxista ? 'Editar Taxista' : 'Nuevo Taxista'}
            </Text>
            
            <TextInput
              label="Nombre completo *"
              value={taxistaForm.nombre}
              onChangeText={(v) => setTaxistaForm({...taxistaForm, nombre: v})}
              mode="outlined"
              style={styles.input}
            />
            
            {!editingTaxista && (
              <>
                <TextInput
                  label="Usuario (login) *"
                  value={taxistaForm.username}
                  onChangeText={(v) => setTaxistaForm({...taxistaForm, username: v})}
                  mode="outlined"
                  style={styles.input}
                  autoCapitalize="none"
                />
                <TextInput
                  label="Contraseña *"
                  value={taxistaForm.password}
                  onChangeText={(v) => setTaxistaForm({...taxistaForm, password: v})}
                  mode="outlined"
                  style={styles.input}
                  secureTextEntry
                />
              </>
            )}
            
            {editingTaxista && (
              <TextInput
                label="Nueva contraseña (dejar vacío para mantener)"
                value={taxistaForm.password}
                onChangeText={(v) => setTaxistaForm({...taxistaForm, password: v})}
                mode="outlined"
                style={styles.input}
                secureTextEntry
              />
            )}
            
            <TextInput
              label="Teléfono"
              value={taxistaForm.telefono}
              onChangeText={(v) => setTaxistaForm({...taxistaForm, telefono: v})}
              mode="outlined"
              style={styles.input}
              keyboardType="phone-pad"
            />
            
            <Text variant="labelLarge" style={{ marginTop: 8, marginBottom: 8 }}>Organización *</Text>
            <View style={styles.orgSelector}>
              {organizations.map(org => (
                <Chip
                  key={org.id}
                  selected={taxistaForm.organization_id === org.id}
                  onPress={() => setTaxistaForm({...taxistaForm, organization_id: org.id})}
                  style={styles.orgSelectorChip}
                >
                  {org.nombre}
                </Chip>
              ))}
            </View>
            
            <View style={styles.modalActions}>
              <Button mode="outlined" onPress={() => setTaxistaModalVisible(false)} disabled={saving}>Cancelar</Button>
              <Button mode="contained" onPress={saveTaxista} loading={saving} disabled={saving}>
                {editingTaxista ? 'Guardar' : 'Crear'}
              </Button>
            </View>
          </ScrollView>
        </Modal>
      </Portal>

      {/* Modal Vehículo */}
      <Portal>
        <Modal visible={vehiculoModalVisible} onDismiss={() => setVehiculoModalVisible(false)} contentContainerStyle={styles.modal}>
          <ScrollView>
            <Text variant="headlineSmall" style={styles.modalTitle}>
              {editingVehiculo ? 'Editar Vehículo' : 'Nuevo Vehículo'}
            </Text>
            
            <TextInput
              label="Matrícula *"
              value={vehiculoForm.matricula}
              onChangeText={(v) => setVehiculoForm({...vehiculoForm, matricula: v.toUpperCase()})}
              mode="outlined"
              style={styles.input}
              autoCapitalize="characters"
            />
            <TextInput
              label="Marca"
              value={vehiculoForm.marca}
              onChangeText={(v) => setVehiculoForm({...vehiculoForm, marca: v})}
              mode="outlined"
              style={styles.input}
            />
            <TextInput
              label="Modelo"
              value={vehiculoForm.modelo}
              onChangeText={(v) => setVehiculoForm({...vehiculoForm, modelo: v})}
              mode="outlined"
              style={styles.input}
            />
            <TextInput
              label="Número de Licencia"
              value={vehiculoForm.licencia}
              onChangeText={(v) => setVehiculoForm({...vehiculoForm, licencia: v})}
              mode="outlined"
              style={styles.input}
            />
            
            <Text variant="labelLarge" style={{ marginTop: 8, marginBottom: 8 }}>Organización *</Text>
            <View style={styles.orgSelector}>
              {organizations.map(org => (
                <Chip
                  key={org.id}
                  selected={vehiculoForm.organization_id === org.id}
                  onPress={() => setVehiculoForm({...vehiculoForm, organization_id: org.id})}
                  style={styles.orgSelectorChip}
                >
                  {org.nombre}
                </Chip>
              ))}
            </View>
            
            <View style={styles.modalActions}>
              <Button mode="outlined" onPress={() => setVehiculoModalVisible(false)} disabled={saving}>Cancelar</Button>
              <Button mode="contained" onPress={saveVehiculo} loading={saving} disabled={saving}>
                {editingVehiculo ? 'Guardar' : 'Crear'}
              </Button>
            </View>
          </ScrollView>
        </Modal>
      </Portal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  scrollView: { flex: 1 },
  header: { padding: 24, backgroundColor: '#fff', borderBottomWidth: 1, borderBottomColor: '#e0e0e0' },
  title: { fontWeight: 'bold', color: '#333' },
  subtitle: { color: '#666', marginTop: 4 },
  tabContainer: { padding: 16, backgroundColor: '#fff' },
  filterContainer: { padding: 16, backgroundColor: '#fff', borderBottomWidth: 1, borderBottomColor: '#e0e0e0' },
  filterLabel: { marginBottom: 8, color: '#666' },
  filterChip: { marginRight: 8 },
  content: { padding: 16, paddingBottom: 100 },
  itemCard: { marginBottom: 12, borderRadius: 12 },
  itemHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  itemInfo: { flexDirection: 'row', alignItems: 'center', flex: 1 },
  subText: { color: '#666' },
  orgChip: { backgroundColor: '#E3F2FD' },
  emptyCard: { borderRadius: 12, marginTop: 32 },
  emptyContent: { alignItems: 'center', padding: 48 },
  emptyText: { color: '#666', marginTop: 16 },
  fab: { position: 'absolute', margin: 16, right: 0, bottom: 0, backgroundColor: '#0066CC' },
  modal: { backgroundColor: 'white', padding: 24, margin: 20, borderRadius: 12, maxHeight: '90%', maxWidth: 500, alignSelf: 'center', width: '100%' },
  modalTitle: { marginBottom: 16, fontWeight: 'bold' },
  input: { marginBottom: 12 },
  orgSelector: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  orgSelectorChip: { marginBottom: 8 },
  modalActions: { flexDirection: 'row', justifyContent: 'flex-end', gap: 12, marginTop: 24 },
});
