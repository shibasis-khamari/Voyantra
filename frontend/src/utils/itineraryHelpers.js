/**
 * Voyantra Itinerary Helper Utilities
 * Centralizes slot identification to guarantee that day-level metadata
 * (such as city_id, day_budget_inr, estimated_travel_time_minutes) are never
 * misidentified or rendered as itinerary stops.
 */

export const KNOWN_DAY_METADATA_KEYS = new Set([
  'day_number',
  'theme',
  'city_id',
  'day_budget_inr',
  'estimated_travel_time_minutes',
  'custom_stops',
  'quality_score'
]);

export function isSlotKey(key, value) {
  if (!key) return false;
  if (KNOWN_DAY_METADATA_KEYS.has(key)) return false;
  if (!value) return false;

  // A valid stop must be an object with place_name, slot_id, category, or est_time
  if (typeof value === 'object' && !Array.isArray(value)) {
    return Boolean(value.place_name || value.slot_id || value.category || value.est_time);
  }

  // Allow string slot value only if key is an authentic time slot name
  if (typeof value === 'string' && (['morning', 'afternoon', 'evening'].includes(key) || key.startsWith('custom_'))) {
    return true;
  }

  return false;
}
