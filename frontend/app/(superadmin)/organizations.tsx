import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ScrollView, RefreshControl, Platform, Image, TouchableOpacity } from 'react-native';
import { Text, Card, Button, FAB, Portal, Modal, TextInput, useTheme, ActivityIndicator, IconButton, Chip, Divider, Switch } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as ImagePicker from 'expo-image-picker';
import { API_URL } from '../../config/api';

interface Organization {
  id: string;
  nombre: string;
  slug: string;
  cif: string;
  direccion: string;
  codigo_postal: string;
  localidad: string;
  provincia: string;
  telefono: string;
  email: string;
  web: string;
  color_primario: string;
  color_secundario: string;
  logo_base64: string | null;
  notas: string;
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

const emptyFormData = {
  nombre: '',
  cif: '',
  direccion: '',
  codigo_postal: '',
  localidad: '',
  provincia: '',
  telefono: '',
  email: '',
  web: '',
  color_primario: '#0066CC',
  color_secundario: '#FFD700',
  logo_base64: '' as string | null,
  notas: '',
};

export default function OrganizationsScreen() {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [adminModalVisible, setAdminModalVisible] = useState(false);
  const [selectedOrg, setSelectedOrg] = useState<Organization | null>(null);
  const [saving, setSaving] = useState(false);
  const theme = useTheme();

  // Form states for new/edit organization
  const [formData, setFormData] = useState(emptyFormData);
  const [editFormData, setEditFormData] = useState(emptyFormData);

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

  const pickImage = async (isEdit: boolean) => {
    try {
      // Request permission
      const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (status !== 'granted') {
        alert('Se necesita permiso para acceder a la galería');
        return;
      }

      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        aspect: [1, 1],
        quality: 0.5,
        base64: true,
      });

      if (!result.canceled && result.assets[0].base64) {
        const base64Image = `data:image/jpeg;base64,${result.assets[0].base64}`;
        if (isEdit) {
          setEditFormData({ ...editFormData, logo_base64: base64Image });
        } else {
          setFormData({ ...formData, logo_base64: base64Image });
        }
      }
    } catch (error) {
      console.error('Error picking image:', error);
      alert('Error al seleccionar imagen');
    }
  };

  const removeLogo = (isEdit: boolean) => {
    if (isEdit) {
      setEditFormData({ ...editFormData, logo_base64: null });
    } else {
      setFormData({ ...formData, logo_base64: null });
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
      setFormData(emptyFormData);
      loadOrganizations();
      alert('Organizacion creada correctamente');
    } catch (error: any) {
      console.error('Error creating organization:', error);
      alert(error.response?.data?.detail || 'Error al crear organizacion');
    } finally {
      setSaving(false);
    }
  };

  const handleEditOrganization = async () => {
    if (!selectedOrg) return;
    if (!editFormData.nombre.trim()) {
      alert('El nombre es obligatorio');
      return;
    }

    setSaving(true);
    try {
      const token = await AsyncStorage.getItem('token');
      await axios.put(`${API_URL}/organizations/${selectedOrg.id}`, editFormData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setEditModalVisible(false);
      setSelectedOrg(null);
      loadOrganizations();
      alert('Organizacion actualizada correctamente');
    } catch (error: any) {
      console.error('Error updating organization:', error);
      alert(error.response?.data?.detail || 'Error al actualizar organizacion');
    } finally {
      setSaving(false);
    }
  };

  const openEditModal = (org: Organization) => {
    setSelectedOrg(org);
    setEditFormData({
      nombre: org.nombre || '',
      cif: org.cif || '',
      direccion: org.direccion || '',
      codigo_postal: org.codigo_postal || '',
      localidad: org.localidad || '',
      provincia: org.provincia || '',
      telefono: org.telefono || '',
      email: org.email || '',
      web: org.web || '',
      color_primario: org.color_primario || '#0066CC',
      color_secundario: org.color_secundario || '#FFD700',
      logo_base64: org.logo_base64 || null,
      notas: org.notas || '',
    });
    setEditModalVisible(true);
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
      alert(error.response?.data?.detail || 'Error al actualizar organizacion');
    }
  };

  const handleDeleteOrganization = async (org: Organization) => {
    const confirmMsg = `¿Estás seguro de eliminar "${org.nombre}"? Se eliminarán TODOS los datos: usuarios, vehiculos, clientes, turnos y servicios.`;
    
    if (Platform.OS === 'web') {
      if (!window.confirm(confirmMsg)) return;
    } else {
      return; // Disable delete on mobile for safety
    }

    try {
      const token = await AsyncStorage.getItem('token');
      await axios.delete(`${API_URL}/organizations/${org.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      loadOrganizations();
      alert('Organizacion eliminada correctamente');
    } catch (error: any) {
      console.error('Error deleting organization:', error);
      alert(error.response?.data?.detail || 'Error al eliminar organizacion');
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadOrganizations();
  };

  // Render logo picker component
  const renderLogoPicker = (logoBase64: string | null, isEdit: boolean) => (
    <View style={styles.logoSection}>
      <Text variant="titleSmall" style={styles.sectionTitle}>Logo de la empresa</Text>
      <View style={styles.logoContainer}>
        {logoBase64 ? (
          <View style={styles.logoPreviewContainer}>
            <Image source={{ uri: logoBase64 }} style={styles.logoPreview} />
            <View style={styles.logoActions}>
              <Button 
                mode="outlined" 
                onPress={() => pickImage(isEdit)}
                icon="pencil"
                compact
              >
                Cambiar
              </Button>
              <Button 
                mode="outlined" 
                onPress={() => removeLogo(isEdit)}
                icon="delete"
                textColor="#f44336"
                compact
              >
                Quitar
              </Button>
            </View>
          </View>
        ) : (
          <TouchableOpacity style={styles.logoPlaceholder} onPress={() => pickImage(isEdit)}>
            <MaterialCommunityIcons name="image-plus" size={40} color="#999" />
            <Text variant="bodySmall" style={styles.logoPlaceholderText}>
              Pulsa para añadir logo
            </Text>
            <Text variant="labelSmall" style={styles.logoHint}>
              Recomendado: imagen cuadrada
            </Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );

  // Render form fields (reusable for create and edit)
  const renderFormFields = (data: typeof formData, setData: (data: typeof formData) => void, isEdit: boolean) => (
    <>
      <TextInput
        label="Nombre de la empresa *"
        value={data.nombre}
        onChangeText={(text) => setData({...data, nombre: text})}
        mode="outlined"
        style={styles.input}
      />

      {/* Logo picker */}
      {renderLogoPicker(data.logo_base64, isEdit)}

      <Divider style={{ marginVertical: 16 }} />
      <Text variant="titleSmall" style={styles.sectionTitle}>Datos fiscales</Text>

      <TextInput
        label="CIF/NIF"
        value={data.cif}
        onChangeText={(text) => setData({...data, cif: text})}
        mode="outlined"
        style={styles.input}
      />
      <TextInput
        label="Direccion"
        value={data.direccion}
        onChangeText={(text) => setData({...data, direccion: text})}
        mode="outlined"
        style={styles.input}
      />
      <TextInput
        label="Codigo Postal"
        value={data.codigo_postal}
        onChangeText={(text) => setData({...data, codigo_postal: text})}
        mode="outlined"
        style={styles.input}
        keyboardType="numeric"
      />
      <View style={styles.row}>
        <TextInput
          label="Localidad"
          value={data.localidad}
          onChangeText={(text) => setData({...data, localidad: text})}
          mode="outlined"
          style={[styles.input, { flex: 1, marginRight: 8 }]}
        />
        <TextInput
          label="Provincia"
          value={data.provincia}
          onChangeText={(text) => setData({...data, provincia: text})}
          mode="outlined"
          style={[styles.input, { flex: 1 }]}
        />
      </View>

      <Divider style={{ marginVertical: 16 }} />
      <Text variant="titleSmall" style={styles.sectionTitle}>Contacto</Text>

      <TextInput
        label="Telefono"
        value={data.telefono}
        onChangeText={(text) => setData({...data, telefono: text})}
        mode="outlined"
        style={styles.input}
        keyboardType="phone-pad"
      />
      <TextInput
        label="Email"
        value={data.email}
        onChangeText={(text) => setData({...data, email: text})}
        mode="outlined"
        style={styles.input}
        keyboardType="email-address"
      />
      <TextInput
        label="Web"
        value={data.web}
        onChangeText={(text) => setData({...data, web: text})}
        mode="outlined"
        style={styles.input}
      />
      
      <Divider style={{ marginVertical: 16 }} />
      <Text variant="titleSmall" style={styles.sectionTitle}>Personalizacion de marca</Text>
      <Text variant="bodySmall" style={styles.brandingHint}>
        Estos colores se mostrarán en la app de los taxistas
      </Text>
      
      <View style={styles.row}>
        <View style={[styles.colorPreview, { backgroundColor: data.color_primario }]} />
        <TextInput
          label="Color Primario"
          value={data.color_primario}
          onChangeText={(text) => setData({...data, color_primario: text})}
          mode="outlined"
          style={[styles.input, { flex: 1 }]}
          placeholder="#0066CC"
        />
      </View>
      <View style={styles.row}>
        <View style={[styles.colorPreview, { backgroundColor: data.color_secundario }]} />
        <TextInput
          label="Color Secundario"
          value={data.color_secundario}
          onChangeText={(text) => setData({...data, color_secundario: text})}
          mode="outlined"
          style={[styles.input, { flex: 1 }]}
          placeholder="#FFD700"
        />
      </View>
      
      <TextInput
        label="Notas internas"
        value={data.notas}
        onChangeText={(text) => setData({...data, notas: text})}
        mode="outlined"
        style={styles.input}
        multiline
        numberOfLines={3}
      />
    </>
  );

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
                    {org.logo_base64 ? (
                      <Image source={{ uri: org.logo_base64 }} style={styles.orgLogo} />
                    ) : (
                      <View style={[styles.orgLogoPlaceholder, { backgroundColor: org.color_primario || '#0066CC' }]}>
                        <MaterialCommunityIcons name="office-building" size={24} color="#FFF" />
                      </View>
                    )}
                    <View style={{ flex: 1, marginLeft: 12 }}>
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
                  {org.cif && (
                    <View style={styles.detailRow}>
                      <MaterialCommunityIcons name="card-account-details" size={16} color="#666" />
                      <Text variant="bodySmall" style={styles.detailText}>CIF: {org.cif}</Text>
                    </View>
                  )}
                  {(org.direccion || org.localidad) && (
                    <View style={styles.detailRow}>
                      <MaterialCommunityIcons name="map-marker" size={16} color="#666" />
                      <Text variant="bodySmall" style={styles.detailText}>
                        {org.direccion ? `${org.direccion}, ` : ''}
                        {org.codigo_postal ? `${org.codigo_postal} ` : ''}
                        {org.localidad}{org.provincia ? ` (${org.provincia})` : ''}
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
                  {org.web && (
                    <View style={styles.detailRow}>
                      <MaterialCommunityIcons name="web" size={16} color="#666" />
                      <Text variant="bodySmall" style={styles.detailText}>{org.web}</Text>
                    </View>
                  )}
                </View>

                {/* Color preview */}
                <View style={styles.colorRow}>
                  <View style={styles.colorItem}>
                    <View style={[styles.colorSwatch, { backgroundColor: org.color_primario || '#0066CC' }]} />
                    <Text variant="labelSmall">Primario</Text>
                  </View>
                  <View style={styles.colorItem}>
                    <View style={[styles.colorSwatch, { backgroundColor: org.color_secundario || '#FFD700' }]} />
                    <Text variant="labelSmall">Secundario</Text>
                  </View>
                </View>

                <View style={styles.statsRow}>
                  <Chip icon="account" style={styles.statChip}>{org.total_taxistas} taxistas</Chip>
                  <Chip icon="car" style={styles.statChip}>{org.total_vehiculos} vehiculos</Chip>
                  <Chip icon="briefcase" style={styles.statChip}>{org.total_clientes} clientes</Chip>
                </View>
              </Card.Content>
              
              <Card.Actions style={styles.cardActions}>
                <Button 
                  mode="contained"
                  onPress={() => openEditModal(org)}
                  icon="pencil"
                  buttonColor="#0066CC"
                >
                  Editar
                </Button>
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
                  Crea tu primera organizacion para empezar a gestionar empresas de taxi
                </Text>
                <Button mode="contained" onPress={() => setModalVisible(true)} style={{ marginTop: 24 }}>
                  Crear Primera Organizacion
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
        label="Nueva Organizacion"
      />

      {/* Modal: Create Organization */}
      <Portal>
        <Modal visible={modalVisible} onDismiss={() => setModalVisible(false)} contentContainerStyle={styles.modal}>
          <ScrollView showsVerticalScrollIndicator={false}>
            <Text variant="headlineSmall" style={styles.modalTitle}>Nueva Organizacion</Text>
            
            {renderFormFields(formData, setFormData, false)}
            
            <View style={styles.modalActions}>
              <Button mode="outlined" onPress={() => setModalVisible(false)} disabled={saving}>
                Cancelar
              </Button>
              <Button mode="contained" onPress={handleCreateOrganization} loading={saving} disabled={saving}>
                Crear Organizacion
              </Button>
            </View>
          </ScrollView>
        </Modal>
      </Portal>

      {/* Modal: Edit Organization */}
      <Portal>
        <Modal visible={editModalVisible} onDismiss={() => setEditModalVisible(false)} contentContainerStyle={styles.modal}>
          <ScrollView showsVerticalScrollIndicator={false}>
            <Text variant="headlineSmall" style={styles.modalTitle}>Editar Organizacion</Text>
            {selectedOrg && (
              <Text variant="bodyMedium" style={styles.modalSubtitle}>
                ID: {selectedOrg.id} | Slug: /{selectedOrg.slug}
              </Text>
            )}
            
            {renderFormFields(editFormData, setEditFormData, true)}
            
            <View style={styles.modalActions}>
              <Button mode="outlined" onPress={() => setEditModalVisible(false)} disabled={saving}>
                Cancelar
              </Button>
              <Button mode="contained" onPress={handleEditOrganization} loading={saving} disabled={saving}>
                Guardar Cambios
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
    flex: 1,
  },
  statusDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 12,
  },
  orgLogo: {
    width: 48,
    height: 48,
    borderRadius: 8,
  },
  orgLogoPlaceholder: {
    width: 48,
    height: 48,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
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
    flex: 1,
  },
  colorRow: {
    flexDirection: 'row',
    gap: 16,
    marginTop: 12,
    marginBottom: 8,
  },
  colorItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  colorSwatch: {
    width: 24,
    height: 24,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: '#ddd',
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
  cardActions: {
    flexWrap: 'wrap',
    justifyContent: 'flex-start',
    gap: 4,
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
    alignItems: 'center',
  },
  colorPreview: {
    width: 40,
    height: 40,
    borderRadius: 8,
    marginRight: 12,
    borderWidth: 1,
    borderColor: '#ddd',
  },
  modalActions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 12,
    marginTop: 16,
  },
  // Logo styles
  logoSection: {
    marginTop: 8,
    marginBottom: 8,
  },
  sectionTitle: {
    color: '#666',
    marginBottom: 12,
    fontWeight: '600',
  },
  brandingHint: {
    color: '#999',
    marginBottom: 12,
  },
  logoContainer: {
    alignItems: 'center',
  },
  logoPreviewContainer: {
    alignItems: 'center',
  },
  logoPreview: {
    width: 120,
    height: 120,
    borderRadius: 12,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#ddd',
  },
  logoActions: {
    flexDirection: 'row',
    gap: 12,
  },
  logoPlaceholder: {
    width: 150,
    height: 150,
    borderRadius: 12,
    borderWidth: 2,
    borderStyle: 'dashed',
    borderColor: '#ddd',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#fafafa',
  },
  logoPlaceholderText: {
    color: '#999',
    marginTop: 8,
  },
  logoHint: {
    color: '#bbb',
    marginTop: 4,
  },
});
