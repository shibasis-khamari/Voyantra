import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, HelpCircle } from 'lucide-react';

const FAQ_ITEMS = [
  {
    q: 'How does Voyantra generate its personalized itineraries?',
    a: 'Voyantra connects to Google Gemini generative models while strictly constraining recommendations to our catalog of verified attractions, heritage sites, and dining venues in Pondicherry and Chennai. This prevents hallucinated locations or geographically impossible schedules.'
  },
  {
    q: 'What happens if the external AI service is unreachable?',
    a: "Voyantra's web client connects to our FastAPI backend. If the remote Gemini LLM is temporarily unreachable or rate-limited, the backend automatically engages an offline heuristic planner that builds a feasible day-by-day itinerary directly from the local MongoDB places repository."
  },
  {
    q: 'How are dietary and demographic preferences respected?',
    a: 'You can choose between Young Adult, Senior Traveler, or Family pacing, and apply dietary filters for Pure Vegetarian, Jain, Vegan, or Halal. Venues in our database are classified based on self-declared menus; we always advise travelers to reconfirm specific preparation requirements on-site.'
  },
  {
    q: 'Is Voyantra free to use?',
    a: 'Yes, Voyantra is built as an open-source, free-tier platform. Note that live conversational AI queries utilize Google Gemini free-tier quotas (subject to a rate limit of 10 requests per minute).'
  },
  {
    q: 'Which geographical areas are currently supported?',
    a: 'Voyantra is purpose-built and strictly scoped to Pondicherry (Puducherry) and Chennai, Tamil Nadu. We intentionally do not generate itineraries outside these regions to ensure depth, localized crowd heuristics, and accurate transit buffers.'
  }
];

export function AccordionFaq() {
  const [openIndex, setOpenIndex] = useState(0);

  const toggleItem = (idx) => {
    setOpenIndex(openIndex === idx ? null : idx);
  };

  return (
    <section className="relative overflow-hidden py-16 sm:py-20 text-white border-t border-sandstone">
      {/* Full Section Background Image: Destination Map with Pins */}
      <div className="absolute inset-0 z-0">
        <img 
          src="/images/z-TrhLCn1abMU-unsplash.jpg"
          alt="Verified Destination Map with Location Pins"
          className="w-full h-full object-cover object-center opacity-85 scale-105 contrast-105 saturate-110"
        />
        <div className="absolute inset-0 bg-gradient-to-b from-slate-950/75 via-slate-950/40 to-slate-950/80" />
        <div className="absolute top-0 right-0 w-80 h-80 bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />
      </div>

      <div className="relative z-10 max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        {/* Header */}
        <div className="text-center space-y-3">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-950/60 border border-white/20 text-amber-300 text-xs font-bold font-logo uppercase tracking-widest backdrop-blur-md shadow-md">
            <HelpCircle className="w-3.5 h-3.5 text-terracotta" />
            <span>Frequently Asked Questions</span>
          </div>
          <h2 className="font-serif text-3xl sm:text-4xl font-bold text-white drop-shadow-[0_4px_16px_rgba(0,0,0,0.85)]">
            Clarity & Travel Guidelines
          </h2>
          <p className="text-xs sm:text-sm text-slate-100 font-sans max-w-xl mx-auto drop-shadow-[0_2px_8px_rgba(0,0,0,0.85)] font-medium">
            Everything you need to know about our catalog grounding, data sources, and system tiers.
          </p>
        </div>

        {/* Accordion List with High-Contrast White Cards */}
        <div className="space-y-3">
          {FAQ_ITEMS.map((item, idx) => {
            const isOpen = openIndex === idx;

            return (
              <div 
                key={idx}
                className="bg-white/95 rounded-2xl border border-sandstone shadow-md overflow-hidden transition-all backdrop-blur-md"
              >
                <button
                  onClick={() => toggleItem(idx)}
                  className="w-full px-6 py-4 text-left flex items-center justify-between gap-4 font-bold font-logo tracking-wide text-sm sm:text-base text-slate-900 hover:text-brand-700 transition-colors cursor-pointer"
                >
                  <span>{item.q}</span>
                  <ChevronDown className={`w-4 h-4 text-slate-400 shrink-0 transition-transform duration-200 ${isOpen ? 'rotate-180 text-terracotta' : ''}`} />
                </button>

                <AnimatePresence initial={false}>
                  {isOpen && (
                    <motion.div
                      key="content"
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.25, ease: 'easeInOut' }}
                      className="overflow-hidden"
                    >
                      <div className="px-6 pb-5 pt-1 text-xs sm:text-sm text-slate-700 leading-relaxed border-t border-sandstone/60 font-sans">
                        {item.a}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}