import React, { createContext, useContext, useState } from 'react';

const PreferencesContext = createContext(null);

export function PreferencesProvider({ children }) {
  const [ageGroup, setAgeGroup] = useState('young_adult');
  const [dietaryPreference, setDietaryPreference] = useState('all');
  const [budgetTier, setBudgetTier] = useState('moderate');
  const [tripPlan, setTripPlan] = useState([]);
  const [favorites, setFavorites] = useState([]);

  const toggleFavorite = (id) => {
    setFavorites(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  };

  const addToTripPlan = (place) => {
    if (!tripPlan.find(p => p.id === place.id)) {
      setTripPlan(prev => [...prev, place]);
    }
  };

  const removeFromTripPlan = (id) => {
    setTripPlan(prev => prev.filter(p => p.id !== id));
  };

  return (
    <PreferencesContext.Provider value={{
      ageGroup,
      setAgeGroup,
      dietaryPreference,
      setDietaryPreference,
      budgetTier,
      setBudgetTier,
      tripPlan,
      addToTripPlan,
      removeFromTripPlan,
      favorites,
      toggleFavorite
    }}>
      {children}
    </PreferencesContext.Provider>
  );
}

export function usePreferences() {
  return useContext(PreferencesContext);
}
