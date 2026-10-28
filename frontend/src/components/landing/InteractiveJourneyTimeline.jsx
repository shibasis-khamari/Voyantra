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
    <section className="relative overflow-hidden py-16 sm:py-20 text-white border-t border-sandstone">
      {/* Full Section Background Image: Sara Dubler Coastal Villa & Pool */}
      <div className="absolute inset-0 z-0">
        <img 
          src="/images/sara-dubler-Koei_7yYtIo-unsplash.jpg"
          alt="Coastal Villa and French Courtyard"
          className="w-full h-full object-cover object-center opacity-85 scale-105 contrast-105 saturate-110"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-slate-950/75 via-slate-950/40 to-slate-950/80" />
        <div className="absolute top-0 right-0 w-96 h-96 bg-brand-500/15 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-terracotta/15 rounded-full blur-3xl pointer-events-none" />
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
        {/* Header & City Tabs */}
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 border-b border-white/20 pb-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-950/60 border border-white/20 text-amber-300 text-xs font-bold font-sans uppercase tracking-[0.14em] backdrop-blur-md shadow-md">
              <Compass className="w-3.5 h-3.5" />
              <span>Curated Trajectory Preview</span>
            </div>
            <h2 className="font-serif text-4xl sm:text-5xl lg:text-[52px] font-normal text-white [text-shadow:0_2px_24px_rgba(0,0,0,.35)] leading-[1.08] tracking-[-0.01em]">
              A Day in the Coast
            </h2>
            <p className="text-sm sm:text-base text-slate-100 font-sans max-w-xl drop-shadow-[0_2px_8px_rgba(0,0,0,0.85)] font-medium leading-relaxed">
              Preview realistic single-day flows designed for proximity, heat pacing, and cultural etiquette.
            </p>
          </div>

          {/* Tab Switcher */}
          <div className="flex bg-slate-950/60 backdrop-blur-md p-1.5 rounded-2xl border border-white/20 self-start sm:self-auto shadow-md">
            <button
              onClick={() => setSelectedCity('pondicherry')}
              className={`px-4 py-2 rounded-xl text-xs font-bold font-logo tracking-wider transition-all cursor-pointer ${
                selectedCity === 'pondicherry'
                  ? 'bg-terracotta text-white shadow-md'
                  : 'text-slate-200 hover:text-white'
              }`}
            >
              Pondicherry Trail
            </button>
            <button
              onClick={() => setSelectedCity('chennai')}
              className={`px-4 py-2 rounded-xl text-xs font-bold font-logo tracking-wider transition-all cursor-pointer ${
                selectedCity === 'chennai'
                  ? 'bg-terracotta text-white shadow-md'
                  : 'text-slate-200 hover:text-white'
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
            className="space-y-8"
          >
            <div className="space-y-1">
              <h3 className="text-2xl sm:text-3xl font-serif font-normal text-white drop-shadow-[0_2px_8px_rgba(0,0,0,0.85)]">{activeJourney.title}</h3>
              <p className="text-xs sm:text-sm text-amber-200 drop-shadow-[0_1px_4px_rgba(0,0,0,0.85)] font-medium">{activeJourney.tagline}</p>
            </div>

            {/* Timeline Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {activeJourney.stops.map((stop, idx) => (
                <div 
                  key={stop.title}
                  className="bg-white/95 rounded-3xl p-6 border border-white/20 shadow-xl flex flex-col justify-between space-y-4 hover:border-amber-400/50 transition-all text-slate-900 backdrop-blur-md"
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] font-bold font-sans tracking-wider px-2.5 py-1 rounded-full bg-brand-50 text-brand-800 border border-brand-200 tabular-nums">
                        {stop.time}
                      </span>
                      <span className="text-[10px] font-bold font-sans tracking-wider text-slate-400 uppercase tabular-nums">
                        Stop 0{idx + 1}
                      </span>
                    </div>

                    <h4 className="text-[22px] font-serif font-normal text-slate-900 leading-snug">
                      {stop.title}
                    </h4>

                    <p className="text-xs text-slate-600 leading-relaxed font-sans">
                      {stop.description}
                    </p>
                  </div>

                  <div className="pt-3 border-t border-slate-200 space-y-2 text-[11px]">
                    <div className="flex items-center justify-between font-bold text-slate-700 font-sans text-xs">
                      <span className="text-brand-700 font-bold tracking-wide">{stop.category}</span>
                      <span className="text-emerald-700 font-extrabold tabular-nums">{stop.cost}</span>
                    </div>
                    <div className="text-[10px] text-slate-500 flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-terracotta shrink-0" />
                      <span>{stop.decorum}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Bottom Callout */}
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between p-4 bg-white/10 backdrop-blur-md rounded-2xl border border-white/15 text-xs text-slate-200 gap-3">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>All stops selected from verified catalog places with realistic transit buffers.</span>
              </div>
              <button
                onClick={() => setActiveTab('planner')}
                className="font-bold font-logo tracking-wider text-amber-300 hover:text-amber-200 flex items-center gap-1.5 transition-colors shrink-0 cursor-pointer"
              >
                <span>Customize in Trip Planner</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </motion.div>
        </AnimatePresence>
      </div>
    </section>
  );
}