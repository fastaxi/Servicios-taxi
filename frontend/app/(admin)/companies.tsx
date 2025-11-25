import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ScrollView, Alert, Modal, KeyboardAvoidingView, Platform, Keyboard } from 'react-native';
import {
  TextInput,
  Button,
  Text,
  FAB,
  Snackbar,
  Card,
  IconButton,
  Appbar,
} from 'react-native-paper';
import { useAuth } from '../../contexts/AuthContext';
import axios from 'axios';
import { API_URL } from '../../config/api';

interface Company {
  id: string;
  nombre: string;
  numero_cliente: string;
  contacto?: string;
  telefono?: string;
  email?: string;
  direccion?: string;
}

export default function CompaniesScreen() {
  const { token } = useAuth();
  const [companies, setCompanies] = useState<Company[]>([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [snackbar, setSnackbar] = useState({ visible: false, message: '' });
  const [editingCompany, setEditingCompany] = useState<Company | null>(null);

  // Form states
  const [nombre, setNombre] = useState('');
  const [cif, setCif] = useState('');
  const [numeroCliente, setNumeroCliente] = useState('');
  const [contacto, setContacto] = useState('');
  const [telefono, setTelefono] = useState('');
  const [email, setEmail] = useState('');
  const [direccion, setDireccion] = useState('');

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
      setSnackbar({ visible: true, message: 'Error al cargar empresas' });
    }
  };

  const openModal = (company?: Company) => {
    if (company) {
      setEditingCompany(company);
      setNombre(company.nombre);
      setNumeroCliente(company.numero_cliente);
      setContacto(company.contacto || '');
      setTelefono(company.telefono || '');
      setEmail(company.email || '');
      setDireccion(company.direccion || '');
    } else {
      resetForm();
    }
    setModalVisible(true);
  };

  const resetForm = () => {
    setEditingCompany(null);
    setNombre('');
    setNumeroCliente('');
    setContacto('');
    setTelefono('');
    setEmail('');
    setDireccion('');
  };

  const handleSubmit = async () => {
    if (!nombre || !numeroCliente) {
      setSnackbar({ visible: true, message: 'Por favor, completa los campos obligatorios' });
      return;
    }

    const companyData = {
      nombre,
      numero_cliente: numeroCliente,
      contacto: contacto || undefined,
      telefono: telefono || undefined,
      email: email || undefined,
      direccion: direccion || undefined,
    };

    try {
      if (editingCompany) {
        await axios.put(`${API_URL}/companies/${editingCompany.id}`, companyData, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setSnackbar({ visible: true, message: 'Empresa actualizada correctamente' });
      } else {
        await axios.post(`${API_URL}/companies`, companyData, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setSnackbar({ visible: true, message: 'Empresa creada correctamente' });
      }
      
      setModalVisible(false);
      resetForm();
      loadCompanies();
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Error al guardar la empresa';
      setSnackbar({ visible: true, message: errorMsg });
    }
  };

  const handleDelete = (company: Company) => {
    Alert.alert(
      'Eliminar Empresa',
      `¿Estás seguro de que deseas eliminar la empresa ${company.nombre}?`,
      [
        { text: 'Cancelar', style: 'cancel' },
        {
          text: 'Eliminar',
          style: 'destructive',
          onPress: async () => {
            try {
              await axios.delete(`${API_URL}/companies/${company.id}`, {
                headers: { Authorization: `Bearer ${token}` },
              });
              setSnackbar({ visible: true, message: 'Empresa eliminada correctamente' });
              loadCompanies();
            } catch (error) {
              setSnackbar({ visible: true, message: 'Error al eliminar la empresa' });
            }
          },
        },
      ]
    );
  };

  return (
    <View style={styles.container}>
      <ScrollView>
        {companies.map((company) => (
          <Card key={company.id} style={styles.card}>
            <Card.Title
              title={company.nombre}
              subtitle={`Cliente: ${company.numero_cliente}`}
              right={(props) => (
                <View style={styles.cardActions}>
                  <IconButton {...props} icon="pencil" onPress={() => openModal(company)} />
                  <IconButton {...props} icon="delete" onPress={() => handleDelete(company)} />
                </View>
              )}
            />
            <Card.Content>
              {company.contacto && <Text>Contacto: {company.contacto}</Text>}
              {company.telefono && <Text>Teléfono: {company.telefono}</Text>}
              {company.email && <Text>Email: {company.email}</Text>}
              {company.direccion && <Text>Dirección: {company.direccion}</Text>}
            </Card.Content>
          </Card>
        ))}
      </ScrollView>

      <FAB
        style={styles.fab}
        icon="plus"
        onPress={() => openModal()}
      />

      <Modal
        visible={modalVisible}
        animationType="slide"
        onRequestClose={() => setModalVisible(false)}
      >
        <View style={styles.modalContainer}>
          <Appbar.Header>
            <Appbar.BackAction onPress={() => setModalVisible(false)} />
            <Appbar.Content title={editingCompany ? 'Editar Empresa' : 'Nueva Empresa'} />
            <Appbar.Action icon="check" onPress={handleSubmit} />
          </Appbar.Header>
          
          <KeyboardAvoidingView
            style={styles.keyboardAvoid}
            behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
            keyboardVerticalOffset={0}
          >
            <ScrollView 
              style={styles.modalContent}
              contentContainerStyle={styles.modalScrollContent}
              keyboardShouldPersistTaps="handled"
            >
              <TextInput
                label="Nombre *"
                value={nombre}
                onChangeText={setNombre}
                mode="outlined"
                style={styles.input}
              />
              <TextInput
                label="Número de Cliente *"
                value={numeroCliente}
                onChangeText={setNumeroCliente}
                mode="outlined"
                style={styles.input}
              />
              <TextInput
                label="Contacto"
                value={contacto}
                onChangeText={setContacto}
                mode="outlined"
                style={styles.input}
              />
              <TextInput
                label="Teléfono"
                value={telefono}
                onChangeText={setTelefono}
                mode="outlined"
                keyboardType="phone-pad"
                style={styles.input}
              />
              <TextInput
                label="Email"
                value={email}
                onChangeText={setEmail}
                mode="outlined"
                keyboardType="email-address"
                autoCapitalize="none"
                style={styles.input}
              />
              <TextInput
                label="Dirección"
                value={direccion}
                onChangeText={setDireccion}
                mode="outlined"
                multiline
                numberOfLines={3}
                style={styles.input}
              />
              <View style={styles.buttonContainer}>
                <Button mode="outlined" onPress={() => setModalVisible(false)} style={styles.modalButton}>
                  Cancelar
                </Button>
                <Button mode="contained" onPress={handleSubmit} style={styles.modalButton}>
                  Guardar
                </Button>
              </View>
            </ScrollView>
          </KeyboardAvoidingView>
        </View>
      </Modal>

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
  card: {
    margin: 8,
  },
  cardActions: {
    flexDirection: 'row',
  },
  fab: {
    position: 'absolute',
    margin: 16,
    right: 0,
    bottom: 0,
    backgroundColor: '#0066CC',
  },
  modalContainer: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  keyboardAvoid: {
    flex: 1,
  },
  modalContent: {
    flex: 1,
  },
  modalScrollContent: {
    padding: 16,
    paddingBottom: 40,
  },
  input: {
    marginBottom: 16,
  },
  buttonContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 24,
    gap: 12,
  },
  modalButton: {
    flex: 1,
  },
});