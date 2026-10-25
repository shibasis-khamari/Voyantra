import React from 'react';
import { Star, MapPin, Clock, IndianRupee, Plus, Check, Heart, Eye, Sparkles } from 'lucide-react';
import { CrowdBadge } from './CrowdBadge';
import { AdvisoryBadge } from './AdvisoryBadge';
import { usePreferences } from '../context/PreferencesContext';

export function PlaceCard({ place, matchScore, matchReasons, onSelect }) {
  const { tripPlan, addToTripPlan, removeFromTripPlan, favorites, toggleFavorite } = usePreferences();

  const isPlanned = tripPlan.some(p => p.id === place.id);
  const isFav = favorites.includes(place.id);

  return (
    <div className="group bg-white rounded-2xl border border-sandstone hover:border-terracotta/50 shadow-2xs hover:shadow-md transition-all duration-300 flex flex-col justify-between relative">
      <div>
        {/* Card Image Banner */}
        <div className="relative h-52 w-full bg-sandstone-light rounded-t-3xl">
          <div className="overflow-hidden h-full w-full rounded-t-3xl">
            <img
              src={place.image_url}
              alt={place.name}
              loading="lazy"
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
            />
          </div>
          <div className="absolute inset-0 bg-gradient-to-t from-slate-950/70 via-slate-950/10 to-transparent pointer-events-none rounded-t-3xl" />

          {/* Top badges */}
          <div className="absolute top-3 left-3 right-3 flex items-center justify-between z-10">
            <span className="text-[10px] font-extrabold tracking-widest uppercase px-2.5 py-1 rounded-full bg-white/90 backdrop-blur-md text-brand-700 shadow-xs border border-sandstone/60">
              {place.category}
            </span>
            <button
              onClick={(e) => {
                e.stopPropagation();
                toggleFavorite(place.id);
              }}
              className="w-8 h-8 rounded-full bg-white/90 backdrop-blur-md flex items-center justify-center text-slate-600 hover:text-terracotta shadow-xs transition-colors border border-sandstone/60"
            >
              <Heart className={`w-4 h-4 ${isFav ? 'fill-terracotta text-terracotta' : ''}`} />
            </button>
          </div>

          {/* Bottom image metadata */}
          <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between text-white text-xs z-20">
            <CrowdBadge placeId={place.id} placeName={place.name} cityId={place.city_id || 'pondicherry'} tendency={place.crowd_tendency} />
            <span className="flex items-center gap-1 font-bold bg-slate-900/60 px-2.5 py-1 rounded-full backdrop-blur-md border border-white/10">
              <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
              {place.rating}
            </span>
          </div>
        </div>

        {/* Card Body */}
        <div className="p-5 space-y-3">
          {/* Match Score (in Planner mode) */}
          {matchScore !== undefined && (
            <div className="flex items-center justify-between py-1.5 px-3 rounded-xl bg-teal-500/10 border border-teal-500/20 text-xs">
              <span className="font-bold text-teal-900 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-teal-600" /> Personal Match
              </span>
              <span className="font-extrabold text-teal-700">{matchScore}%</span>
            </div>
          )}

          <div>
            <h3 
              onClick={onSelect}
              className="font-serif text-lg font-bold text-brand-700 group-hover:text-terracotta transition-colors cursor-pointer line-clamp-1 leading-snug"
            >
              {place.name}
            </h3>
            <p className="text-xs text-slate-500 flex items-center gap-1 mt-1 line-clamp-1">
              <MapPin className="w-3.5 h-3.5 text-terracotta shrink-0" />
              {place.address}
            </p>
          </div>

          <p className="text-xs text-slate-600 line-clamp-2 leading-relaxed font-sans">
            {place.description}
          </p>

          {/* Advisories & tags */}
          <AdvisoryBadge
            dressCode={place.dress_code_advisory}
            accessibilityRating={place.accessibility_rating}
            dietaryTag={place.dietary_options}
          />
        </div>
      </div>

      {/* Card Footer */}
      <div className="p-5 pt-0 border-t border-sandstone/50 mt-3 flex items-center justify-between gap-2 pt-3">
        <div className="text-xs">
          <div className="text-slate-400 font-semibold uppercase tracking-wider text-[10px]">Est. Budget</div>
          <div className="font-bold text-brand-700 flex items-center text-sm">
            <IndianRupee className="w-3.5 h-3.5 text-slate-600" />
            {place.estimated_cost_inr === 0 ? 'Free Entry' : place.estimated_cost_inr}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={onSelect}
            className="p-2 rounded-xl bg-sandstone-light hover:bg-sandstone text-slate-700 transition-colors border border-sandstone"
            title="View Details"
          >
            <Eye className="w-4 h-4" />
          </button>

          <button
            onClick={() => isPlanned ? removeFromTripPlan(place.id) : addToTripPlan(place)}
            className={`flex items-center gap-1.5 px-3.5 py-2 rounded-full text-xs font-bold transition-all shadow-xs ${
              isPlanned 
                ? 'bg-rose-50 text-rose-700 border border-rose-200 hover:bg-rose-100'
                : 'bg-brand-700 text-white hover:bg-terracotta shadow-brand-700/10'
            }`}
          >
            {isPlanned ? (
              <>
                <Check className="w-3.5 h-3.5" /> Added
              </>
            ) : (
              <>
                <Plus className="w-3.5 h-3.5" /> Add to Trip
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
