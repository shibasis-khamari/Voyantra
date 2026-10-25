import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

export function CrowdBadge({ tendency = 'medium' }) {
  const level = (tendency || 'medium').toLowerCase();

  let bg = '#fef3c7';
  let text = '#b45309';
  let label = 'Moderate Crowd';

  if (level === 'low') {
    bg = '#d1fae5';
    text = '#047857';
    label = 'Low Crowd';
  } else if (level === 'high') {
    bg = '#ffe4e6';
    text = '#be123c';
    label = 'High Footfall';
  }

  return (
    <View style={[styles.badge, { backgroundColor: bg }]}>
      <Text style={[styles.text, { color: text }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 12,
    alignSelf: 'flex-start',
  },
  text: {
    fontSize: 11,
    fontWeight: '700',
  },
});
