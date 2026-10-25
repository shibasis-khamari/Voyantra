import React, { useState, useEffect } from 'react';
import { View, Text, TextInput, FlatList, TouchableOpacity, StyleSheet, SafeAreaView, StatusBar } from 'react-native';
import { PlaceCard } from '../components/PlaceCard';
import { PlaceModal } from '../components/PlaceModal';
import { MobileAPI } from '../services/api';
import { CATEGORIES, COLORS } from '../constants/theme';
import { usePreferences } from '../context/PreferencesContext';

export function ExploreScreen() {
  const [places, setPlaces] = useState([]);
  const [search, setSearch] = useState('');
  const [selectedCat, setSelectedCat] = useState('all');
  const [activeModal, setActiveModal] = useState(null);
  const { tripPlan } = usePreferences();

  useEffect(() => {
    MobileAPI.getPlaces({ category: selectedCat, search }).then(setPlaces);
  }, [selectedCat, search]);

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor="#ffffff" />
      
      {/* App Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.appTitle}>Voyantra</Text>
          <Text style={styles.subTitle}>Pondicherry Pilot Guide</Text>
        </View>
        <View style={styles.tripBadge}>
          <Text style={styles.tripBadgeText}>🧺 {tripPlan.length} in Basket</Text>
        </View>
      </View>

      {/* Search Input */}
      <View style={styles.searchWrap}>
        <TextInput
          style={styles.searchInput}
          placeholder="Search places, cafes, heritage..."
          placeholderTextColor="#94a3b8"
          value={search}
          onChangeText={setSearch}
        />
      </View>

      {/* Category Filter Horizontal Scroll */}
      <View style={styles.catWrap}>
        <FlatList
          horizontal
          showsHorizontalScrollIndicator={false}
          data={CATEGORIES}
          keyExtractor={item => item.id}
          renderItem={({ item }) => (
            <TouchableOpacity
              style={[styles.catBtn, selectedCat === item.id && styles.catBtnActive]}
              onPress={() => setSelectedCat(item.id)}
            >
              <Text style={[styles.catText, selectedCat === item.id && styles.catTextActive]}>
                {item.label}
              </Text>
            </TouchableOpacity>
          )}
          contentContainerStyle={{ paddingHorizontal: 16 }}
        />
      </View>

      {/* Places List */}
      <FlatList
        data={places}
        keyExtractor={item => item.id}
        renderItem={({ item }) => (
          <PlaceCard place={item} onPress={() => setActiveModal(item)} />
        )}
        contentContainerStyle={styles.list}
      />

      <PlaceModal
        place={activeModal}
        visible={!!activeModal}
        onClose={() => setActiveModal(null)}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#f1f5f9',
  },
  appTitle: {
    fontSize: 22,
    fontWeight: '900',
    color: '#0d9488',
  },
  subTitle: {
    fontSize: 11,
    color: '#64748b',
    fontWeight: '600',
  },
  tripBadge: {
    backgroundColor: '#0f172a',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 20,
  },
  tripBadgeText: {
    color: '#ffffff',
    fontSize: 11,
    fontWeight: '700',
  },
  searchWrap: {
    paddingHorizontal: 16,
    paddingTop: 10,
  },
  searchInput: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 10,
    fontSize: 14,
    borderWidth: 1,
    borderColor: '#e2e8f0',
    color: '#0f172a',
  },
  catWrap: {
    paddingVertical: 10,
  },
  catBtn: {
    paddingHorizontal: 14,
    paddingVertical: 7,
    borderRadius: 20,
    backgroundColor: '#ffffff',
    borderWidth: 1,
    borderColor: '#e2e8f0',
    marginRight: 8,
  },
  catBtnActive: {
    backgroundColor: '#0d9488',
    borderColor: '#0d9488',
  },
  catText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#475569',
  },
  catTextActive: {
    color: '#ffffff',
  },
  list: {
    paddingHorizontal: 16,
    paddingBottom: 20,
  },
});
