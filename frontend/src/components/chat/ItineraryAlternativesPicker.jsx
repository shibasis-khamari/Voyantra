import React from 'react';
import { Sparkles, Sun, Landmark, Compass, IndianRupee } from 'lucide-react';

export function ItineraryAlternativesPicker({
  alternatives = [],
  activeAlternativeId,
  onSelectAlternative
}) {
  if (!alternatives || alternatives.length === 0) return null;

  const getAlternativeIcon = (tag) => {
    switch (tag) {
      case 'relaxed':
        return <Sun className="w-3.5 h-3.5 text-amber-500" />;
      case 'cultural':
        return <Landmark className="w-3.5 h-3.5 text-indigo-500" />;
      case 'active':
        return <Compass className="w-3.5 h-3.5 text-emerald-500" />;
      default:
        return <Sparkles className="w-3.5 h-3.5 text-[#FCD34D]" />;
    }
  };

  return (
    <div className="flex flex-col gap-1.5 p-2 bg-slate-100 rounded-2xl border border-slate-200">
      <div className="flex items-center justify-between px-1">
        <span className="text-[10px] font-extrabold uppercase tracking-wider text-slate-500">
          Generated Alternatives (Choose Style)
        </span>
        <span className="text-[10px] text-slate-400">3 Curated Themes</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-1.5">
        {alternatives.map((alt) => {
          const isActive = alt.id === activeAlternativeId;
          return (
            <button
              key={alt.id}
              type="button"
              onClick={() => onSelectAlternative(alt.id)}
              className={`p-2 rounded-xl text-left transition-all border cursor-pointer flex flex-col justify-between ${
                isActive
                  ? 'bg-white border-[#FCD34D] shadow-sm ring-2 ring-[#FCD34D]/40'
                  : 'bg-white/60 hover:bg-white border-transparent hover:border-slate-300'
              }`}
            >
              <div className="flex items-center gap-1.5">
                {getAlternativeIcon(alt.tag)}
                <span className={`text-xs font-bold truncate ${isActive ? 'text-slate-900' : 'text-slate-700'}`}>
                  {alt.name}
                </span>
              </div>

              <p className="text-[10px] text-slate-500 line-clamp-1 mt-0.5">
                {alt.summary}
              </p>

              <div className="mt-1 flex items-center justify-between text-[10px] font-semibold text-slate-600">
                <span>{alt.days?.length || 1} Days</span>
                {alt.quality_score && (
                  <span className="text-[9px] font-bold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200">
                    {alt.quality_score}/100
                  </span>
                )}
                <span className="font-bold text-slate-900">₹{alt.total_estimated_budget_inr || 0}</span>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
