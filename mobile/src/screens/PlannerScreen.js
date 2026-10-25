import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, SafeAreaView, ScrollView } from 'react-native';
import { PlaceCard } from '../components/PlaceCard';
import { PlaceModal } from '../components/PlaceModal';
import { MobileAPI } from '../services/api';
import { AGE_GROUPS, DIETARY_OPTIONS } from '../constants/theme';
import { usePreferences } from '../context/PreferencesContext';

export function PlannerScreen() {
  const { ageGroup, setAgeGroup, dietaryPreference, setDietaryPreference, budgetTier, tripPlan, removeFromTripPlan } = usePreferences();
  const [recommendations, setRecommendations] = useState([]);
  const [activeModal, setActiveModal] = useState(null);

  useEffect(() => {
    MobileAPI.getPersonalizedRecommendations({ age_group: ageGroup, dietary_preference: dietaryPreference, budget_tier: budgetTier })
      .then(res => setRecommendations(res.ranked_places || []));
  }, [ageGroup, dietaryPreference, budgetTier]);

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>Personalized Planner</Text>
          <Text style={styles.subtitle}>Demographic & dietary weighting engine</Text>
        </View>

        {/* Age Group Selector Chips */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>1. Age Bracket</Text>
          <View style={styles.chipsRow}>
            {AGE_GROUPS.map(a => (
              <TouchableOpacity
                key={a.id}
                style={[styles.chip, ageGroup === a.id && styles.chipActive]}
                onPress={() => setAgeGroup(a.id)}
              >
                <Text style={[styles.chipText, ageGroup === a.id && styles.chipTextActive]}>
                  {a.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Dietary Preference Chips */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>2. Dietary (Opt-in)</Text>
          <View style={styles.chipsRow}>
            {DIETARY_OPTIONS.map(d => (
              <TouchableOpacity
                key={d.id}
                style={[styles.chip, dietaryPreference === d.id && styles.chipActive]}
                onPress={() => setDietaryPreference(d.id)}
              >
                <Text style={[styles.chipText, dietaryPreference === d.id && styles.chipTextActive]}>
                  {d.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Ranked Places */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Ranked for You ({recommendations.length})</Text>
          {recommendations.map(item => (
            <PlaceCard
              key={item.place.id}
              place={item.place}
              matchScore={item.match_score}
              matchReasons={item.match_reasons}
              onPress={() => setActiveModal(item)}
            />
          ))}
        </View>
      </ScrollView>

      <PlaceModal
        place={activeModal?.place}
        matchInfo={activeModal}
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
  section: {
    paddingHorizontal: 16,
    paddingTop: 16,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '800',
    color: '#334155',
    textTransform: 'uppercase',
    marginBottom: 8,
  },
  chipsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  chip: {
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 10,
    backgroundColor: '#ffffff',
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  chipActive: {
    backgroundColor: '#0d9488',
    borderColor: '#0d9488',
  },
  chipText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#475569',
  },
  chipTextActive: {
    color: '#ffffff',
  },
});
