import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, SafeAreaView } from 'react-native';
import { ExploreScreen } from './src/screens/ExploreScreen';
import { PlannerScreen } from './src/screens/PlannerScreen';
import { HotelsScreen } from './src/screens/HotelsScreen';
import { MapScreen } from './src/screens/MapScreen';
import { ProfileScreen } from './src/screens/ProfileScreen';
import { PreferencesProvider } from './src/context/PreferencesContext';

export default function App() {
  const [currentTab, setCurrentTab] = useState('explore');

  const renderScreen = () => {
    switch (currentTab) {
      case 'explore':
        return <ExploreScreen />;
      case 'planner':
        return <PlannerScreen />;
      case 'hotels':
        return <HotelsScreen />;
      case 'map':
        return <MapScreen />;
      case 'profile':
        return <ProfileScreen />;
      default:
        return <ExploreScreen />;
    }
  };

  const tabs = [
    { id: 'explore', label: 'Explore', icon: '🧭' },
    { id: 'planner', label: 'Planner', icon: '✨' },
    { id: 'hotels', label: 'Hotels', icon: '🏨' },
    { id: 'map', label: 'Map', icon: '🗺️' },
    { id: 'profile', label: 'Profile', icon: '👤' },
  ];

  return (
    <PreferencesProvider>
      <View style={styles.container}>
        {/* Active Screen View */}
        <View style={styles.content}>
          {renderScreen()}
        </View>

        {/* Bottom Tab Bar */}
        <View style={styles.tabBar}>
          {tabs.map(tab => {
            const isActive = currentTab === tab.id;
            return (
              <TouchableOpacity
                key={tab.id}
                style={styles.tabItem}
                onPress={() => setCurrentTab(tab.id)}
              >
                <Text style={styles.tabIcon}>{tab.icon}</Text>
                <Text style={[styles.tabLabel, isActive && styles.tabLabelActive]}>
                  {tab.label}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>
      </View>
    </PreferencesProvider>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  content: {
    flex: 1,
  },
  tabBar: {
    flexDirection: 'row',
    height: 64,
    backgroundColor: '#ffffff',
    borderTopWidth: 1,
    borderTopColor: '#e2e8f0',
    paddingBottom: 8,
    paddingTop: 6,
  },
  tabItem: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  tabIcon: {
    fontSize: 18,
    marginBottom: 2,
  },
  tabLabel: {
    fontSize: 10,
    fontWeight: '600',
    color: '#64748b',
  },
  tabLabelActive: {
    color: '#0d9488',
    fontWeight: '800',
  },
});
