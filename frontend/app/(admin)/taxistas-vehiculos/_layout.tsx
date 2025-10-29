import React from 'react';
import { MaterialTopTabBar, createMaterialTopTabNavigator } from '@react-navigation/material-top-tabs';

const Tab = createMaterialTopTabNavigator();

export default function TaxistasVehiculosLayout() {
  return (
    <Tab.Navigator
      screenOptions={{
        tabBarActiveTintColor: '#0066CC',
        tabBarInactiveTintColor: '#666',
        tabBarIndicatorStyle: {
          backgroundColor: '#0066CC',
        },
        tabBarStyle: {
          backgroundColor: '#FFFFFF',
        },
      }}
    >
      <Tab.Screen
        name="taxistas-list"
        options={{ title: 'Taxistas' }}
      />
      <Tab.Screen
        name="vehiculos-list"
        options={{ title: 'Vehículos' }}
      />
    </Tab.Navigator>
  );
}
