import React from 'react';
import { X, MapPin, Clock, IndianRupee, Navigation, Check, ShieldCheck, Heart, Sparkles } from 'lucide-react';
import { CrowdBadge } from './CrowdBadge';
import { AdvisoryBadge } from './AdvisoryBadge';
import { usePreferences } from '../context/PreferencesContext';

export function PlaceModal({ place, matchInfo, onClose }) {
  const { tripPlan, addToTripPlan, removeFromTripPlan, favorites, toggleFavorite } = usePreferences();

  if (!place) return null;

  const isPlanned = tripPlan.some(p => p.id === place.id);
  const isFav = favorites.includes(place.id);

  // Deep-link to OSRM navigation (OpenStreetMap free routing)
  const osrmUrl = `https://www.openstreetmap.org/directions?engine=fossgis_osrm_car&route=%3B${place.coordinates.lat}%2C${place.coordinates.lng}`;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-fadeIn">
      <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl border border-slate-100 relative">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-10 w-9 h-9 rounded-full bg-slate-900/70 hover:bg-slate-900 text-white flex items-center justify-center transition-colors shadow-md"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Hero Image */}
        <div className="relative h-64 sm:h-72 w-full overflow-hidden bg-slate-100">
          <img
            src={place.image_url}
            alt={place.name}
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent flex flex-col justify-end p-6 text-white">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs uppercase font-bold tracking-wider px-2.5 py-0.5 rounded bg-brand-500 text-white">
                {place.category}
              </span>
              <CrowdBadge 
                placeId={place.id} 
                placeName={place.name} 
                cityId={place.city_id || 'pondicherry'} 
                tendency={place.crowd_tendency} 
                variant="overlay"
              />
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight">{place.name}</h2>
            <p className="text-sm text-slate-200 mt-1 flex items-center gap-1">
              <MapPin className="w-4 h-4 text-brand-400" />
              {place.address}
            </p>
          </div>
        </div>

        {/* Modal Content */}
        <div className="p-6 space-y-6">
          {/* Match Reasons Banner (if in personalized ranking) */}
          {matchInfo && (
            <div className="p-4 rounded-xl bg-gradient-to-r from-teal-50 to-emerald-50 border border-teal-200">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold uppercase tracking-wider text-teal-800 flex items-center gap-1.5">
                  <Sparkles className="w-4 h-4 text-teal-600" /> Personal Match Score
                </span>
                <span className="text-lg font-black text-teal-700 bg-white px-2.5 py-0.5 rounded-lg border border-teal-200 shadow-2xs">
                  {matchInfo.match_score}%
                </span>
              </div>
              <ul className="space-y-1">
                {matchInfo.match_reasons.map((reason, idx) => (
                  <li key={idx} className="text-xs text-teal-900 flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-teal-500"></span>
                    {reason}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Quick Metrics */}
          <div className="grid grid-cols-3 gap-3 p-3 bg-slate-50 rounded-xl border border-slate-200/60 text-center">
            <div>
              <div className="text-xs text-slate-500 font-medium">Estimated Cost</div>
              <div className="text-sm font-bold text-slate-800 flex items-center justify-center gap-0.5 mt-0.5">
                <IndianRupee className="w-3.5 h-3.5" />
                {place.estimated_cost_inr === 0 ? 'Free Entry' : `₹${place.estimated_cost_inr}`}
              </div>
            </div>
            <div>
              <div className="text-xs text-slate-500 font-medium">Duration</div>
              <div className="text-sm font-bold text-slate-800 flex items-center justify-center gap-1 mt-0.5">
                <Clock className="w-3.5 h-3.5 text-slate-500" />
                ~{place.duration_minutes} mins
              </div>
            </div>
            <div>
              <div className="text-xs text-slate-500 font-medium">Rating</div>
              <div className="text-sm font-bold text-amber-600 mt-0.5">
                ★ {place.rating} <span className="text-xs text-slate-400 font-normal">({place.review_count})</span>
              </div>
            </div>
          </div>

          {/* Description */}
          <div>
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider mb-2">About This Place</h3>
            <p className="text-sm text-slate-600 leading-relaxed">{place.description}</p>
          </div>

          {/* Key Highlights */}
          {place.highlights && place.highlights.length > 0 && (
            <div>
              <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider mb-2">Key Highlights</h3>
              <div className="space-y-1.5">
                {place.highlights.map((h, i) => (
                  <div key={i} className="flex items-start gap-2 text-xs sm:text-sm text-slate-700">
                    <ShieldCheck className="w-4 h-4 text-brand-600 shrink-0 mt-0.5" />
                    <span>{h}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Best Time & Advisories */}
          <div className="p-4 bg-slate-50 rounded-xl space-y-3 border border-slate-200/80">
            <div>
              <div className="text-xs font-bold text-slate-700">Best Time to Visit:</div>
              <div className="text-xs sm:text-sm text-slate-600 mt-0.5">{place.best_time_to_visit}</div>
            </div>

            {place.dress_code_advisory && (
              <div>
                <div className="text-xs font-bold text-purple-800">Dress Code & Etiquette:</div>
                <div className="text-xs text-purple-700 mt-0.5">{place.dress_code_advisory}</div>
              </div>
            )}

            <div>
              <div className="text-xs font-bold text-slate-700 mb-1.5">Accessibility & Dietary Tags:</div>
              <AdvisoryBadge 
                dressCode={place.dress_code_advisory}
                accessibilityRating={place.accessibility_rating}
                dietaryTag={place.dietary_options}
              />
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-3 pt-2">
            <button
              onClick={() => toggleFavorite(place.id)}
              className={`p-3 rounded-xl border transition-colors ${
                isFav ? 'bg-rose-50 border-rose-200 text-rose-600' : 'bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100'
              }`}
              title="Bookmark Place"
            >
              <Heart className={`w-5 h-5 ${isFav ? 'fill-rose-500' : ''}`} />
            </button>

            <a
              href={osrmUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 text-sm font-semibold transition-colors border border-slate-300"
            >
              <Navigation className="w-4 h-4 text-brand-600" />
              OSRM Directions
            </a>

            <button
              onClick={() => isPlanned ? removeFromTripPlan(place.id) : addToTripPlan(place)}
              className={`flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-xl text-sm font-semibold transition-colors shadow-sm ${
                isPlanned 
                  ? 'bg-rose-600 hover:bg-rose-700 text-white' 
                  : 'bg-brand-600 hover:bg-brand-700 text-white'
              }`}
            >
              {isPlanned ? (
                <>
                  <X className="w-4 h-4" /> Remove from Trip
                </>
              ) : (
                <>
                  <Check className="w-4 h-4" /> Add to Trip
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
