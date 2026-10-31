import React, { createContext, useContext, useState, useEffect } from 'react';
import { LocationPromptModal } from '../components/LocationPromptModal';

const PreferencesContext = createContext(null);

// Coords: Pondicherry (11.9416, 79.8083), Chennai (13.0827, 80.2707)
function calculateDistanceKm(lat1, lon1, lat2, lon2) {
  const R = 6371; // Radius of earth in km
  const dLat = (lat2 - lat1) * (Math.PI / 180);
  const dLon = (lon2 - lon1) * (Math.PI / 180);
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * (Math.PI / 180)) * Math.cos(lat2 * (Math.PI / 180)) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

export function PreferencesProvider({ children }) {
  const [selectedCity, setSelectedCity] = useState(() => {
    return localStorage.getItem('voyantra_city') || 'all';
  });

  const [ageGroup, setAgeGroup] = useState(() => {
    return localStorage.getItem('voyantra_age_group') || 'young_adult';
  });

  const [dietaryPreference, setDietaryPreference] = useState(() => {
    return localStorage.getItem('voyantra_dietary') || 'all';
  });

  const [budgetTier, setBudgetTier] = useState(() => {
    return localStorage.getItem('voyantra_budget') || 'moderate';
  });

  const [tripPlan, setTripPlan] = useState(() => {
    try {
      const saved = localStorage.getItem('voyantra_trip_plan');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  const [favorites, setFavorites] = useState(() => {
    try {
      const saved = localStorage.getItem('voyantra_favorites');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  const [activeItinerary, setActiveItineraryState] = useState(() => {
    try {
      const saved = localStorage.getItem('voyantra_active_itinerary');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  const setActiveItinerary = (itin) => {
    setActiveItineraryState(itin);
    try {
      if (itin) {
        localStorage.setItem('voyantra_active_itinerary', JSON.stringify(itin));
      } else {
        localStorage.removeItem('voyantra_active_itinerary');
      }
    } catch (e) {
      console.warn('Failed to save active itinerary to localStorage', e);
    }
  };

  // Geolocation & Location Detection State
  const [locationNotice, setLocationNotice] = useState(null);
  const [isLocationModalOpen, setIsLocationModalOpen] = useState(false);
  const [locationStatus, setLocationStatus] = useState(null);

  const detectCurrentLocation = (manualTrigger = false) => {
    if (!navigator.geolocation) {
      if (manualTrigger) {
        setLocationStatus({
          title: 'Geolocation Notice',
          message: 'Your browser does not support GPS location detection. You can explore any destination worldwide or select a featured city.'
        });
        setIsLocationModalOpen(true);
      }
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        const distPondy = calculateDistanceKm(latitude, longitude, 11.9416, 79.8083);
        const distChennai = calculateDistanceKm(latitude, longitude, 13.0827, 80.2707);

        if (distPondy <= 70) {
          setLocationNotice(`📍 Detected GPS: Near Pondicherry (${Math.round(distPondy)} km)`);
        } else if (distChennai <= 70) {
          setLocationNotice(`📍 Detected GPS: Near Chennai (${Math.round(distChennai)} km)`);
        } else {
          setLocationNotice(`📍 Detected GPS: ${latitude.toFixed(2)}°, ${longitude.toFixed(2)}°`);
        }
      },
      (error) => {
        console.warn('Geolocation notice:', error);
      },
      { timeout: 8000, enableHighAccuracy: true }
    );
  };

  // Geolocation is intentionally accessed ONLY during explicit routing actions,
  // not on initial page visit.
  useEffect(() => {
    // No automatic GPS access on page load
  }, []);

  useEffect(() => {
    localStorage.setItem('voyantra_age_group', ageGroup);
  }, [ageGroup]);

  useEffect(() => {
    localStorage.setItem('voyantra_dietary', dietaryPreference);
  }, [dietaryPreference]);

  useEffect(() => {
    localStorage.setItem('voyantra_budget', budgetTier);
  }, [budgetTier]);

  useEffect(() => {
    localStorage.setItem('voyantra_trip_plan', JSON.stringify(tripPlan));
  }, [tripPlan]);

  useEffect(() => {
    localStorage.setItem('voyantra_favorites', JSON.stringify(favorites));
  }, [favorites]);

  useEffect(() => {
    localStorage.setItem('voyantra_city', selectedCity);
  }, [selectedCity]);

  const toggleFavorite = (placeId) => {
    setFavorites(prev => 
      prev.includes(placeId) ? prev.filter(id => id !== placeId) : [...prev, placeId]
    );
  };

  const addToTripPlan = (place) => {
    if (!tripPlan.find(item => item.id === place.id)) {
      setTripPlan(prev => [...prev, place]);
    }
  };

  const removeFromTripPlan = (placeId) => {
    setTripPlan(prev => prev.filter(item => item.id !== placeId));
  };

  const clearTripPlan = () => setTripPlan([]);

  const handleSelectCityManually = (city) => {
    setSelectedCity(city);
    localStorage.setItem('voyantra_city_prompted', 'true');
    setLocationNotice(`📍 Selected Destination: ${city === 'pondicherry' ? 'Pondicherry' : 'Chennai'}`);
  };

  return (
    <PreferencesContext.Provider value={{
      selectedCity,
      setSelectedCity,
      ageGroup,
      setAgeGroup,
      dietaryPreference,
      setDietaryPreference,
      budgetTier,
      setBudgetTier,
      tripPlan,
      addToTripPlan,
      removeFromTripPlan,
      clearTripPlan,
      favorites,
      toggleFavorite,
      activeItinerary,
      setActiveItinerary,
      detectCurrentLocation,
      locationNotice,
      isLocationModalOpen,
      setIsLocationModalOpen,
      locationStatus,
      handleSelectCityManually
    }}>
      {children}

      {/* Global Location Selection Modal */}
      <LocationPromptModal
        isOpen={isLocationModalOpen}
        onClose={() => setIsLocationModalOpen(false)}
        currentCity={selectedCity}
        onSelectCity={handleSelectCityManually}
        locationStatus={locationStatus}
      />
    </PreferencesContext.Provider>
  );
}

export function usePreferences() {
  const context = useContext(PreferencesContext);
  if (!context) {
    throw new Error('usePreferences must be used within a PreferencesProvider');
  }
  return context;
}
