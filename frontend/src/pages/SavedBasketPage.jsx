import React, { useState } from 'react';
import { 
  Luggage, IndianRupee, Clock, Trash2, MapPin, Compass, Sparkles, 
  ArrowRight, CheckCircle2, AlertCircle, Share2, Eye
} from 'lucide-react';
import { usePreferences } from '../context/PreferencesContext';
import { PlaceModal } from '../components/PlaceModal';

export function SavedBasketPage({ setActiveTab }) {
  const { 
    tripPlan, 
    removeFromTripPlan, 
    clearTripPlan, 
    setActiveItinerary 
  } = usePreferences();

  const [activeModalPlace, setActiveModalPlace] = useState(null);
  const [showClearConfirm, setShowClearConfirm] = useState(false);

  // Calculate Basket Totals
  const totalCost = tripPlan.reduce((acc, item) => acc + (item.estimated_cost_inr || 0), 0);
  const totalMinutes = tripPlan.reduce((acc, item) => acc + (item.duration_minutes || 0), 0);
  const totalHours = (totalMinutes / 60).toFixed(1);

  // City Breakdown
  const pondyCount = tripPlan.filter(p => !p.city_id || p.city_id === 'pondicherry').length;
  const chennaiCount = tripPlan.filter(p => p.city_id === 'chennai').length;

  const handleRouteOnMap = () => {
    // Package basket items into an active itinerary format for map routing
    if (tripPlan.length > 0) {
      const generatedDays = [{
        day_number: 1,
        theme: "Personalized Saved Basket Route",
        morning: tripPlan[0] ? { place_name: tripPlan[0].name, activity_note: tripPlan[0].description, est_time: "Morning" } : null,
        afternoon: tripPlan[1] ? { place_name: tripPlan[1].name, activity_note: tripPlan[1].description, est_time: "Afternoon" } : null,
        evening: tripPlan[2] ? { place_name: tripPlan[2].name, activity_note: tripPlan[2].description, est_time: "Evening" } : null
      }];

      // Add additional slots for subsequent items
      tripPlan.slice(3).forEach((item, idx) => {
        generatedDays[0][`custom_${idx + 1}`] = {
          place_name: item.name,
          activity_note: item.description,
          est_time: "Flexible Time"
        };
      });

      setActiveItinerary({
        itinerary_title: "Saved Basket Custom Tour",
        summary: `Custom personalized tour with ${tripPlan.length} destinations selected across Pondicherry & Chennai.`,
        days: generatedDays,
        total_estimated_budget_inr: totalCost,
        city_id: chennaiCount > pondyCount ? 'chennai' : 'pondicherry'
      });
    }

    if (setActiveTab) {
      setActiveTab('map');
    }
  };

  return (
    <div className="relative min-h-screen">
      {/* Background Image Layer */}
      <div 
        className="fixed inset-0 z-0 overflow-hidden pointer-events-none select-none"
        aria-hidden="true"
      >
        <img
          src="/images/luisa-linkous-L03SoHMhbz8-unsplash.jpg"
          alt="Scenic Coastal Horizon"
          className="w-full h-full object-cover object-center fixed scale-105 filter brightness-[0.98] contrast-[1.04] saturate-[1.12]"
        />
        <div className="absolute inset-0 bg-slate-950/30" />
        <div className="absolute inset-0 bg-gradient-to-b from-slate-950/40 via-transparent to-slate-950/50" />
      </div>

      {/* Main Content */}
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        
        {/* Page Header */}
        <div className="rounded-3xl bg-white/75 backdrop-blur-xl border border-white/60 p-6 sm:p-8 shadow-2xl flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#FCD34D]/25 border border-[#FCD34D]/50 text-slate-950 text-xs font-bold font-sans">
              <Luggage className="w-3.5 h-3.5 text-amber-800" />
              <span>Trip Storage & Itinerary Basket</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight font-sans">
              Saved Trip Basket
            </h1>
            <p className="text-xs sm:text-sm text-slate-600 max-w-2xl font-sans leading-relaxed">
              Curate, review, and coordinate your dream destinations across Pondicherry and Chennai in one convenient basket.
            </p>
          </div>

          {/* Quick Actions */}
          <div className="flex flex-wrap items-center gap-3">
            {tripPlan.length > 0 && (
              <>
                <button
                  onClick={handleRouteOnMap}
                  className="px-5 py-2.5 rounded-2xl bg-slate-950 hover:bg-slate-900 text-white font-bold text-xs sm:text-sm font-sans shadow-lg flex items-center gap-2 transition-all cursor-pointer"
                >
                  <Compass className="w-4 h-4 text-amber-300" />
                  <span>Route on Map</span>
                </button>

                <button
                  onClick={() => setShowClearConfirm(true)}
                  className="px-4 py-2.5 rounded-2xl bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 font-bold text-xs font-sans transition-all cursor-pointer flex items-center gap-1.5"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>Clear All</span>
                </button>
              </>
            )}

            <button
              onClick={() => setActiveTab('explore')}
              className="px-4 py-2.5 rounded-2xl bg-white/80 hover:bg-white text-slate-800 border border-slate-200 font-bold text-xs font-sans transition-all cursor-pointer flex items-center gap-1.5"
            >
              <span>+ Explore More</span>
            </button>
          </div>
        </div>

        {/* Clear Confirmation Banner */}
        {showClearConfirm && (
          <div className="p-4 rounded-2xl bg-rose-50/95 backdrop-blur-md border border-rose-300 text-rose-950 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-md animate-fadeIn">
            <div className="flex items-center gap-2 text-xs font-bold">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
              <span>Are you sure you want to remove all {tripPlan.length} places from your basket?</span>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <button
                onClick={() => setShowClearConfirm(false)}
                className="px-3 py-1.5 rounded-xl border border-rose-300 bg-white text-xs font-semibold text-slate-700 hover:bg-slate-50 cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  clearTripPlan();
                  setShowClearConfirm(false);
                }}
                className="px-3.5 py-1.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold cursor-pointer"
              >
                Yes, Clear All
              </button>
            </div>
          </div>
        )}

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-4 sm:p-5 rounded-2xl bg-white/70 backdrop-blur-xl border border-white/50 shadow-md space-y-1">
            <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider font-sans">Total Destinations</div>
            <div className="text-2xl font-black text-slate-900 font-sans flex items-center gap-2">
              <Luggage className="w-5 h-5 text-terracotta" />
              <span>{tripPlan.length} Places</span>
            </div>
            <div className="text-[10px] text-slate-600">
              {pondyCount > 0 && `${pondyCount} in Pondicherry`}
              {pondyCount > 0 && chennaiCount > 0 && ' • '}
              {chennaiCount > 0 && `${chennaiCount} in Chennai`}
            </div>
          </div>

          <div className="p-4 sm:p-5 rounded-2xl bg-white/70 backdrop-blur-xl border border-white/50 shadow-md space-y-1">
            <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider font-sans">Est. Activity Budget</div>
            <div className="text-2xl font-black text-slate-900 font-sans flex items-center gap-1">
              <IndianRupee className="w-5 h-5 text-emerald-600" />
              <span>{totalCost === 0 ? 'Free' : `₹${totalCost.toLocaleString()}`}</span>
            </div>
            <div className="text-[10px] text-slate-600">Based on standard entry & activities</div>
          </div>

          <div className="p-4 sm:p-5 rounded-2xl bg-white/70 backdrop-blur-xl border border-white/50 shadow-md space-y-1">
            <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider font-sans">Total Time Needed</div>
            <div className="text-2xl font-black text-slate-900 font-sans flex items-center gap-2">
              <Clock className="w-5 h-5 text-amber-700" />
              <span>~{totalHours} Hours</span>
            </div>
            <div className="text-[10px] text-slate-600">Approx. {Math.max(1, Math.ceil(totalMinutes / 360))} day(s) itinerary</div>
          </div>

          <div className="p-4 sm:p-5 rounded-2xl bg-white/70 backdrop-blur-xl border border-white/50 shadow-md space-y-1 flex flex-col justify-between">
            <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider font-sans">AI Route Optimizer</div>
            <button
              onClick={() => setActiveTab('planner')}
              className="w-full py-2 px-3 rounded-xl bg-[#FCD34D] hover:bg-amber-400 text-slate-950 font-bold text-xs font-sans shadow-xs flex items-center justify-center gap-1.5 transition-all cursor-pointer"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Plan with AI</span>
            </button>
            <div className="text-[10px] text-slate-600 text-center">Auto-schedule with AI Concierge</div>
          </div>
        </div>

        {/* Empty State */}
        {tripPlan.length === 0 ? (
          <div className="rounded-3xl bg-white/70 backdrop-blur-xl border border-white/50 p-12 text-center space-y-4 shadow-xl">
            <div className="w-16 h-16 rounded-full bg-white/80 border border-white/60 flex items-center justify-center mx-auto text-slate-400 shadow-inner">
              <Luggage className="w-8 h-8 text-slate-400" />
            </div>
            <h3 className="text-xl font-extrabold text-slate-900 font-sans">Your Basket is Currently Empty</h3>
            <p className="text-xs sm:text-sm text-slate-600 max-w-md mx-auto font-sans leading-relaxed">
              You haven't saved any destinations yet. Browse through popular places in Pondicherry and Chennai, or ask the AI Concierge to curate an itinerary!
            </p>
            <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
              <button
                onClick={() => setActiveTab('explore')}
                className="px-5 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs font-sans shadow-md cursor-pointer transition-all flex items-center gap-2"
              >
                <Compass className="w-4 h-4 text-amber-300" />
                <span>Explore Destinations</span>
              </button>
              <button
                onClick={() => setActiveTab('planner')}
                className="px-5 py-2.5 rounded-xl bg-[#FCD34D] hover:bg-amber-400 text-slate-950 font-bold text-xs font-sans shadow-md cursor-pointer transition-all flex items-center gap-2"
              >
                <Sparkles className="w-4 h-4" />
                <span>Ask AI Concierge</span>
              </button>
            </div>
          </div>
        ) : (
          /* Places Cards Grid */
          <div className="space-y-4">
            <div className="flex items-center justify-between px-2">
              <h2 className="text-base sm:text-lg font-bold text-white drop-shadow-sm font-sans">
                Saved Destinations ({tripPlan.length})
              </h2>
              <span className="text-xs text-white/80 font-sans">
                Drag or manage stops directly before routing
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {tripPlan.map((place, idx) => {
                const isChennai = place.city_id === 'chennai';
                const cityLabel = isChennai ? 'Chennai' : 'Pondicherry';

                return (
                  <div
                    key={place.id || idx}
                    className="rounded-3xl bg-white/80 backdrop-blur-xl border border-white/60 shadow-lg overflow-hidden flex flex-col justify-between hover:border-[#FCD34D] transition-all group"
                  >
                    {/* Top Image & Badges */}
                    <div className="relative h-44 w-full overflow-hidden bg-slate-200">
                      {place.image_url ? (
                        <img
                          src={place.image_url}
                          alt={place.name}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center bg-slate-100 text-slate-400">
                          <MapPin className="w-8 h-8" />
                        </div>
                      )}

                      {/* Top Overlay Badges */}
                      <div className="absolute top-3 left-3 flex flex-wrap items-center gap-1.5">
                        <span className="px-2.5 py-1 rounded-full bg-slate-950/80 backdrop-blur-md text-white text-[10px] font-bold font-sans flex items-center gap-1 shadow-xs">
                          <MapPin className="w-3 h-3 text-amber-300" />
                          <span>{cityLabel}</span>
                        </span>
                        <span className="px-2 py-0.5 rounded-full bg-white/90 backdrop-blur-md text-slate-800 text-[10px] font-bold uppercase tracking-wider font-sans shadow-xs">
                          {place.category}
                        </span>
                      </div>

                      {/* Remove Button */}
                      <button
                        onClick={() => removeFromTripPlan(place.id)}
                        className="absolute top-3 right-3 w-8 h-8 rounded-full bg-white/90 hover:bg-rose-500 hover:text-white text-slate-600 backdrop-blur-md flex items-center justify-center transition-colors shadow-md cursor-pointer"
                        title="Remove from basket"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>

                    {/* Card Body */}
                    <div className="p-5 flex-1 flex flex-col justify-between space-y-3">
                      <div>
                        <div className="flex items-center gap-2 text-xs font-bold text-slate-500 font-sans">
                          <span>Stop #{idx + 1}</span>
                          <span>•</span>
                          <span>{place.duration_minutes ? `${place.duration_minutes} mins` : 'Flexible'}</span>
                          <span>•</span>
                          <span className="text-slate-900 font-bold">
                            {place.estimated_cost_inr === 0 ? 'Free' : `₹${place.estimated_cost_inr}`}
                          </span>
                        </div>

                        <h3 className="font-extrabold text-slate-900 text-base sm:text-lg mt-1 font-sans line-clamp-1">
                          {place.name}
                        </h3>

                        <p className="text-xs text-slate-600 mt-1 line-clamp-2 leading-relaxed font-sans">
                          {place.description || place.sub_category}
                        </p>

                        {place.highlights && place.highlights.length > 0 && (
                          <div className="mt-2.5 flex items-center gap-1.5 text-[11px] text-amber-900 bg-amber-50/80 px-2.5 py-1 rounded-xl border border-amber-200">
                            <span className="shrink-0">✨</span>
                            <span className="truncate">{place.highlights[0]}</span>
                          </div>
                        )}
                      </div>

                      {/* Footer Actions */}
                      <div className="pt-2 border-t border-slate-100 flex items-center justify-between gap-2">
                        <button
                          onClick={() => setActiveModalPlace(place)}
                          className="px-3 py-1.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-bold font-sans flex items-center gap-1 transition-colors cursor-pointer"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          <span>View Details</span>
                        </button>

                        <button
                          onClick={handleRouteOnMap}
                          className="px-3.5 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-amber-300 text-xs font-bold font-sans flex items-center gap-1 transition-colors cursor-pointer"
                        >
                          <span>Route Map</span>
                          <ArrowRight className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

      </div>

      {/* Place Details Modal */}
      {activeModalPlace && (
        <PlaceModal
          place={activeModalPlace}
          onClose={() => setActiveModalPlace(null)}
        />
      )}
    </div>
  );
}

export default SavedBasketPage;
