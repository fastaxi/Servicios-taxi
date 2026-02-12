import React, { useState, useEffect } from 'react';
import { View, StyleSheet, Image, KeyboardAvoidingView, Platform, ScrollView } from 'react-native';
import { TextInput, Button, Text, Snackbar } from 'react-native-paper';
import { useAuth } from '../contexts/AuthContext';
import { useConfig } from '../contexts/ConfigContext';
import { useRouter } from 'expo-router';
import TaxiFastLogo from '../components/TaxiFastLogo';

export default function LoginScreen() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { user, login, loading: authLoading } = useAuth();
  const { config, loading: configLoading } = useConfig();
  const router = useRouter();

  useEffect(() => {
    if (user && !authLoading) {
      if (user.role === 'superadmin') {
        router.replace('/(superadmin)/dashboard');
      } else if (user.role === 'admin') {
        router.replace('/(admin)/dashboard');
      } else {
        router.replace('/(tabs)/services');
      }
    }
  }, [user, authLoading]);

  const handleLogin = async () => {
    if (!username || !password) {
      setError('Por favor, completa todos los campos');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await login(username, password);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (authLoading || configLoading) {
    return (
      <View style={styles.container}>
        <Text>Cargando...</Text>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView 
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView 
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
      >
        <View style={styles.logoContainer}>
          <TaxiFastLogo size="large" />
        </View>

        <View style={styles.formContainer}>
          <Text variant="headlineMedium" style={styles.title}>
            TaxiFast
          </Text>
          <Text variant="bodyMedium" style={styles.subtitle}>
            Gestión de Servicios
          </Text>

          <TextInput
            label="Usuario"
            value={username}
            onChangeText={setUsername}
            mode="outlined"
            style={styles.input}
            autoCapitalize="none"
            disabled={loading}
          />

          <TextInput
            label="Contraseña"
            value={password}
            onChangeText={setPassword}
            mode="outlined"
            secureTextEntry={!showPassword}
            style={styles.input}
            disabled={loading}
            right={<TextInput.Icon icon={showPassword ? "eye-off" : "eye"} onPress={() => setShowPassword(!showPassword)} />}
          />

          <Button
            mode="contained"
            onPress={handleLogin}
            style={styles.button}
            loading={loading}
            disabled={loading}
          >
            Iniciar Sesión
          </Button>

          {__DEV__ && (
            <Text variant="bodySmall" style={styles.debugText}>
              API: {process.env.EXPO_PUBLIC_BACKEND_URL || 'https://taxi-services-1.preview.emergentagent.com'}
            </Text>
          )}

          <View style={styles.footer}>
            <Text variant="bodySmall" style={styles.footerText}>
              {config.web}
            </Text>
            <Text variant="bodySmall" style={styles.footerText}>
              {config.telefono}
            </Text>
          </View>
        </View>

        <Snackbar
          visible={!!error}
          onDismiss={() => setError('')}
          duration={3000}
          style={styles.snackbar}
        >
          {error}
        </Snackbar>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 24,
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 32,
  },
  logo: {
    width: 200,
    height: 150,
  },
  formContainer: {
    backgroundColor: 'white',
    borderRadius: 16,
    padding: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  title: {
    textAlign: 'center',
    marginBottom: 8,
    color: '#0066CC',
    fontWeight: 'bold',
  },
  subtitle: {
    textAlign: 'center',
    marginBottom: 24,
    color: '#666',
  },
  input: {
    marginBottom: 16,
  },
  button: {
    marginTop: 8,
    paddingVertical: 8,
  },
  footer: {
    marginTop: 24,
    alignItems: 'center',
  },
  footerText: {
    color: '#666',
    marginTop: 4,
  },
  debugText: {
    color: '#999',
    fontSize: 10,
    marginTop: 8,
    textAlign: 'center',
  },
  snackbar: {
    backgroundColor: '#D32F2F',
  },
});
