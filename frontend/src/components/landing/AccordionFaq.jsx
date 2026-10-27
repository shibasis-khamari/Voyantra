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
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-16 space-y-8">
      {/* Header */}
      <div className="text-center space-y-3">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-sandstone-light text-brand-700 text-xs font-bold uppercase tracking-widest border border-sandstone">
          <HelpCircle className="w-3.5 h-3.5 text-terracotta" />
          <span>Frequently Asked Questions</span>
        </div>
        <h2 className="font-serif text-3xl sm:text-4xl font-bold text-brand-700">
          Clarity & Travel Guidelines
        </h2>
        <p className="text-xs sm:text-sm text-slate-600 font-sans">
          Everything you need to know about our catalog grounding, data sources, and system tiers.
        </p>
      </div>

      {/* Accordion List */}
      <div className="space-y-3">
        {FAQ_ITEMS.map((item, idx) => {
          const isOpen = openIndex === idx;

          return (
            <div 
              key={idx}
              className="bg-white rounded-2xl border border-sandstone shadow-2xs overflow-hidden transition-colors"
            >
              <button
                onClick={() => toggleItem(idx)}
                className="w-full px-6 py-4 text-left flex items-center justify-between gap-4 font-bold text-sm text-slate-900 hover:text-brand-700 transition-colors"
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
                    <div className="px-6 pb-5 pt-1 text-xs text-slate-600 leading-relaxed border-t border-sandstone/40 font-sans">
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
  );
}