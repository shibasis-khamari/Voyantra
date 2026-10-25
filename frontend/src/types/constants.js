export const CATEGORIES = [
  { id: 'all', label: 'All Places', icon: 'Sparkles' },
  { id: 'heritage', label: 'French Heritage', icon: 'Landmark' },
  { id: 'beach', label: 'Beaches & Sea', icon: 'Waves' },
  { id: 'spiritual', label: 'Spiritual & Ashram', icon: 'HeartHandshake' },
  { id: 'cafe', label: 'French Cafes', icon: 'Coffee' },
  { id: 'dining', label: 'Dining & Food', icon: 'Utensils' },
  { id: 'nature', label: 'Nature & Parks', icon: 'Trees' },
  { id: 'adventure', label: 'Adventure & Surf', icon: 'Compass' },
  { id: 'shopping', label: 'Boutiques & Crafts', icon: 'ShoppingBag' }
];

export const AGE_GROUPS = [
  { 
    id: 'young_adult', 
    label: '18 - 25 yrs (Young Adult / Gen-Z)', 
    shortLabel: '18-25',
    desc: 'Prioritizes trendy cafes, active beach sports, nightlife, and photo spots.' 
  },
  { 
    id: 'adult', 
    label: '26 - 40 yrs (Young Professional / Couple)', 
    shortLabel: '26-40',
    desc: 'Balances cultural heritage walks, boutique dining, and serene coastal retreats.' 
  },
  { 
    id: 'family', 
    label: '41 - 60 yrs (Family & Group Travel)', 
    shortLabel: '41-60',
    desc: 'Focuses on family-friendly pace, nature gardens, clean amenities, and ease of access.' 
  },
  { 
    id: 'senior', 
    label: '60+ yrs (Senior Travelers)', 
    shortLabel: '60+',
    desc: 'Emphasizes high accessibility, tranquil ashrams, minimal stairs, and relaxed pacing.' 
  }
];

export const DIETARY_OPTIONS = [
  { id: 'all', label: 'No Dietary Preference', desc: 'Show all general cuisines and bistros' },
  { id: 'vegetarian', label: 'Vegetarian Friendly', desc: 'Cafes and restaurants with strong vegetarian options' },
  { id: 'pure_veg_jain', label: 'Pure Veg & Jain', desc: 'Strict pure vegetarian kitchens and Jain options (e.g., Surguru)' },
  { id: 'halal', label: 'Halal Certified', desc: 'Halal certified dining' },
  { id: 'vegan', label: 'Vegan Friendly', desc: 'Organic plant-based spots in Auroville & White Town' }
];

export const BUDGET_TIERS = [
  { id: 'budget', label: 'Budget (₹)', symbol: '₹', desc: 'Free spots, pocket-friendly street food, hostels' },
  { id: 'moderate', label: 'Moderate (₹₹)', symbol: '₹₹', desc: 'Standard cafes, entry tickets, boutique hotels' },
  { id: 'luxury', label: 'Luxury (₹₹₹)', symbol: '₹₹₹', desc: 'Gourmet French mansions, luxury heritage resorts' }
];

export const DEFAULT_COORDINATES = {
  lat: 11.9338,
  lng: 79.8358, // Promenade Beach, Pondicherry
  zoom: 13
};
