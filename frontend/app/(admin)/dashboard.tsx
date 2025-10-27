import React, { useState, useEffect } from 'react';
import {
  View,
  StyleSheet,
  FlatList,
  RefreshControl,
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
  TextInput,
  IconButton,
} from 'react-native-paper';
import { useAuth } from '../../contexts/AuthContext';
import { useRouter, useFocusEffect } from 'expo-router';
import axios from 'axios';
import * as FileSystem from 'expo-file-system';
import * as Sharing from 'expo-sharing';
import { format } from 'date-fns';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL + '/api';

interface Service {
  id: string;
  fecha: string;
  hora: string;
  taxista_nombre: string;
  origen: string;
  destino: string;
  importe: number;
  importe_espera: number;
  importe_total: number;
  kilometros: number;
  tipo: string;
  empresa_nombre?: string;
}

interface Company {
  id: string;
  nombre: string;
}

interface Taxista {
  id: string;
  nombre: string;
  username: string;
}

export default function DashboardScreen() {
  const [services, setServices] = useState<Service[]>([]);
  const [filteredServices, setFilteredServices] = useState<Service[]>([]);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [taxistas, setTaxistas] = useState<Taxista[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [filterType, setFilterType] = useState('todos');
  const [selectedCompany, setSelectedCompany] = useState<string | null>(null);
  const [selectedTaxista, setSelectedTaxista] = useState<string | null>(null);
  const [fechaInicio, setFechaInicio] = useState('');
  const [fechaFin, setFechaFin] = useState('');
  const [menuVisible, setMenuVisible] = useState(false);
  const [taxistaMenuVisible, setTaxistaMenuVisible] = useState(false);
  const [exportMenuVisible, setExportMenuVisible] = useState(false);
  const [snackbar, setSnackbar] = useState({ visible: false, message: '' });
  const { token } = useAuth();
  const router = useRouter();

  useEffect(() => {
    loadData();
  }, []);

  // Recargar datos cada vez que se enfoca la pantalla
  useFocusEffect(
    React.useCallback(() => {
      loadData();
    }, [])
  );

  useEffect(() => {
    applyFilters();
  }, [services, filterType, selectedCompany, selectedTaxista, fechaInicio, fechaFin]);

  const loadData = async () => {
    try {
      const [servicesRes, companiesRes, taxistasRes] = await Promise.all([
        axios.get(`${API_URL}/services`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        axios.get(`${API_URL}/companies`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        axios.get(`${API_URL}/users`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ]);

      setServices(servicesRes.data);
      setCompanies(companiesRes.data);
      setTaxistas(taxistasRes.data);
    } catch (error) {
      console.error('Error loading data:', error);
    }
  };

  const applyFilters = () => {
    let filtered = [...services];

    // Filtro por tipo
    if (filterType === 'empresa') {
      filtered = filtered.filter((s) => s.tipo === 'empresa');
      if (selectedCompany) {
        filtered = filtered.filter((s) => s.empresa_nombre === selectedCompany);
      }
    } else if (filterType === 'particular') {
      filtered = filtered.filter((s) => s.tipo === 'particular');
    }

    // Filtro por taxista
    if (selectedTaxista) {
      filtered = filtered.filter((s) => s.taxista_nombre === selectedTaxista);
    }

    // Filtro por fechas
    if (fechaInicio) {
      filtered = filtered.filter((s) => s.fecha >= fechaInicio);
    }
    if (fechaFin) {
      filtered = filtered.filter((s) => s.fecha <= fechaFin);
    }

    setFilteredServices(filtered);
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const limpiarFiltros = () => {
    setFilterType('todos');
    setSelectedCompany(null);
    setSelectedTaxista(null);
    setFechaInicio('');
    setFechaFin('');
  };

  const formatEuro = (amount: number) => {
    return amount.toFixed(2).replace('.', ',') + ' €';
  };

  const getTotalImporte = () => {
    return formatEuro(filteredServices.reduce((sum, s) => sum + s.importe, 0));
  };

  const getTotalKilometros = () => {
    return filteredServices.reduce((sum, s) => sum + s.kilometros, 0).toFixed(2);
  };

  const exportData = async (format: 'csv' | 'excel' | 'pdf') => {
    try {
      let queryParams = new URLSearchParams();
      
      if (filterType === 'empresa') {
        queryParams.append('tipo', 'empresa');
        if (selectedCompany) {
          const company = companies.find((c) => c.nombre === selectedCompany);
          if (company) {
            queryParams.append('empresa_id', company.id);
          }
        }
      } else if (filterType === 'particular') {
        queryParams.append('tipo', 'particular');
      }

      if (selectedTaxista) {
        const taxista = taxistas.find((t) => t.nombre === selectedTaxista);
        if (taxista) {
          queryParams.append('taxista_id', taxista.id);
        }
      }

      if (fechaInicio) {
        queryParams.append('fecha_inicio', fechaInicio);
      }
      if (fechaFin) {
        queryParams.append('fecha_fin', fechaFin);
      }

      const queryString = queryParams.toString();
      const url = `${API_URL}/services/export/${format}${queryString ? '?' + queryString : ''}`;

      const response = await axios.get(url, {
        headers: { Authorization: `Bearer ${token}` },
        responseType: 'blob',
      });

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
          <View style={styles.cardTitleContainer}>
            <Text variant="titleMedium" style={styles.cardTitle}>
              {item.origen} → {item.destino}
            </Text>
            <Chip mode="flat" style={styles.chip}>
              {formatEuro(item.importe_total || item.importe)}
            </Chip>
          </View>
          <IconButton
            icon="pencil"
            size={20}
            onPress={() => router.push(`/(admin)/edit-service?id=${item.id}`)}
            iconColor="#0066CC"
          />
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

        {item.importe_espera > 0 && (
          <View style={styles.detailRow}>
            <Text variant="bodySmall" style={styles.label}>Imp. espera:</Text>
            <Text variant="bodySmall">{formatEuro(item.importe_espera)}</Text>
          </View>
        )}

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
              {getTotalImporte()}
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
        <Text variant="titleMedium" style={styles.filterTitle}>Filtros</Text>
        
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
              <Button mode="outlined" onPress={() => setMenuVisible(true)} icon="office-building">
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
          visible={taxistaMenuVisible}
          onDismiss={() => setTaxistaMenuVisible(false)}
          anchor={
            <Button 
              mode="outlined" 
              onPress={() => setTaxistaMenuVisible(true)} 
              icon="account"
              style={styles.filterButton}
            >
              {selectedTaxista || 'Todos los taxistas'}
            </Button>
          }
        >
          <Menu.Item
            onPress={() => {
              setSelectedTaxista(null);
              setTaxistaMenuVisible(false);
            }}
            title="Todos los taxistas"
          />
          {taxistas.map((taxista) => (
            <Menu.Item
              key={taxista.id}
              onPress={() => {
                setSelectedTaxista(taxista.nombre);
                setTaxistaMenuVisible(false);
              }}
              title={taxista.nombre}
            />
          ))}
        </Menu>

        <View style={styles.dateRow}>
          <TextInput
            label="Fecha Inicio"
            value={fechaInicio}
            onChangeText={setFechaInicio}
            mode="outlined"
            placeholder="dd/mm/yyyy"
            style={styles.dateInput}
            dense
          />
          <TextInput
            label="Fecha Fin"
            value={fechaFin}
            onChangeText={setFechaFin}
            mode="outlined"
            placeholder="dd/mm/yyyy"
            style={styles.dateInput}
            dense
          />
        </View>

        <View style={styles.actionRow}>
          <Button
            mode="outlined"
            onPress={limpiarFiltros}
            icon="filter-remove"
            style={styles.actionButton}
          >
            Limpiar
          </Button>

          <Menu
            visible={exportMenuVisible}
            onDismiss={() => setExportMenuVisible(false)}
            anchor={
              <Button
                mode="contained"
                onPress={() => setExportMenuVisible(true)}
                icon="download"
                style={styles.actionButton}
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
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  filterTitle: {
    marginBottom: 12,
    color: '#0066CC',
    fontWeight: 'bold',
  },
  segmented: {
    marginBottom: 12,
  },
  filterButton: {
    marginBottom: 12,
  },
  dateRow: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 12,
  },
  dateInput: {
    flex: 1,
  },
  actionRow: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 8,
  },
  actionButton: {
    flex: 1,
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
    alignItems: 'center',
    marginBottom: 8,
  },
  cardTitleContainer: {
    flex: 1,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
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
