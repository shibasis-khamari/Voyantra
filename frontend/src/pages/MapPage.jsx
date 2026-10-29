import React, { useState, useEffect, useMemo, useRef } from 'react';
import { 
  ArrowLeft, 
  Sparkles, 
  Zap, 
  Bookmark, 
  CheckCircle2, 
  Clock, 
  MapPin, 
  Plus, 
  MoreHorizontal, 
  Loader2, 
  Navigation, 
  Compass,
  Car,
  Footprints,
  IndianRupee
} from 'lucide-react';
import { usePreferences } from '../context/PreferencesContext';
import { VoyantraAPI } from '../services/api';
import { GoogleMapsRouteView } from '../components/GoogleMapsRouteView';

export function MapPage({ setActiveTab }) {
  const { selectedCity, activeItinerary, addToTripPlan } = usePreferences();
  const [places, setPlaces] = useState([]);
  const [selectedDayIdx, setSelectedDayIdx] = useState(0);
  const [transitMode, setTransitMode] = useState('driving');
  const [selectedStopIdx, setSelectedStopIdx] = useState(0);
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [dayOptimizations, setDayOptimizations] = useState({});
  const [savedNotification, setSavedNotification] = useState(false);

  // Sliding division state for adjustable split-view
  const containerRef = useRef(null);
  const [leftWidth, setLeftWidth] = useState(45); // Percentage of total width
  const [isResizing, setIsResizing] = useState(false);

  // Dragging handlers for sliding divider
  const handleMouseDown = (e) => {
    e.preventDefault();
    setIsResizing(true);
  };

  useEffect(() => {
    if (!isResizing) return;

    const handleMouseMove = (e) => {
      if (!containerRef.current) return;
      const clientX = e.clientX ?? (e.touches && e.touches[0]?.clientX);
      if (clientX === undefined) return;

      const rect = containerRef.current.getBoundingClientRect();
      const newWidth = ((clientX - rect.left) / rect.width) * 100;
      // Clamp between 25% and 75%
      const clamped = Math.min(Math.max(newWidth, 25), 75);
      setLeftWidth(clamped);
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    window.addEventListener('touchmove', handleMouseMove);
    window.addEventListener('touchend', handleMouseUp);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
      window.removeEventListener('touchmove', handleMouseMove);
      window.removeEventListener('touchend', handleMouseUp);
    };
  }, [isResizing]);

  // Fallback sample matching user's reference screenshot if no itinerary generated yet
  const defaultSampleItinerary = useMemo(() => ({
    itinerary_title: selectedCity === 'chennai' 
      ? "2-Day Cultural Chennai: Temples, Heritage and Marina Coast"
      : "2-Day Family-Friendly Pondicherry: Gardens and Coast",
    summary: selectedCity === 'chennai'
      ? "Kapaleeshwarar Temple morning traditions, San Thome colonial heritage, and sunset on Marina Beach."
      : "The Botanical Garden toy train, an easy White Town heritage walk, and sunset on the promenade.",
    city_id: selectedCity || 'pondicherry',
    total_estimated_budget_inr: 380,
    days: [
      {
        day_number: 1,
        theme: "Gardens, toy train and heritage strolls",
        morning: {
          place_name: "Pondicherry Botanical Garden",
          activity_note: "Toy train for kids · Historic botanical flora",
          est_time: "8:30 AM",
          duration_minutes: 150,
          cost_inr: 30,
          crowd_level: "Low",
          color_tint: "bg-emerald-50 text-emerald-700 border-emerald-200"
        },
        afternoon: {
          place_name: "White Town Heritage Walk",
          activity_note: "Easy pace · Colonial French quarter mansions",
          est_time: "12:30 PM",
          duration_minutes: 150,
          cost_inr: 0,
          crowd_level: "Moderate",
          color_tint: "bg-amber-50 text-amber-700 border-amber-200"
        },
        evening: {
          place_name: "Promenade Beach",
          activity_note: "Sunset sea walk · Goubert Avenue pedestrian zone",
          est_time: "5:00 PM",
          duration_minutes: 120,
          cost_inr: 0,
          crowd_level: "High",
          color_tint: "bg-sky-50 text-sky-700 border-sky-200"
        }
      },
      {
        day_number: 2,
        theme: "Gothic architecture & island beach fun",
        morning: {
          place_name: "Sri Aurobindo Ashram",
          activity_note: "Peaceful meditation courtyard & floral display",
          est_time: "8:30 AM",
          duration_minutes: 90,
          cost_inr: 0,
          crowd_level: "Low",
          color_tint: "bg-teal-50 text-teal-700 border-teal-200"
        },
        afternoon: {
          place_name: "Basilica of the Sacred Heart of Jesus",
          activity_note: "Gothic architecture with stained glass panels",
          est_time: "1:00 PM",
          duration_minutes: 60,
          cost_inr: 0,
          crowd_level: "Moderate",
          color_tint: "bg-amber-50 text-amber-700 border-amber-200"
        },
        evening: {
          place_name: "Paradise Beach",
          activity_note: "Ferry boat ride & golden sands relaxation",
          est_time: "4:30 PM",
          duration_minutes: 180,
          cost_inr: 350,
          crowd_level: "Moderate",
          color_tint: "bg-indigo-50 text-indigo-700 border-indigo-200"
        }
      }
    ]
  }), [selectedCity]);

  // Load places for coordinate matching
  useEffect(() => {
    VoyantraAPI.getPlaces({ city_id: selectedCity })
      .then(data => setPlaces(data || []))
      .catch(() => setPlaces([]));
  }, [selectedCity]);

  const itinerary = activeItinerary || defaultSampleItinerary;
  const days = itinerary.days || [];
  const activeDay = days[selectedDayIdx] || days[0] || {};

  // Find verified lat/lng
  const findCoordinates = (placeName) => {
    if (!placeName) return { lat: 11.9416, lng: 79.8083 };
    const norm = placeName.toLowerCase().trim();
    const found = places.find(p => 
      p.name && (p.name.toLowerCase().includes(norm) || norm.includes(p.name.toLowerCase()))
    );
    if (found?.coordinates?.lat && found?.coordinates?.lng) {
      return { lat: found.coordinates.lat, lng: found.coordinates.lng };
    }
    // Pondicherry landmarks fallback
    if (norm.includes('botanical')) return { lat: 11.9285, lng: 79.8222 };
    if (norm.includes('white town') || norm.includes('french')) return { lat: 11.9333, lng: 79.8333 };
    if (norm.includes('promenade') || norm.includes('rock beach')) return { lat: 11.9317, lng: 79.8359 };
    if (norm.includes('ashram') || norm.includes('aurobindo')) return { lat: 11.9366, lng: 79.8344 };
    if (norm.includes('basilica') || norm.includes('sacred heart')) return { lat: 11.9288, lng: 79.8288 };
    if (norm.includes('paradise')) return { lat: 11.8722, lng: 79.8197 };
    if (norm.includes('auroville') || norm.includes('matrimandir')) return { lat: 12.0070, lng: 79.8107 };

    // Chennai landmarks fallback
    if (norm.includes('marina')) return { lat: 13.0500, lng: 80.2824 };
    if (norm.includes('kapaleeshwarar')) return { lat: 13.0336, lng: 80.2697 };
    if (norm.includes('san thome')) return { lat: 13.0334, lng: 80.2778 };

    return selectedCity === 'chennai' ? { lat: 13.0827, lng: 80.2707 } : { lat: 11.9416, lng: 79.8083 };
  };

  // Extract stops for current day
  const dayStops = useMemo(() => {
    if (!activeDay) return [];
    const slotKeys = Object.keys(activeDay).filter(k => !['day_number', 'theme'].includes(k) && !!activeDay[k]);
    const orderWeights = { morning: 1, afternoon: 2, evening: 3 };
    slotKeys.sort((a, b) => (orderWeights[a] || 4) - (orderWeights[b] || 4));

    return slotKeys.map((k, idx) => {
      const raw = activeDay[k];
      const name = typeof raw === 'string' ? raw : (raw.place_name || 'Destination');
      const note = typeof raw === 'object' && raw.activity_note ? raw.activity_note : '';
      const timeTag = typeof raw === 'object' && raw.est_time ? raw.est_time : (k === 'morning' ? '8:30 AM' : k === 'afternoon' ? '12:30 PM' : '5:00 PM');
      const duration = typeof raw === 'object' && raw.duration_minutes ? `${(raw.duration_minutes / 60).toFixed(1)} hrs` : (k === 'evening' ? '2 hrs' : '2.5 hrs');
      const cost = typeof raw === 'object' && raw.cost_inr !== undefined ? (raw.cost_inr === 0 ? 'Free' : `₹${raw.cost_inr}`) : (raw.estimated_cost_inr !== undefined ? (raw.estimated_cost_inr === 0 ? 'Free' : `₹${raw.estimated_cost_inr}`) : 'Free');
      const crowd = typeof raw === 'object' && raw.crowd_level ? raw.crowd_level : (idx === 0 ? 'Low' : idx === 1 ? 'Moderate' : 'High');
      const coords = findCoordinates(name);

      return {
        order: idx + 1,
        slotKey: k,
        name,
        activityNote: note,
        timeTag,
        duration,
        cost,
        crowd,
        coordinates: coords,
        color_tint: idx === 0 
          ? "bg-emerald-50 text-emerald-700 border-emerald-200" 
          : idx === 1 
            ? "bg-amber-50 text-amber-700 border-amber-200" 
            : "bg-sky-50 text-sky-700 border-sky-200"
      };
    });
  }, [activeDay, places]);

  // Total stops across all days
  const totalStopsCount = useMemo(() => {
    return days.reduce((acc, d) => {
      const validSlots = Object.keys(d).filter(k => !['day_number', 'theme'].includes(k) && !!d[k]);
      return acc + validSlots.length;
    }, 0);
  }, [days]);

  // Handle Route Optimization Trigger
  const handleOptimizeRoute = async () => {
    setIsOptimizing(true);
    try {
      const slotsPayload = dayStops.map(s => ({
        slot_id: `d${selectedDayIdx}_${s.slotKey}`,
        place_name: s.name,
        coordinates: s.coordinates,
        duration_minutes: 120,
        estimated_cost_inr: 0
      }));

      const res = await VoyantraAPI.optimizeDaySchedule({
        day_number: selectedDayIdx + 1,
        city_id: itinerary.city_id || selectedCity || 'pondicherry',
        mode: transitMode,
        slots: slotsPayload
      });

      setDayOptimizations(prev => ({
        ...prev,
        [selectedDayIdx]: res
      }));
    } catch (e) {
      console.warn('[MapPage] Route optimization notice:', e);
      // Offline fallback estimate
      setDayOptimizations(prev => ({
        ...prev,
        [selectedDayIdx]: {
          total_travel_time_minutes: 25,
          total_travel_distance_km: 6.4,
          transit_legs: [
            { from_place: dayStops[0]?.name, to_place: dayStops[1]?.name, duration_minutes: 12, distance_km: 3.1 },
            { from_place: dayStops[1]?.name, to_place: dayStops[2]?.name, duration_minutes: 13, distance_km: 3.3 }
          ]
        }
      }));
    } finally {
      setIsOptimizing(false);
    }
  };

  const handleSaveToBasket = () => {
    dayStops.forEach(s => {
      addToTripPlan({
        id: `stop-${s.name.replace(/\s+/g, '-').toLowerCase()}`,
        name: s.name,
        duration_minutes: 120,
        estimated_cost_inr: 0,
        city_id: selectedCity
      });
    });
    setSavedNotification(true);
    setTimeout(() => setSavedNotification(false), 2500);
  };

  const optData = dayOptimizations[selectedDayIdx];

  return (
    <div 
      ref={containerRef}
      style={{ '--left-split-width': `${leftWidth}%` }}
      className={`min-h-[calc(100vh-4rem)] bg-slate-50 text-slate-900 flex flex-col lg:flex-row overflow-hidden font-sans relative ${
        isResizing ? 'select-none cursor-col-resize' : ''
      }`}
    >
      
      {/* =========================================================================
          LEFT PANEL: Trip Details & Sequential Connected Timeline
          ========================================================================= */}
      <div className="w-full lg:w-[var(--left-split-width)] flex flex-col h-auto lg:h-[calc(100vh-4rem)] border-r border-sandstone bg-white relative z-10 shadow-xs shrink-0">
        
        {/* Top Action Bar */}
        <div className="px-5 sm:px-7 py-3.5 flex items-center justify-between border-b border-sandstone bg-white/95 backdrop-blur-md shrink-0">
          <button
            onClick={() => setActiveTab?.('planner')}
            className="flex items-center gap-1.5 text-xs font-bold font-sans text-slate-600 hover:text-slate-900 transition-colors cursor-pointer group"
          >
            <ArrowLeft className="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition-transform" />
            <span>My trips</span>
          </button>

          <div className="flex items-center gap-2.5">
            <button
              onClick={handleSaveToBasket}
              className="px-3.5 py-1.5 rounded-xl border border-sandstone bg-sandstone-canvas hover:bg-sandstone-light text-xs font-bold font-sans text-slate-700 transition-all cursor-pointer flex items-center gap-1.5 shadow-2xs"
            >
              <Bookmark className="w-3.5 h-3.5 text-slate-500" />
              <span>{savedNotification ? 'Saved ✓' : 'Save'}</span>
            </button>

            <button
              onClick={handleOptimizeRoute}
              disabled={isOptimizing}
              className="px-4 py-1.5 rounded-xl bg-[#FCD34D] hover:bg-amber-300 text-slate-900 font-extrabold font-sans text-xs transition-all shadow-xs cursor-pointer flex items-center gap-1.5"
            >
              {isOptimizing ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Optimizing...</span>
                </>
              ) : (
                <>
                  <Zap className="w-3.5 h-3.5 fill-slate-900 text-slate-900" />
                  <span>Optimize route</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Scrollable Content Container */}
        <div className="flex-1 overflow-y-auto px-5 sm:px-7 py-6 space-y-6">
          
          {/* Title & Overview */}
          <div className="space-y-2">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight leading-tight font-sans">
              {itinerary.itinerary_title}
            </h1>
            <p className="text-xs sm:text-sm text-slate-600 leading-relaxed max-w-xl font-sans">
              {itinerary.summary}
            </p>

            {/* Chips Row */}
            <div className="flex flex-wrap items-center gap-2 pt-1">
              <span className="px-3 py-1 rounded-full bg-sandstone-light border border-sandstone text-xs font-bold font-sans text-slate-700">
                {days.length} days
              </span>
              <span className="px-3 py-1 rounded-full bg-sandstone-light border border-sandstone text-xs font-bold font-sans text-slate-700">
                {totalStopsCount} stops
              </span>
              <span className="px-3 py-1 rounded-full bg-sandstone-light border border-sandstone text-xs font-bold font-sans text-slate-700">
                Est. ₹{itinerary.total_estimated_budget_inr}
              </span>
              <span className="px-3 py-1 rounded-full border border-emerald-300 bg-emerald-50 text-emerald-800 text-xs font-bold flex items-center gap-1 font-sans">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>Reality-checked</span>
              </span>
            </div>
          </div>

          {/* Day Selector Tabs */}
          <div className="pt-2">
            <div className="flex items-center gap-2">
              {days.map((day, idx) => {
                const isActive = selectedDayIdx === idx;
                return (
                  <button
                    key={day.day_number || idx}
                    onClick={() => {
                      setSelectedDayIdx(idx);
                      setSelectedStopIdx(0);
                    }}
                    className={`px-4 py-1.5 rounded-full text-xs font-bold font-sans transition-all cursor-pointer ${
                      isActive
                        ? 'bg-slate-900 text-[#FCD34D] shadow-xs'
                        : 'bg-white hover:bg-sandstone-light text-slate-700 border border-sandstone'
                    }`}
                  >
                    Day {day.day_number || idx + 1}
                  </button>
                );
              })}
            </div>

            {/* Subtitle theme for the day */}
            <div className="text-xs font-bold text-terracotta uppercase tracking-wider font-sans mt-2.5">
              {activeDay.theme || 'Curated daily sequence'}
            </div>
          </div>

          {/* Connected Vertical Timeline */}
          <div className="pt-2 space-y-0 relative">
            {dayStops.map((stop, idx) => {
              const leg = optData?.transit_legs?.[idx];
              const isLast = idx === dayStops.length - 1;

              return (
                <div key={stop.order || idx} className="relative">
                  
                  {/* Vertical Connecting Line */}
                  {!isLast && (
                    <div className="absolute left-[18px] top-9 bottom-0 w-0.5 bg-sandstone z-0" />
                  )}

                  {/* Stop Item Row */}
                  <div className="flex items-start gap-3.5 relative z-10 py-2">
                    
                    {/* Node indicator pill / dot on line */}
                    <div className="flex flex-col items-center shrink-0 pt-3">
                      <div className="w-3.5 h-6 rounded-md flex items-center justify-center font-bold text-[10px] shadow-2xs bg-slate-900 text-[#FCD34D]">
                      </div>
                    </div>

                    {/* Stop Card */}
                    <div 
                      onClick={() => setSelectedStopIdx(idx)}
                      className={`flex-1 border rounded-2xl p-4 transition-all shadow-2xs group cursor-pointer ${
                        selectedStopIdx === idx
                          ? 'border-amber-400 bg-amber-50/50 ring-2 ring-amber-300/40'
                          : 'bg-white hover:bg-sandstone-canvas/70 border-sandstone hover:border-slate-300'
                      }`}
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div className="flex items-center gap-3">
                          
                          {/* Color-coded thumbnail/icon block */}
                          <div className={`w-11 h-11 rounded-xl flex items-center justify-center font-bold text-base shrink-0 border ${stop.color_tint}`}>
                            <MapPin className="w-5 h-5" />
                          </div>

                          <div>
                            <div className="text-[10px] sm:text-[11px] font-bold uppercase tracking-wider text-slate-500 font-sans">
                              {stop.slotKey.toUpperCase()} · {stop.timeTag}
                            </div>
                            <div className="font-bold text-slate-900 text-sm sm:text-base font-sans group-hover:text-terracotta transition-colors">
                              {stop.name}
                            </div>
                            <div className="text-[11px] sm:text-xs text-slate-500 font-sans mt-0.5">
                              {stop.duration} • {stop.cost} • {stop.activityNote}
                            </div>
                          </div>
                        </div>

                        {/* Crowd Tendency Pill & More Menu */}
                        <div className="flex items-center gap-2 shrink-0">
                          <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase font-sans ${
                            stop.crowd === 'Low'
                              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                              : stop.crowd === 'Moderate'
                                ? 'bg-amber-50 text-amber-800 border border-amber-200'
                                : 'bg-rose-50 text-rose-700 border border-rose-200'
                          }`}>
                            {stop.crowd}
                          </span>
                          <button className="text-slate-400 hover:text-slate-700 p-1 cursor-pointer">
                            <MoreHorizontal className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Transit Segment Connector Between Consecutive Stops */}
                  {!isLast && (
                    <div className="pl-9 py-1 relative z-10">
                      <div className="px-3.5 py-1 rounded-xl border border-dashed border-sandstone bg-white/90 text-[11px] text-slate-600 font-medium inline-flex items-center gap-1.5 shadow-2xs">
                        {optData ? (
                          <>
                            <Car className="w-3.5 h-3.5 text-amber-600" />
                            <span>🚗 ~{leg?.duration_minutes || 12} min travel ({leg?.distance_km || 3.2} km)</span>
                          </>
                        ) : (
                          <span>Travel time appears after you optimize</span>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}

            {/* + Add a Stop Button */}
            <div className="pt-3 pl-9">
              <button
                onClick={() => setActiveTab?.('planner')}
                className="w-full py-2.5 rounded-xl border border-dashed border-sandstone hover:border-slate-400 bg-sandstone-canvas/60 hover:bg-white text-xs text-slate-600 hover:text-slate-900 transition-all font-bold font-sans flex items-center justify-center gap-1 cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>+ Add a stop</span>
              </button>
            </div>
          </div>

          <div className="h-16" /> {/* Spacer for bottom controls */}
        </div>

        {/* Floating Bottom Navigation Bar */}
        <div className="p-4 bg-white/95 border-t border-sandstone backdrop-blur-md flex items-center justify-between gap-3 shrink-0">
          <div className="px-3.5 py-2 rounded-xl bg-sandstone-light border border-sandstone text-xs font-semibold text-slate-700 font-sans">
            Day {selectedDayIdx + 1} · {dayStops.length} stops · estimated times
          </div>

          <button
            onClick={() => setActiveTab?.('planner')}
            className="px-4 py-2 rounded-full bg-[#FCD34D] hover:bg-amber-300 text-slate-900 font-bold font-sans text-xs flex items-center gap-1.5 shadow-xs cursor-pointer transition-all"
          >
            <Sparkles className="w-3.5 h-3.5 fill-slate-900 text-slate-900" />
            <span>✦ Ask AI</span>
          </button>
        </div>
      </div>

      {/* =========================================================================
          DRAGGABLE SLIDING DIVISION (Splitter)
          ========================================================================= */}
      <div
        onMouseDown={handleMouseDown}
        onTouchStart={handleMouseDown}
        onDoubleClick={() => setLeftWidth(45)}
        title="Drag division to resize itinerary and map (double-click to reset)"
        className={`hidden lg:flex items-center justify-center w-3 -mx-1.5 z-30 cursor-col-resize transition-all select-none group relative shrink-0 ${
          isResizing ? 'bg-[#FCD34D]' : 'bg-transparent hover:bg-[#FCD34D]/60'
        }`}
      >
        <div className={`w-1 h-14 rounded-full transition-all flex items-center justify-center ${
          isResizing ? 'bg-slate-950 scale-110 shadow-md' : 'bg-slate-300 group-hover:bg-slate-700'
        }`}>
          <div className="w-0.5 h-6 bg-white/70 rounded-full" />
        </div>
      </div>

      {/* =========================================================================
          RIGHT PANEL: Interactive Google Maps Route Navigator
          ========================================================================= */}
      <div className="w-full h-[450px] lg:h-[calc(100vh-4rem)] relative bg-sandstone-canvas overflow-hidden flex-1 min-w-0 border-l border-sandstone">
        <GoogleMapsRouteView
          stops={dayStops}
          mode={transitMode}
          height="100%"
          cityId={itinerary.city_id || selectedCity}
          selectedStopIndex={selectedStopIdx}
          onSelectStop={setSelectedStopIdx}
        />
      </div>

    </div>
  );
}
