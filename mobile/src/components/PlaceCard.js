import React from 'react';
import { View, Text, Image, TouchableOpacity, StyleSheet } from 'react-native';
import { CrowdBadge } from './CrowdBadge';
import { COLORS } from '../constants/theme';
import { usePreferences } from '../context/PreferencesContext';

export function PlaceCard({ place, matchScore, matchReasons, onPress }) {
  const { tripPlan, addToTripPlan, removeFromTripPlan, favorites, toggleFavorite } = usePreferences();
  const isPlanned = tripPlan.some(p => p.id === place.id);
  const isFav = favorites.includes(place.id);

  return (
    <TouchableOpacity activeOpacity={0.9} style={styles.card} onPress={onPress}>
      {/* Image */}
      <View style={styles.imageContainer}>
        <Image source={{ uri: place.image_url }} style={styles.image} />
        <View style={styles.categoryBadge}>
          <Text style={styles.categoryText}>{place.category.toUpperCase()}</Text>
        </View>
        <TouchableOpacity 
          style={styles.favButton}
          onPress={() => toggleFavorite(place.id)}
        >
          <Text style={{ fontSize: 16 }}>{isFav ? '❤️' : '🤍'}</Text>
        </TouchableOpacity>
      </View>

      {/* Body */}
      <View style={styles.body}>
        {matchScore !== undefined && (
          <View style={styles.matchBadge}>
            <Text style={styles.matchText}>✨ {matchScore}% Personal Match</Text>
          </View>
        )}

        <Text style={styles.title} numberOfLines={1}>{place.name}</Text>
        <Text style={styles.address} numberOfLines={1}>📍 {place.address}</Text>
        <Text style={styles.desc} numberOfLines={2}>{place.description}</Text>

        {/* Footer */}
        <View style={styles.footer}>
          <CrowdBadge tendency={place.crowd_tendency} />
          
          <TouchableOpacity
            style={[styles.actionBtn, isPlanned && styles.actionBtnActive]}
            onPress={() => isPlanned ? removeFromTripPlan(place.id) : addToTripPlan(place)}
          >
            <Text style={[styles.actionBtnText, isPlanned && styles.actionBtnTextActive]}>
              {isPlanned ? '✓ In Trip' : '+ Add'}
            </Text>
          </TouchableOpacity>
        </View>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#ffffff',
    borderRadius: 16,
    marginBottom: 16,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: '#e2e8f0',
    elevation: 2,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 2 },
  },
  imageContainer: {
    height: 160,
    width: '100%',
    position: 'relative',
    backgroundColor: '#f1f5f9',
  },
  image: {
    width: '100%',
    height: '100%',
  },
  categoryBadge: {
    position: 'absolute',
    top: 10,
    left: 10,
    backgroundColor: 'rgba(255,255,255,0.92)',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
  },
  categoryText: {
    fontSize: 10,
    fontWeight: '800',
    color: '#0f172a',
  },
  favButton: {
    position: 'absolute',
    top: 10,
    right: 10,
    backgroundColor: 'rgba(255,255,255,0.92)',
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  body: {
    padding: 14,
  },
  matchBadge: {
    backgroundColor: '#ccfbef',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
    alignSelf: 'flex-start',
    marginBottom: 6,
  },
  matchText: {
    color: '#0f766e',
    fontSize: 11,
    fontWeight: '700',
  },
  title: {
    fontSize: 16,
    fontWeight: '700',
    color: '#0f172a',
    marginBottom: 2,
  },
  address: {
    fontSize: 12,
    color: '#64748b',
    marginBottom: 6,
  },
  desc: {
    fontSize: 12,
    color: '#475569',
    lineHeight: 18,
    marginBottom: 10,
  },
  footer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#f1f5f9',
  },
  actionBtn: {
    backgroundColor: '#f0fdf9',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#9af6df',
  },
  actionBtnActive: {
    backgroundColor: '#0d9488',
    borderColor: '#0d9488',
  },
  actionBtnText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#0d9488',
  },
  actionBtnTextActive: {
    color: '#ffffff',
  },
});
