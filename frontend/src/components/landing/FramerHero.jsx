import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Sparkles, 
  ArrowRight, 
  MapPin, 
  Clock, 
  Users, 
  ShieldCheck, 
  Compass, 
  Info,
  CheckCircle2,
  Calendar
} from 'lucide-react';
import { VoyantraAPI } from '../../services/api';

export function FramerHero({ setActiveTab, selectedCity = 'pondicherry' }) {
  const [crowdEstimate, setCrowdEstimate] = useState(null);
  const [crowdLoading, setCrowdLoading] = useState(true);
  const [crowdError, setCrowdError] = useState(false);

  useEffect(() => {
    let isMounted = true;
    async function fetchPromenadeCrowd() {
      try {
        setCrowdLoading(true);
        // Live crowd estimation call for Promenade Beach (pondy-01)
        const res = await VoyantraAPI.getPlaceCrowdEstimate('pondy-01', 'pondicherry');
        if (isMounted && res) {
          setCrowdEstimate(res);
        }
      } catch (err) {
        if (isMounted) setCrowdError(true);
      } finally {
        if (isMounted) setCrowdLoading(false);
      }
    }
    fetchPromenadeCrowd();
    return () => { isMounted = false; };
  }, []);

  const scrollToCatalog = () => {
    const el = document.getElementById('places-catalog');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.12,
        delayChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] }
    }
  };

  return (
    <div className="relative overflow-hidden min-h-[100dvh] lg:h-[100dvh] flex flex-col justify-center pt-24 pb-10 sm:pt-28 sm:pb-12 lg:pt-24 lg:pb-8 text-white">
      {/* Full Section Background Image: Luisa Linkous Coastal Horizon */}
      <div className="absolute inset-0 z-0">
        <img 
          src="/images/luisa-linkous-L03SoHMhbz8-unsplash.jpg"
          alt="Scenic Coastal Horizon of the Bay of Bengal"
          className="w-full h-full object-cover object-center opacity-85 scale-105 contrast-105 saturate-110"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-slate-950/75 via-slate-950/40 to-slate-950/80" />
        <div className="absolute top-0 right-0 w-96 h-96 bg-terracotta/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-brand-500/20 rounded-full blur-3xl pointer-events-none" />
      </div>

      <motion.div 
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-8 xl:gap-12 items-center my-auto"
      >
        {/* Left Column: Badging, Editorial Headline, Subtext & CTAs */}
        <div className="lg:col-span-5 xl:col-span-5 text-left space-y-4 sm:space-y-5">
          {/* Animated Eyebrow Badge */}
          <motion.div variants={itemVariants} className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-950/60 border border-white/20 shadow-lg backdrop-blur-md">
            <span className="w-2 h-2 rounded-full bg-terracotta animate-pulse" />
            <span className="text-[11px] font-bold text-amber-300 uppercase tracking-[0.14em] font-sans drop-shadow-xs">
              Coastal Tamil Nadu & Pondicherry • AI Travel Concierge
            </span>
          </motion.div>

          {/* Main Editorial Headline */}
          <motion.h1 
            variants={itemVariants}
            className="font-serif text-3xl sm:text-5xl lg:text-[40px] xl:text-[50px] 2xl:text-[56px] leading-[1.06] tracking-[-0.02em] text-white font-normal [text-shadow:0_2px_24px_rgba(0,0,0,.35)]"
          >
            Curated Journeys.<br />
            Intelligent Pacing.<br />
            <span className="italic bg-gradient-to-r from-amber-300 to-orange-500 bg-clip-text text-transparent">
              Unhurried Coastlines.
            </span>
          </motion.h1>

          {/* Subtext - Compact & High-Impact */}
          <motion.p 
            variants={itemVariants}
            className="text-xs sm:text-sm text-slate-100 font-sans font-medium leading-relaxed max-w-lg drop-shadow-[0_2px_8px_rgba(0,0,0,0.85)]"
          >
            Personalized multi-day itineraries for Pondicherry and Chennai. Grounded in verified sights, real-time crowd pacing, and dietary preferences.
          </motion.p>

          {/* Action CTAs */}
          <motion.div variants={itemVariants} className="flex flex-wrap items-center justify-start gap-3 pt-1">
            <button
              onClick={() => setActiveTab('planner')}
              className="group flex items-center gap-2 px-5 py-3 rounded-2xl bg-terracotta hover:bg-terracotta/90 text-white text-xs sm:text-sm font-bold font-sans tracking-wide shadow-lg shadow-terracotta/30 hover:shadow-xl transition-all cursor-pointer"
            >
              <span>Open Trip Planner</span>
              <ArrowRight className="w-4 h-4 text-white group-hover:translate-x-1 transition-transform" />
            </button>

            <button
              onClick={scrollToCatalog}
              className="flex items-center gap-2 px-4 py-3 rounded-2xl bg-white/10 hover:bg-white/20 text-white border border-white/20 text-xs sm:text-sm font-bold font-sans tracking-wide transition-colors backdrop-blur-sm cursor-pointer"
            >
              <Compass className="w-4 h-4 text-amber-300" />
              <span>Browse Catalog</span>
            </button>
          </motion.div>
        </div>

        {/* Right Column: Visual Centerpiece (Hero Showcase Deck - Glass Finish Itinerary Timeline) */}
        <motion.div 
          variants={itemVariants}
          className="lg:col-span-7 xl:col-span-7 relative w-full"
        >
          {/* Deck Container - Frosted Glass Finish */}
          <div className="bg-slate-950/60 backdrop-blur-xl rounded-3xl p-4 sm:p-5 lg:p-5 border border-white/20 shadow-[0_8px_32px_rgba(0,0,0,0.37)] text-white space-y-3">
            
            {/* Header of Deck */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-white/10 gap-2">
              <div className="flex items-center gap-2.5">
                <div className="w-7 h-7 rounded-lg bg-terracotta/20 border border-terracotta/30 text-terracotta-light flex items-center justify-center shrink-0">
                  <Calendar className="w-3.5 h-3.5" />
                </div>
                <div>
                  <div className="text-xs font-bold text-white flex items-center gap-1.5">
                    <span className="font-sans font-bold tracking-wide">Example Day 1 Itinerary</span>
                    <span className="px-1.5 py-0.5 rounded bg-white/10 border border-white/15 text-[10px] text-amber-300 font-semibold font-sans">
                      Pondicherry
                    </span>
                  </div>
                  <p className="text-[10px] text-slate-300">Sequenced by proximity & sunlight hours</p>
                </div>
              </div>

              {/* Status pill */}
              <div className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-emerald-500/15 border border-emerald-400/30 text-emerald-300 text-[10px] font-bold font-sans tracking-wide self-start sm:self-auto shrink-0 shadow-xs backdrop-blur-sm">
                <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                <span>Feasibility Verified</span>
              </div>
            </div>

            {/* Responsive Vertical Sequence Rows - Nested Frosted Glass Boxes */}
            <div className="space-y-2">
              
              {/* Stop 1: Morning Slot */}
              <div className="bg-white/[0.07] hover:bg-white/[0.14] backdrop-blur-md p-2.5 sm:p-3 rounded-2xl border border-white/15 hover:border-white/30 flex items-center justify-between gap-3 transition-all shadow-xs group">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-7 h-7 rounded-xl bg-amber-400/20 border border-amber-300/30 text-amber-300 font-sans font-bold text-xs flex items-center justify-center shrink-0 tabular-nums">
                    1
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-amber-200 bg-amber-400/15 px-1.5 py-0.5 rounded border border-amber-300/25 font-sans font-semibold text-[10px] tabular-nums">
                        8:30 AM • 60m
                      </span>
                      <span className="text-[10px] text-slate-300 font-medium hidden sm:inline">Morning Visit</span>
                    </div>
                    <h4 className="text-sm sm:text-base font-serif font-normal text-white leading-snug group-hover:text-amber-200 transition-colors">
                      Sri Aurobindo Ashram
                    </h4>
                    <p className="text-[11px] text-slate-300 line-clamp-1">
                      Reflective courtyard & spiritual samadhi surrounded by seasonal floral tributes.
                    </p>
                  </div>
                </div>
                <div className="shrink-0 flex flex-col items-end gap-1 text-[10px]">
                  <span className="px-2 py-0.5 rounded-full bg-brand-400/20 text-brand-200 border border-brand-300/30 font-semibold font-sans">
                    Modest Attire
                  </span>
                  <span className="text-slate-400">Entry: Free</span>
                </div>
              </div>

              {/* Stop 2: Afternoon Slot */}
              <div className="bg-white/[0.07] hover:bg-white/[0.14] backdrop-blur-md p-2.5 sm:p-3 rounded-2xl border border-white/15 hover:border-white/30 flex items-center justify-between gap-3 transition-all shadow-xs group">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-7 h-7 rounded-xl bg-brand-400/20 border border-brand-300/30 text-brand-300 font-sans font-bold text-xs flex items-center justify-center shrink-0 tabular-nums">
                    2
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-brand-200 bg-brand-400/15 px-1.5 py-0.5 rounded border border-brand-300/25 font-sans font-semibold text-[10px] tabular-nums">
                        12:30 PM • 120m
                      </span>
                      <span className="text-[10px] text-slate-300 font-medium hidden sm:inline">Heritage Walk</span>
                    </div>
                    <h4 className="text-sm sm:text-base font-serif font-normal text-white leading-snug group-hover:text-brand-200 transition-colors">
                      White Town French Quarter
                    </h4>
                    <p className="text-[11px] text-slate-300 line-clamp-1">
                      Mustard colonial facades, bougainvillea streets, and artisanal French cafes.
                    </p>
                  </div>
                </div>
                <div className="shrink-0 flex flex-col items-end gap-1 text-[10px]">
                  <span className="px-2 py-0.5 rounded-full bg-brand-400/20 text-brand-200 border border-brand-300/30 font-semibold font-sans">
                    Self-Paced
                  </span>
                  <span className="text-slate-400">Walking Trail</span>
                </div>
              </div>

              {/* Stop 3: Evening Slot */}
              <div className="bg-white/[0.07] hover:bg-white/[0.14] backdrop-blur-md p-2.5 sm:p-3 rounded-2xl border border-white/15 hover:border-white/30 flex items-center justify-between gap-3 transition-all shadow-xs group">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-7 h-7 rounded-xl bg-orange-400/20 border border-orange-300/30 text-orange-300 font-sans font-bold text-xs flex items-center justify-center shrink-0 tabular-nums">
                    3
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-orange-200 bg-orange-400/15 px-1.5 py-0.5 rounded border border-orange-300/25 font-sans font-semibold text-[10px] tabular-nums">
                        5:00 PM • 90m
                      </span>
                      <span className="text-[10px] text-slate-300 font-medium hidden sm:inline">Sunset Walk</span>
                    </div>
                    <h4 className="text-sm sm:text-base font-serif font-normal text-white leading-snug group-hover:text-orange-200 transition-colors">
                      Promenade Beach (Rock Beach)
                    </h4>
                    <p className="text-[11px] text-slate-300 line-clamp-1">
                      Pedestrian-only oceanfront seaside promenade along the Bay of Bengal.
                    </p>
                  </div>
                </div>
                <div className="shrink-0 flex flex-col items-end gap-1 text-[10px]">
                  <span className="px-2 py-0.5 rounded-full bg-brand-400/20 text-brand-200 border border-brand-300/30 font-semibold font-sans">
                    Sunset Hours
                  </span>
                  <span className="text-slate-400">Oceanfront</span>
                </div>
              </div>

            </div>

            {/* Bottom Real-Time & Demographic Indicators */}
            <div className="pt-2 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 text-xs border-t border-white/10">
              
              {/* Live Crowd Fetch with Attribution */}
              <div className="flex items-center gap-1.5 text-slate-200 min-w-0">
                <Users className="w-3.5 h-3.5 text-terracotta shrink-0" />
                {crowdLoading ? (
                  <span className="text-[10px] text-slate-400">Checking crowd estimate...</span>
                ) : crowdError || !crowdEstimate ? (
                  <span className="text-[10px] text-slate-400">Promenade crowd model on-demand</span>
                ) : (
                  <div className="flex items-center gap-1 text-[10px] truncate">
                    <span className="font-bold text-white">
                      Promenade Crowd: {crowdEstimate.crowd_level || crowdEstimate.estimated_crowd || 'Moderate'}
                    </span>
                    <span className="text-slate-400 italic hidden md:inline">
                      • {crowdEstimate.source_attribution || 'Source: 2014 survey prior'}
                    </span>
                  </div>
                )}
              </div>

              {/* Dietary Preferences Note */}
              <div className="text-[10px] text-slate-300 flex items-center gap-1.5 shrink-0">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                <span>Dietary filters (Veg, Jain, Vegan, Halal)</span>
              </div>
            </div>

          </div>
        </motion.div>
      </motion.div>
    </div>
  );
}