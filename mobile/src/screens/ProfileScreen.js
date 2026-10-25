import React from 'react';
import { View, Text, TouchableOpacity, ScrollView, StyleSheet, SafeAreaView } from 'react-native';
import { usePreferences } from '../context/PreferencesContext';
import { AGE_GROUPS, DIETARY_OPTIONS, COLORS } from '../constants/theme';

export function ProfileScreen() {
  const { ageGroup, setAgeGroup, dietaryPreference, setDietaryPreference, tripPlan } = usePreferences();

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView>
        <View style={styles.header}>
          <Text style={styles.title}>My Preferences</Text>
          <Text style={styles.subtitle}>Self-declared demographic & dietary profile</Text>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Age Demographic Bracket</Text>
          {AGE_GROUPS.map(a => {
            const active = ageGroup === a.id;
            return (
              <TouchableOpacity
                key={a.id}
                style={[styles.card, active && styles.cardActive]}
                onPress={() => setAgeGroup(a.id)}
              >
                <View style={styles.row}>
                  <Text style={[styles.cardTitle, active && styles.cardTitleActive]}>{a.label}</Text>
                  {active && <Text style={styles.check}>✓</Text>}
                </View>
                <Text style={styles.cardDesc}>{a.desc}</Text>
              </TouchableOpacity>
            );
          })}
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Dietary Preference (Opt-in)</Text>
          {DIETARY_OPTIONS.map(d => {
            const active = dietaryPreference === d.id;
            return (
              <TouchableOpacity
                key={d.id}
                style={[styles.card, active && styles.cardActive]}
                onPress={() => setDietaryPreference(d.id)}
              >
                <View style={styles.row}>
                  <Text style={[styles.cardTitle, active && styles.cardTitleActive]}>{d.label}</Text>
                  {active && <Text style={styles.check}>✓</Text>}
                </View>
              </TouchableOpacity>
            );
          })}
        </View>
      </ScrollView>
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
    padding: 16,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '800',
    color: '#334155',
    textTransform: 'uppercase',
    marginBottom: 10,
  },
  card: {
    backgroundColor: '#ffffff',
    padding: 14,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#e2e8f0',
    marginBottom: 8,
  },
  cardActive: {
    backgroundColor: '#f0fdf9',
    borderColor: '#0d9488',
    borderWidth: 1.5,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  cardTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#0f172a',
  },
  cardTitleActive: {
    color: '#0d9488',
  },
  check: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#0d9488',
  },
  cardDesc: {
    fontSize: 11,
    color: '#64748b',
    marginTop: 4,
  },
});
