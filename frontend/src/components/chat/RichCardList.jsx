import React from 'react';
import { MapPin, Hotel, Utensils, Star, Plus, ShieldCheck, IndianRupee, Clock } from 'lucide-react';

export function RichCardList({
  places = [],
  hotels = [],
  restaurants = [],
  onAddToBasket,
  onOpenDetails
}) {
  const hasItems = (places && places.length > 0) || (hotels && hotels.length > 0) || (restaurants && restaurants.length > 0);
  if (!hasItems) return null;

  return (
    <div className="w-full max-w-[95%] sm:max-w-[90%] space-y-3 pt-2">
      {/* Places Grid */}
      {places && places.length > 0 && (
        <div className="space-y-1.5">
          <div className="flex items-center gap-1.5 text-[11px] font-bold text-slate-700">
            <MapPin className="w-3.5 h-3.5 text-terracotta" />
            <span>Recommended Attractions</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {places.map((p) => (
              <div
                key={p.id}
                className="p-3 rounded-2xl bg-white/95 backdrop-blur-md border border-slate-200/90 shadow-xs flex flex-col justify-between gap-2 hover:border-[#FCD34D] transition-all"
              >
                <div>
                  <div className="flex items-center justify-between gap-1">
                    <span className="font-extrabold text-xs text-slate-900 line-clamp-1">{p.name}</span>
                    <span className="px-1.5 py-0.5 rounded text-[9px] font-bold uppercase bg-[#FCD34D]/25 text-slate-950 border border-[#FCD34D]/50">
                      {p.category}
                    </span>
                  </div>

                  <p className="text-[11px] text-slate-600 mt-1 line-clamp-2">
                    {p.highlights && p.highlights.length > 0 ? p.highlights.join(' • ') : p.address}
                  </p>

                  <div className="flex items-center gap-2 mt-1 text-[10px] text-slate-600">
                    <span>₹{p.estimated_cost_inr || 0}</span>
                    <span>•</span>
                    <span>{p.duration_minutes || 60} mins</span>
                    {p.rating && (
                      <>
                        <span>•</span>
                        <span className="flex items-center gap-0.5 text-amber-600 font-bold">
                          <Star className="w-2.5 h-2.5 fill-amber-400 text-amber-400" />
                          {p.rating}
                        </span>
                      </>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-1.5 pt-1 border-t border-slate-100">
                  {onOpenDetails && (
                    <button
                      type="button"
                      onClick={() => onOpenDetails(p)}
                      className="px-2.5 py-1 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-[10px] font-bold transition-colors cursor-pointer"
                    >
                      Details
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => onAddToBasket(p, 'place')}
                    className="flex-1 py-1 rounded-xl bg-[#FCD34D]/30 hover:bg-[#FCD34D] text-slate-950 text-[10px] font-extrabold border border-[#FCD34D]/50 transition-colors cursor-pointer flex items-center justify-center gap-1"
                  >
                    <Plus className="w-3 h-3" />
                    <span>Add to Basket</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Hotels Grid */}
      {hotels && hotels.length > 0 && (
        <div className="space-y-1.5 pt-1">
          <div className="flex items-center gap-1.5 text-[11px] font-bold text-slate-700">
            <Hotel className="w-3.5 h-3.5 text-indigo-600" />
            <span>Verified Accommodations</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {hotels.map((h) => (
              <div
                key={h.id}
                className="p-3 rounded-2xl bg-white/95 backdrop-blur-md border border-slate-200/90 shadow-xs flex flex-col justify-between gap-2 hover:border-indigo-400 transition-all"
              >
                <div>
                  <div className="flex items-center justify-between gap-1">
                    <span className="font-extrabold text-xs text-slate-900 line-clamp-1">{h.name}</span>
                    <span className="px-1.5 py-0.5 rounded text-[9px] font-bold uppercase bg-indigo-50 text-indigo-700 border border-indigo-200">
                      {h.budget_tier}
                    </span>
                  </div>

                  <div className="flex items-center gap-1.5 mt-1">
                    <span className="text-xs font-black text-slate-900">₹{h.price_per_night_inr}</span>
                    <span className="text-[10px] text-slate-500">/ night</span>
                    {h.rating && (
                      <span className="ml-auto flex items-center gap-0.5 text-[10px] font-bold text-amber-600">
                        <Star className="w-2.5 h-2.5 fill-amber-400 text-amber-400" />
                        {h.rating}
                      </span>
                    )}
                  </div>

                  {h.amenities && h.amenities.length > 0 && (
                    <p className="text-[10px] text-slate-600 mt-1 line-clamp-1">
                      {h.amenities.join(' • ')}
                    </p>
                  )}

                  {/* Grounded fact notice */}
                  <div className="mt-1 flex items-center gap-1 text-[9px] text-slate-500 bg-slate-50 p-1 rounded-lg">
                    <ShieldCheck className="w-3 h-3 text-emerald-600 shrink-0" />
                    <span className="line-clamp-1">{h.booking_notice || "Rates subject to direct property verification."}</span>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => onAddToBasket(h, 'hotel')}
                  className="w-full py-1 rounded-xl bg-indigo-50 hover:bg-indigo-600 hover:text-white text-indigo-700 text-[10px] font-extrabold border border-indigo-200 transition-all cursor-pointer flex items-center justify-center gap-1"
                >
                  <Plus className="w-3 h-3" />
                  <span>Add Hotel to Basket</span>
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Restaurants Grid */}
      {restaurants && restaurants.length > 0 && (
        <div className="space-y-1.5 pt-1">
          <div className="flex items-center gap-1.5 text-[11px] font-bold text-slate-700">
            <Utensils className="w-3.5 h-3.5 text-amber-700" />
            <span>Recommended Dining</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {restaurants.map((r) => (
              <div
                key={r.id}
                className="p-3 rounded-2xl bg-white/95 backdrop-blur-md border border-slate-200/90 shadow-xs flex flex-col justify-between gap-2 hover:border-amber-400 transition-all"
              >
                <div>
                  <div className="flex items-center justify-between gap-1">
                    <span className="font-extrabold text-xs text-slate-900 line-clamp-1">{r.name}</span>
                    <span className="px-1.5 py-0.5 rounded text-[9px] font-bold uppercase bg-amber-50 text-amber-800 border border-amber-200">
                      {r.category}
                    </span>
                  </div>

                  <div className="flex items-center gap-1.5 mt-1 text-[11px]">
                    <span className="font-bold text-slate-900">₹{r.estimated_cost_inr || 350}</span>
                    <span className="text-[10px] text-slate-500">• {r.budget_tier}</span>
                  </div>

                  {r.dietary_options && r.dietary_options.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1">
                      {r.dietary_options.map((opt, i) => (
                        <span key={i} className="text-[9px] px-1 rounded bg-slate-100 text-slate-600 font-semibold">
                          {opt}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                <button
                  type="button"
                  onClick={() => onAddToBasket(r, 'restaurant')}
                  className="w-full py-1 rounded-xl bg-amber-50 hover:bg-amber-500 hover:text-white text-amber-900 text-[10px] font-extrabold border border-amber-200 transition-all cursor-pointer flex items-center justify-center gap-1"
                >
                  <Plus className="w-3 h-3" />
                  <span>Add Restaurant to Basket</span>
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
