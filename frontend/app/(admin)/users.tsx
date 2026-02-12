import React, { useState, useEffect } from 'react';
import {
  View,
  StyleSheet,
  FlatList,
  RefreshControl,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  useWindowDimensions,
} from 'react-native';
import {
  Text,
  Card,
  FAB,
  Portal,
  Modal,
  TextInput,
  Button,
  IconButton,
  Snackbar,
  SegmentedButtons,
  Menu,
} from 'react-native-paper';
import { useAuth } from '../../contexts/AuthContext';
import axios from 'axios';
import VehiculosScreen from './vehiculos';

import { API_URL } from '../../config/api';

interface User {
  id: string;
  username: string;
  nombre: string;
  role: string;
  licencia?: string;
  vehiculo_id?: string;
  vehiculo_matricula?: string;
}

interface Vehiculo {
  id: string;
  matricula: string;
  marca: string;
  modelo: string;
}

export default function UsersScreen() {
  const [activeTab, setActiveTab] = useState('taxistas');
  const [users, setUsers] = useState<User[]>([]);
  const [vehiculos, setVehiculos] = useState<Vehiculo[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [snackbar, setSnackbar] = useState({ visible: false, message: '' });
  const [vehiculoMenuVisible, setVehiculoMenuVisible] = useState(false);
  const { width } = useWindowDimensions();
  const isDesktop = Platform.OS === 'web' && width >= 1024;
  
  const [formData, setFormData] = useState({
    username: '',
    nombre: '',
    password: '',
    confirmPassword: '',
    licencia: '',
    vehiculo_id: '',
    vehiculo_matricula: '',
  });

  const { token } = useAuth();

  useEffect(() => {
    loadUsers();
    loadVehiculos();
  }, []);

  const loadUsers = async () => {
    try {
      const response = await axios.get(`${API_URL}/users`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setUsers(response.data);
    } catch (error) {
      console.error('Error loading users:', error);
    }
  };

  const loadVehiculos = async () => {
    try {
      const response = await axios.get(`${API_URL}/vehiculos`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      console.log('Vehiculos cargados:', response.data);
      setVehiculos(response.data);
    } catch (error) {
      console.error('Error loading vehiculos:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadUsers();
    setRefreshing(false);
  };

  const openModal = (user?: User) => {
    console.log('=== openModal llamado ===');
    console.log('user recibido:', user);
    console.log('Vehiculos disponibles:', vehiculos);
    
    // Recargar vehiculos para asegurar que tenemos la lista actualizada
    loadVehiculos();
    
    if (user) {
      console.log('MODO EDICIÓN - Seteando editingUser:', user);
      setEditingUser(user);
      setFormData({
        username: user.username,
        nombre: user.nombre,
        password: '', // No mostramos la contrasena
        confirmPassword: '',
        licencia: user.licencia || '',
        vehiculo_id: user.vehiculo_id || '',
        vehiculo_matricula: user.vehiculo_matricula || '',
      });
    } else {
      console.log('MODO CREACIÓN - Limpiando editingUser a null');
      setEditingUser(null);
      setFormData({
        username: '',
        nombre: '',
        password: '',
        confirmPassword: '',
        licencia: '',
        vehiculo_id: '',
        vehiculo_matricula: '',
      });
    }
    setModalVisible(true);
  };

  const closeModal = () => {
    setModalVisible(false);
    setEditingUser(null);
  };

  const handleSubmit = async () => {
    console.log('=== DEBUG handleSubmit ===');
    console.log('editingUser:', editingUser);
    console.log('formData:', formData);
    
    if (editingUser) {
      // Modo edición: no requerimos contrasena (es opcional)
      if (!formData.nombre || !formData.licencia) {
        setSnackbar({ visible: true, message: 'Por favor, completa todos los campos obligatorios' });
        return;
      }
    } else {
      // Modo creación: requerimos nombre, password y licencia (username se genera automáticamente)
      if (!formData.nombre || !formData.password || !formData.licencia) {
        setSnackbar({ visible: true, message: 'Por favor, completa: Nombre, Contrasena y Licencia' });
        return;
      }
    }

    // Validar que las contrasenas coincidan
    if (formData.password && formData.password.trim() !== '') {
      if (formData.password !== formData.confirmPassword) {
        setSnackbar({ visible: true, message: 'Las contrasenas no coinciden' });
        return;
      }
    }

    try {
      if (editingUser) {
        console.log('Modo EDICIÓN - ID:', editingUser.id);
        // Actualizar taxista existente
        const updateData: any = { 
          username: formData.username,
          nombre: formData.nombre,
          licencia: formData.licencia,
          vehiculo_id: formData.vehiculo_id || null,
          vehiculo_matricula: formData.vehiculo_matricula || null,
          role: 'taxista'
        };
        
        // Solo incluir contrasena si se proporcionó y coincide
        if (formData.password && formData.password.trim() !== '') {
          updateData.password = formData.password;
        }
        
        console.log('=== Actualizando usuario ===');
        console.log('User ID:', editingUser?.id);
        console.log('Datos a enviar:', updateData);
        console.log('vehiculo_id:', updateData.vehiculo_id);
        console.log('vehiculo_matricula:', updateData.vehiculo_matricula);
        
        await axios.put(
          `${API_URL}/users/${editingUser.id}`,
          updateData,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        setSnackbar({ visible: true, message: 'Taxista actualizado correctamente' });
      } else {
        // Crear nuevo taxista - generar username a partir del nombre
        console.log('Modo CREACIÓN');
        const generatedUsername = formData.nombre
          .toLowerCase()
          .normalize('NFD')
          .replace(/[\u0300-\u036f]/g, '') // Eliminar acentos
          .replace(/\s+/g, '') // Eliminar espacios
          .replace(/[^a-z0-9]/g, ''); // Solo letras y numeros
        
        console.log('Username generado:', generatedUsername);
        
        await axios.post(
          `${API_URL}/users`,
          { 
            username: generatedUsername,
            nombre: formData.nombre,
            password: formData.password,
            licencia: formData.licencia,
            vehiculo_id: formData.vehiculo_id || null,
            vehiculo_matricula: formData.vehiculo_matricula || null,
            role: 'taxista' 
          },
          { headers: { Authorization: `Bearer ${token}` } }
        );
        setSnackbar({ visible: true, message: `Taxista creado correctamente. Usuario: ${generatedUsername}` });
      }
      
      await loadUsers();
      closeModal();
    } catch (error: any) {
      console.error('Error saving user:', error);
      const errorMessage = typeof error.response?.data?.detail === 'string' 
        ? error.response.data.detail 
        : error.response?.data?.message || error.message || 'Error al guardar taxista';
      setSnackbar({
        visible: true,
        message: errorMessage,
      });
    }
  };

  const handleDelete = async (userId: string) => {
    try {
      await axios.delete(`${API_URL}/users/${userId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setSnackbar({ visible: true, message: 'Taxista eliminado correctamente' });
      await loadUsers();
    } catch (error: any) {
      console.error('Error deleting user:', error);
      const errorMessage = typeof error.response?.data?.detail === 'string' 
        ? error.response.data.detail 
        : error.response?.data?.message || error.message || 'Error al eliminar taxista';
      setSnackbar({
        visible: true,
        message: errorMessage,
      });
    }
  };

  const renderUser = ({ item }: { item: User }) => (
    <Card style={styles.card}>
      <Card.Content>
        <View style={styles.cardHeader}>
          <View style={styles.userInfo}>
            <Text variant="titleMedium" style={styles.userName}>
              {item.nombre}
            </Text>
            <Text variant="bodySmall" style={styles.username}>
              @{item.username}
            </Text>
            {item.licencia && (
              <Text variant="bodySmall" style={styles.licencia}>
                Licencia: {item.licencia}
              </Text>
            )}
            {item.vehiculo_matricula && (
              <Text variant="bodySmall" style={styles.vehiculo}>
                🚗 {item.vehiculo_matricula}
              </Text>
            )}
          </View>
          <View style={styles.actions}>
            <IconButton
              icon="pencil"
              size={20}
              onPress={() => openModal(item)}
              iconColor="#0066CC"
            />
            <IconButton
              icon="delete"
              size={20}
              onPress={() => handleDelete(item.id)}
              iconColor="#D32F2F"
            />
          </View>
        </View>
      </Card.Content>
    </Card>
  );

  return (
    <View style={styles.container}>
      <View style={styles.tabContainer}>
        <SegmentedButtons
          value={activeTab}
          onValueChange={setActiveTab}
          buttons={[
            { value: 'taxistas', label: 'Taxistas' },
            { value: 'vehiculos', label: 'Vehiculos' },
          ]}
        />
      </View>
      
      {activeTab === 'vehiculos' ? (
        <VehiculosScreen />
      ) : (
        <>
          <FlatList
            data={users}
            renderItem={renderUser}
            keyExtractor={(item) => item.id}
            contentContainerStyle={styles.list}
            refreshControl={
              <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={['#0066CC']} />
            }
            ListEmptyComponent={
              <View style={styles.emptyContainer}>
                <Text variant="bodyLarge" style={styles.emptyText}>
                  No hay taxistas registrados
                </Text>
              </View>
            }
          />

          <FAB
            icon="plus"
            style={styles.fab}
            onPress={() => openModal()}
          />

          <Portal>
        <Modal
          visible={modalVisible}
          onDismiss={closeModal}
          contentContainerStyle={styles.modal}
        >
          <KeyboardAvoidingView
            behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          >
            <ScrollView keyboardShouldPersistTaps="handled">
              <Text variant="titleLarge" style={styles.modalTitle}>
                {editingUser ? 'Editar Taxista' : 'Nuevo Taxista'}
              </Text>

              <TextInput
                label="Nombre *"
                value={formData.nombre}
                onChangeText={(text) => setFormData({ ...formData, nombre: text })}
                mode="outlined"
                style={styles.input}
              />

              {editingUser && (
                <TextInput
                  label="Usuario"
                  value={formData.username}
                  mode="outlined"
                  style={styles.input}
                  disabled={true}
                  editable={false}
                />
              )}

              {!editingUser && (
                <Text variant="bodySmall" style={styles.helperText}>
                  El usuario se generará automáticamente a partir del nombre
                </Text>
              )}

              <TextInput
                label={editingUser ? "Contrasena (dejar vacio para no cambiar)" : "Contrasena *"}
                value={formData.password}
                onChangeText={(text) => setFormData({ ...formData, password: text })}
                mode="outlined"
                secureTextEntry
                style={styles.input}
                placeholder={editingUser ? "Dejar vacio si no deseas cambiar" : ""}
              />

              <TextInput
                label={editingUser ? "Confirmar Contrasena" : "Confirmar Contrasena *"}
                value={formData.confirmPassword}
                onChangeText={(text) => setFormData({ ...formData, confirmPassword: text })}
                mode="outlined"
                secureTextEntry
                style={styles.input}
                placeholder="Vuelve a escribir la contrasena"
              />

              <TextInput
                label="Licencia Nº *"
                value={formData.licencia}
                onChangeText={(text) => setFormData({ ...formData, licencia: text })}
                mode="outlined"
                style={styles.input}
              />

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
                    {formData.vehiculo_matricula || 'Sin vehiculo asignado'}
                  </Button>
                }
              >
                <Menu.Item
                  onPress={() => {
                    setFormData({ ...formData, vehiculo_id: '', vehiculo_matricula: '' });
                    setVehiculoMenuVisible(false);
                  }}
                  title="Sin vehiculo"
                />
                {vehiculos.map((vehiculo) => (
                  <Menu.Item
                    key={vehiculo.id}
                    onPress={() => {
                      setFormData({
                        ...formData,
                        vehiculo_id: vehiculo.id,
                        vehiculo_matricula: vehiculo.matricula,
                      });
                      setVehiculoMenuVisible(false);
                    }}
                    title={`${vehiculo.matricula} - ${vehiculo.marca} ${vehiculo.modelo}`}
                  />
                ))}
              </Menu>

              <View style={styles.modalActions}>
                <Button mode="outlined" onPress={closeModal} style={styles.modalButton}>
                  Cancelar
                </Button>
                <Button mode="contained" onPress={handleSubmit} style={styles.modalButton}>
                  Crear
                </Button>
              </View>
            </ScrollView>
          </KeyboardAvoidingView>
        </Modal>
          </Portal>

          <Snackbar
            visible={snackbar.visible}
            onDismiss={() => setSnackbar({ ...snackbar, visible: false })}
            duration={3000}
          >
            {snackbar.message}
          </Snackbar>
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  tabContainer: {
    padding: 16,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  list: {
    padding: 16,
  },
  card: {
    marginBottom: 16,
    backgroundColor: 'white',
    elevation: 2,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  userInfo: {
    flex: 1,
  },
  userName: {
    fontWeight: 'bold',
    color: '#0066CC',
    marginBottom: 4,
  },
  username: {
    color: '#666',
  },
  licencia: {
    color: '#666',
    marginTop: 4,
  },
  vehiculo: {
    color: '#0066CC',
    marginTop: 4,
    fontWeight: '600',
  },
  actions: {
    flexDirection: 'row',
  },
  helperText: {
    color: '#666',
    fontStyle: 'italic',
    marginBottom: 16,
    marginTop: -8,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 100,
  },
  emptyText: {
    color: '#999',
  },
  fab: {
    position: 'absolute',
    right: 16,
    bottom: 16,
    backgroundColor: '#0066CC',
  },
  modal: {
    backgroundColor: 'white',
    padding: 24,
    margin: 20,
    borderRadius: 12,
  },
  modalTitle: {
    marginBottom: 16,
    color: '#0066CC',
    fontWeight: 'bold',
  },
  input: {
    marginBottom: 16,
  },
  modalActions: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 16,
  },
  modalButton: {
    flex: 1,
    marginHorizontal: 4,
  },
});
