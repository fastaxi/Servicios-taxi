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

interface Company {
  id: string;
  nombre: string;
  cif: string;
  direccion: string;
  localidad: string;
  provincia: string;
}

export default function CompaniesScreen() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingCompany, setEditingCompany] = useState<Company | null>(null);
  const [snackbar, setSnackbar] = useState({ visible: false, message: '' });
  
  const [formData, setFormData] = useState({
    nombre: '',
    cif: '',
    direccion: '',
    codigo_postal: '',
    localidad: '',
    provincia: 'Asturias',
    telefono: '',
    email: '',
  });

  const { token } = useAuth();

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

  const onRefresh = async () => {
    setRefreshing(true);
    await loadCompanies();
    setRefreshing(false);
  };

  const openModal = (company?: Company) => {
    if (company) {
      setEditingCompany(company);
      setFormData({
        nombre: company.nombre,
        cif: company.cif,
        direccion: company.direccion,
        codigo_postal: company.codigo_postal,
        localidad: company.localidad,
        provincia: company.provincia,
        telefono: company.telefono,
        email: company.email,
      });
    } else {
      setEditingCompany(null);
      setFormData({
        nombre: '',
        cif: '',
        direccion: '',
        localidad: '',
        provincia: 'Asturias',
      });
    }
    setModalVisible(true);
  };

  const closeModal = () => {
    setModalVisible(false);
    setEditingCompany(null);
  };

  const handleSubmit = async () => {
    if (!formData.nombre || !formData.cif || !formData.direccion || !formData.localidad) {
      setSnackbar({ visible: true, message: 'Por favor, completa todos los campos' });
      return;
    }

    try {
      if (editingCompany) {
        await axios.put(
          `${API_URL}/companies/${editingCompany.id}`,
          formData,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        setSnackbar({ visible: true, message: 'Empresa actualizada correctamente' });
      } else {
        await axios.post(`${API_URL}/companies`, formData, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setSnackbar({ visible: true, message: 'Empresa creada correctamente' });
      }

      await loadCompanies();
      closeModal();
    } catch (error: any) {
      console.error('Error saving company:', error);
      setSnackbar({
        visible: true,
        message: error.response?.data?.detail || 'Error al guardar empresa',
      });
    }
  };

  const handleDelete = async (companyId: string) => {
    try {
      await axios.delete(`${API_URL}/companies/${companyId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setSnackbar({ visible: true, message: 'Empresa eliminada correctamente' });
      await loadCompanies();
    } catch (error: any) {
      console.error('Error deleting company:', error);
      setSnackbar({
        visible: true,
        message: error.response?.data?.detail || 'Error al eliminar empresa',
      });
    }
  };

  const renderCompany = ({ item }: { item: Company }) => (
    <Card style={styles.card}>
      <Card.Content>
        <View style={styles.cardHeader}>
          <Text variant="titleMedium" style={styles.companyName}>
            {item.nombre}
          </Text>
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

        <View style={styles.detailRow}>
          <Text variant="bodySmall" style={styles.label}>CIF:</Text>
          <Text variant="bodySmall">{item.cif}</Text>
        </View>

        <View style={styles.detailRow}>
          <Text variant="bodySmall" style={styles.label}>Dirección:</Text>
          <Text variant="bodySmall">{item.direccion}</Text>
        </View>

        <View style={styles.detailRow}>
          <Text variant="bodySmall" style={styles.label}>Localidad:</Text>
          <Text variant="bodySmall">{item.localidad}</Text>
        </View>

        <View style={styles.detailRow}>
          <Text variant="bodySmall" style={styles.label}>Provincia:</Text>
          <Text variant="bodySmall">{item.provincia}</Text>
        </View>
      </Card.Content>
    </Card>
  );

  return (
    <View style={styles.container}>
      <FlatList
        data={companies}
        renderItem={renderCompany}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={['#0066CC']} />
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text variant="bodyLarge" style={styles.emptyText}>
              No hay empresas registradas
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
                {editingCompany ? 'Editar Empresa' : 'Nueva Empresa'}
              </Text>

              <TextInput
                label="Nombre *"
                value={formData.nombre}
                onChangeText={(text) => setFormData({ ...formData, nombre: text })}
                mode="outlined"
                style={styles.input}
              />

              <TextInput
                label="CIF *"
                value={formData.cif}
                onChangeText={(text) => setFormData({ ...formData, cif: text })}
                mode="outlined"
                style={styles.input}
              />

              <TextInput
                label="Dirección *"
                value={formData.direccion}
                onChangeText={(text) => setFormData({ ...formData, direccion: text })}
                mode="outlined"
                style={styles.input}
              />

              <TextInput
                label="Localidad *"
                value={formData.localidad}
                onChangeText={(text) => setFormData({ ...formData, localidad: text })}
                mode="outlined"
                style={styles.input}
              />

              <TextInput
                label="Provincia *"
                value={formData.provincia}
                onChangeText={(text) => setFormData({ ...formData, provincia: text })}
                mode="outlined"
                style={styles.input}
              />

              <View style={styles.modalActions}>
                <Button mode="outlined" onPress={closeModal} style={styles.modalButton}>
                  Cancelar
                </Button>
                <Button mode="contained" onPress={handleSubmit} style={styles.modalButton}>
                  Guardar
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
    marginBottom: 8,
  },
  companyName: {
    flex: 1,
    fontWeight: 'bold',
    color: '#0066CC',
  },
  actions: {
    flexDirection: 'row',
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 4,
  },
  label: {
    fontWeight: '600',
    color: '#666',
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
    maxHeight: '80%',
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
