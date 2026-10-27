import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Compass, 
  MapPin, 
  Clock, 
  Sparkles, 
  ArrowRight,
  ShieldAlert,
  CheckCircle2
} from 'lucide-react';

const JOURNEY_DATA = {
  pondicherry: {
    title: 'A Day in Pondicherry: French Quarters & Bay Strolls',
    tagline: 'Quiet spiritual mornings, vintage cobblestone cafes, and seaside twilight.',
    stops: [
      {
        time: '8:30 AM – 9:30 AM',
        title: 'Sri Aurobindo Ashram',
        category: 'Spiritual Sanctuary',
        cost: 'Free Entry',
        description: 'Floral samadhi courtyard, library, and peaceful morning meditation in White Town.',
        decorum: 'Footwear off outside, modest dress code.'
      },
      {
        time: '12:30 PM – 2:30 PM',
        title: 'Cafe des Arts & French Quarter Heritage Walk',
        category: 'French Dining & Heritage',
        cost: 'Est. ₹450 / person',
        description: '19th-century courtyard cafe with fresh crepes followed by a stroll along Rue Dumas and mustard villas.',
        decorum: 'Casual, pedestrian-friendly walkways.'
      },
      {
        time: '5:00 PM – 7:00 PM',
        title: 'Promenade Beach (Rock Beach)',
        category: 'Scenic Coastal Walk',
        cost: 'Free Entry',
        description: 'Pedestrian-only seaside boulevard, Gandhi Statue, and cooling ocean breeze at sunset.',
        decorum: 'Vehicle-free after 5 PM.'
      }
    ]
  },
  chennai: {
    title: 'A Day in Chennai: Dravidian Heritage & Marina Coast',
    tagline: 'Ancient temple architecture, authentic filter kaapi, and the Coromandel shoreline.',
    stops: [
      {
        time: '8:30 AM – 10:00 AM',
        title: 'Kapaleeshwarar Temple (Mylapore)',
        category: '7th-Century Heritage',
        cost: 'Free Entry',
        description: 'Vibrant Dravidian gopuram carvings, sacred temple tank, and traditional morning chants.',
        decorum: 'Traditional or modest dress code required.'
      },
      {
        time: '12:30 PM – 2:00 PM',
        title: 'Murugan Idli Shop & Local Flavors',
        category: 'Traditional South Indian Dining',
        cost: 'Est. ₹250 / person',
        description: 'World-famous steaming ghee podi idlis, crispy vadas, and authentic Chennai filter kaapi.',
        decorum: 'Casual dining.'
      },
      {
        time: '5:00 PM – 7:30 PM',
        title: 'Marina Beach & Light House',
        category: 'Seaside Promenade',
        cost: 'Free Entry',
        description: 'One of the longest natural urban beaches in the world with evening sea breeze and panoramic lighthouse views.',
        decorum: 'Family-friendly evening gathering.'
      }
    ]
  }
};

export function InteractiveJourneyTimeline({ setActiveTab }) {
  const [selectedCity, setSelectedCity] = useState('pondicherry');
  const activeJourney = JOURNEY_DATA[selectedCity];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 space-y-8">
      {/* Header & City Tabs */}
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 border-b border-sandstone pb-6">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-sandstone-light text-brand-700 text-xs font-bold uppercase tracking-widest border border-sandstone">
            <Compass className="w-3.5 h-3.5 text-terracotta" />
            <span>Curated Trajectory Preview</span>
          </div>
          <h2 className="font-serif text-3xl sm:text-4xl font-bold text-brand-700">
            A Day in the Coast
          </h2>
          <p className="text-xs sm:text-sm text-slate-600 font-sans">
            Preview realistic single-day flows designed for proximity, heat pacing, and cultural etiquette.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex bg-sandstone-light p-1.5 rounded-2xl border border-sandstone self-start sm:self-auto">
          <button
            onClick={() => setSelectedCity('pondicherry')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              selectedCity === 'pondicherry'
                ? 'bg-brand-700 text-white shadow-xs'
                : 'text-slate-600 hover:text-brand-700'
            }`}
          >
            Pondicherry Trail
          </button>
          <button
            onClick={() => setSelectedCity('chennai')}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              selectedCity === 'chennai'
                ? 'bg-brand-700 text-white shadow-xs'
                : 'text-slate-600 hover:text-brand-700'
            }`}
          >
            Chennai Trail
          </button>
        </div>
      </div>

      {/* Content Area with Animation */}
      <AnimatePresence mode="wait">
        <motion.div
          key={selectedCity}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -12 }}
          transition={{ duration: 0.35, ease: 'easeOut' }}
          className="space-y-6"
        >
          <div className="space-y-1">
            <h3 className="text-lg font-bold text-slate-900">{activeJourney.title}</h3>
            <p className="text-xs text-slate-500">{activeJourney.tagline}</p>
          </div>

          {/* Timeline Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {activeJourney.stops.map((stop, idx) => (
              <div 
                key={stop.title}
                className="bg-white rounded-3xl p-6 border border-sandstone shadow-sm flex flex-col justify-between space-y-4 hover:border-terracotta/40 transition-colors"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-bold px-2.5 py-1 rounded-full bg-sandstone-light text-brand-700 border border-sandstone">
                      {stop.time}
                    </span>
                    <span className="text-[10px] font-semibold text-slate-400">
                      Stop 0{idx + 1}
                    </span>
                  </div>

                  <h4 className="text-base font-bold text-slate-900 leading-snug">
                    {stop.title}
                  </h4>

                  <p className="text-xs text-slate-600 leading-relaxed font-sans">
                    {stop.description}
                  </p>
                </div>

                <div className="pt-3 border-t border-sandstone/60 space-y-2 text-[11px]">
                  <div className="flex items-center justify-between font-bold text-slate-700">
                    <span className="text-brand-700 font-medium">{stop.category}</span>
                    <span>{stop.cost}</span>
                  </div>
                  <div className="text-[10px] text-slate-500 flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-terracotta" />
                    <span>{stop.decorum}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Bottom Callout */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-4 bg-sandstone-canvas rounded-2xl border border-sandstone text-xs text-slate-600 gap-3">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>All stops selected from verified catalog places with realistic transit buffers.</span>
            </div>
            <button
              onClick={() => setActiveTab('planner')}
              className="font-bold text-brand-700 hover:text-terracotta flex items-center gap-1.5 transition-colors shrink-0"
            >
              <span>Customize in Trip Planner</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </motion.div>
      </AnimatePresence>
    </div>
  );
}