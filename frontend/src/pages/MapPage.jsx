import React, { useState, useEffect } from 'react';
import { MapView } from '../components/MapView';
import { PlaceModal } from '../components/PlaceModal';
import { VoyantraAPI } from '../services/api';
import { MapPin, Navigation, Eye, Compass, Layers } from 'lucide-react';
import { CrowdBadge } from '../components/CrowdBadge';
import { usePreferences } from '../context/PreferencesContext';

export function MapPage() {
  const { selectedCity } = usePreferences();
  const [places, setPlaces] = useState([]);
  const [selectedPlace, setSelectedPlace] = useState(null);
  const [activeModal, setActiveModal] = useState(null);

  const [backendError, setBackendError] = useState(null);

  useEffect(() => {
    VoyantraAPI.getPlaces({ city_id: selectedCity })
      .then(data => {
        setPlaces(data);
        if (data.length > 0) setSelectedPlace(data[0]);
        setBackendError(null);
      })
      .catch(e => {
        setBackendError(e.message);
        setPlaces([]);
      });
  }, [selectedCity]);

  const cityName = selectedCity === 'chennai' ? 'Chennai' : 'Pondicherry';

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Backend Disconnected Notice */}
      {backendError && (
        <div className="p-5 rounded-2xl bg-rose-50 border-2 border-rose-300 text-rose-900 space-y-2 shadow-md animate-fadeIn">
          <div className="flex items-center gap-2 font-black text-rose-800 text-sm uppercase tracking-wider">
            <span className="px-2 py-0.5 rounded bg-rose-200 text-rose-900 font-extrabold text-[11px]">
              ⚠️ BACKEND DISCONNECTED
            </span>
          </div>
          <p className="text-xs text-rose-900 leading-relaxed font-medium">
            {backendError}
          </p>
          <div className="p-2.5 rounded-lg bg-rose-100/90 font-mono text-[11px] text-rose-950 font-bold">
            Start Server Command: cd E:\Voyantra\backend && python run.py
          </div>
        </div>
      )}
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Interactive OpenStreetMap View
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Explore {places.length} {cityName} POIs on Leaflet with live OSRM routing triggers.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs font-semibold px-3 py-1.5 rounded-xl bg-teal-50 text-teal-800 border border-teal-200">
          <Navigation className="w-4 h-4 text-teal-600" />
          <span>Zero Paid Google Maps API Traps</span>
        </div>
      </div>

      {/* Map + Sidebar Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Main Map */}
        <div className="lg:col-span-2">
          <MapView
            places={places}
            selectedPlace={selectedPlace}
            onSelectPlace={(p) => setSelectedPlace(p)}
            height="620px"
          />
        </div>

        {/* Places Scroll List */}
        <div className="bg-white rounded-2xl p-4 border border-slate-200 shadow-xs space-y-3 h-[620px] flex flex-col">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-600">Points of Interest</span>
            <span className="text-xs text-brand-600 font-bold">{places.length} Total</span>
          </div>

          <div className="space-y-2 overflow-y-auto flex-1 pr-1">
            {places.map(p => {
              const isSelected = selectedPlace?.id === p.id;
              const osrmUrl = `https://www.openstreetmap.org/directions?engine=fossgis_osrm_car&route=%3B${p.coordinates.lat}%2C${p.coordinates.lng}`;
              return (
                <div
                  key={p.id}
                  onClick={() => setSelectedPlace(p)}
                  className={`p-3 rounded-xl border text-xs cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-brand-50 border-brand-500 ring-2 ring-brand-500/20'
                      : 'bg-slate-50 border-slate-200/80 hover:bg-slate-100'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="font-bold text-slate-900 line-clamp-1">{p.name}</div>
                    <CrowdBadge 
                      placeId={p.id} 
                      placeName={p.name} 
                      cityId={p.city_id || selectedCity} 
                      tendency={p.crowd_tendency} 
                    />
                  </div>
                  <div className="text-slate-500 mt-1 line-clamp-1 flex items-center gap-1">
                    <MapPin className="w-3 h-3 text-slate-400 shrink-0" />
                    {p.address}
                  </div>
                  
                  <div className="mt-2 pt-2 border-t border-slate-200/50 flex items-center justify-between">
                    <span className="text-[10px] uppercase font-bold text-brand-700 bg-brand-100/60 px-1.5 py-0.5 rounded">
                      {p.category}
                    </span>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setActiveModal(p);
                        }}
                        className="text-slate-500 hover:text-slate-800 p-1 font-semibold flex items-center gap-0.5"
                      >
                        <Eye className="w-3.5 h-3.5" /> Details
                      </button>
                      <a
                        href={osrmUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="text-teal-700 hover:text-teal-900 font-semibold p-1 flex items-center gap-0.5"
                      >
                        <Navigation className="w-3.5 h-3.5" /> OSRM
                      </a>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {activeModal && (
        <PlaceModal place={activeModal} onClose={() => setActiveModal(null)} />
      )}
    </div>
  );
}
