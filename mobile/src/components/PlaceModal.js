import React from 'react';
import { Modal, View, Text, Image, TouchableOpacity, ScrollView, StyleSheet, Linking } from 'react-native';
import { CrowdBadge } from './CrowdBadge';
import { COLORS } from '../constants/theme';
import { usePreferences } from '../context/PreferencesContext';

export function PlaceModal({ place, matchInfo, visible, onClose }) {
  const { tripPlan, addToTripPlan, removeFromTripPlan } = usePreferences();
  if (!place) return null;

  const isPlanned = tripPlan.some(p => p.id === place.id);

  const openNavigation = () => {
    const url = `https://www.openstreetmap.org/directions?engine=fossgis_osrm_car&route=%3B${place.coordinates.lat}%2C${place.coordinates.lng}`;
    Linking.openURL(url);
  };

  return (
    <Modal visible={visible} animationType="slide" transparent={true} onRequestClose={onClose}>
      <View style={styles.overlay}>
        <View style={styles.sheet}>
          <ScrollView contentContainerStyle={styles.scroll}>
            {/* Header Image */}
            <View style={styles.imageWrap}>
              <Image source={{ uri: place.image_url }} style={styles.image} />
              <TouchableOpacity style={styles.closeBtn} onPress={onClose}>
                <Text style={styles.closeText}>✕</Text>
              </TouchableOpacity>
            </View>

            {/* Details */}
            <View style={styles.content}>
              <View style={styles.row}>
                <Text style={styles.category}>{place.category.toUpperCase()}</Text>
                <CrowdBadge tendency={place.crowd_tendency} />
              </View>

              <Text style={styles.title}>{place.name}</Text>
              <Text style={styles.address}>📍 {place.address}</Text>

              {matchInfo && (
                <View style={styles.matchBanner}>
                  <Text style={styles.matchScore}>✨ {matchInfo.match_score}% Match for your Profile</Text>
                  {matchInfo.match_reasons.map((r, i) => (
                    <Text key={i} style={styles.matchReason}>• {r}</Text>
                  ))}
                </View>
              )}

              <Text style={styles.sectionHeader}>About This Destination</Text>
              <Text style={styles.desc}>{place.description}</Text>

              <View style={styles.metaBox}>
                <Text style={styles.metaText}>⏱ Duration: ~{place.duration_minutes} mins</Text>
                <Text style={styles.metaText}>💰 Est. Cost: {place.estimated_cost_inr === 0 ? 'Free' : `₹${place.estimated_cost_inr}`}</Text>
                <Text style={styles.metaText}>♿ Accessibility Rating: {place.accessibility_rating}/5</Text>
                <Text style={styles.metaText}>🌅 Best Time: {place.best_time_to_visit}</Text>
              </View>

              {/* Action Buttons */}
              <View style={styles.actions}>
                <TouchableOpacity style={styles.navBtn} onPress={openNavigation}>
                  <Text style={styles.navBtnText}>🧭 OSRM Directions</Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={[styles.tripBtn, isPlanned && styles.tripBtnRemove]}
                  onPress={() => isPlanned ? removeFromTripPlan(place.id) : addToTripPlan(place)}
                >
                  <Text style={styles.tripBtnText}>
                    {isPlanned ? '✕ Remove from Trip' : '✓ Add to Trip'}
                  </Text>
                </TouchableOpacity>
              </View>
            </View>
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  sheet: {
    backgroundColor: '#ffffff',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    maxHeight: '85%',
    overflow: 'hidden',
  },
  scroll: {
    paddingBottom: 30,
  },
  imageWrap: {
    height: 200,
    width: '100%',
    position: 'relative',
    backgroundColor: '#f1f5f9',
  },
  image: {
    width: '100%',
    height: '100%',
  },
  closeBtn: {
    position: 'absolute',
    top: 14,
    right: 14,
    backgroundColor: 'rgba(0,0,0,0.6)',
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  closeText: {
    color: '#ffffff',
    fontWeight: 'bold',
    fontSize: 14,
  },
  content: {
    padding: 18,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  category: {
    fontSize: 11,
    fontWeight: '800',
    color: '#0d9488',
  },
  title: {
    fontSize: 20,
    fontWeight: '800',
    color: '#0f172a',
    marginBottom: 4,
  },
  address: {
    fontSize: 13,
    color: '#64748b',
    marginBottom: 12,
  },
  matchBanner: {
    backgroundColor: '#f0fdf9',
    padding: 12,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#ccfbef',
    marginBottom: 14,
  },
  matchScore: {
    fontSize: 13,
    fontWeight: '800',
    color: '#0f766e',
    marginBottom: 4,
  },
  matchReason: {
    fontSize: 11,
    color: '#134e4a',
    marginTop: 2,
  },
  sectionHeader: {
    fontSize: 13,
    fontWeight: '800',
    color: '#0f172a',
    textTransform: 'uppercase',
    marginBottom: 6,
  },
  desc: {
    fontSize: 13,
    color: '#475569',
    lineHeight: 20,
    marginBottom: 14,
  },
  metaBox: {
    backgroundColor: '#f8fafc',
    padding: 12,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#e2e8f0',
    gap: 6,
    marginBottom: 18,
  },
  metaText: {
    fontSize: 12,
    color: '#334155',
    fontWeight: '600',
  },
  actions: {
    flexDirection: 'row',
    gap: 10,
  },
  navBtn: {
    flex: 1,
    backgroundColor: '#f1f5f9',
    paddingVertical: 12,
    borderRadius: 12,
    alignItems: 'center',
  },
  navBtnText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#0f172a',
  },
  tripBtn: {
    flex: 1,
    backgroundColor: '#0d9488',
    paddingVertical: 12,
    borderRadius: 12,
    alignItems: 'center',
  },
  tripBtnRemove: {
    backgroundColor: '#e11d48',
  },
  tripBtnText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#ffffff',
  },
});
