import React from 'react';
import { Star, MapPin, IndianRupee, Plus, Check, Heart, Eye, Sparkles } from 'lucide-react';
import { CrowdBadge } from './CrowdBadge';
import { AdvisoryBadge } from './AdvisoryBadge';
import { usePreferences } from '../context/PreferencesContext';

const LOCAL_DESTINATION_IMAGES = [
  '/images/maniraj-i3FLO6Nthw4-unsplash.jpg',
  '/images/rohit-durbha-3GpBMD609o4-unsplash.jpg',
  '/images/llxvisuals--E7dpukTajA-unsplash.jpg',
  '/images/sara-dubler-Koei_7yYtIo-unsplash.jpg',
  '/images/luisa-linkous-L03SoHMhbz8-unsplash.jpg',
  '/images/z-TrhLCn1abMU-unsplash.jpg'
];

export function PlaceCard({ place, matchScore, matchReasons, onSelect }) {
  const { tripPlan, addToTripPlan, removeFromTripPlan, favorites, toggleFavorite } = usePreferences();

  const isPlanned = tripPlan.some(p => p.id === place.id);
  const isFav = favorites.includes(place.id);
  const imageIndex = place.id ? [...place.id].reduce((sum, char) => sum + char.charCodeAt(0), 0) % LOCAL_DESTINATION_IMAGES.length : 0;
  const imageSrc = place.image_url || '/images/luisa-linkous-L03SoHMhbz8-unsplash.jpg';

  return (
    <article className="group bg-white rounded-3xl border border-slate-200/80 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 flex flex-col overflow-hidden">
      <div className="relative h-56 overflow-hidden bg-slate-100">
        <img src={imageSrc} alt={place.name} loading="lazy" className="w-full h-full object-cover group-hover:scale-[1.03] transition-transform duration-500" />
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950/70 via-transparent to-slate-950/10" />
        <div className="absolute top-4 left-4 right-4 flex items-start justify-between gap-3">
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-[10px] font-bold uppercase px-2.5 py-1 rounded-full bg-slate-950/80 text-white backdrop-blur-md shadow-sm flex items-center gap-1">
              <MapPin className="w-3 h-3 text-amber-300" />
              {place.city_id === 'chennai' ? 'Chennai' : 'Pondicherry'}
            </span>
            <span className="max-w-[120px] truncate text-[10px] font-bold tracking-[0.12em] uppercase px-2.5 py-1 rounded-full bg-white/95 text-brand-700 shadow-sm">
              {place.category}
            </span>
          </div>
          <button
            aria-label={isFav ? 'Remove from favourites' : 'Add to favourites'}
            onClick={(e) => { e.stopPropagation(); toggleFavorite(place.id); }}
            className="w-9 h-9 shrink-0 rounded-full bg-white/95 flex items-center justify-center text-slate-600 hover:text-terracotta shadow-sm"
          >
            <Heart className={`w-4 h-4 ${isFav ? 'fill-terracotta text-terracotta' : ''}`} />
          </button>
        </div>
        <div className="absolute bottom-4 left-4 right-4 flex items-center justify-between gap-2 text-white text-xs">
          <CrowdBadge placeId={place.id} placeName={place.name} cityId={place.city_id || 'pondicherry'} tendency={place.crowd_tendency} variant="overlay" />
          <span className="flex items-center gap-1 font-bold bg-slate-950/80 px-2.5 py-1.5 rounded-full">
            <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
            {place.rating}
          </span>
        </div>
      </div>

      <div className="flex flex-col flex-1 p-5">
        {matchScore !== undefined && (
          <div className="flex items-center justify-between mb-3 py-2 px-3 rounded-xl bg-teal-50 border border-teal-100 text-xs">
            <span class="font-bold text-teal-900 flex items-center gap-1.5"><Sparkles className="w-3.5 h-3.5" />Personal match</span>
            <span className="font-extrabold text-teal-700">{matchScore}%</span>
          </div>
        )}
        <button onClick={onSelect} className="text-left">
          <h3 className="font-serif text-[24px] text-brand-700 leading-tight group-hover:text-terracotta transition-colors">{place.name}</h3>
        </button>
        <p className="mt-1.5 text-xs text-slate-500 flex items-start gap-1.5">
          <MapPin className="w-3.5 h-3.5 mt-0.5 text-terracotta shrink-0" />
          <span className="line-clamp-1">{place.address}</span>
        </p>
        <p className="mt-3 text-sm text-slate-600 leading-relaxed line-clamp-2">{place.description}</p>
        <div className="mt-4"><AdvisoryBadge dressCode={place.dress_code_advisory} accessibilityRating={place.accessibility_rating} dietaryTag={place.dietary_options} /></div>

        <div className="mt-auto pt-5">
          <div className="flex items-center justify-between gap-3 border-t border-slate-100 pt-4">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Budget</div>
              <div className="mt-0.5 font-bold text-brand-700 flex items-center text-sm">
                <IndianRupee className="w-3.5 h-3.5" />
                {place.estimated_cost_inr === 0 ? 'Free entry' : place.estimated_cost_inr}
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <button aria-label="View details" onClick={onSelect} className="w-10 h-10 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 flex items-center justify-center">
                <Eye className="w-4 h-4" />
              </button>
              <button
                onClick={() => isPlanned ? removeFromTripPlan(place.id) : addToTripPlan(place)}
                className={`h-10 flex items-center justify-center gap-1.5 px-4 rounded-xl text-xs font-bold transition-all whitespace-nowrap ${isPlanned ? 'bg-rose-50 text-rose-700 border border-rose-200' : 'bg-brand-700 text-white hover:bg-brand-800'}`}
              >
                {isPlanned ? <><Check className="w-4 h-4" />Added</> : <><Plus className="w-4 h-4" />Add to trip</>}
              </button>
            </div>
          </div>
        </div>
      </div>
    </article>
  );
}
