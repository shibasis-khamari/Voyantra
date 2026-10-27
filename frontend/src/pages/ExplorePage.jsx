import React, { useState, useEffect } from 'react';
import { FilterBar } from '../components/FilterBar';
import { PlaceCard } from '../components/PlaceCard';
import { PlaceModal } from '../components/PlaceModal';
import { FestivalAdvisoryBanner } from '../components/FestivalAdvisoryBanner';
import { VoyantraAPI } from '../services/api';
import { usePreferences } from '../context/PreferencesContext';
import { Sparkles, MapPin, Compass, ArrowUpDown } from 'lucide-react';

// Framer Landing Experience Components
import { FramerHero } from '../components/landing/FramerHero';
import { InfiniteMarquee } from '../components/landing/InfiniteMarquee';
import { BentoGridFeatures } from '../components/landing/BentoGridFeatures';
import { InteractiveJourneyTimeline } from '../components/landing/InteractiveJourneyTimeline';
import { AccordionFaq } from '../components/landing/AccordionFaq';
import { FramerCtaBanner } from '../components/landing/FramerCtaBanner';

export function ExplorePage({ setActiveTab }) {
  const { ageGroup, dietaryPreference, budgetTier, selectedCity } = usePreferences();

  const [places, setPlaces] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedBudget, setSelectedBudget] = useState('');
  const [selectedDietary, setSelectedDietary] = useState(dietaryPreference);
  const [selectedAgeGroup, setSelectedAgeGroup] = useState(ageGroup);
  const [activePlaceModal, setActivePlaceModal] = useState(null);
  const [sortBy, setSortBy] = useState('rating'); // rating, cost_asc, cost_desc

  const [backendError, setBackendError] = useState(null);

  useEffect(() => {
    loadPlaces();
  }, [selectedCategory, selectedBudget, selectedDietary, search, selectedAgeGroup, selectedCity]);

  const loadPlaces = async () => {
    setLoading(true);
    try {
      const data = await VoyantraAPI.getPlaces({
        city_id: selectedCity,
        category: selectedCategory,
        budget: selectedBudget,
        dietary: selectedDietary,
        search: search,
        age_group: selectedAgeGroup
      });
      setPlaces(data);
      setBackendError(null);
    } catch (e) {
      setBackendError(e.message);
      setPlaces([]);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setSearch('');
    setSelectedCategory('all');
    setSelectedBudget('');
    setSelectedDietary('all');
    setSelectedAgeGroup('young_adult');
  };

  // Sort places
  const sortedPlaces = [...places].sort((a, b) => {
    if (sortBy === 'rating') return b.rating - a.rating;
    if (sortBy === 'cost_asc') return a.estimated_cost_inr - b.estimated_cost_inr;
    if (sortBy === 'cost_desc') return b.estimated_cost_inr - a.estimated_cost_inr;
    return 0;
  });

  return (
    <div className="space-y-0">
      {/* 1. Framer-Inspired Editorial Hero - IMAGE BACKGROUND */}
      <FramerHero setActiveTab={setActiveTab} selectedCity={selectedCity} />

      {/* 2. Seamless Infinite Marquee of Real Catalog Places - WHITE DIVIDER */}
      <InfiniteMarquee />

      {/* 3. Asymmetric Bento Grid Features - WHITE BACKGROUND */}
      <BentoGridFeatures setActiveTab={setActiveTab} />

      {/* 4. Interactive Single-Day Timeline Switcher - IMAGE BACKGROUND */}
      <InteractiveJourneyTimeline setActiveTab={setActiveTab} />

      {/* 5. Destination Catalog & Interactive Filtering - WHITE BACKGROUND */}
      <section id="places-catalog" className="w-full bg-white py-16 border-t border-sandstone scroll-mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
          
          {/* Catalog Section Header on White Canvas */}
          <div className="bg-sandstone-canvas rounded-3xl p-6 sm:p-10 border border-sandstone shadow-xs space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sandstone-light border border-sandstone text-xs font-bold uppercase tracking-widest text-brand-700">
              <Compass className="w-3.5 h-3.5 text-terracotta" />
              Verified Local Catalog
            </div>
            <h2 className="font-serif text-3xl sm:text-4xl font-bold leading-tight text-slate-900">
              Curated Destination Repository
            </h2>
            <p className="text-xs sm:text-sm text-slate-600 leading-relaxed font-sans max-w-2xl">
              Filter through verified cultural landmarks, seaside promenades, and bohemian cafes with real-time crowd estimates and dietary indicators.
            </p>
          </div>

          {/* Phase 3 Festival & Road Closure Advisory Banner */}
          <FestivalAdvisoryBanner selectedCity={selectedCity} />

        {/* Backend Disconnected Notice */}
        {backendError && (
          <div className="p-5 rounded-2xl bg-rose-50 border-2 border-rose-300 text-rose-900 space-y-2 shadow-md animate-fadeIn">
            <div className="flex items-center gap-2 font-black text-rose-800 text-sm uppercase tracking-wider">
              <span className="px-2 py-0.5 rounded bg-rose-200 text-rose-900 font-extrabold text-[11px]">
                ⚠️ BACKEND DISCONNECTED
              </span>
            </div>
            <p className="text-xs text-rose-900 leading-relaxed font-medium">
              {backendError}
            </p>
            <div className="p-2.5 rounded-lg bg-rose-100/90 font-mono text-[11px] text-rose-950 font-bold">
              Start Server Command: cd E:\Voyantra\backend && python run.py
            </div>
          </div>
        )}

        {/* Filter Bar */}
        <FilterBar
          search={search}
          setSearch={setSearch}
          selectedCategory={selectedCategory}
          setSelectedCategory={setSelectedCategory}
          selectedBudget={selectedBudget}
          setSelectedBudget={setSelectedBudget}
          selectedDietary={selectedDietary}
          setSelectedDietary={setSelectedDietary}
          selectedAgeGroup={selectedAgeGroup}
          setSelectedAgeGroup={setSelectedAgeGroup}
          onReset={handleReset}
        />

        {/* Results Header & Sort */}
        <div className="flex items-center justify-between pt-2">
          <div className="text-sm text-slate-600 font-medium">
            Showing <span className="font-bold text-brand-700">{sortedPlaces.length}</span> curated destinations
          </div>
          <div className="flex items-center gap-2 text-xs">
            <ArrowUpDown className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-slate-500 font-medium">Sort by:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-2.5 py-1 rounded-lg border border-slate-200 bg-white font-semibold text-slate-700 outline-none cursor-pointer"
            >
              <option value="rating">Top Rated</option>
              <option value="cost_asc">Cost: Low to High</option>
              <option value="cost_desc">Cost: High to Low</option>
            </select>
          </div>
        </div>

        {/* Places Grid */}
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 animate-pulse">
            {[1, 2, 3, 4, 5, 6].map(i => (
              <div key={i} className="h-80 bg-slate-200 rounded-2xl"></div>
            ))}
          </div>
        ) : sortedPlaces.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {sortedPlaces.map(place => (
              <PlaceCard
                key={place.id}
                place={place}
                onSelect={() => setActivePlaceModal(place)}
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-16 bg-white rounded-3xl border border-slate-200 p-8 space-y-3">
            <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mx-auto text-slate-400">
              <Compass className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-800">No destinations match your filters</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Try adjusting your search keywords, clearing dietary filters, or resetting category options.
            </p>
            <button
              onClick={handleReset}
              className="px-4 py-2 rounded-xl bg-brand-600 text-white text-xs font-semibold hover:bg-brand-700 transition-colors"
            >
              Clear All Filters
            </button>
          </div>
        )}
        </div>
      </section>

      {/* 6. Clarity & Guidelines FAQ Accordion - IMAGE BACKGROUND */}
      <AccordionFaq />

      {/* 7. Bottom Action CTA Banner */}
      <FramerCtaBanner setActiveTab={setActiveTab} />

      {/* Place Details Modal */}
      {activePlaceModal && (
        <PlaceModal
          place={activePlaceModal}
          onClose={() => setActivePlaceModal(null)}
        />
      )}
    </div>
  );
}