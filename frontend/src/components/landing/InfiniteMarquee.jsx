import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { MapPin, Sparkles } from 'lucide-react';

const HIGHLIGHT_PLACES = [
  { name: 'White Town French Quarter', city: 'Pondicherry', category: 'Heritage' },
  { name: 'Promenade Beach (Rock Beach)', city: 'Pondicherry', category: 'Seaside' },
  { name: 'Auroville & Matrimandir', city: 'Pondicherry', category: 'Spiritual' },
  { name: 'Kapaleeshwarar Temple', city: 'Chennai', category: 'Heritage' },
  { name: 'Marina Beach & Lighthouse', city: 'Chennai', category: 'Seaside' },
  { name: 'Cafe des Arts Vintage Courtyard', city: 'Pondicherry', category: 'Culinary' },
  { name: 'Coromandel Cafe & French Villa', city: 'Pondicherry', category: 'Culinary' },
  { name: 'Fort St. George & Museum', city: 'Chennai', category: 'Historical' },
  { name: 'San Thome Basilica', city: 'Chennai', category: 'Heritage' },
  { name: 'Surguru Pure Vegetarian', city: 'Pondicherry', category: 'Dining' },
  { name: 'Paradise Beach & Backwaters', city: 'Pondicherry', category: 'Coastal' }
];

export function InfiniteMarquee() {
  const [isPaused, setIsPaused] = useState(false);

  // Duplicate items for continuous seamless loop
  const marqueeItems = [...HIGHLIGHT_PLACES, ...HIGHLIGHT_PLACES];

  return (
    <div className="w-full py-6 bg-white border-y border-sandstone overflow-hidden relative">
      {/* Edge gradient masks for smooth fade */}
      <div className="absolute left-0 top-0 bottom-0 w-16 sm:w-28 bg-gradient-to-r from-white to-transparent z-10 pointer-events-none" />
      <div className="absolute right-0 top-0 bottom-0 w-16 sm:w-28 bg-gradient-to-l from-white to-transparent z-10 pointer-events-none" />

      <div 
        className="flex"
        onMouseEnter={() => setIsPaused(true)}
        onMouseLeave={() => setIsPaused(false)}
      >
        <motion.div
          animate={{ x: isPaused ? undefined : ['0%', '-50%'] }}
          transition={{
            ease: 'linear',
            duration: 32,
            repeat: Infinity
          }}
          className="flex items-center gap-6 shrink-0"
        >
          {marqueeItems.map((item, index) => (
            <div
              key={`${item.name}-${index}`}
              className="flex items-center gap-3 px-4 py-2 rounded-2xl bg-sandstone-canvas border border-sandstone text-xs hover:border-terracotta/40 transition-colors shrink-0 shadow-2xs"
            >
              <div className="w-6 h-6 rounded-lg bg-brand-700/5 text-brand-700 flex items-center justify-center shrink-0">
                <MapPin className="w-3.5 h-3.5 text-terracotta" />
              </div>
              <div>
                <span className="font-bold text-slate-800">{item.name}</span>
                <div className="flex items-center gap-1.5 text-[10px] text-slate-400 mt-0.5">
                  <span>{item.city}</span>
                  <span>•</span>
                  <span className="text-brand-600 font-semibold">{item.category}</span>
                </div>
              </div>
            </div>
          ))}
        </motion.div>
      </div>
    </div>
  );
}