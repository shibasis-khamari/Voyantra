import React, { useState } from 'react';
import { MapPin, Compass, Navigation, CheckCircle2, AlertCircle, Sparkles, X } from 'lucide-react';

export function LocationPromptModal({ isOpen, onClose, currentCity, onSelectCity, locationStatus }) {
  const [selected, setSelected] = useState(currentCity || 'pondicherry');

  if (!isOpen) return null;

  const handleConfirm = () => {
    onSelectCity(selected);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-fadeIn">
      <div className="bg-white rounded-3xl max-w-lg w-full p-6 sm:p-8 space-y-6 shadow-2xl border border-sandstone relative text-left">
        {onClose && (
          <button
            onClick={onClose}
            className="absolute top-5 right-5 p-2 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-all"
          >
            <X className="w-5 h-5" />
          </button>
        )}

        <div className="space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sandstone-light text-brand-700 text-xs font-bold font-sans uppercase tracking-[0.14em] border border-sandstone">
            <Compass className="w-3.5 h-3.5 text-terracotta" />
            Location Detection Advisory
          </div>
          
          <h2 className="font-serif text-2xl sm:text-3xl font-normal text-brand-700 leading-tight">
            Select Your Destination City
          </h2>

          <div className="p-3.5 rounded-2xl bg-amber-50 border border-amber-200 text-xs text-amber-900 leading-relaxed font-medium space-y-1">
            <div className="flex items-center gap-1.5 font-bold text-amber-950">
              <AlertCircle className="w-4 h-4 text-amber-600 shrink-0" />
              <span>{locationStatus?.title || 'Location Detection Notice'}</span>
            </div>
            <p className="text-[11px] text-amber-900/90">
              {locationStatus?.message || 'Voyantra offers worldwide travel concierge support, with featured local catalog guides for Pondicherry and Chennai. Select a featured city or ask about any destination in chat.'}
            </p>
          </div>
        </div>

        {/* City Selection Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {/* Pondicherry Card */}
          <button
            type="button"
            onClick={() => setSelected('pondicherry')}
            className={`p-5 rounded-2xl border text-left transition-all relative flex flex-col justify-between space-y-3 ${
              selected === 'pondicherry'
                ? 'bg-brand-50/70 border-brand-500 ring-2 ring-brand-500/20 text-brand-900 shadow-sm'
                : 'bg-white border-sandstone hover:border-brand-300 hover:bg-slate-50 text-slate-700'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-2xl">🏛️</span>
              {selected === 'pondicherry' && (
                <CheckCircle2 className="w-5 h-5 text-brand-600" />
              )}
            </div>
            <div>
              <h3 className="font-bold text-base text-slate-900">Pondicherry</h3>
              <p className="text-xs text-slate-500 mt-1 line-clamp-2 leading-relaxed">
                French Quarter heritage, Promenade beach, Auroville, & quiet cafes.
              </p>
            </div>
          </button>

          {/* Chennai Card */}
          <button
            type="button"
            onClick={() => setSelected('chennai')}
            className={`p-5 rounded-2xl border text-left transition-all relative flex flex-col justify-between space-y-3 ${
              selected === 'chennai'
                ? 'bg-brand-50/70 border-brand-500 ring-2 ring-brand-500/20 text-brand-900 shadow-sm'
                : 'bg-white border-sandstone hover:border-brand-300 hover:bg-slate-50 text-slate-700'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-2xl">🌴</span>
              {selected === 'chennai' && (
                <CheckCircle2 className="w-5 h-5 text-brand-600" />
              )}
            </div>
            <div>
              <h3 className="font-bold text-base text-slate-900">Chennai</h3>
              <p className="text-xs text-slate-500 mt-1 line-clamp-2 leading-relaxed">
                Marina Beach, Kapaleeshwarar Temple, Carnatic culture, & coastal seafood.
              </p>
            </div>
          </button>
        </div>

        {/* Action Button */}
        <div className="pt-2">
          <button
            onClick={handleConfirm}
            className="w-full py-3.5 rounded-2xl bg-brand-700 hover:bg-brand-800 text-white font-bold text-sm shadow-md transition-all flex items-center justify-center gap-2"
          >
            <MapPin className="w-4 h-4 text-terracotta" />
            <span>Proceed with {selected === 'pondicherry' ? 'Pondicherry' : 'Chennai'}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
