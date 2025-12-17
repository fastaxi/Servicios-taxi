import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ScrollView, RefreshControl, Platform } from 'react-native';
import { Text, Card, Button, FAB, Portal, Modal, TextInput, useTheme, ActivityIndicator, IconButton, Chip, Divider, Switch } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_URL } from '../../config/api';

interface Organization {
  id: string;
  nombre: string;
  slug: string;
  cif: string;
  direccion: string;
  localidad: string;
  provincia: string;
  telefono: string;
  email: string;
  web: string;
  color_primario: string;
  color_secundario: string;
  activa: boolean;
  total_taxistas: number;
  total_vehiculos: number;
  total_clientes: number;
  created_at: string;
}

interface NewAdmin {
  username: string;
  password: string;
  nombre: string;
}

export default function OrganizationsScreen() {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [adminModalVisible, setAdminModalVisible] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedOrg, setSelectedOrg] = useState<Organization | null>(null);
  const [saving, setSaving] = useState(false);
  const theme = useTheme();

  // Form states for new organization
  const [formData, setFormData] = useState({
    nombre: '',
    cif: '',
    direccion: '',
    localidad: '',
    provincia: '',
    telefono: '',
    email: '',
    web: '',
    color_primario: '#0066CC',
    color_secundario: '#FFD700',
  });

  // Form state for new admin
  const [adminData, setAdminData] = useState<NewAdmin>({
    username: '',
    password: '',
    nombre: '',
  });

  useEffect(() => {
    loadOrganizations();
  }, []);

  const loadOrganizations = async () => {
    try {
      const token = await AsyncStorage.getItem('token');
      const response = await axios.get(`${API_URL}/organizations`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setOrganizations(response.data);
    } catch (error) {
      console.error('Error loading organizations:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleCreateOrganization = async () => {
    if (!formData.nombre.trim()) {
      alert('El nombre es obligatorio');
      return;
    }

    setSaving(true);
    try {
      const token = await AsyncStorage.getItem('token');
      await axios.post(`${API_URL}/organizations`, formData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setModalVisible(false);
      setFormData({
        nombre: '',
        cif: '',
        direccion: '',
        localidad: '',
        provincia: '',
        telefono: '',
        email: '',
        web: '',
        color_primario: '#0066CC',
        color_secundario: '#FFD700',
      });
      loadOrganizations();
      alert('Organización creada correctamente');
    } catch (error: any) {
      console.error('Error creating organization:', error);
      alert(error.response?.data?.detail || 'Error al crear organización');
    } finally {
      setSaving(false);
    }
  };

  const handleCreateAdmin = async () => {
    if (!selectedOrg) return;
    if (!adminData.username.trim() || !adminData.password.trim() || !adminData.nombre.trim()) {
      alert('Todos los campos son obligatorios');
      return;
    }

    setSaving(true);
    try {
      const token = await AsyncStorage.getItem('token');
      await axios.post(`${API_URL}/organizations/${selectedOrg.id}/admin`, adminData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setAdminModalVisible(false);
      setAdminData({ username: '', password: '', nombre: '' });
      alert(`Administrador "${adminData.username}" creado para ${selectedOrg.nombre}`);
    } catch (error: any) {
      console.error('Error creating admin:', error);
      alert(error.response?.data?.detail || 'Error al crear administrador');
    } finally {
      setSaving(false);
    }
  };

  const handleToggleActive = async (org: Organization) => {
    try {
      const token = await AsyncStorage.getItem('token');
      await axios.put(`${API_URL}/organizations/${org.id}`, 
        { activa: !org.activa },
        { headers: { Authorization: `Bearer ${token}` }}
      );
      loadOrganizations();
    } catch (error: any) {
      console.error('Error toggling organization:', error);
      alert(error.response?.data?.detail || 'Error al actualizar organización');
    }
  };

  const handleDeleteOrganization = async (org: Organization) => {
    const confirmMsg = `¿Estás seguro de eliminar "${org.nombre}"? Se eliminarán TODOS los datos: usuarios, vehículos, clientes, turnos y servicios.`;
    
    if (Platform.OS === 'web') {
      if (!window.confirm(confirmMsg)) return;
    } else {
      // For mobile, we'd use Alert.alert but for simplicity:
      return; // Disable delete on mobile for safety
    }

    try {
      const token = await AsyncStorage.getItem('token');
      await axios.delete(`${API_URL}/organizations/${org.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      loadOrganizations();
      alert('Organización eliminada correctamente');
    } catch (error: any) {
      console.error('Error deleting organization:', error);
      alert(error.response?.data?.detail || 'Error al eliminar organización');
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadOrganizations();
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" />
        <Text style={{ marginTop: 16 }}>Cargando organizaciones...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        <View style={styles.header}>
          <Text variant="headlineMedium" style={styles.title}>🏢 Organizaciones</Text>
          <Text variant="bodyMedium" style={styles.subtitle}>
            {organizations.length} organizaciones registradas
          </Text>
        </View>

        <View style={styles.content}>
          {organizations.map((org) => (
            <Card key={org.id} style={styles.orgCard}>
              <Card.Content>
                <View style={styles.orgHeader}>
                  <View style={styles.orgTitleContainer}>
                    <View style={[styles.statusDot, { backgroundColor: org.activa ? '#4caf50' : '#f44336' }]} />
                    <View>
                      <Text variant="titleLarge">{org.nombre}</Text>
                      <Text variant="bodySmall" style={styles.slugText}>/{org.slug}</Text>
                    </View>
                  </View>
                  <Switch
                    value={org.activa}
                    onValueChange={() => handleToggleActive(org)}
                  />
                </View>

                <Divider style={styles.divider} />

                <View style={styles.orgDetails}>
                  {org.localidad && (
                    <View style={styles.detailRow}>
                      <MaterialCommunityIcons name="map-marker" size={16} color="#666" />
                      <Text variant="bodySmall" style={styles.detailText}>
                        {org.localidad}{org.provincia ? `, ${org.provincia}` : ''}
                      </Text>
                    </View>
                  )}
                  {org.telefono && (
                    <View style={styles.detailRow}>
                      <MaterialCommunityIcons name="phone" size={16} color="#666" />
                      <Text variant="bodySmall" style={styles.detailText}>{org.telefono}</Text>
                    </View>
                  )}
                  {org.email && (
                    <View style={styles.detailRow}>
                      <MaterialCommunityIcons name="email" size={16} color="#666" />
                      <Text variant="bodySmall" style={styles.detailText}>{org.email}</Text>
                    </View>
                  )}
                </View>

                <View style={styles.statsRow}>
                  <Chip icon="account" style={styles.statChip}>{org.total_taxistas} taxistas</Chip>
                  <Chip icon="car" style={styles.statChip}>{org.total_vehiculos} vehículos</Chip>
                  <Chip icon="briefcase" style={styles.statChip}>{org.total_clientes} clientes</Chip>
                </View>
              </Card.Content>
              
              <Card.Actions>
                <Button 
                  mode="outlined" 
                  onPress={() => {
                    setSelectedOrg(org);
                    setAdminModalVisible(true);
                  }}
                  icon="account-plus"
                >
                  Crear Admin
                </Button>
                <Button 
                  mode="outlined" 
                  textColor="#f44336"
                  onPress={() => handleDeleteOrganization(org)}
                  icon="delete"
                >
                  Eliminar
                </Button>
              </Card.Actions>
            </Card>
          ))}

          {organizations.length === 0 && (
            <Card style={styles.emptyCard}>
              <Card.Content style={styles.emptyContent}>
                <MaterialCommunityIcons name="domain-plus" size={64} color="#ccc" />
                <Text variant="headlineSmall" style={styles.emptyTitle}>No hay organizaciones</Text>
                <Text variant="bodyMedium" style={styles.emptyText}>
                  Crea tu primera organización para empezar a gestionar empresas de taxi
                </Text>
                <Button mode="contained" onPress={() => setModalVisible(true)} style={{ marginTop: 24 }}>
                  Crear Primera Organización
                </Button>
              </Card.Content>
            </Card>
          )}
        </View>
      </ScrollView>

      {/* FAB to create new organization */}
      <FAB
        icon="plus"
        style={styles.fab}
        onPress={() => setModalVisible(true)}
        label="Nueva Organización"
      />

      {/* Modal: Create Organization */}
      <Portal>
        <Modal visible={modalVisible} onDismiss={() => setModalVisible(false)} contentContainerStyle={styles.modal}>
          <ScrollView>
            <Text variant="headlineSmall" style={styles.modalTitle}>Nueva Organización</Text>
            
            <TextInput
              label="Nombre de la empresa *"
              value={formData.nombre}
              onChangeText={(text) => setFormData({...formData, nombre: text})}
              mode="outlined"
              style={styles.input}
            />
            <TextInput
              label="CIF/NIF"
              value={formData.cif}
              onChangeText={(text) => setFormData({...formData, cif: text})}
              mode="outlined"
              style={styles.input}
            />
            <TextInput
              label="Dirección"
              value={formData.direccion}
              onChangeText={(text) => setFormData({...formData, direccion: text})}
              mode="outlined"
              style={styles.input}
            />
            <View style={styles.row}>
              <TextInput
                label="Localidad"
                value={formData.localidad}
                onChangeText={(text) => setFormData({...formData, localidad: text})}
                mode="outlined"
                style={[styles.input, { flex: 1, marginRight: 8 }]}
              />
              <TextInput
                label="Provincia"
                value={formData.provincia}
                onChangeText={(text) => setFormData({...formData, provincia: text})}
                mode="outlined"
                style={[styles.input, { flex: 1 }]}
              />
            </View>
            <TextInput
              label="Teléfono"
              value={formData.telefono}
              onChangeText={(text) => setFormData({...formData, telefono: text})}
              mode="outlined"
              style={styles.input}
              keyboardType="phone-pad"
            />
            <TextInput
              label="Email"
              value={formData.email}
              onChangeText={(text) => setFormData({...formData, email: text})}
              mode="outlined"
              style={styles.input}
              keyboardType="email-address"
            />
            <TextInput
              label="Web"
              value={formData.web}
              onChangeText={(text) => setFormData({...formData, web: text})}
              mode="outlined"
              style={styles.input}
            />
            
            <View style={styles.modalActions}>
              <Button mode="outlined" onPress={() => setModalVisible(false)} disabled={saving}>
                Cancelar
              </Button>
              <Button mode="contained" onPress={handleCreateOrganization} loading={saving} disabled={saving}>
                Crear Organización
              </Button>
            </View>
          </ScrollView>
        </Modal>
      </Portal>

      {/* Modal: Create Admin */}
      <Portal>
        <Modal visible={adminModalVisible} onDismiss={() => setAdminModalVisible(false)} contentContainerStyle={styles.modal}>
          <Text variant="headlineSmall" style={styles.modalTitle}>
            Crear Administrador
          </Text>
          {selectedOrg && (
            <Text variant="bodyMedium" style={styles.modalSubtitle}>
              Para: {selectedOrg.nombre}
            </Text>
          )}
          
          <TextInput
            label="Nombre completo *"
            value={adminData.nombre}
            onChangeText={(text) => setAdminData({...adminData, nombre: text})}
            mode="outlined"
            style={styles.input}
          />
          <TextInput
            label="Usuario (login) *"
            value={adminData.username}
            onChangeText={(text) => setAdminData({...adminData, username: text})}
            mode="outlined"
            style={styles.input}
            autoCapitalize="none"
          />
          <TextInput
            label="Contraseña *"
            value={adminData.password}
            onChangeText={(text) => setAdminData({...adminData, password: text})}
            mode="outlined"
            style={styles.input}
            secureTextEntry
          />
          
          <View style={styles.modalActions}>
            <Button mode="outlined" onPress={() => setAdminModalVisible(false)} disabled={saving}>
              Cancelar
            </Button>
            <Button mode="contained" onPress={handleCreateAdmin} loading={saving} disabled={saving}>
              Crear Admin
            </Button>
          </View>
        </Modal>
      </Portal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  scrollView: {
    flex: 1,
  },
  header: {
    padding: 24,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  title: {
    fontWeight: 'bold',
    color: '#333',
  },
  subtitle: {
    color: '#666',
    marginTop: 4,
  },
  content: {
    padding: 16,
    paddingBottom: 100,
  },
  orgCard: {
    marginBottom: 16,
    borderRadius: 12,
  },
  orgHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  orgTitleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 12,
  },
  slugText: {
    color: '#666',
  },
  divider: {
    marginVertical: 12,
  },
  orgDetails: {
    gap: 8,
  },
  detailRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  detailText: {
    color: '#666',
  },
  statsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 12,
  },
  statChip: {
    backgroundColor: '#f0f0f0',
  },
  emptyCard: {
    borderRadius: 12,
    marginTop: 32,
  },
  emptyContent: {
    alignItems: 'center',
    padding: 48,
  },
  emptyTitle: {
    marginTop: 24,
    color: '#666',
  },
  emptyText: {
    textAlign: 'center',
    color: '#999',
    marginTop: 8,
  },
  fab: {
    position: 'absolute',
    margin: 16,
    right: 0,
    bottom: 0,
    backgroundColor: '#0066CC',
  },
  modal: {
    backgroundColor: 'white',
    padding: 24,
    margin: 20,
    borderRadius: 12,
    maxHeight: '90%',
    maxWidth: 500,
    alignSelf: 'center',
    width: '100%',
  },
  modalTitle: {
    marginBottom: 8,
    fontWeight: 'bold',
  },
  modalSubtitle: {
    color: '#666',
    marginBottom: 16,
  },
  input: {
    marginBottom: 12,
  },
  row: {
    flexDirection: 'row',
  },
  modalActions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 12,
    marginTop: 16,
  },
});
