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
    <div className="relative overflow-hidden pt-28 pb-16 sm:pt-32 sm:pb-20 lg:pt-36 lg:pb-24 text-white">
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
        className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12"
      >
        {/* Top Badging & Editorial Headlines */}
        <div className="text-center max-w-3xl mx-auto space-y-6">
          {/* Animated Eyebrow Badge */}
          <motion.div variants={itemVariants} className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-slate-950/60 border border-white/20 shadow-lg backdrop-blur-md">
            <span className="w-2 h-2 rounded-full bg-terracotta animate-pulse" />
            <span className="text-[11px] font-bold text-amber-300 uppercase tracking-widest font-logo drop-shadow-xs">
              Coastal Tamil Nadu & Pondicherry • Intelligent Travel Planning
            </span>
          </motion.div>

          {/* Main Editorial Headline */}
          <motion.h1 
            variants={itemVariants}
            className="font-serif text-4xl sm:text-5xl lg:text-6xl font-bold text-white tracking-tight leading-[1.12] drop-shadow-[0_4px_16px_rgba(0,0,0,0.85)]"
          >
            Curated Journeys. Intelligent Pacing.{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-amber-300 via-terracotta-light to-amber-200">
              Unhurried Coastlines.
            </span>
          </motion.h1>

          {/* Subtext */}
          <motion.p 
            variants={itemVariants}
            className="text-sm sm:text-base text-slate-100 leading-relaxed font-sans max-w-2xl mx-auto drop-shadow-[0_2px_8px_rgba(0,0,0,0.85)] font-medium"
          >
            Experience personalized multi-day itineraries for Pondicherry and Chennai. Powered by local catalog grounding, real-time crowd advisories, and self-declared demographic and dietary preferences.
          </motion.p>

          {/* Action CTAs */}
          <motion.div variants={itemVariants} className="flex flex-wrap items-center justify-center gap-3 pt-2">
            <button
              onClick={() => setActiveTab('planner')}
              className="group flex items-center gap-2.5 px-6 py-3.5 rounded-2xl bg-terracotta hover:bg-terracotta/90 text-white text-xs sm:text-sm font-bold font-logo tracking-wide shadow-lg shadow-terracotta/30 hover:shadow-xl transition-all cursor-pointer"
            >
              <span>Open Trip Planner</span>
              <ArrowRight className="w-4 h-4 text-white group-hover:translate-x-1 transition-transform" />
            </button>

            <button
              onClick={scrollToCatalog}
              className="flex items-center gap-2 px-5 py-3.5 rounded-2xl bg-white/10 hover:bg-white/20 text-white border border-white/20 text-xs sm:text-sm font-bold font-logo tracking-wide transition-colors backdrop-blur-sm cursor-pointer"
            >
              <Compass className="w-4 h-4 text-amber-300" />
              <span>Browse Catalog Places</span>
            </button>
          </motion.div>
        </div>

        {/* Visual Centerpiece (Hero Showcase Deck) */}
        <motion.div 
          variants={itemVariants}
          className="relative max-w-4xl mx-auto"
        >
          {/* Deck Container */}
          <div className="bg-white/95 rounded-3xl p-6 sm:p-8 border border-sandstone/30 shadow-2xl backdrop-blur-md text-slate-900 space-y-6">
            
            {/* Header of Deck */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-sandstone gap-2">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-terracotta/10 text-terracotta flex items-center justify-center">
                  <Calendar className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-bold text-slate-900 flex items-center gap-2">
                    <span className="font-logo font-bold tracking-wide">Example Curated Day 1 Sequence (Self-Paced)</span>
                    <span className="px-2 py-0.5 rounded bg-sandstone text-[10px] text-slate-600 font-semibold font-logo tracking-wider">
                      Pondicherry
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-500">Sequenced by proximity and optimal sunlight hours</p>
                </div>
              </div>

              {/* Status pill */}
              <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 text-[11px] font-bold font-logo tracking-wide self-start sm:self-auto">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>Catalog Feasibility Verified</span>
              </div>
            </div>

            {/* Timeline Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              
              {/* Morning Slot */}
              <div className="bg-sandstone-canvas p-4 rounded-2xl border border-sandstone flex flex-col justify-between space-y-3">
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between text-[11px] font-bold">
                    <span className="text-amber-800 bg-amber-50 px-2 py-0.5 rounded border border-amber-200 font-logo font-semibold tracking-wider">Morning • 8:30 AM</span>
                    <span className="text-slate-400 font-logo text-[10px]">60 mins</span>
                  </div>
                  <h3 className="text-sm font-bold text-slate-900 font-serif">Sri Aurobindo Ashram</h3>
                  <p className="text-[11px] text-slate-600 leading-snug">
                    Quiet reflective courtyard & spiritual samadhi surrounded by seasonal floral tributes.
                  </p>
                </div>
                <div className="pt-2 border-t border-sandstone/60 flex items-center justify-between text-[10px] text-slate-500 font-medium font-logo">
                  <span>Entry: Free</span>
                  <span className="text-brand-700 font-bold tracking-wider">Modest Attire</span>
                </div>
              </div>

              {/* Afternoon Slot */}
              <div className="bg-sandstone-canvas p-4 rounded-2xl border border-sandstone flex flex-col justify-between space-y-3">
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between text-[11px] font-bold">
                    <span className="text-brand-800 bg-brand-50 px-2 py-0.5 rounded border border-brand-200 font-logo font-semibold tracking-wider">Afternoon • 12:30 PM</span>
                    <span className="text-slate-400 font-logo text-[10px]">120 mins</span>
                  </div>
                  <h3 className="text-sm font-bold text-slate-900 font-serif">White Town Heritage Walk</h3>
                  <p className="text-[11px] text-slate-600 leading-snug">
                    Mustard yellow colonial facades, bougainvillea streets, and artisanal French boutiques.
                  </p>
                </div>
                <div className="pt-2 border-t border-sandstone/60 flex items-center justify-between text-[10px] text-slate-500 font-medium font-logo">
                  <span>Walking Trail</span>
                  <span className="text-brand-700 font-bold tracking-wider">Self-Paced</span>
                </div>
              </div>

              {/* Evening Slot */}
              <div className="bg-sandstone-canvas p-4 rounded-2xl border border-sandstone flex flex-col justify-between space-y-3">
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between text-[11px] font-bold">
                    <span className="text-terracotta-dark bg-terracotta/10 px-2 py-0.5 rounded border border-terracotta/20 font-logo font-semibold tracking-wider">Evening • 5:00 PM</span>
                    <span className="text-slate-400 font-logo text-[10px]">90 mins</span>
                  </div>
                  <h3 className="text-sm font-bold text-slate-900 font-serif">Promenade Beach (Rock Beach)</h3>
                  <p className="text-[11px] text-slate-600 leading-snug">
                    Pedestrian-only oceanfront promenade along the Bay of Bengal at sunset.
                  </p>
                </div>
                <div className="pt-2 border-t border-sandstone/60 flex items-center justify-between text-[10px] text-slate-500 font-medium font-logo">
                  <span>Scenic Sea Walk</span>
                  <span className="text-brand-700 font-bold tracking-wider">Sunset Hours</span>
                </div>
              </div>

            </div>

            {/* Bottom Real-Time & Demographic Indicators */}
            <div className="pt-2 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs border-t border-sandstone/80">
              
              {/* Live Crowd Fetch with Phase 6 Source Attribution */}
              <div className="flex items-center gap-2 text-slate-700">
                <Users className="w-4 h-4 text-terracotta shrink-0" />
                {crowdLoading ? (
                  <span className="text-[11px] text-slate-500">Checking Promenade crowd estimate...</span>
                ) : crowdError || !crowdEstimate ? (
                  <span className="text-[11px] text-slate-500">Promenade Beach crowd model available on-demand</span>
                ) : (
                  <div className="flex flex-wrap items-center gap-1.5">
                    <span className="font-bold text-slate-900">
                      Promenade Crowd: {crowdEstimate.crowd_level || crowdEstimate.estimated_crowd || 'Moderate'}
                    </span>
                    <span className="text-[10px] text-slate-400 italic">
                      • {crowdEstimate.source_attribution || 'Source: 2014 survey data, rough prior'}
                    </span>
                  </div>
                )}
              </div>

              {/* Self-Declared Dietary Preferences Note */}
              <div className="text-[11px] text-slate-500 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                <span>Dietary filters (self-declared: Veg, Jain, Vegan, Halal) • Verify locally</span>
              </div>
            </div>

          </div>
        </motion.div>
      </motion.div>
    </div>
  );
}