import React, { useState, useEffect } from 'react';
import { X, Calendar, MapPin, AlertCircle, ShieldAlert, Sparkles } from 'lucide-react';
import { VoyantraAPI } from '../services/api';

export function FestivalCalendarModal({ selectedCity = 'pondicherry', onClose }) {
  const [festivals, setFestivals] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadFestivals();
  }, [selectedCity]);

  const loadFestivals = async () => {
    setLoading(true);
    try {
      const data = await VoyantraAPI.getFestivals(selectedCity);
      setFestivals(data || []);
    } catch (e) {
      setFestivals([]);
    } finally {
      setLoading(false);
    }
  };

  const cityName = selectedCity.charAt(0).toUpperCase() + selectedCity.slice(1);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-fadeIn">
      <div className="bg-white rounded-3xl max-w-2xl w-full p-6 space-y-6 shadow-2xl border border-slate-200 max-h-[85vh] overflow-y-auto">
        <div className="flex items-center justify-between pb-4 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-amber-100 text-amber-800 flex items-center justify-center font-bold">
              <Calendar className="w-5 h-5 text-amber-700" />
            </div>
            <div>
              <h3 className="text-lg font-black text-slate-900">
                {cityName} Festival & Procession Advisory Calendar
              </h3>
              <p className="text-xs text-slate-500">
                Rule-based local festival schedule, affected zones, and traffic advisories
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-all"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {loading ? (
          <div className="text-center py-8 space-y-2">
            <div className="w-8 h-8 mx-auto border-4 border-amber-500 border-t-transparent rounded-full animate-spin"></div>
            <p className="text-xs text-slate-500 font-medium">Loading local festival records...</p>
          </div>
        ) : (
          <div className="space-y-4">
            {festivals.map((fest) => (
              <div 
                key={fest.id}
                className="p-4 rounded-2xl bg-slate-50 border border-slate-200 space-y-2 hover:border-amber-400 hover:bg-amber-50/30 transition-all"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="space-y-0.5">
                    <span className="px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-900 font-bold text-[10px] uppercase tracking-wider">
                      🗓️ {fest.month_day_start} to {fest.month_day_end}
                    </span>
                    <h4 className="font-bold text-slate-900 text-sm mt-1">{fest.name}</h4>
                  </div>
                  <span className="px-2 py-1 rounded-lg bg-rose-100 text-rose-900 text-[10px] font-extrabold flex items-center gap-1 border border-rose-200 shrink-0">
                    <ShieldAlert className="w-3 h-3 text-rose-600" />
                    {fest.advisory_level}
                  </span>
                </div>

                <p className="text-xs text-slate-600 leading-relaxed font-medium">
                  {fest.description}
                </p>

                {fest.affected_areas && fest.affected_areas.length > 0 && (
                  <div className="flex items-center gap-1.5 text-xs text-slate-700 font-semibold pt-1">
                    <MapPin className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                    <span>Affected Streets & Zones: {fest.affected_areas.join(', ')}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        <div className="p-3.5 rounded-xl bg-slate-100 text-slate-600 text-[11px] font-medium flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-amber-600 shrink-0" />
          <span>
            Voyantra's Phase 3 engine automatically audits these dates against your active travel itinerary.
          </span>
        </div>
      </div>
    </div>
  );
}
