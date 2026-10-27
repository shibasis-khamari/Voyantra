import React from 'react';
import { motion } from 'framer-motion';
import { Sparkles, ArrowRight, Compass, ShieldCheck } from 'lucide-react';

export function FramerCtaBanner({ setActiveTab }) {
  const scrollToCatalog = () => {
    const el = document.getElementById('places-catalog');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="bg-gradient-to-br from-brand-900 via-slate-900 to-terracotta rounded-3xl p-8 sm:p-12 text-white shadow-xl relative overflow-hidden flex flex-col md:flex-row items-start md:items-center justify-between gap-8">
        
        {/* Ambient atmospheric lighting */}
        <div className="absolute top-0 right-0 w-80 h-80 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-80 h-80 bg-terracotta/20 rounded-full blur-3xl pointer-events-none" />

        <div className="space-y-4 max-w-2xl relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 border border-white/20 text-xs font-bold uppercase tracking-widest text-amber-300">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Ready to Explore?</span>
          </div>
          <h2 className="font-serif text-3xl sm:text-4xl font-bold leading-tight">
            Begin Planning Your Coastal Journey
          </h2>
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed font-sans">
            Craft a feasible, balanced day-by-day plan across Pondicherry and Chennai with intelligent route sequencing, transit estimates, and local dining highlights.
          </p>
          <div className="flex items-center gap-4 text-[11px] text-slate-400 pt-1">
            <span className="flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              Verified Catalog Venues
            </span>
            <span>•</span>
            <span>Free-tier & Open-Source</span>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 w-full md:w-auto relative z-10 shrink-0">
          <button
            onClick={() => setActiveTab('planner')}
            className="flex items-center justify-center gap-2 px-6 py-3.5 rounded-2xl bg-white hover:bg-sandstone-light text-slate-900 text-xs sm:text-sm font-bold shadow-md transition-all hover:shadow-lg"
          >
            <span>Launch Personalized Planner</span>
            <ArrowRight className="w-4 h-4 text-terracotta" />
          </button>
          
          <button
            onClick={scrollToCatalog}
            className="flex items-center justify-center gap-2 px-5 py-3.5 rounded-2xl bg-white/10 hover:bg-white/20 text-white border border-white/20 text-xs sm:text-sm font-bold transition-colors"
          >
            <Compass className="w-4 h-4 text-sandstone" />
            <span>Browse Places</span>
          </button>
        </div>

      </div>
    </div>
  );
}