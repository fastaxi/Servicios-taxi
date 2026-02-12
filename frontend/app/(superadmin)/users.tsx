import React, { useState, useEffect } from 'react';
import { View, StyleSheet, ScrollView, RefreshControl } from 'react-native';
import { Text, Card, Button, Portal, Modal, ActivityIndicator, Chip, Divider, RadioButton } from 'react-native-paper';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_URL } from '../../config/api';

interface UnassignedUser {
  id: string;
  username: string;
  nombre: string;
  role: string;
  created_at: string;
}

interface Organization {
  id: string;
  nombre: string;
}

export default function UsersScreen() {
  const [users, setUsers] = useState<UnassignedUser[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [assignModalVisible, setAssignModalVisible] = useState(false);
  const [selectedUser, setSelectedUser] = useState<UnassignedUser | null>(null);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const token = await AsyncStorage.getItem('token');
      const [usersRes, orgsRes] = await Promise.all([
        axios.get(`${API_URL}/users/unassigned`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API_URL}/organizations`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);
      setUsers(usersRes.data);
      setOrganizations(orgsRes.data);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const openAssignModal = (user: UnassignedUser) => {
    setSelectedUser(user);
    setSelectedOrgId('');
    setAssignModalVisible(true);
  };

  const handleAssign = async () => {
    if (!selectedUser || !selectedOrgId) {
      alert('Selecciona una organizacion');
      return;
    }

    setSaving(true);
    try {
      const token = await AsyncStorage.getItem('token');
      await axios.put(
        `${API_URL}/users/${selectedUser.id}/assign-organization/${selectedOrgId}`,
        {},
        { headers: { Authorization: `Bearer ${token}` }}
      );
      
      setAssignModalVisible(false);
      setSelectedUser(null);
      setSelectedOrgId('');
      loadData();
      alert('Usuario asignado correctamente');
    } catch (error: any) {
      console.error('Error assigning user:', error);
      alert(error.response?.data?.detail || 'Error al asignar usuario');
    } finally {
      setSaving(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  const getRoleLabel = (role: string) => {
    switch (role) {
      case 'admin': return 'Administrador';
      case 'taxista': return 'Taxista';
      default: return role;
    }
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'admin': return '#2196F3';
      case 'taxista': return '#4CAF50';
      default: return '#9E9E9E';
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" />
        <Text style={{ marginTop: 16 }}>Cargando usuarios...</Text>
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
          <Text variant="headlineMedium" style={styles.title}>👥 Usuarios Sin Asignar</Text>
          <Text variant="bodyMedium" style={styles.subtitle}>
            {users.length} usuarios pendientes de asignar a una organizacion
          </Text>
        </View>

        <View style={styles.content}>
          {users.length === 0 ? (
            <Card style={styles.emptyCard}>
              <Card.Content style={styles.emptyContent}>
                <MaterialCommunityIcons name="check-circle" size={64} color="#4CAF50" />
                <Text variant="headlineSmall" style={styles.emptyTitle}>¡Todo en orden!</Text>
                <Text variant="bodyMedium" style={styles.emptyText}>
                  Todos los usuarios estan asignados a una organizacion
                </Text>
              </Card.Content>
            </Card>
          ) : (
            <>
              <Card style={styles.infoCard}>
                <Card.Content>
                  <View style={styles.infoRow}>
                    <MaterialCommunityIcons name="information" size={24} color="#FF9800" />
                    <Text variant="bodyMedium" style={styles.infoText}>
                      Estos usuarios fueron creados antes del sistema multi-tenant. 
                      Asignalos a una organizacion para que puedan ver el branding correcto.
                    </Text>
                  </View>
                </Card.Content>
              </Card>

              {users.map((user) => (
                <Card key={user.id} style={styles.userCard}>
                  <Card.Content>
                    <View style={styles.userHeader}>
                      <View style={styles.userInfo}>
                        <MaterialCommunityIcons 
                          name={user.role === 'admin' ? 'shield-account' : 'account'} 
                          size={40} 
                          color={getRoleColor(user.role)} 
                        />
                        <View style={styles.userDetails}>
                          <Text variant="titleMedium">{user.nombre}</Text>
                          <Text variant="bodySmall" style={styles.username}>@{user.username}</Text>
                        </View>
                      </View>
                      <Chip 
                        style={[styles.roleChip, { backgroundColor: getRoleColor(user.role) + '20' }]}
                        textStyle={{ color: getRoleColor(user.role) }}
                      >
                        {getRoleLabel(user.role)}
                      </Chip>
                    </View>
                  </Card.Content>
                  <Card.Actions>
                    <Button 
                      mode="contained" 
                      onPress={() => openAssignModal(user)}
                      icon="domain"
                    >
                      Asignar a Organizacion
                    </Button>
                  </Card.Actions>
                </Card>
              ))}
            </>
          )}
        </View>
      </ScrollView>

      {/* Modal: Assign to Organization */}
      <Portal>
        <Modal visible={assignModalVisible} onDismiss={() => setAssignModalVisible(false)} contentContainerStyle={styles.modal}>
          <Text variant="headlineSmall" style={styles.modalTitle}>
            Asignar a Organizacion
          </Text>
          {selectedUser && (
            <Text variant="bodyMedium" style={styles.modalSubtitle}>
              Usuario: {selectedUser.nombre} (@{selectedUser.username})
            </Text>
          )}
          
          <Divider style={{ marginVertical: 16 }} />
          
          <Text variant="titleSmall" style={styles.sectionTitle}>Selecciona organizacion:</Text>
          
          <RadioButton.Group onValueChange={value => setSelectedOrgId(value)} value={selectedOrgId}>
            {organizations.map((org) => (
              <RadioButton.Item
                key={org.id}
                label={org.nombre}
                value={org.id}
                style={styles.radioItem}
              />
            ))}
          </RadioButton.Group>
          
          <View style={styles.modalActions}>
            <Button mode="outlined" onPress={() => setAssignModalVisible(false)} disabled={saving}>
              Cancelar
            </Button>
            <Button 
              mode="contained" 
              onPress={handleAssign} 
              loading={saving} 
              disabled={saving || !selectedOrgId}
            >
              Asignar
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
    paddingBottom: 32,
  },
  infoCard: {
    marginBottom: 16,
    backgroundColor: '#FFF3E0',
    borderRadius: 12,
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
  },
  infoText: {
    flex: 1,
    color: '#E65100',
  },
  userCard: {
    marginBottom: 12,
    borderRadius: 12,
  },
  userHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  userInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  userDetails: {
    flex: 1,
  },
  username: {
    color: '#666',
  },
  roleChip: {
    borderRadius: 16,
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
    color: '#4CAF50',
  },
  emptyText: {
    textAlign: 'center',
    color: '#666',
    marginTop: 8,
  },
  modal: {
    backgroundColor: 'white',
    padding: 24,
    margin: 20,
    borderRadius: 12,
    maxHeight: '80%',
    maxWidth: 400,
    alignSelf: 'center',
    width: '100%',
  },
  modalTitle: {
    marginBottom: 8,
    fontWeight: 'bold',
  },
  modalSubtitle: {
    color: '#666',
  },
  sectionTitle: {
    color: '#666',
    marginBottom: 8,
  },
  radioItem: {
    paddingVertical: 8,
  },
  modalActions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: 12,
    marginTop: 24,
  },
});
