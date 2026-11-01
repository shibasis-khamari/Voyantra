import React, { useState, useEffect } from 'react';
import { RefreshCw, Sparkles, Compass } from 'lucide-react';

const STATUS_MESSAGES = [
  "Applying your latest preferences & budget...",
  "Recalculating authentic stops & transit routes...",
  "Verifying opening hours & accessibility...",
  "Balancing pacing for multi-day schedule...",
  "Polishing refreshed itinerary alternatives..."
];

export function ItineraryRefreshScreen({ isUpdating, customMessage }) {
  const [msgIndex, setMsgIndex] = useState(0);

  useEffect(() => {
    if (!isUpdating) {
      setMsgIndex(0);
      return;
    }

    const interval = setInterval(() => {
      setMsgIndex(prev => (prev + 1) % STATUS_MESSAGES.length);
    }, 1800);

    return () => clearInterval(interval);
  }, [isUpdating]);

  if (!isUpdating) return null;

  return (
    <div 
      className="absolute inset-0 z-40 bg-slate-900/40 backdrop-blur-md flex items-center justify-center p-4 transition-all duration-300 animate-fadeIn"
      role="status"
      aria-live="polite"
      aria-label="Updating itinerary"
    >
      <div className="relative max-w-xs sm:max-w-sm w-full bg-white/95 dark:bg-slate-900/95 backdrop-blur-xl border border-amber-300/80 dark:border-amber-400/40 rounded-3xl shadow-2xl p-6 sm:p-7 text-center space-y-4 transform transition-all animate-pulse-slow">
        
        {/* Animated Glow & Refresh Spinner Icon */}
        <div className="relative w-14 h-14 mx-auto flex items-center justify-center">
          <div className="absolute inset-0 rounded-full bg-amber-400/25 animate-ping" />
          <div className="relative w-12 h-12 rounded-2xl bg-gradient-to-tr from-amber-500 via-amber-400 to-[#FCD34D] p-0.5 shadow-md flex items-center justify-center">
            <div className="w-full h-full bg-slate-950 rounded-[14px] flex items-center justify-center">
              <RefreshCw className="w-6 h-6 text-[#FCD34D] animate-spin" />
            </div>
          </div>
        </div>

        {/* Refresh Headings */}
        <div className="space-y-1">
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-800 dark:text-amber-300 text-[10px] font-extrabold uppercase tracking-wider">
            <Sparkles className="w-3 h-3 text-amber-500" />
            <span>AI Itinerary Refresh</span>
          </div>
          <h3 className="text-base sm:text-lg font-black text-slate-900 dark:text-white tracking-tight">
            Updating Itinerary...
          </h3>
          <p className="text-xs text-slate-600 dark:text-slate-300 font-medium min-h-[34px] flex items-center justify-center transition-all duration-300 px-2 leading-relaxed">
            {customMessage || STATUS_MESSAGES[msgIndex]}
          </p>
        </div>

        {/* Indeterminate Shimmer Progress Bar */}
        <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-1.5 overflow-hidden relative">
          <div className="w-1/2 h-full bg-gradient-to-r from-amber-400 via-amber-500 to-orange-500 rounded-full animate-indeterminate" />
        </div>

        {/* Subtle Bottom Trust Cue */}
        <div className="flex items-center justify-center gap-1.5 text-[10px] font-bold text-slate-400 dark:text-slate-500">
          <Compass className="w-3 h-3 text-amber-500" />
          <span>Curating real places & verified routes</span>
        </div>
      </div>
    </div>
  );
}
