import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { MaterialCommunityIcons } from '@expo/vector-icons';

interface TaxiFastLogoProps {
  size?: 'small' | 'medium' | 'large';
  color?: string;
  showIcon?: boolean;
}

export default function TaxiFastLogo({ 
  size = 'medium', 
  color = '#0066CC',
  showIcon = true 
}: TaxiFastLogoProps) {
  const sizes = {
    small: { fontSize: 24, iconSize: 28, spacing: 8 },
    medium: { fontSize: 32, iconSize: 40, spacing: 10 },
    large: { fontSize: 48, iconSize: 56, spacing: 12 },
  };

  const { fontSize, iconSize, spacing } = sizes[size];

  return (
    <View style={styles.container}>
      {showIcon && (
        <View style={[styles.iconContainer, { backgroundColor: color }]}>
          <MaterialCommunityIcons name="taxi" size={iconSize} color="#FFD700" />
        </View>
      )}
      <View style={[styles.textContainer, showIcon && { marginTop: spacing }]}>
        <Text style={[styles.taxiText, { fontSize, color }]}>Taxi</Text>
        <Text style={[styles.fastText, { fontSize, color: '#FFD700' }]}>Fast</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconContainer: {
    padding: 16,
    borderRadius: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  textContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  taxiText: {
    fontWeight: 'bold',
    letterSpacing: 1,
  },
  fastText: {
    fontWeight: 'bold',
    letterSpacing: 1,
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 1, height: 1 },
    textShadowRadius: 2,
  },
});
