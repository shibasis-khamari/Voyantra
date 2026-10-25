import React, { useState, useEffect } from 'react';
import { Calendar, AlertTriangle, MapPin, Info, ChevronRight } from 'lucide-react';
import { VoyantraAPI } from '../services/api';
import { FestivalCalendarModal } from './FestivalCalendarModal';

export function FestivalAdvisoryBanner({ selectedCity = 'pondicherry', showOnlyWhenActive = true }) {
  const [activeFestivals, setActiveFestivals] = useState([]);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    fetchActive();
  }, [selectedCity]);

  const fetchActive = async () => {
    try {
      const data = await VoyantraAPI.getActiveFestivals(selectedCity);
      setActiveFestivals(data || []);
    } catch (e) {
      setActiveFestivals([]);
    }
  };

  if (showOnlyWhenActive && activeFestivals.length === 0) {
    return null;
  }

  const cityNameFormatted = selectedCity.charAt(0).toUpperCase() + selectedCity.slice(1);

  return (
    <>
      <div className="bg-gradient-to-r from-amber-500/10 via-amber-500/5 to-transparent border border-amber-500/30 rounded-2xl p-4 transition-all">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div className="flex items-start gap-3">
            <div className="w-9 h-9 rounded-xl bg-amber-500/20 text-amber-900 flex items-center justify-center shrink-0 mt-0.5">
              <AlertTriangle className="w-5 h-5 text-amber-700" />
            </div>

            <div className="space-y-1">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="px-2 py-0.5 rounded-full bg-amber-200 text-amber-900 font-extrabold text-[10px] uppercase tracking-wider">
                  Phase 3: Festival Advisory
                </span>
                <h4 className="font-bold text-slate-900 text-xs sm:text-sm">
                  {activeFestivals.length > 0 
                    ? `Active Festival Advisory in ${cityNameFormatted} (${activeFestivals.length} Event)`
                    : `Local Festival & Traffic Advisory Calendar (${cityNameFormatted})`}
                </h4>
              </div>

              <p className="text-xs text-slate-600 leading-relaxed">
                {activeFestivals.length > 0
                  ? activeFestivals.map(f => `${f.name}: ${f.description}`).join(' | ')
                  : `Check road closures, temple processions, and high tourist footfall calendars for ${cityNameFormatted}.`}
              </p>

              {activeFestivals.length > 0 && activeFestivals[0].affected_areas && (
                <div className="flex items-center gap-1.5 text-[11px] font-bold text-amber-800 pt-0.5">
                  <MapPin className="w-3.5 h-3.5" />
                  <span>Affected Areas: {activeFestivals[0].affected_areas.join(', ')}</span>
                </div>
              )}
            </div>
          </div>

          <button
            onClick={() => setShowModal(true)}
            className="px-3.5 py-2 rounded-xl bg-amber-600 hover:bg-amber-700 text-white font-bold text-xs flex items-center justify-center gap-1.5 shadow-xs transition-all shrink-0 self-start md:self-center"
          >
            <Calendar className="w-4 h-4" />
            <span>View Full Festival Calendar</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {showModal && (
        <FestivalCalendarModal
          selectedCity={selectedCity}
          onClose={() => setShowModal(false)}
        />
      )}
    </>
  );
}
