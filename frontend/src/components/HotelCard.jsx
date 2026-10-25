import React from 'react';
import { Star, MapPin, IndianRupee, Wifi, Coffee, ExternalLink } from 'lucide-react';
import { AdvisoryBadge } from './AdvisoryBadge';

export function HotelCard({ hotel }) {
  return (
    <div className="group bg-white rounded-2xl border border-slate-200/90 hover:border-brand-400/80 shadow-xs hover:shadow-md transition-all duration-200 overflow-hidden flex flex-col justify-between">
      <div>
        {/* Hotel Image */}
        <div className="relative h-44 w-full overflow-hidden bg-slate-100">
          <img
            src={hotel.image_url}
            alt={hotel.name}
            loading="lazy"
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
          <div className="absolute top-3 left-3">
            <span className="text-[11px] font-bold tracking-wider uppercase px-2.5 py-0.5 rounded-full bg-white/90 backdrop-blur-xs text-brand-800 shadow-xs">
              {hotel.budget_tier}
            </span>
          </div>
          <div className="absolute bottom-3 right-3 bg-black/50 backdrop-blur-xs px-2 py-0.5 rounded text-white text-xs font-semibold flex items-center gap-1">
            <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
            {hotel.rating}
          </div>
        </div>

        {/* Hotel Details */}
        <div className="p-4 space-y-2">
          <h3 className="text-base font-bold text-slate-900 group-hover:text-brand-600 transition-colors line-clamp-1">
            {hotel.name}
          </h3>

          <p className="text-xs text-brand-700 font-medium flex items-center gap-1">
            <MapPin className="w-3.5 h-3.5 text-brand-500 shrink-0" />
            {hotel.proximity_tag || hotel.address}
          </p>

          <p className="text-xs text-slate-600 line-clamp-2 leading-relaxed">
            {hotel.description}
          </p>

          {/* Amenities Pills */}
          <div className="flex flex-wrap gap-1 pt-1">
            {hotel.amenities.slice(0, 3).map((amenity, idx) => (
              <span key={idx} className="text-[10px] px-2 py-0.5 bg-slate-100 text-slate-700 rounded-md font-medium">
                {amenity}
              </span>
            ))}
            {hotel.amenities.length > 3 && (
              <span className="text-[10px] px-1.5 py-0.5 bg-slate-50 text-slate-400 rounded-md">
                +{hotel.amenities.length - 3} more
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Hotel Price & CTA */}
      <div className="p-4 pt-0 border-t border-slate-100 mt-2 flex items-center justify-between">
        <div>
          <div className="text-[11px] text-slate-400">Starting from</div>
          <div className="text-base font-extrabold text-slate-900 flex items-center">
            <IndianRupee className="w-4 h-4 text-slate-700" />
            {hotel.price_per_night_inr.toLocaleString()}
            <span className="text-xs font-normal text-slate-400 ml-1">/ night</span>
          </div>
        </div>

        <button 
          onClick={() => alert(`Direct link to open partner bookings for ${hotel.name}`)}
          className="flex items-center gap-1 px-3.5 py-2 rounded-xl bg-slate-900 hover:bg-brand-600 text-white text-xs font-semibold transition-colors"
        >
          <span>View Rates</span>
          <ExternalLink className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}
