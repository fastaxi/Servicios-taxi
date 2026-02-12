import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ScrollView, RefreshControl, Platform } from 'react-native';
import { Text, Card, Button, Portal, Modal, TextInput, ActivityIndicator, Chip, Divider, SegmentedButtons, FAB, Switch, Menu, List } from 'react-native-paper';
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
  email?: string;
  licencia?: string;
  organization_id?: string;
  organization_nombre?: string;
  vehiculo_asignado_id?: string;
  vehiculo_asignado_matricula?: string;
  activo?: boolean;
  created_at?: string;
}

interface Vehiculo {
  id: string;
  matricula: string;
  marca: string;
  modelo: string;
  licencia?: string;
  plazas?: number;
  km_iniciales?: number;
  fecha_compra?: string;
  activo?: boolean;
  organization_id?: string;
  organization_nombre?: string;
  taxista_asignado_id?: string;
  taxista_asignado_nombre?: string;
}

interface Admin {
  id: string;
  username: string;
  nombre: string;
  email?: string;
  telefono?: string;
  organization_id?: string;
  organization_nombre?: string;
  created_at?: string;
}

export default function GestionScreen() {
  const [activeTab, setActiveTab] = useState('taxistas');
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [taxistas, setTaxistas] = useState<Taxista[]>([]);
  const [admins, setAdmins] = useState<Admin[]>([]);
  const [vehiculos, setVehiculos] = useState<Vehiculo[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedOrg, setSelectedOrg] = useState<string>('all');
  
  // Modals
  const [taxistaModalVisible, setTaxistaModalVisible] = useState(false);
  const [vehiculoModalVisible, setVehiculoModalVisible] = useState(false);
  const [assignVehiculoModalVisible, setAssignVehiculoModalVisible] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [passwordModalVisible, setPasswordModalVisible] = useState(false);
  const [editingTaxista, setEditingTaxista] = useState<Taxista | null>(null);
  const [editingVehiculo, setEditingVehiculo] = useState<Vehiculo | null>(null);
  const [selectedTaxistaForAssign, setSelectedTaxistaForAssign] = useState<Taxista | null>(null);
  const [selectedDetail, setSelectedDetail] = useState<Taxista | Vehiculo | null>(null);
  const [selectedUserForPassword, setSelectedUserForPassword] = useState<{id: string, nombre: string, username: string} | null>(null);
  const [detailType, setDetailType] = useState<'taxista' | 'vehiculo'>('taxista');
  const [saving, setSaving] = useState(false);
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [showTaxistaPassword, setShowTaxistaPassword] = useState(false);
  const [snackbar, setSnackbar] = useState({ visible: false, message: '', type: 'success' });

  // Form data
  const [taxistaForm, setTaxistaForm] = useState({
    username: '',
    password: '',
    nombre: '',
    telefono: '',
    email: '',
    licencia: '',
    organization_id: '',
    activo: true
  });
  
  const [vehiculoForm, setVehiculoForm] = useState({
    matricula: '',
    marca: '',
    modelo: '',
    licencia: '',
    plazas: 4,
    km_iniciales: 0,
    fecha_compra: '',
    activo: true,
    organization_id: ''
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const token = await AsyncStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };
      
      const [orgsRes, taxistasRes, adminsRes, vehiculosRes] = await Promise.all([
        axios.get(`${API_URL}/organizations`, { headers }),
        axios.get(`${API_URL}/superadmin/taxistas`, { headers }),
        axios.get(`${API_URL}/superadmin/admins`, { headers }),
        axios.get(`${API_URL}/superadmin/vehiculos`, { headers })
      ]);
      
      setOrganizations(orgsRes.data);
      setTaxistas(taxistasRes.data);
      setAdmins(adminsRes.data);
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

  const filteredAdmins = selectedOrg === 'all'
    ? admins
    : admins.filter(a => a.organization_id === selectedOrg);

  // Get available vehicles for a taxista (same organization, not assigned)
  const getAvailableVehiculos = (taxista: Taxista) => {
    return vehiculos.filter(v => 
      v.organization_id === taxista.organization_id && 
      (!v.taxista_asignado_id || v.taxista_asignado_id === taxista.id)
    );
  };

  // TAXISTA CRUD
  const openTaxistaModal = (taxista?: Taxista) => {
    if (taxista) {
      setEditingTaxista(taxista);
      setTaxistaForm({
        username: taxista.username,
        password: '',
        nombre: taxista.nombre,
        telefono: taxista.telefono || '',
        email: taxista.email || '',
        licencia: taxista.licencia || '',
        organization_id: taxista.organization_id || '',
        activo: taxista.activo !== false
      });
    } else {
      setEditingTaxista(null);
      setTaxistaForm({
        username: '',
        password: '',
        nombre: '',
        telefono: '',
        email: '',
        licencia: '',
        organization_id: organizations[0]?.id || '',
        activo: true
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
          email: taxistaForm.email,
          organization_id: taxistaForm.organization_id,
          activo: taxistaForm.activo,
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
      if (!window.confirm(`¿Eliminar taxista "${taxista.nombre}"? Se eliminarán también sus turnos y servicios.`)) return;
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

  const toggleTaxistaActivo = async (taxista: Taxista) => {
    try {
      const token = await AsyncStorage.getItem('token');
      await axios.put(`${API_URL}/superadmin/taxistas/${taxista.id}`, {
        activo: !taxista.activo
      }, { headers: { Authorization: `Bearer ${token}` }});
      loadData();
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error al actualizar');
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
        plazas: vehiculo.plazas || 4,
        km_iniciales: vehiculo.km_iniciales || 0,
        fecha_compra: vehiculo.fecha_compra || '',
        activo: vehiculo.activo !== false,
        organization_id: vehiculo.organization_id || ''
      });
    } else {
      setEditingVehiculo(null);
      setVehiculoForm({
        matricula: '',
        marca: '',
        modelo: '',
        licencia: '',
        plazas: 4,
        km_iniciales: 0,
        fecha_compra: '',
        activo: true,
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

  // Assign vehicle to taxista
  const openAssignVehiculoModal = (taxista: Taxista) => {
    setSelectedTaxistaForAssign(taxista);
    setAssignVehiculoModalVisible(true);
  };

  const assignVehiculo = async (vehiculoId: string | null) => {
    if (!selectedTaxistaForAssign) return;

    setSaving(true);
    try {
      const token = await AsyncStorage.getItem('token');
      await axios.put(`${API_URL}/superadmin/taxistas/${selectedTaxistaForAssign.id}/vehiculo`, {
        vehiculo_id: vehiculoId
      }, { headers: { Authorization: `Bearer ${token}` }});
      
      setAssignVehiculoModalVisible(false);
      loadData();
      alert(vehiculoId ? 'Vehículo asignado' : 'Vehículo desasignado');
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Error al asignar vehículo');
    } finally {
      setSaving(false);
    }
  };

  // View details
  const openDetailModal = (item: Taxista | Vehiculo, type: 'taxista' | 'vehiculo') => {
    setSelectedDetail(item);
    setDetailType(type);
    setDetailModalVisible(true);
  };

  // Change password
  const openPasswordModal = (user: {id: string, nombre: string, username: string}) => {
    setSelectedUserForPassword(user);
    setNewPassword('');
    setConfirmPassword('');
    setPasswordModalVisible(true);
  };

  const changePassword = async () => {
    if (!selectedUserForPassword) return;
    
    if (newPassword.length < 6) {
      setSnackbar({ visible: true, message: 'La contraseña debe tener al menos 6 caracteres', type: 'error' });
      return;
    }
    
    if (newPassword !== confirmPassword) {
      setSnackbar({ visible: true, message: 'Las contraseñas no coinciden', type: 'error' });
      return;
    }

    setSaving(true);
    try {
      const token = await AsyncStorage.getItem('token');
      await axios.put(`${API_URL}/superadmin/users/${selectedUserForPassword.id}/change-password`, {
        new_password: newPassword
      }, { headers: { Authorization: `Bearer ${token}` }});
      
      setPasswordModalVisible(false);
      setSnackbar({ visible: true, message: `Contraseña de "${selectedUserForPassword.nombre}" actualizada correctamente`, type: 'success' });
    } catch (error: any) {
      setSnackbar({ visible: true, message: error.response?.data?.detail || 'Error al cambiar contraseña', type: 'error' });
    } finally {
      setSaving(false);
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

        {/* Stats */}
        <View style={styles.statsContainer}>
          <Card style={styles.statCard}>
            <Card.Content style={styles.statContent}>
              <MaterialCommunityIcons name="account-group" size={32} color="#4CAF50" />
              <Text variant="headlineMedium" style={styles.statNumber}>{taxistas.length}</Text>
              <Text variant="bodySmall">Taxistas</Text>
            </Card.Content>
          </Card>
          <Card style={styles.statCard}>
            <Card.Content style={styles.statContent}>
              <MaterialCommunityIcons name="car" size={32} color="#2196F3" />
              <Text variant="headlineMedium" style={styles.statNumber}>{vehiculos.length}</Text>
              <Text variant="bodySmall">Vehículos</Text>
            </Card.Content>
          </Card>
          <Card style={styles.statCard}>
            <Card.Content style={styles.statContent}>
              <MaterialCommunityIcons name="domain" size={32} color="#FF9800" />
              <Text variant="headlineMedium" style={styles.statNumber}>{organizations.length}</Text>
              <Text variant="bodySmall">Organizaciones</Text>
            </Card.Content>
          </Card>
        </View>

        {/* Tabs */}
        <View style={styles.tabContainer}>
          <SegmentedButtons
            value={activeTab}
            onValueChange={setActiveTab}
            buttons={[
              { value: 'taxistas', label: `Taxistas (${filteredTaxistas.length})`, icon: 'account-group' },
              { value: 'admins', label: `Admins (${filteredAdmins.length})`, icon: 'shield-account' },
              { value: 'vehiculos', label: `Vehículos (${filteredVehiculos.length})`, icon: 'car' },
            ]}
          />
        </View>

        {/* Filter by Organization */}
        {organizations.length > 0 && (
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
        )}

        <View style={styles.content}>
          {/* TAXISTAS TAB */}
          {activeTab === 'taxistas' && (
            <>
              {organizations.length === 0 ? (
                <Card style={styles.warningCard}>
                  <Card.Content style={styles.warningContent}>
                    <MaterialCommunityIcons name="alert" size={48} color="#FF9800" />
                    <Text variant="titleMedium" style={{ marginTop: 16 }}>Primero crea una organización</Text>
                    <Text variant="bodySmall" style={{ color: '#666', textAlign: 'center', marginTop: 8 }}>
                      Antes de crear taxistas, debes crear al menos una organización en la sección "Organizaciones"
                    </Text>
                  </Card.Content>
                </Card>
              ) : filteredTaxistas.length === 0 ? (
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
                  <Card key={taxista.id} style={[styles.itemCard, taxista.activo === false && styles.itemCardInactive]}>
                    <Card.Content>
                      <View style={styles.itemHeader}>
                        <View style={styles.itemInfo}>
                          <View style={[styles.avatarContainer, { backgroundColor: taxista.activo === false ? '#ccc' : '#4CAF50' }]}>
                            <MaterialCommunityIcons name="account" size={28} color="#fff" />
                          </View>
                          <View style={{ marginLeft: 12, flex: 1 }}>
                            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                              <Text variant="titleMedium">{taxista.nombre}</Text>
                              {taxista.activo === false && (
                                <Chip compact style={styles.inactiveChip}>Inactivo</Chip>
                              )}
                            </View>
                            <Text variant="bodySmall" style={styles.subText}>@{taxista.username}</Text>
                            {taxista.telefono && (
                              <Text variant="bodySmall" style={styles.subText}>📞 {taxista.telefono}</Text>
                            )}
                            {taxista.vehiculo_asignado_matricula ? (
                              <Chip icon="car" compact style={styles.vehiculoChip}>
                                {taxista.vehiculo_asignado_matricula}
                              </Chip>
                            ) : (
                              <Text variant="bodySmall" style={styles.noVehiculo}>Sin vehículo asignado</Text>
                            )}
                          </View>
                        </View>
                        <View style={styles.itemActions}>
                          <Chip style={styles.orgChip}>{taxista.organization_nombre || 'Sin org'}</Chip>
                          <Switch
                            value={taxista.activo !== false}
                            onValueChange={() => toggleTaxistaActivo(taxista)}
                          />
                        </View>
                      </View>
                    </Card.Content>
                    <Card.Actions style={styles.cardActions}>
                      <Button onPress={() => openDetailModal(taxista, 'taxista')} icon="eye">Ver</Button>
                      <Button onPress={() => openTaxistaModal(taxista)} icon="pencil">Editar</Button>
                      <Button onPress={() => openPasswordModal({id: taxista.id, nombre: taxista.nombre, username: taxista.username})} icon="lock-reset">Clave</Button>
                      <Button onPress={() => openAssignVehiculoModal(taxista)} icon="car">Vehículo</Button>
                      <Button onPress={() => deleteTaxista(taxista)} icon="delete" textColor="#f44336">Eliminar</Button>
                    </Card.Actions>
                  </Card>
                ))
              )}
            </>
          )}

          {/* ADMINS TAB */}
          {activeTab === 'admins' && (
            <>
              {filteredAdmins.length === 0 ? (
                <Card style={styles.emptyCard}>
                  <Card.Content style={styles.emptyContent}>
                    <MaterialCommunityIcons name="shield-account-outline" size={64} color="#ccc" />
                    <Text variant="titleMedium" style={styles.emptyText}>No hay administradores</Text>
                    <Text variant="bodySmall" style={{ color: '#666', textAlign: 'center', marginTop: 8 }}>
                      Los administradores se crean desde la sección "Organizaciones"
                    </Text>
                  </Card.Content>
                </Card>
              ) : (
                filteredAdmins.map(admin => (
                  <Card key={admin.id} style={styles.itemCard}>
                    <Card.Content>
                      <View style={styles.itemHeader}>
                        <View style={styles.itemInfo}>
                          <View style={[styles.avatarContainer, { backgroundColor: '#9C27B0' }]}>
                            <MaterialCommunityIcons name="shield-account" size={28} color="#fff" />
                          </View>
                          <View style={{ marginLeft: 12, flex: 1 }}>
                            <Text variant="titleMedium">{admin.nombre}</Text>
                            <Text variant="bodySmall" style={styles.subText}>@{admin.username}</Text>
                            {admin.email && (
                              <Text variant="bodySmall" style={styles.subText}>{admin.email}</Text>
                            )}
                          </View>
                        </View>
                        <Chip style={styles.orgChip}>{admin.organization_nombre || 'Sin org'}</Chip>
                      </View>
                    </Card.Content>
                    <Card.Actions style={styles.cardActions}>
                      <Button onPress={() => openPasswordModal({id: admin.id, nombre: admin.nombre, username: admin.username})} icon="lock-reset">Cambiar Clave</Button>
                    </Card.Actions>
                  </Card>
                ))
              )}
            </>
          )}

          {/* VEHICULOS TAB */}
          {activeTab === 'vehiculos' && (
            <>
              {organizations.length === 0 ? (
                <Card style={styles.warningCard}>
                  <Card.Content style={styles.warningContent}>
                    <MaterialCommunityIcons name="alert" size={48} color="#FF9800" />
                    <Text variant="titleMedium" style={{ marginTop: 16 }}>Primero crea una organización</Text>
                    <Text variant="bodySmall" style={{ color: '#666', textAlign: 'center', marginTop: 8 }}>
                      Antes de crear vehículos, debes crear al menos una organización en la sección "Organizaciones"
                    </Text>
                  </Card.Content>
                </Card>
              ) : filteredVehiculos.length === 0 ? (
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
                          <View style={[styles.avatarContainer, { backgroundColor: '#2196F3' }]}>
                            <MaterialCommunityIcons name="car" size={28} color="#fff" />
                          </View>
                          <View style={{ marginLeft: 12, flex: 1 }}>
                            <Text variant="titleMedium">{vehiculo.matricula}</Text>
                            <Text variant="bodySmall" style={styles.subText}>
                              {vehiculo.marca} {vehiculo.modelo}
                            </Text>
                            {vehiculo.licencia && (
                              <Text variant="bodySmall" style={styles.subText}>Licencia: {vehiculo.licencia}</Text>
                            )}
                            {vehiculo.taxista_asignado_nombre ? (
                              <Chip icon="account" compact style={styles.taxistaChip}>
                                {vehiculo.taxista_asignado_nombre}
                              </Chip>
                            ) : (
                              <Text variant="bodySmall" style={styles.noVehiculo}>Sin taxista asignado</Text>
                            )}
                          </View>
                        </View>
                        <Chip style={styles.orgChip}>{vehiculo.organization_nombre || 'Sin org'}</Chip>
                      </View>
                    </Card.Content>
                    <Card.Actions style={styles.cardActions}>
                      <Button onPress={() => openDetailModal(vehiculo, 'vehiculo')} icon="eye">Ver</Button>
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
      {organizations.length > 0 && (
        <FAB
          icon="plus"
          style={styles.fab}
          onPress={() => activeTab === 'taxistas' ? openTaxistaModal() : openVehiculoModal()}
          label={activeTab === 'taxistas' ? 'Nuevo Taxista' : 'Nuevo Vehículo'}
        />
      )}

      {/* Modal Taxista */}
      <Portal>
        <Modal visible={taxistaModalVisible} onDismiss={() => setTaxistaModalVisible(false)} contentContainerStyle={styles.modal}>
          <ScrollView showsVerticalScrollIndicator={false}>
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

            <TextInput
              label="Email"
              value={taxistaForm.email}
              onChangeText={(v) => setTaxistaForm({...taxistaForm, email: v})}
              mode="outlined"
              style={styles.input}
              keyboardType="email-address"
            />

            <TextInput
              label="Número de Licencia"
              value={taxistaForm.licencia}
              onChangeText={(v) => setTaxistaForm({...taxistaForm, licencia: v})}
              mode="outlined"
              style={styles.input}
            />
            
            <Divider style={{ marginVertical: 16 }} />
            <Text variant="labelLarge" style={{ marginBottom: 8 }}>Organización *</Text>
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

            <View style={styles.switchRow}>
              <Text variant="bodyLarge">Taxista activo</Text>
              <Switch
                value={taxistaForm.activo}
                onValueChange={(v) => setTaxistaForm({...taxistaForm, activo: v})}
              />
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
          <ScrollView showsVerticalScrollIndicator={false}>
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
            <TextInput
              label="Plazas"
              value={String(vehiculoForm.plazas)}
              onChangeText={(v) => setVehiculoForm({...vehiculoForm, plazas: parseInt(v) || 4})}
              mode="outlined"
              style={styles.input}
              keyboardType="numeric"
            />
            <TextInput
              label="Kilómetros Iniciales"
              value={String(vehiculoForm.km_iniciales)}
              onChangeText={(v) => setVehiculoForm({...vehiculoForm, km_iniciales: parseInt(v) || 0})}
              mode="outlined"
              style={styles.input}
              keyboardType="numeric"
            />
            <TextInput
              label="Fecha de Compra (dd/mm/yyyy)"
              value={vehiculoForm.fecha_compra}
              onChangeText={(v) => setVehiculoForm({...vehiculoForm, fecha_compra: v})}
              mode="outlined"
              style={styles.input}
            />

            <View style={styles.switchRow}>
              <Text variant="bodyLarge">Vehículo activo</Text>
              <Switch
                value={vehiculoForm.activo}
                onValueChange={(v) => setVehiculoForm({...vehiculoForm, activo: v})}
              />
            </View>
            
            <Divider style={{ marginVertical: 16 }} />
            <Text variant="labelLarge" style={{ marginBottom: 8 }}>Organización *</Text>
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

      {/* Modal Asignar Vehículo */}
      <Portal>
        <Modal visible={assignVehiculoModalVisible} onDismiss={() => setAssignVehiculoModalVisible(false)} contentContainerStyle={styles.modal}>
          <Text variant="headlineSmall" style={styles.modalTitle}>Asignar Vehículo</Text>
          {selectedTaxistaForAssign && (
            <Text variant="bodyMedium" style={{ marginBottom: 16, color: '#666' }}>
              Taxista: <Text style={{ fontWeight: 'bold' }}>{selectedTaxistaForAssign.nombre}</Text>
            </Text>
          )}
          
          <List.Section>
            <List.Item
              title="Sin vehículo"
              description="Quitar vehículo asignado"
              left={props => <List.Icon {...props} icon="car-off" />}
              onPress={() => assignVehiculo(null)}
              style={styles.listItem}
            />
            <Divider />
            {selectedTaxistaForAssign && getAvailableVehiculos(selectedTaxistaForAssign).map(v => (
              <List.Item
                key={v.id}
                title={v.matricula}
                description={`${v.marca} ${v.modelo}${v.taxista_asignado_id === selectedTaxistaForAssign.id ? ' (actual)' : ''}`}
                left={props => <List.Icon {...props} icon="car" color={v.taxista_asignado_id === selectedTaxistaForAssign.id ? '#4CAF50' : undefined} />}
                onPress={() => assignVehiculo(v.id)}
                style={[styles.listItem, v.taxista_asignado_id === selectedTaxistaForAssign.id && styles.listItemActive]}
              />
            ))}
          </List.Section>
          
          <Button mode="outlined" onPress={() => setAssignVehiculoModalVisible(false)} style={{ marginTop: 16 }}>
            Cancelar
          </Button>
        </Modal>
      </Portal>

      {/* Modal Detalles */}
      <Portal>
        <Modal visible={detailModalVisible} onDismiss={() => setDetailModalVisible(false)} contentContainerStyle={styles.modal}>
          {selectedDetail && (
            <ScrollView showsVerticalScrollIndicator={false}>
              <Text variant="headlineSmall" style={styles.modalTitle}>
                {detailType === 'taxista' ? '👤 Detalles del Taxista' : '🚗 Detalles del Vehículo'}
              </Text>
              
              {detailType === 'taxista' && (
                <>
                  <List.Item title="Nombre" description={(selectedDetail as Taxista).nombre} left={props => <List.Icon {...props} icon="account" />} />
                  <List.Item title="Usuario" description={(selectedDetail as Taxista).username} left={props => <List.Icon {...props} icon="at" />} />
                  <List.Item title="Teléfono" description={(selectedDetail as Taxista).telefono || 'No especificado'} left={props => <List.Icon {...props} icon="phone" />} />
                  <List.Item title="Email" description={(selectedDetail as Taxista).email || 'No especificado'} left={props => <List.Icon {...props} icon="email" />} />
                  <List.Item title="Organización" description={(selectedDetail as Taxista).organization_nombre || 'Sin asignar'} left={props => <List.Icon {...props} icon="domain" />} />
                  <List.Item title="Vehículo" description={(selectedDetail as Taxista).vehiculo_asignado_matricula || 'Sin vehículo'} left={props => <List.Icon {...props} icon="car" />} />
                  <List.Item title="Estado" description={(selectedDetail as Taxista).activo !== false ? 'Activo' : 'Inactivo'} left={props => <List.Icon {...props} icon={(selectedDetail as Taxista).activo !== false ? "check-circle" : "close-circle"} color={(selectedDetail as Taxista).activo !== false ? '#4CAF50' : '#f44336'} />} />
                </>
              )}
              
              {detailType === 'vehiculo' && (
                <>
                  <List.Item title="Matrícula" description={(selectedDetail as Vehiculo).matricula} left={props => <List.Icon {...props} icon="card-text" />} />
                  <List.Item title="Marca" description={(selectedDetail as Vehiculo).marca || 'No especificada'} left={props => <List.Icon {...props} icon="car" />} />
                  <List.Item title="Modelo" description={(selectedDetail as Vehiculo).modelo || 'No especificado'} left={props => <List.Icon {...props} icon="car-side" />} />
                  <List.Item title="Licencia" description={(selectedDetail as Vehiculo).licencia || 'No especificada'} left={props => <List.Icon {...props} icon="license" />} />
                  <List.Item title="Organización" description={(selectedDetail as Vehiculo).organization_nombre || 'Sin asignar'} left={props => <List.Icon {...props} icon="domain" />} />
                  <List.Item title="Taxista Asignado" description={(selectedDetail as Vehiculo).taxista_asignado_nombre || 'Sin asignar'} left={props => <List.Icon {...props} icon="account" />} />
                </>
              )}
              
              <Button mode="outlined" onPress={() => setDetailModalVisible(false)} style={{ marginTop: 16 }}>
                Cerrar
              </Button>
            </ScrollView>
          )}
        </Modal>

        {/* MODAL CAMBIAR CONTRASEÑA */}
        <Modal visible={passwordModalVisible} onDismiss={() => setPasswordModalVisible(false)} contentContainerStyle={styles.modal}>
          <Text variant="titleLarge" style={styles.modalTitle}>
            🔐 Cambiar Contraseña
          </Text>
          {selectedUserForPassword && (
            <>
              <Text variant="bodyMedium" style={{ marginBottom: 16, color: '#666' }}>
                Usuario: <Text style={{ fontWeight: 'bold' }}>{selectedUserForPassword.nombre}</Text> ({selectedUserForPassword.username})
              </Text>
              <TextInput
                label="Nueva Contraseña"
                value={newPassword}
                onChangeText={setNewPassword}
                secureTextEntry={!showNewPassword}
                mode="outlined"
                style={styles.input}
                right={<TextInput.Icon icon={showNewPassword ? "eye-off" : "eye"} onPress={() => setShowNewPassword(!showNewPassword)} />}
              />
              <TextInput
                label="Confirmar Contraseña"
                value={confirmPassword}
                onChangeText={setConfirmPassword}
                secureTextEntry={!showConfirmPassword}
                mode="outlined"
                style={styles.input}
                right={<TextInput.Icon icon={showConfirmPassword ? "eye-off" : "eye"} onPress={() => setShowConfirmPassword(!showConfirmPassword)} />}
              />
              <Text variant="bodySmall" style={{ color: '#999', marginBottom: 16 }}>
                * Mínimo 6 caracteres
              </Text>
              <View style={styles.modalActions}>
                <Button onPress={() => setPasswordModalVisible(false)}>Cancelar</Button>
                <Button mode="contained" onPress={changePassword} loading={saving} disabled={saving}>
                  Guardar
                </Button>
              </View>
            </>
          )}
        </Modal>
      </Portal>

      {/* SNACKBAR */}
      <Portal>
        <Modal visible={snackbar.visible} onDismiss={() => setSnackbar({...snackbar, visible: false})} contentContainerStyle={[styles.modal, { padding: 16, maxWidth: 400 }]}>
          <Text variant="bodyMedium" style={{ color: snackbar.type === 'error' ? '#f44336' : '#4CAF50' }}>
            {snackbar.type === 'error' ? '❌' : '✅'} {snackbar.message}
          </Text>
          <Button onPress={() => setSnackbar({...snackbar, visible: false})} style={{ marginTop: 16 }}>
            Cerrar
          </Button>
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
  statsContainer: { flexDirection: 'row', padding: 16, gap: 12 },
  statCard: { flex: 1, borderRadius: 12 },
  statContent: { alignItems: 'center', padding: 8 },
  statNumber: { fontWeight: 'bold', marginTop: 4 },
  tabContainer: { padding: 16, backgroundColor: '#fff' },
  filterContainer: { padding: 16, backgroundColor: '#fff', borderBottomWidth: 1, borderBottomColor: '#e0e0e0' },
  filterLabel: { marginBottom: 8, color: '#666' },
  filterChip: { marginRight: 8 },
  content: { padding: 16, paddingBottom: 100 },
  itemCard: { marginBottom: 12, borderRadius: 12 },
  itemCardInactive: { opacity: 0.7, backgroundColor: '#f5f5f5' },
  itemHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' },
  itemInfo: { flexDirection: 'row', alignItems: 'flex-start', flex: 1 },
  itemActions: { alignItems: 'flex-end', gap: 8 },
  avatarContainer: { width: 48, height: 48, borderRadius: 24, alignItems: 'center', justifyContent: 'center' },
  subText: { color: '#666', marginTop: 2 },
  orgChip: { backgroundColor: '#E3F2FD' },
  vehiculoChip: { backgroundColor: '#E8F5E9', marginTop: 4 },
  taxistaChip: { backgroundColor: '#FFF3E0', marginTop: 4 },
  inactiveChip: { backgroundColor: '#ffcdd2' },
  noVehiculo: { color: '#999', fontStyle: 'italic', marginTop: 4 },
  cardActions: { flexWrap: 'wrap', justifyContent: 'flex-start', paddingTop: 0 },
  emptyCard: { borderRadius: 12, marginTop: 32 },
  emptyContent: { alignItems: 'center', padding: 48 },
  emptyText: { color: '#666', marginTop: 16 },
  warningCard: { borderRadius: 12, marginTop: 32, backgroundColor: '#FFF3E0' },
  warningContent: { alignItems: 'center', padding: 32 },
  fab: { position: 'absolute', margin: 16, right: 0, bottom: 0, backgroundColor: '#0066CC' },
  modal: { backgroundColor: 'white', padding: 24, margin: 20, borderRadius: 12, maxHeight: '90%', maxWidth: 500, alignSelf: 'center', width: '100%' },
  modalTitle: { marginBottom: 16, fontWeight: 'bold' },
  input: { marginBottom: 12 },
  orgSelector: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  orgSelectorChip: { marginBottom: 8 },
  switchRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 12 },
  modalActions: { flexDirection: 'row', justifyContent: 'flex-end', gap: 12, marginTop: 24 },
  listItem: { paddingVertical: 8 },
  listItemActive: { backgroundColor: '#E8F5E9' },
});
