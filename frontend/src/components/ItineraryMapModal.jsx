import React, { useState, useMemo, useEffect } from 'react';
import { 
  X, 
  MapPin, 
  Navigation, 
  Car, 
  Footprints, 
  Clock, 
  Compass, 
  ExternalLink, 
  Calendar, 
  Layers, 
  ChevronRight, 
  ChevronDown,
  Sparkles,
  Info,
  LocateFixed,
  Locate,
  Minimize2,
  Maximize2,
  RefreshCw
} from 'lucide-react';
import { GoogleMapsRouteView } from './GoogleMapsRouteView';

export function ItineraryMapModal({
  isOpen,
  onClose,
  itinerary,
  initialDayIndex = 0,
  placesCatalog = []
}) {
  if (!isOpen || !itinerary) return null;

  const [selectedDayIdx, setSelectedDayIdx] = useState(initialDayIndex || 0);
  const [travelMode, setTravelMode] = useState('driving'); // 'driving' | 'walking'
  const [showTraffic, setShowTraffic] = useState(false);
  const [selectedStopIdx, setSelectedStopIdx] = useState(null);
  const [expandedLegIdx, setExpandedLegIdx] = useState(null);
  const [computedRouteData, setComputedRouteData] = useState(null);

  // User Geolocation & Live Route from Current Location States
  const [userLocation, setUserLocation] = useState(null);
  const [isLocatingGps, setIsLocatingGps] = useState(false);
  const [gpsError, setGpsError] = useState(null);
  const [selectedUserTargetIdx, setSelectedUserTargetIdx] = useState(0);
  const [routeFromUser, setRouteFromUser] = useState(false);
  const [isUserRouteWindowMinimized, setIsUserRouteWindowMinimized] = useState(false);

  const days = itinerary.days || [];
  const activeDay = days[selectedDayIdx] || days[0];

  // Helper to extract verified coordinates for places
  const findCoordinates = (placeName) => {
    if (!placeName) return null;
    const norm = placeName.toLowerCase().trim();
    const found = placesCatalog.find(p => 
      p.name && (p.name.toLowerCase().includes(norm) || norm.includes(p.name.toLowerCase()))
    );
    if (found?.coordinates?.lat && found?.coordinates?.lng) {
      return { lat: found.coordinates.lat, lng: found.coordinates.lng, address: found.address || '', category: found.category || '' };
    }
    // Hardcoded known fallbacks for core pondy / chennai sights
    if (norm.includes('aurobindo')) return { lat: 11.9366, lng: 79.8344, address: 'Rue de la Marine, White Town', category: 'spiritual' };
    if (norm.includes('white town') || norm.includes('french')) return { lat: 11.9333, lng: 79.8333, address: 'French Quarter, Pondicherry', category: 'heritage' };
    if (norm.includes('promenade') || norm.includes('rock beach')) return { lat: 11.9317, lng: 79.8359, address: 'Goubert Ave, Pondicherry', category: 'nature' };
    if (norm.includes('auroville') || norm.includes('matrimandir')) return { lat: 12.0070, lng: 79.8107, address: 'Auroville, Tamil Nadu', category: 'spiritual' };
    if (norm.includes('paradise beach')) return { lat: 11.8722, lng: 79.8197, address: 'Chunnambar, Pondicherry', category: 'beach' };
    if (norm.includes('marina beach')) return { lat: 13.0500, lng: 80.2824, address: 'Marina Beach Road, Chennai', category: 'beach' };
    if (norm.includes('kapaleeshwarar')) return { lat: 13.0336, lng: 80.2697, address: 'Mylapore, Chennai', category: 'spiritual' };
    if (norm.includes('san thome')) return { lat: 13.0334, lng: 80.2778, address: 'Santhome High Rd, Chennai', category: 'heritage' };

    const isChennai = itinerary.city_id === 'chennai';
    return isChennai ? { lat: 13.0827, lng: 80.2707, address: 'Chennai', category: 'city' } : { lat: 11.9416, lng: 79.8083, address: 'Pondicherry', category: 'city' };
  };

  // Extract stops for current active day in chronological order
  const dayStops = useMemo(() => {
    if (!activeDay) return [];

    const slotKeys = Object.keys(activeDay).filter(k => !['day_number', 'theme'].includes(k) && !!activeDay[k]);
    
    // Sort slots by time: morning -> afternoon -> evening -> custom
    const orderWeights = { morning: 1, afternoon: 2, evening: 3 };
    slotKeys.sort((a, b) => (orderWeights[a] || 4) - (orderWeights[b] || 4));

    return slotKeys.map((slotKey, idx) => {
      const raw = activeDay[slotKey];
      const placeName = typeof raw === 'string' ? raw : (raw.place_name || 'Destination');
      const timeTag = typeof raw === 'object' && raw.est_time ? raw.est_time : (slotKey === 'morning' ? '8:30 AM' : slotKey === 'afternoon' ? '12:30 PM' : '5:00 PM');
      const note = typeof raw === 'object' && raw.activity_note ? raw.activity_note : '';
      const duration = typeof raw === 'object' && raw.duration_minutes ? raw.duration_minutes : 60;
      const meta = findCoordinates(placeName);

      return {
        order: idx + 1,
        slotKey,
        name: placeName,
        timeTag,
        activityNote: note,
        duration,
        coordinates: meta ? { lat: meta.lat, lng: meta.lng } : null,
        address: meta?.address || '',
        category: meta?.category || 'sight'
      };
    }).filter(s => s.coordinates !== null);
  }, [activeDay, placesCatalog]);

  // Geolocation Request Handler
  const requestUserLocation = () => {
    const isChennai = itinerary.city_id === 'chennai';
    const fallbackCoord = isChennai 
      ? { lat: 13.0827, lng: 80.2707, label: 'Chennai Central (Reference GPS)' } 
      : { lat: 11.9333, lng: 79.8333, label: 'Pondicherry White Town (Reference GPS)' };

    if (!navigator.geolocation) {
      setUserLocation({ ...fallbackCoord, isLive: false });
      setGpsError('Browser geolocation not supported.');
      return;
    }

    setIsLocatingGps(true);
    setGpsError(null);

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setUserLocation({
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
          isLive: true,
          label: 'Live GPS Location'
        });
        setIsLocatingGps(false);
      },
      (err) => {
        console.warn('Geolocation prompt/error:', err.message);
        setUserLocation({ ...fallbackCoord, isLive: false });
        setIsLocatingGps(false);
        setGpsError(
          err.code === 1 
            ? 'Location permission denied. Using city center reference.' 
            : 'Unable to acquire accurate GPS fix. Using city center reference.'
        );
      },
      { enableHighAccuracy: true, timeout: 7000, maximumAge: 60000 }
    );
  };

  useEffect(() => {
    if (isOpen) {
      requestUserLocation();
    }
  }, [isOpen, itinerary?.city_id]);

  // Reset target index and route when day changes
  useEffect(() => {
    setSelectedUserTargetIdx(0);
    setRouteFromUser(false);
  }, [selectedDayIdx]);

  // Haversine distance calculator in km
  const getHaversineDistance = (lat1, lon1, lat2, lon2) => {
    const R = 6371;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = 
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
      Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  };

  // Instant calculated metrics from user location to all day destinations
  const destinationsWithUserDistance = useMemo(() => {
    if (!userLocation) return dayStops;

    return dayStops.map((stop) => {
      if (!stop.coordinates) return stop;
      const straightDistKm = getHaversineDistance(
        userLocation.lat,
        userLocation.lng,
        stop.coordinates.lat,
        stop.coordinates.lng
      );
      
      // Real urban driving/walking factor multiplier
      const roadFactor = travelMode === 'walking' ? 1.25 : 1.35;
      const effectiveDistKm = Math.max(0.1, Number((straightDistKm * roadFactor).toFixed(1)));
      
      const speedKmH = travelMode === 'walking' ? 4.5 : 24.0;
      const durationMinutes = Math.max(2, Math.round((effectiveDistKm / speedKmH) * 60));

      const navUrl = `https://www.google.com/maps/dir/?api=1&origin=Current+Location&destination=${stop.coordinates.lat},${stop.coordinates.lng}&travelmode=${travelMode}`;

      return {
        ...stop,
        userDistanceKm: effectiveDistKm,
        userDurationMinutes: durationMinutes,
        userDurationText: travelMode === 'walking' ? `${durationMinutes}m walk` : `${durationMinutes}m drive`,
        navUrl
      };
    });
  }, [dayStops, userLocation, travelMode]);

  const activeTargetStop = destinationsWithUserDistance[selectedUserTargetIdx] || destinationsWithUserDistance[0];

  // Construct official Google Maps directions universal URL for the full day sequence
  const googleMapsUrl = useMemo(() => {
    if (dayStops.length < 2) return null;
    const origin = `${dayStops[0].coordinates.lat},${dayStops[0].coordinates.lng}`;
    const destination = `${dayStops[dayStops.length - 1].coordinates.lat},${dayStops[dayStops.length - 1].coordinates.lng}`;
    const intermediate = dayStops.slice(1, -1).map(s => `${s.coordinates.lat},${s.coordinates.lng}`).join('|');
    
    let url = `https://www.google.com/maps/dir/?api=1&origin=${encodeURIComponent(origin)}&destination=${encodeURIComponent(destination)}&travelmode=${travelMode}`;
    if (intermediate) {
      url += `&waypoints=${encodeURIComponent(intermediate)}`;
    }
    return url;
  }, [dayStops, travelMode]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-5 bg-slate-950/80 backdrop-blur-md animate-fadeIn">
      <div className="relative w-full max-w-6xl h-[92vh] max-h-[850px] bg-white rounded-3xl shadow-2xl border border-sandstone flex flex-col overflow-hidden text-slate-900">
        
        {/* Header Bar */}
        <div className="px-5 py-4 bg-sandstone-canvas border-b border-sandstone flex flex-wrap items-center justify-between gap-3 shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-terracotta/10 border border-terracotta/20 flex items-center justify-center text-terracotta shrink-0">
              <Navigation className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base sm:text-lg font-bold font-sans text-slate-900 leading-tight">
                  Google Maps Route Navigator
                </h2>
                <span className="px-2 py-0.5 rounded-full bg-sandstone text-[10px] text-slate-700 font-semibold uppercase tracking-wider font-sans">
                  {itinerary.city_id === 'chennai' ? 'Chennai' : 'Pondicherry'}
                </span>
                {routeFromUser && (
                  <span className="px-2 py-0.5 rounded-full bg-blue-100 text-[10px] text-blue-800 font-bold uppercase tracking-wider font-sans flex items-center gap-1 border border-blue-200">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-600 animate-pulse" />
                    From Current Location
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-500 font-sans">
                Interactive preferred turn-by-turn routing powered by Google Directions API
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Travel Mode Toggle */}
            <div className="flex bg-white rounded-xl p-1 border border-sandstone shadow-xs">
              <button
                onClick={() => setTravelMode('driving')}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold font-sans flex items-center gap-1.5 transition-all cursor-pointer ${
                  travelMode === 'driving' 
                    ? 'bg-brand-700 text-white shadow-xs' 
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <Car className="w-3.5 h-3.5" />
                <span>Driving</span>
              </button>
              <button
                onClick={() => setTravelMode('walking')}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold font-sans flex items-center gap-1.5 transition-all cursor-pointer ${
                  travelMode === 'walking' 
                    ? 'bg-purple-700 text-white shadow-xs' 
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <Footprints className="w-3.5 h-3.5" />
                <span>Walking</span>
              </button>
            </div>

            {/* Traffic Toggle */}
            <button
              onClick={() => setShowTraffic(prev => !prev)}
              className={`hidden sm:flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold font-sans border transition-all cursor-pointer ${
                showTraffic 
                  ? 'bg-emerald-50 border-emerald-300 text-emerald-800 shadow-xs' 
                  : 'bg-white border-sandstone text-slate-600 hover:bg-slate-50'
              }`}
              title="Toggle Live Traffic Layer"
            >
              <Layers className="w-3.5 h-3.5 text-emerald-600" />
              <span>Traffic</span>
            </button>

            {/* Open in Google Maps App (Native Navigation) */}
            {googleMapsUrl && (
              <a
                href={googleMapsUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-terracotta hover:bg-terracotta/90 text-white text-xs font-bold font-sans shadow-md hover:shadow-lg transition-all cursor-pointer"
                title="Launch turn-by-turn voice navigation in the Google Maps App"
              >
                <span>Navigate in App</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            )}

            {/* Close Button */}
            <button
              onClick={onClose}
              className="p-2 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-sandstone transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Day Switcher Tabs */}
        {days.length > 1 && (
          <div className="px-5 py-2.5 bg-white border-b border-sandstone flex items-center gap-2 overflow-x-auto shrink-0">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider font-sans mr-1">
              Select Day:
            </span>
            {days.map((d, idx) => {
              const isSelected = idx === selectedDayIdx;
              return (
                <button
                  key={d.day_number || idx}
                  onClick={() => {
                    setSelectedDayIdx(idx);
                    setSelectedStopIdx(null);
                    setExpandedLegIdx(null);
                  }}
                  className={`px-3.5 py-1.5 rounded-xl text-xs font-bold font-sans transition-all cursor-pointer whitespace-nowrap ${
                    isSelected
                      ? 'bg-brand-700 text-white shadow-xs'
                      : 'bg-sandstone-canvas text-slate-600 hover:bg-sandstone hover:text-slate-900 border border-sandstone'
                  }`}
                >
                  Day {d.day_number}: {d.theme || `Sequence ${idx + 1}`}
                </button>
              );
            })}
          </div>
        )}

        {/* Main Content: Split Route List & Interactive Google Map */}
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 min-h-0 overflow-hidden">
          
          {/* Left Panel: Turn-by-Turn Waypoints & Route Statistics */}
          <div className="lg:col-span-4 bg-sandstone-canvas/50 border-r border-sandstone flex flex-col min-h-0 overflow-hidden order-2 lg:order-1">
            
            {/* Day Theme & Live Stats Banner */}
            <div className="p-4 bg-white border-b border-sandstone space-y-2 shrink-0">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-brand-700 font-sans">
                  {routeFromUser ? 'Direct Route from Location' : `Day ${activeDay?.day_number || 1} • ${activeDay?.theme || 'Curated Trail'}`}
                </span>
                <span className="text-[11px] font-semibold text-slate-500 tabular-nums">
                  {routeFromUser ? `To Stop ${selectedUserTargetIdx + 1}` : `${dayStops.length} Destinations`}
                </span>
              </div>

              {computedRouteData && (
                <div className="grid grid-cols-2 gap-2 pt-1 text-xs">
                  <div className="p-2 rounded-xl bg-sandstone-canvas border border-sandstone">
                    <span className="text-[10px] text-slate-500 font-medium block">
                      {routeFromUser ? 'Direct Path Distance' : 'Total Travel Distance'}
                    </span>
                    <span className="font-bold text-slate-900 tabular-nums text-sm">
                      {computedRouteData.total_distance_km} km
                    </span>
                  </div>
                  <div className="p-2 rounded-xl bg-sandstone-canvas border border-sandstone">
                    <span className="text-[10px] text-slate-500 font-medium block">
                      {routeFromUser ? 'Estimated Arrival' : 'Estimated Transit'}
                    </span>
                    <span className="font-bold text-slate-900 tabular-nums text-sm">
                      ~{computedRouteData.total_duration_minutes} mins
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* Scrollable Waypoints & Legs List */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {dayStops.map((stop, idx) => {
                const isSelected = selectedStopIdx === idx || (routeFromUser && selectedUserTargetIdx === idx);
                const leg = computedRouteData?.legs?.[idx];
                const isLegExpanded = expandedLegIdx === idx;
                const distanceInfo = destinationsWithUserDistance[idx];

                return (
                  <React.Fragment key={stop.order}>
                    {/* Destination Stop Card */}
                    <div
                      onClick={() => {
                        setSelectedStopIdx(idx);
                        setSelectedUserTargetIdx(idx);
                      }}
                      className={`p-3 rounded-2xl border transition-all cursor-pointer ${
                        isSelected
                          ? 'bg-white border-brand-500 ring-2 ring-brand-500/20 shadow-md'
                          : 'bg-white border-sandstone hover:border-slate-300 shadow-2xs'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex items-start gap-2.5 min-w-0">
                          <span className={`w-6 h-6 rounded-xl font-bold text-xs flex items-center justify-center shrink-0 mt-0.5 tabular-nums ${
                            isSelected ? 'bg-brand-700 text-white' : 'bg-slate-100 text-slate-700'
                          }`}>
                            {stop.order}
                          </span>
                          <div className="min-w-0">
                            <h4 className="font-serif text-base font-normal text-slate-900 leading-snug truncate">
                              {stop.name}
                            </h4>
                            <p className="text-[11px] text-slate-500 truncate">
                              {stop.address || stop.category}
                            </p>
                          </div>
                        </div>

                        <div className="shrink-0 text-right space-y-0.5">
                          <span className="text-[10px] font-bold text-amber-800 bg-amber-50 px-2 py-0.5 rounded border border-amber-200 font-sans tabular-nums inline-block">
                            {stop.timeTag}
                          </span>
                          {distanceInfo?.userDistanceKm !== undefined && (
                            <div className="text-[10px] text-blue-700 font-semibold tabular-nums">
                              {distanceInfo.userDistanceKm} km from you
                            </div>
                          )}
                        </div>
                      </div>

                      {stop.activityNote && (
                        <p className="text-[11px] text-slate-600 italic pt-1.5 border-t border-slate-100 mt-2">
                          "{stop.activityNote}"
                        </p>
                      )}
                    </div>

                    {/* Transit Leg Connector to next destination (in sequence mode) */}
                    {!routeFromUser && idx < dayStops.length - 1 && (
                      <div className="px-3 py-1.5 rounded-xl bg-slate-100/80 border border-slate-200 text-xs space-y-1">
                        <div 
                          onClick={() => setExpandedLegIdx(isLegExpanded ? null : idx)}
                          className="flex items-center justify-between text-[11px] text-slate-600 cursor-pointer hover:text-slate-900 font-medium"
                        >
                          <div className="flex items-center gap-1.5 font-sans">
                            {travelMode === 'walking' ? (
                              <Footprints className="w-3.5 h-3.5 text-purple-600" />
                            ) : (
                              <Car className="w-3.5 h-3.5 text-brand-600" />
                            )}
                            <span>To Stop {idx + 2}:</span>
                            <strong className="text-slate-900 tabular-nums">
                              {leg?.distance_text || 'Calculating...'}
                            </strong>
                            <span>•</span>
                            <strong className="text-slate-900 tabular-nums">
                              ~{leg?.duration_text || 'calculating'}
                            </strong>
                          </div>

                          <div className="flex items-center gap-1 text-[10px] text-brand-700 font-bold">
                            <span>{isLegExpanded ? 'Hide' : 'Turns'}</span>
                            {isLegExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                          </div>
                        </div>

                        {/* Turn-by-Turn Maneuvers Drawer */}
                        {isLegExpanded && leg?.steps && (
                          <div className="pt-2 border-t border-slate-200 space-y-1 pl-4 text-[10px] text-slate-600">
                            {leg.steps.map((st, sIdx) => (
                              <div key={sIdx} className="flex items-start gap-1.5">
                                <span className="text-slate-400 font-mono">•</span>
                                <span className="flex-1">{st.instructions}</span>
                                <span className="text-slate-400 shrink-0 tabular-nums">({st.distance})</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </React.Fragment>
                );
              })}
            </div>

            {/* Bottom Notice */}
            <div className="p-3 bg-white border-t border-sandstone text-[10px] text-slate-400 flex items-center justify-between shrink-0">
              <span>Google Maps Platform Grounded</span>
              <span className="font-semibold text-slate-600">Verified Waypoints</span>
            </div>
          </div>

          {/* Right Panel: Interactive Google Map View + Floating "Route from My Location" Window */}
          <div className="lg:col-span-8 relative h-full flex flex-col order-1 lg:order-2 overflow-hidden">
            <GoogleMapsRouteView
              stops={dayStops}
              mode={travelMode}
              height="100%"
              showTraffic={showTraffic}
              selectedStopIndex={selectedStopIdx}
              onRouteComputed={(data) => setComputedRouteData(data)}
              cityId={itinerary.city_id || 'pondicherry'}
              userLocation={userLocation}
              routeFromUser={routeFromUser}
              activeUserRouteStop={activeTargetStop}
            />

            {/* Floating "Route from My Location" Window */}
            {activeTargetStop && (
              <div className="pointer-events-none absolute inset-0 p-3 sm:p-4 z-20 flex flex-col items-end justify-start">
                {isUserRouteWindowMinimized ? (
                  /* Minimized Floating Pill */
                  <button
                    onClick={() => setIsUserRouteWindowMinimized(false)}
                    className="pointer-events-auto flex items-center gap-2.5 px-3.5 py-2.5 rounded-2xl bg-white/95 backdrop-blur-md border border-slate-200/90 shadow-xl hover:shadow-2xl hover:border-blue-400 transition-all text-xs font-sans group cursor-pointer text-slate-800"
                  >
                    <span className="relative flex h-2.5 w-2.5">
                      <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${userLocation?.isLive ? 'bg-blue-400' : 'bg-amber-400'}`}></span>
                      <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${userLocation?.isLive ? 'bg-blue-600' : 'bg-amber-500'}`}></span>
                    </span>
                    <span className="font-bold">Route from My Location</span>
                    {activeTargetStop.userDistanceKm !== undefined && (
                      <span className="text-[11px] text-blue-700 font-semibold bg-blue-50 px-2 py-0.5 rounded-full border border-blue-200/60 tabular-nums">
                        {activeTargetStop.userDistanceKm} km • {activeTargetStop.userDurationText}
                      </span>
                    )}
                    <Maximize2 className="w-3.5 h-3.5 text-slate-400 group-hover:text-slate-700 ml-0.5" />
                  </button>
                ) : (
                  /* Expanded Floating Small Window */
                  <div className="pointer-events-auto w-full max-w-[340px] sm:w-[350px] bg-white/95 backdrop-blur-md border border-slate-200/90 rounded-2xl shadow-2xl flex flex-col overflow-hidden text-slate-900 animate-fadeIn transition-all">
                    {/* Window Header */}
                    <div className="px-3.5 py-2.5 bg-gradient-to-r from-blue-50/80 to-slate-50 border-b border-slate-200/80 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="relative flex h-2.5 w-2.5">
                          <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${userLocation?.isLive ? 'bg-blue-400' : 'bg-amber-400'}`}></span>
                          <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${userLocation?.isLive ? 'bg-blue-600' : 'bg-amber-500'}`}></span>
                        </span>
                        <div>
                          <h4 className="text-xs font-bold font-sans text-slate-900 leading-tight">
                            Route from My Location
                          </h4>
                          <span className="text-[10px] text-slate-500 font-medium block">
                            {userLocation?.label || (userLocation?.isLive ? 'Live GPS Active' : 'City Reference GPS')}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center gap-1">
                        <button
                          onClick={requestUserLocation}
                          disabled={isLocatingGps}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-blue-600 hover:bg-white transition-colors cursor-pointer"
                          title="Refresh GPS Location"
                        >
                          <RefreshCw className={`w-3.5 h-3.5 ${isLocatingGps ? 'animate-spin text-blue-600' : ''}`} />
                        </button>
                        <button
                          onClick={() => setIsUserRouteWindowMinimized(true)}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-white transition-colors cursor-pointer"
                          title="Minimize Window"
                        >
                          <Minimize2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    {/* Window Content */}
                    <div className="p-3.5 space-y-3 max-h-[360px] overflow-y-auto">
                      {/* Destination Dropdown */}
                      <div className="space-y-1">
                        <div className="flex items-center justify-between">
                          <label className="text-[10px] font-bold uppercase tracking-wider text-slate-500 font-sans">
                            Destination:
                          </label>
                          <span className="text-[10px] text-blue-600 font-medium font-sans">
                            Stop {selectedUserTargetIdx + 1} of {dayStops.length}
                          </span>
                        </div>
                        <select
                          value={selectedUserTargetIdx}
                          onChange={(e) => {
                            const idx = Number(e.target.value);
                            setSelectedUserTargetIdx(idx);
                            setSelectedStopIdx(idx);
                          }}
                          className="w-full text-xs font-sans font-semibold px-2.5 py-2 rounded-xl bg-slate-50 hover:bg-slate-100/80 border border-slate-200 text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500/30 cursor-pointer transition-all"
                        >
                          {destinationsWithUserDistance.map((stop, sIdx) => (
                            <option key={stop.order || sIdx} value={sIdx}>
                              Stop {stop.order}: {stop.name} ({stop.userDistanceKm || '~'} km)
                            </option>
                          ))}
                        </select>
                      </div>

                      {/* Active Target Quick Metrics Card */}
                      <div className="p-2.5 rounded-xl bg-blue-50/60 border border-blue-100 space-y-2">
                        <div className="flex items-start justify-between gap-2">
                          <div className="min-w-0">
                            <span className="text-[10px] font-bold text-blue-800 uppercase tracking-wider font-sans block">
                              To {activeTargetStop.name}
                            </span>
                            <span className="text-[11px] text-slate-600 truncate block">
                              {activeTargetStop.address || 'Curated Destination'}
                            </span>
                          </div>
                          <div className="text-right shrink-0">
                            <span className="text-sm font-bold text-slate-900 tabular-nums block">
                              {activeTargetStop.userDistanceKm} km
                            </span>
                            <span className="text-[10px] text-blue-700 font-semibold block capitalize">
                              ~{activeTargetStop.userDurationText}
                            </span>
                          </div>
                        </div>

                        {/* Action Buttons Row */}
                        <div className="grid grid-cols-2 gap-1.5 pt-1">
                          <button
                            onClick={() => setRouteFromUser(prev => !prev)}
                            className={`w-full py-1.5 px-2 rounded-lg text-[11px] font-bold font-sans flex items-center justify-center gap-1.5 transition-all cursor-pointer ${
                              routeFromUser
                                ? 'bg-blue-600 hover:bg-blue-700 text-white shadow-xs'
                                : 'bg-white hover:bg-slate-50 text-blue-700 border border-blue-200'
                            }`}
                          >
                            <LocateFixed className="w-3 h-3" />
                            <span>{routeFromUser ? '✓ Path on Map' : 'Show on Map'}</span>
                          </button>

                          <a
                            href={activeTargetStop.navUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="w-full py-1.5 px-2 rounded-lg text-[11px] font-bold font-sans bg-terracotta hover:bg-terracotta/90 text-white shadow-xs flex items-center justify-center gap-1.5 transition-all cursor-pointer"
                            title="Launch Google Maps Live Navigation"
                          >
                            <span>GPS Nav</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        </div>
                      </div>

                      {/* All Day Destinations Quick Distance List */}
                      <div className="space-y-1 pt-1">
                        <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-wider text-slate-400 font-sans">
                          <span>All Stops from You</span>
                          <span>Dist / Est. Time</span>
                        </div>

                        <div className="space-y-1">
                          {destinationsWithUserDistance.map((stop, idx) => {
                            const isSelected = selectedUserTargetIdx === idx;
                            return (
                              <div
                                key={stop.order || idx}
                                onClick={() => {
                                  setSelectedUserTargetIdx(idx);
                                  setSelectedStopIdx(idx);
                                }}
                                className={`flex items-center justify-between p-2 rounded-xl text-xs cursor-pointer transition-all ${
                                  isSelected
                                    ? 'bg-blue-100/70 border border-blue-300 font-semibold text-blue-950'
                                    : 'bg-slate-50/70 hover:bg-slate-100 border border-slate-200/60 text-slate-700'
                                }`}
                              >
                                <div className="flex items-center gap-2 min-w-0 pr-2">
                                  <span className={`w-5 h-5 rounded-lg flex items-center justify-center text-[10px] font-bold shrink-0 tabular-nums ${
                                    isSelected ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-700'
                                  }`}>
                                    {stop.order}
                                  </span>
                                  <span className="truncate text-[11px] font-serif">{stop.name}</span>
                                </div>

                                <div className="shrink-0 text-right text-[10px] font-bold tabular-nums text-slate-600">
                                  <span>{stop.userDistanceKm} km</span>
                                  <span className="text-slate-400 mx-1">•</span>
                                  <span>~{stop.userDurationMinutes}m</span>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>

                      {/* Toggle back to Full Sequence notice if user route is active */}
                      {routeFromUser && (
                        <div className="pt-1">
                          <button
                            onClick={() => setRouteFromUser(false)}
                            className="w-full py-1 text-[11px] font-semibold text-slate-500 hover:text-slate-800 text-center cursor-pointer hover:underline"
                          >
                            ← Switch back to full day itinerary route
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

        </div>

      </div>
    </div>
  );
}
