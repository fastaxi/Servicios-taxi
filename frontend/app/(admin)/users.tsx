import React, { useState, useEffect } from 'react';
import {
  View,
  StyleSheet,
  FlatList,
  RefreshControl,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
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
} from 'react-native-paper';
import { useAuth } from '../../contexts/AuthContext';
import axios from 'axios';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL + '/api';

interface User {
  id: string;
  username: string;
  nombre: string;
  role: string;
}

export default function UsersScreen() {
  const [users, setUsers] = useState<User[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [snackbar, setSnackbar] = useState({ visible: false, message: '' });
  
  const [formData, setFormData] = useState({
    username: '',
    nombre: '',
    password: '',
    licencia: '',
  });

  const { token } = useAuth();

  useEffect(() => {
    loadUsers();
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

  const onRefresh = async () => {
    setRefreshing(true);
    await loadUsers();
    setRefreshing(false);
  };

  const openModal = (user?: User) => {
    if (user) {
      setEditingUser(user);
      setFormData({
        username: user.username,
        nombre: user.nombre,
        password: '', // No mostramos la contraseña
        licencia: user.licencia || '',
      });
    } else {
      setEditingUser(null);
      setFormData({
        username: '',
        nombre: '',
        password: '',
        licencia: '',
      });
    }
    setModalVisible(true);
  };

  const closeModal = () => {
    setModalVisible(false);
  };

  const handleSubmit = async () => {
    if (editingUser) {
      // Modo edición: no requerimos contraseña
      if (!formData.username || !formData.nombre || !formData.licencia) {
        setSnackbar({ visible: true, message: 'Por favor, completa todos los campos' });
        return;
      }
    } else {
      // Modo creación: requerimos todos los campos
      if (!formData.username || !formData.nombre || !formData.password || !formData.licencia) {
        setSnackbar({ visible: true, message: 'Por favor, completa todos los campos' });
        return;
      }
    }

    try {
      if (editingUser) {
        // Actualizar taxista existente
        await axios.put(
          `${API_URL}/users/${editingUser.id}`,
          { 
            username: formData.username,
            nombre: formData.nombre,
            licencia: formData.licencia,
            role: 'taxista'
          },
          { headers: { Authorization: `Bearer ${token}` } }
        );
        setSnackbar({ visible: true, message: 'Taxista actualizado correctamente' });
      } else {
        // Crear nuevo taxista
        await axios.post(
          `${API_URL}/users`,
          { ...formData, role: 'taxista' },
          { headers: { Authorization: `Bearer ${token}` } }
        );
        setSnackbar({ visible: true, message: 'Taxista creado correctamente' });
      }
      
      await loadUsers();
      closeModal();
    } catch (error: any) {
      console.error('Error saving user:', error);
      setSnackbar({
        visible: true,
        message: error.response?.data?.detail || 'Error al guardar taxista',
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
      setSnackbar({
        visible: true,
        message: error.response?.data?.detail || 'Error al eliminar taxista',
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
        onPress={openModal}
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

              <TextInput
                label="Usuario *"
                value={formData.username}
                onChangeText={(text) => setFormData({ ...formData, username: text })}
                mode="outlined"
                autoCapitalize="none"
                style={styles.input}
                disabled={!!editingUser}
              />

              {!editingUser && (
                <TextInput
                  label="Contraseña *"
                  value={formData.password}
                  onChangeText={(text) => setFormData({ ...formData, password: text })}
                  mode="outlined"
                  secureTextEntry
                  style={styles.input}
                />
              )}

              <TextInput
                label="Licencia Nº *"
                value={formData.licencia}
                onChangeText={(text) => setFormData({ ...formData, licencia: text })}
                mode="outlined"
                style={styles.input}
              />

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
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
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
  actions: {
    flexDirection: 'row',
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
