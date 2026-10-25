import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, Image, TouchableOpacity, StyleSheet, SafeAreaView } from 'react-native';
import { MobileAPI } from '../services/api';

export function HotelsScreen() {
  const [hotels, setHotels] = useState([]);

  useEffect(() => {
    MobileAPI.getHotels().then(setHotels);
  }, []);

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Hotels & Stays</Text>
        <Text style={styles.subtitle}>Curated Pondicherry accommodations</Text>
      </View>

      <FlatList
        data={hotels}
        keyExtractor={item => item.id}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Image source={{ uri: item.image_url }} style={styles.image} />
            <View style={styles.body}>
              <View style={styles.row}>
                <Text style={styles.tier}>{item.budget_tier.toUpperCase()}</Text>
                <Text style={styles.rating}>★ {item.rating}</Text>
              </View>
              <Text style={styles.name}>{item.name}</Text>
              <Text style={styles.prox}>📍 {item.proximity_tag || item.address}</Text>
              <Text style={styles.desc} numberOfLines={2}>{item.description}</Text>
              <View style={styles.footer}>
                <Text style={styles.price}>₹{item.price_per_night_inr.toLocaleString()} <Text style={{ fontSize: 11, fontWeight: 'normal', color: '#94a3b8' }}>/ night</Text></Text>
              </View>
            </View>
          </View>
        )}
        contentContainerStyle={styles.list}
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
    padding: 16,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#f1f5f9',
  },
  title: {
    fontSize: 20,
    fontWeight: '800',
    color: '#0f172a',
  },
  subtitle: {
    fontSize: 12,
    color: '#64748b',
    marginTop: 2,
  },
  list: {
    padding: 16,
  },
  card: {
    backgroundColor: '#ffffff',
    borderRadius: 16,
    marginBottom: 16,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  image: {
    height: 140,
    width: '100%',
    backgroundColor: '#f1f5f9',
  },
  body: {
    padding: 14,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  tier: {
    fontSize: 10,
    fontWeight: '800',
    color: '#0d9488',
  },
  rating: {
    fontSize: 12,
    fontWeight: '700',
    color: '#d97706',
  },
  name: {
    fontSize: 16,
    fontWeight: '700',
    color: '#0f172a',
    marginBottom: 2,
  },
  prox: {
    fontSize: 12,
    color: '#0d9488',
    fontWeight: '600',
    marginBottom: 6,
  },
  desc: {
    fontSize: 12,
    color: '#64748b',
    lineHeight: 17,
    marginBottom: 10,
  },
  footer: {
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#f1f5f9',
  },
  price: {
    fontSize: 16,
    fontWeight: '800',
    color: '#0f172a',
  },
});
