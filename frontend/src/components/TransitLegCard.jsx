import React from 'react';
import { Car, Footprints, AlertTriangle, ArrowRight, ShieldAlert } from 'lucide-react';

export function TransitLegCard({ leg, mode = 'driving', onToggleMode }) {
  if (!leg) return null;

  const isDriving = mode === 'driving';

  return (
    <div className="relative my-2 pl-4 pr-3 py-2.5 rounded-xl bg-slate-50 border border-slate-200/80 shadow-2xs hover:bg-slate-100/70 transition-all text-xs">
      {/* Vertical connector line indicator */}
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-slate-700">
          <div className="p-1 rounded-lg bg-white border border-slate-200 text-teal-700 shadow-2xs">
            {isDriving ? <Car className="w-3.5 h-3.5" /> : <Footprints className="w-3.5 h-3.5" />}
          </div>
          <div className="flex items-center gap-1.5 font-semibold text-slate-800">
            <span>{leg.distance_km} km</span>
            <span className="text-slate-400">•</span>
            <span>~{leg.duration_minutes} min travel</span>
            {leg.is_approximate && (
              <span className="text-[10px] text-slate-500 font-normal italic">
                (Approximate travel time)
              </span>
            )}
            <span className="text-[10px] text-slate-400 font-medium">
              • {leg.tier_used === 'haversine_detour' ? 'Haversine Detour' : 'OSRM'}
            </span>
          </div>
        </div>

        {/* Departure & Arrival Time Chips */}
        <div className="flex items-center gap-2">
          {leg.departure_time && leg.arrival_time && (
            <div className="hidden sm:flex items-center gap-1 px-2 py-0.5 rounded-md bg-white border border-slate-200 text-[11px] font-mono text-slate-600">
              <span>{leg.departure_time}</span>
              <ArrowRight className="w-2.5 h-2.5 text-slate-400" />
              <span>{leg.arrival_time}</span>
            </div>
          )}

          {/* Mode Switcher Toggle */}
          {onToggleMode && (
            <button
              onClick={onToggleMode}
              title={`Switch to ${isDriving ? 'Walking' : 'Driving'}`}
              className="px-2 py-1 rounded-lg bg-white border border-slate-200 hover:border-teal-400 text-slate-600 hover:text-teal-700 font-medium text-[11px] flex items-center gap-1 transition-all"
            >
              {isDriving ? (
                <>
                  <Footprints className="w-3 h-3" /> Walk
                </>
              ) : (
                <>
                  <Car className="w-3 h-3" /> Drive
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Festival Road Closure Alert */}
      {leg.closure_affected && (
        <div className="mt-2 p-2 rounded-lg bg-amber-50 border border-amber-300 text-amber-900 text-[11px] flex items-start gap-1.5 animate-fadeIn">
          <ShieldAlert className="w-3.5 h-3.5 text-amber-600 shrink-0 mt-0.5" />
          <div>
            <span className="font-bold">Procession Detour Notice:</span>{' '}
            {leg.closure_warning || 'Route intersects with active festival road closure.'}
          </div>
        </div>
      )}
    </div>
  );
}
