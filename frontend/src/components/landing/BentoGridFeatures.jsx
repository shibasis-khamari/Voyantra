import React from 'react';
import { motion } from 'framer-motion';
import { 
  Sparkles, 
  Users, 
  MapPin, 
  Compass, 
  Clock, 
  ShieldCheck, 
  Utensils, 
  Calendar, 
  Navigation,
  ArrowRight,
  Info
} from 'lucide-react';

export function BentoGridFeatures({ setActiveTab }) {
  return (
    <section className="w-full bg-white py-16 sm:py-20 border-t border-sandstone">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        {/* Section Header */}
        <div className="text-center max-w-2xl mx-auto space-y-3">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-sandstone-light text-brand-700 text-xs font-bold font-sans uppercase tracking-[0.14em] border border-sandstone">
            <Sparkles className="w-3.5 h-3.5 text-terracotta" />
            <span>Intelligent System Architecture</span>
          </div>
          <h2 className="font-serif text-4xl sm:text-5xl lg:text-[52px] font-normal text-brand-700 leading-[1.08] tracking-[-0.01em]">
            Engineered for Coastal Travel Realities
          </h2>
          <p className="text-sm sm:text-base text-slate-600 leading-relaxed font-sans font-medium">
            Voyantra blends generative travel concierges, catalog grounding, and demographic filtering into a cohesive planning platform.
          </p>
        </div>

        {/* Bento Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Card 1: Large Span 2 - Conversational AI Concierge */}
        <motion.div 
          whileHover={{ y: -4 }}
          transition={{ duration: 0.2 }}
          className="lg:col-span-2 bg-white rounded-3xl p-6 sm:p-8 border border-sandstone shadow-sm flex flex-col justify-between space-y-6 relative overflow-hidden"
        >
          <div className="space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <div className="w-9 h-9 rounded-xl bg-brand-700/10 text-brand-700 flex items-center justify-center">
                  <Sparkles className="w-5 h-5 text-terracotta" />
                </div>
                <h3 className="text-base sm:text-lg font-bold text-slate-900">
                  Conversational AI Travel Concierge
                </h3>
              </div>
              <span className="px-2.5 py-1 rounded-full bg-amber-50 border border-amber-200 text-amber-900 text-[10px] font-bold">
                Simulated Demo • Grounded in Real Catalog
              </span>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              Ask natural questions about sights, hotel stays, timings, and dietary dining worldwide with instant answers and verified local insights.
            </p>
          </div>

          {/* Interactive Chat Mockup */}
          <div className="bg-sandstone-canvas rounded-2xl p-4 sm:p-5 border border-sandstone space-y-3">
            {/* User message */}
            <div className="flex justify-end">
              <div className="bg-brand-700 text-white text-xs px-3.5 py-2 rounded-2xl rounded-tr-xs max-w-sm shadow-xs font-sans">
                "Where can I find a quiet French courtyard cafe near White Town with vegetarian breakfast?"
              </div>
            </div>

            {/* AI Assistant reply */}
            <div className="flex justify-start">
              <div className="bg-white text-slate-800 text-xs p-3.5 rounded-2xl rounded-tl-xs max-w-md border border-sandstone shadow-xs space-y-2">
                <div className="flex items-center gap-1.5 text-brand-700 font-bold text-[11px]">
                  <img 
                    src="/images/logo/voyantra-icon-nobg-crop.png" 
                    alt="Voyantra Logo" 
                    className="w-4 h-4 object-contain"
                  />
                  <span>Voyantra Concierge</span>
                </div>
                <p className="text-slate-600 leading-snug">
                  I recommend <strong className="text-slate-900">Cafe des Arts</strong> on Rue Suffren. It features a 19th-century French courtyard, fresh croissants, and vegetarian crepes. After breakfast, you can walk 3 minutes to the <strong className="text-slate-900">French Quarter Heritage Walk</strong>.
                </p>
                <div className="flex flex-wrap gap-1.5 pt-1">
                  <span className="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded border border-slate-200 tabular-nums">
                    Est. ₹450
                  </span>
                  <span className="text-[10px] bg-emerald-50 text-emerald-800 px-2 py-0.5 rounded border border-emerald-200">
                    Vegetarian options
                  </span>
                  <span className="text-[10px] bg-sandstone text-slate-700 px-2 py-0.5 rounded">
                    White Town
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="pt-2 flex items-center justify-between text-xs">
            <span className="text-[11px] text-slate-400">Powered by FastAPI & Google Gemini models</span>
            <button
              onClick={() => setActiveTab('planner')}
              className="text-brand-700 hover:text-terracotta font-bold text-xs flex items-center gap-1 group transition-colors"
            >
              <span>Try Live in Planner</span>
              <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
            </button>
          </div>
        </motion.div>

        {/* Card 2: Single Column - Crowd & Festival Intelligence */}
        <motion.div 
          whileHover={{ y: -4 }}
          transition={{ duration: 0.2 }}
          className="bg-white rounded-3xl p-6 sm:p-8 border border-sandstone shadow-sm flex flex-col justify-between space-y-6"
        >
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <div className="w-9 h-9 rounded-xl bg-terracotta/10 text-terracotta flex items-center justify-center">
                <Users className="w-5 h-5" />
              </div>
              <h3 className="text-base sm:text-lg font-bold text-slate-900">
                Crowd & Festival Intelligence
              </h3>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              Real-time crowd modeling and festival road closure alerts to prevent congested visits.
            </p>
          </div>

          {/* Density Bars Simulation */}
          <div className="bg-sandstone-canvas p-4 rounded-2xl border border-sandstone space-y-3">
            <div className="flex items-center justify-between text-xs">
              <span className="font-bold text-slate-800">Promenade Beach Density</span>
              <span className="text-emerald-700 font-bold text-[11px] bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                Optimal at 5 PM
              </span>
            </div>

            {/* Hourly bar breakdown */}
            <div className="grid grid-cols-4 gap-1.5 text-center pt-1">
              <div className="space-y-1">
                <div className="h-10 bg-emerald-200 rounded-md" />
                <span className="text-[10px] text-slate-500 font-bold">9 AM</span>
              </div>
              <div className="space-y-1">
                <div className="h-14 bg-amber-300 rounded-md" />
                <span className="text-[10px] text-slate-500 font-bold">1 PM</span>
              </div>
              <div className="space-y-1">
                <div className="h-20 bg-emerald-400 rounded-md" />
                <span className="text-[10px] text-slate-500 font-bold">5 PM</span>
              </div>
              <div className="space-y-1">
                <div className="h-24 bg-rose-400 rounded-md" />
                <span className="text-[10px] text-slate-500 font-bold">8 PM</span>
              </div>
            </div>
          </div>

          <div className="pt-1 text-[10px] text-slate-400 italic">
            Model Source: Heuristic calendar & historical survey priors
          </div>
        </motion.div>

        {/* Card 3: Single Column - Demographic & Dietary Filters */}
        <motion.div 
          whileHover={{ y: -4 }}
          transition={{ duration: 0.2 }}
          className="bg-white rounded-3xl p-6 sm:p-8 border border-sandstone shadow-sm flex flex-col justify-between space-y-6"
        >
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <div className="w-9 h-9 rounded-xl bg-emerald-700/10 text-emerald-700 flex items-center justify-center">
                <Utensils className="w-5 h-5" />
              </div>
              <h3 className="text-base sm:text-lg font-bold text-slate-900">
                Demographic & Dietary Customization
              </h3>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              Curate routes tailored to mobility pacing, senior visitors, and strict dietary preferences.
            </p>
          </div>

          {/* Visual Tag Cloud */}
          <div className="space-y-2">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Demographic Presets</span>
            <div className="flex flex-wrap gap-1.5">
              <span className="text-xs px-2.5 py-1 rounded-xl bg-sandstone-canvas border border-sandstone font-medium text-slate-700">
                Senior Traveler
              </span>
              <span className="text-xs px-2.5 py-1 rounded-xl bg-sandstone-canvas border border-sandstone font-medium text-slate-700">
                Young Adult
              </span>
              <span className="text-xs px-2.5 py-1 rounded-xl bg-sandstone-canvas border border-sandstone font-medium text-slate-700">
                Family & Kids
              </span>
            </div>

            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block pt-2">Dietary Offerings</span>
            <div className="flex flex-wrap gap-1.5">
              <span className="text-xs px-2.5 py-1 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 font-bold">
                Pure Vegetarian
              </span>
              <span className="text-xs px-2.5 py-1 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 font-bold">
                Jain (No Root Veg)
              </span>
              <span className="text-xs px-2.5 py-1 rounded-xl bg-teal-50 border border-teal-200 text-teal-900 font-bold">
                Vegan
              </span>
              <span className="text-xs px-2.5 py-1 rounded-xl bg-slate-50 border border-slate-200 text-slate-700 font-bold">
                Halal
              </span>
            </div>
          </div>

          <div className="text-[10px] text-slate-400 italic">
            Self-declared preferences; verify on-site with venue
          </div>
        </motion.div>

        {/* Card 4: Wide Span 2 - Route & Budget Sequencer */}
        <motion.div 
          whileHover={{ y: -4 }}
          transition={{ duration: 0.2 }}
          className="lg:col-span-2 bg-white rounded-3xl p-6 sm:p-8 border border-sandstone shadow-sm flex flex-col justify-between space-y-6"
        >
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <div className="w-9 h-9 rounded-xl bg-brand-700/10 text-brand-700 flex items-center justify-center">
                <Navigation className="w-5 h-5 text-terracotta" />
              </div>
              <h3 className="text-base sm:text-lg font-bold text-slate-900">
                Smart Route & Budget Sequencer
              </h3>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              Optimal daily order sequencer with real OpenStreetMap transit estimates and transparent INR budget calculations.
            </p>
          </div>

          {/* Sequencer Pipeline Mockup */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="p-3.5 bg-sandstone-canvas rounded-2xl border border-sandstone space-y-1">
              <span className="text-[10px] font-bold text-slate-400">Step 1</span>
              <div className="font-bold text-xs text-slate-900">Ashram Morning Visit</div>
              <div className="text-[11px] text-slate-500">Est. 15 mins walk to Cafe</div>
            </div>

            <div className="p-3.5 bg-sandstone-canvas rounded-2xl border border-sandstone space-y-1">
              <span className="text-[10px] font-bold text-slate-400">Step 2</span>
              <div className="font-bold text-xs text-slate-900">White Town Walk & Lunch</div>
              <div className="text-[11px] text-slate-500">Est. 8 mins auto-rickshaw</div>
            </div>

            <div className="p-3.5 bg-sandstone-canvas rounded-2xl border border-sandstone space-y-1">
              <span className="text-[10px] font-bold text-slate-400">Step 3</span>
              <div className="font-bold text-xs text-slate-900">Promenade Sunset Trail</div>
              <div className="text-[11px] text-slate-500">End of Day 1</div>
            </div>
          </div>

          <div className="pt-1 flex items-center justify-between text-xs text-slate-500 border-t border-sandstone/60">
            <span>Automated distance TSP ordering</span>
            <span className="font-bold text-slate-800 tabular-nums">Exact Budget Sum: ₹450 / traveler</span>
          </div>
        </motion.div>

        </div>
      </div>
    </section>
  );
}