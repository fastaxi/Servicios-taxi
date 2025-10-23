import React, { useState, useEffect } from 'react';
import {
  View,
  StyleSheet,
  FlatList,
  RefreshControl,
  Alert,
  ScrollView,
} from 'react-native';
import {
  Text,
  Card,
  Chip,
  SegmentedButtons,
  Button,
  Menu,
  Snackbar,
} from 'react-native-paper';
import { useAuth } from '../../contexts/AuthContext';
import axios from 'axios';
import * as FileSystem from 'expo-file-system';
import * as Sharing from 'expo-sharing';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL + '/api';

interface Service {
  id: string;
  fecha: string;
  hora: string;
  taxista_nombre: string;
  origen: string;
  destino: string;
  importe: number;
  kilometros: number;
  tipo: string;
  empresa_nombre?: string;
}

interface Company {
  id: string;
  nombre: string;
}

export default function DashboardScreen() {
  const [services, setServices] = useState<Service[]>([]);
  const [filteredServices, setFilteredServices] = useState<Service[]>([]);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [filterType, setFilterType] = useState('todos');
  const [selectedCompany, setSelectedCompany] = useState<string | null>(null);
  const [menuVisible, setMenuVisible] = useState(false);
  const [exportMenuVisible, setExportMenuVisible] = useState(false);
  const [snackbar, setSnackbar] = useState({ visible: false, message: '' });
  const { token } = useAuth();

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [services, filterType, selectedCompany]);

  const loadData = async () => {
    try {
      const [servicesRes, companiesRes] = await Promise.all([
        axios.get(`${API_URL}/services`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        axios.get(`${API_URL}/companies`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ]);

      setServices(servicesRes.data);
      setCompanies(companiesRes.data);
    } catch (error) {
      console.error('Error loading data:', error);
    }
  };

  const applyFilters = () => {
    let filtered = [...services];

    if (filterType === 'empresa') {
      filtered = filtered.filter((s) => s.tipo === 'empresa');
      if (selectedCompany) {
        filtered = filtered.filter((s) => s.empresa_nombre === selectedCompany);
      }
    } else if (filterType === 'particular') {
      filtered = filtered.filter((s) => s.tipo === 'particular');
    }

    setFilteredServices(filtered);
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const getTotalImporte = () => {
    return filteredServices.reduce((sum, s) => sum + s.importe, 0).toFixed(2);
  };

  const getTotalKilometros = () => {
    return filteredServices.reduce((sum, s) => sum + s.kilometros, 0).toFixed(2);
  };

  const exportData = async (format: 'csv' | 'excel' | 'pdf') => {
    try {
      let queryParams = '';
      if (filterType === 'empresa') {
        queryParams = '?tipo=empresa';
        if (selectedCompany) {
          const company = companies.find((c) => c.nombre === selectedCompany);
          if (company) {
            queryParams += `&empresa_id=${company.id}`;
          }
        }
      } else if (filterType === 'particular') {
        queryParams = '?tipo=particular';
      }

      const response = await axios.get(
        `${API_URL}/services/export/${format}${queryParams}`,
        {
          headers: { Authorization: `Bearer ${token}` },
          responseType: 'blob',
        }
      );

      const fileUri = `${FileSystem.documentDirectory}servicios.${format}`;
      const base64 = await blobToBase64(response.data);
      await FileSystem.writeAsStringAsync(fileUri, base64, {
        encoding: FileSystem.EncodingType.Base64,
      });

      if (await Sharing.isAvailableAsync()) {
        await Sharing.shareAsync(fileUri);
        setSnackbar({ visible: true, message: `Archivo ${format.toUpperCase()} exportado correctamente` });
      }
    } catch (error) {
      console.error('Error exporting:', error);
      setSnackbar({ visible: true, message: 'Error al exportar datos' });
    }
    setExportMenuVisible(false);
  };

  const blobToBase64 = (blob: Blob): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onerror = reject;
      reader.onload = () => {
        if (typeof reader.result === 'string') {
          resolve(reader.result.split(',')[1]);
        }
      };
      reader.readAsDataURL(blob);
    });
  };

  const renderService = ({ item }: { item: Service }) => (
    <Card style={styles.card}>
      <Card.Content>
        <View style={styles.cardHeader}>
          <Text variant="titleMedium" style={styles.cardTitle}>
            {item.origen} → {item.destino}
          </Text>
          <Chip mode="flat" style={styles.chip}>
            {item.importe}€
          </Chip>
        </View>

        <View style={styles.detailRow}>
          <Text variant="bodySmall" style={styles.label}>Taxista:</Text>
          <Text variant="bodySmall">{item.taxista_nombre}</Text>
        </View>

        <View style={styles.detailRow}>
          <Text variant="bodySmall" style={styles.label}>Fecha:</Text>
          <Text variant="bodySmall">{item.fecha} {item.hora}</Text>
        </View>

        <View style={styles.detailRow}>
          <Text variant="bodySmall" style={styles.label}>KM:</Text>
          <Text variant="bodySmall">{item.kilometros} km</Text>
        </View>

        <View style={styles.detailRow}>
          <Text variant="bodySmall" style={styles.label}>Tipo:</Text>
          <Chip mode="outlined" compact>
            {item.tipo === 'empresa' ? item.empresa_nombre : 'Particular'}
          </Chip>
        </View>
      </Card.Content>
    </Card>
  );

  return (
    <View style={styles.container}>
      <ScrollView horizontal style={styles.statsContainer}>
        <Card style={styles.statCard}>
          <Card.Content>
            <Text variant="titleLarge" style={styles.statValue}>
              {filteredServices.length}
            </Text>
            <Text variant="bodyMedium">Servicios</Text>
          </Card.Content>
        </Card>

        <Card style={styles.statCard}>
          <Card.Content>
            <Text variant="titleLarge" style={[styles.statValue, styles.amountText]}>
              {getTotalImporte()}€
            </Text>
            <Text variant="bodyMedium">Total Importe</Text>
          </Card.Content>
        </Card>

        <Card style={styles.statCard}>
          <Card.Content>
            <Text variant="titleLarge" style={styles.statValue}>
              {getTotalKilometros()}
            </Text>
            <Text variant="bodyMedium">Total KM</Text>
          </Card.Content>
        </Card>
      </ScrollView>

      <View style={styles.filtersContainer}>
        <SegmentedButtons
          value={filterType}
          onValueChange={(value) => {
            setFilterType(value);
            setSelectedCompany(null);
          }}
          buttons={[
            { value: 'todos', label: 'Todos' },
            { value: 'empresa', label: 'Empresa' },
            { value: 'particular', label: 'Particular' },
          ]}
          style={styles.segmented}
        />

        {filterType === 'empresa' && (
          <Menu
            visible={menuVisible}
            onDismiss={() => setMenuVisible(false)}
            anchor={
              <Button mode="outlined" onPress={() => setMenuVisible(true)}>
                {selectedCompany || 'Todas las empresas'}
              </Button>
            }
          >
            <Menu.Item
              onPress={() => {
                setSelectedCompany(null);
                setMenuVisible(false);
              }}
              title="Todas las empresas"
            />
            {companies.map((company) => (
              <Menu.Item
                key={company.id}
                onPress={() => {
                  setSelectedCompany(company.nombre);
                  setMenuVisible(false);
                }}
                title={company.nombre}
              />
            ))}
          </Menu>
        )}

        <Menu
          visible={exportMenuVisible}
          onDismiss={() => setExportMenuVisible(false)}
          anchor={
            <Button
              mode="contained"
              onPress={() => setExportMenuVisible(true)}
              icon="download"
            >
              Exportar
            </Button>
          }
        >
          <Menu.Item onPress={() => exportData('csv')} title="Exportar CSV" />
          <Menu.Item onPress={() => exportData('excel')} title="Exportar Excel" />
          <Menu.Item onPress={() => exportData('pdf')} title="Exportar PDF" />
        </Menu>
      </View>

      <FlatList
        data={filteredServices}
        renderItem={renderService}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={['#0066CC']} />
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text variant="bodyLarge" style={styles.emptyText}>
              No hay servicios con los filtros seleccionados
            </Text>
          </View>
        }
      />

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
  statsContainer: {
    padding: 16,
    flexGrow: 0,
  },
  statCard: {
    width: 140,
    marginRight: 12,
    backgroundColor: 'white',
    elevation: 2,
  },
  statValue: {
    fontWeight: 'bold',
    color: '#0066CC',
  },
  amountText: {
    color: '#4CAF50',
  },
  filtersContainer: {
    padding: 16,
    gap: 12,
  },
  segmented: {
    marginBottom: 8,
  },
  list: {
    padding: 16,
    paddingTop: 0,
  },
  card: {
    marginBottom: 12,
    backgroundColor: 'white',
    elevation: 2,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  cardTitle: {
    flex: 1,
    fontWeight: '600',
    color: '#333',
  },
  chip: {
    backgroundColor: '#0066CC',
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
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
    marginTop: 60,
  },
  emptyText: {
    color: '#999',
    textAlign: 'center',
  },
});
