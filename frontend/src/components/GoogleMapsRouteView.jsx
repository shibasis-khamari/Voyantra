import React, { useState, useEffect, useRef, useMemo } from 'react';
import { 
  Navigation, 
  MapPin, 
  AlertCircle, 
  ExternalLink, 
  Layers, 
  Key, 
  CheckCircle2, 
  Car, 
  Footprints,
  Compass,
  Loader2,
  X
} from 'lucide-react';
import { MapView } from './MapView';

export function GoogleMapsRouteView({
  stops = [],
  mode = 'driving',
  height = '500px',
  onRouteComputed = null,
  selectedStopIndex = null,
  showTraffic = false,
  cityId = 'pondicherry',
  userLocation = null,
  routeFromUser = false,
  activeUserRouteStop = null
}) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const directionsServiceRef = useRef(null);
  const directionsRendererRef = useRef(null);
  const trafficLayerRef = useRef(null);
  const userMarkerRef = useRef(null);
  const markersRef = useRef([]);

  const defaultCenter = cityId === 'chennai' 
    ? { lat: 13.0827, lng: 80.2707 } 
    : { lat: 11.9416, lng: 79.8083 };

  // API Key State (from .env or user session input)
  const envKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || '';
  const [apiKey, setApiKey] = useState(() => {
    return sessionStorage.getItem('voyantra_google_maps_key') || envKey;
  });
  const [keyInput, setKeyInput] = useState('');
  const [showKeyInput, setShowKeyInput] = useState(false);
  const [scriptLoaded, setScriptLoaded] = useState(false);
  const [scriptError, setScriptError] = useState(null);
  const [routeLoading, setRouteLoading] = useState(false);
  const [routeError, setRouteError] = useState(null);
  const [useFallbackMap, setUseFallbackMap] = useState(false);

  // Haversine distance calculator helper
  const getHaversineDist = (lat1, lon1, lat2, lon2) => {
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

  // Instant calculated route data for In-App OpenStreetMap engine
  const osmRouteData = useMemo(() => {
    const roadFactor = mode === 'walking' ? 1.25 : 1.35;
    const speed = mode === 'walking' ? 4.5 : 24.0;

    // If routing from user location to a specific destination
    if (routeFromUser && userLocation && activeUserRouteStop?.coordinates) {
      const d = getHaversineDist(
        userLocation.lat, userLocation.lng,
        activeUserRouteStop.coordinates.lat, activeUserRouteStop.coordinates.lng
      ) * roadFactor;
      const roundedD = Number(d.toFixed(1));
      const mins = Math.max(2, Math.round((d / speed) * 60));

      return {
        legs: [{
          from_place: 'My Current Location',
          to_place: activeUserRouteStop.name,
          distance_km: roundedD,
          distance_text: `${roundedD} km`,
          duration_minutes: mins,
          duration_text: `${mins} min`,
          steps: [
            { instructions: `Depart current location towards ${activeUserRouteStop.name}`, distance: `${roundedD} km` },
            { instructions: `Arrive at ${activeUserRouteStop.name}`, distance: '0 m' }
          ],
          polyline_geojson: {
            coordinates: [
              [userLocation.lng, userLocation.lat],
              [activeUserRouteStop.coordinates.lng, activeUserRouteStop.coordinates.lat]
            ]
          }
        }],
        total_distance_km: roundedD,
        total_duration_minutes: mins
      };
    }

    const validStops = stops.filter(s => s?.coordinates?.lat && s?.coordinates?.lng);
    if (validStops.length < 2) {
      return { legs: [], total_distance_km: 0, total_duration_minutes: 0 };
    }

    let totalKm = 0;
    const legs = [];

    for (let i = 0; i < validStops.length - 1; i++) {
      const s1 = validStops[i];
      const s2 = validStops[i + 1];
      const d = getHaversineDist(
        s1.coordinates.lat, s1.coordinates.lng,
        s2.coordinates.lat, s2.coordinates.lng
      ) * roadFactor;
      const roundedD = Number(d.toFixed(1));
      const mins = Math.max(2, Math.round((d / speed) * 60));
      totalKm += roundedD;

      legs.push({
        from_place: s1.name,
        to_place: s2.name,
        distance_km: roundedD,
        distance_text: `${roundedD} km`,
        duration_minutes: mins,
        duration_text: `${mins} min`,
        steps: [
          { instructions: `Depart ${s1.name} towards ${s2.name}`, distance: `${roundedD} km` },
          { instructions: `Arrive at ${s2.name}`, distance: '0 m' }
        ],
        polyline_geojson: {
          coordinates: [
            [s1.coordinates.lng, s1.coordinates.lat],
            [s2.coordinates.lng, s2.coordinates.lat]
          ]
        }
      });
    }

    return {
      legs,
      total_distance_km: Number(totalKm.toFixed(1)),
      total_duration_minutes: legs.reduce((acc, l) => acc + l.duration_minutes, 0)
    };
  }, [stops, mode, routeFromUser, userLocation, activeUserRouteStop]);

  // Synchronize route metrics in OpenStreetMap mode with parent modal
  useEffect(() => {
    if ((!apiKey || useFallbackMap) && onRouteComputed && osmRouteData) {
      onRouteComputed(osmRouteData);
    }
  }, [apiKey, useFallbackMap, osmRouteData, onRouteComputed]);

  // 1. Dynamic Google Maps JavaScript API Script Loader
  useEffect(() => {
    if (useFallbackMap) return;

    if (!apiKey) {
      setScriptLoaded(false);
      return;
    }

    if (window.google && window.google.maps) {
      setScriptLoaded(true);
      setScriptError(null);
      return;
    }

    const scriptId = 'google-maps-js-sdk';
    const existingScript = document.getElementById(scriptId);

    if (existingScript) {
      existingScript.remove(); // Remove outdated script if key changed
    }

    const script = document.createElement('script');
    script.id = scriptId;
    script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey.trim()}&libraries=places,geometry`;
    script.async = true;
    script.defer = true;

    script.onload = () => {
      setScriptLoaded(true);
      setScriptError(null);
    };

    script.onerror = () => {
      setScriptError('Failed to load Google Maps JavaScript API. Falling back to OpenStreetMap.');
      setUseFallbackMap(true);
      setScriptLoaded(false);
    };

    document.head.appendChild(script);
  }, [apiKey, useFallbackMap]);

  // 2. Initialize Google Map Instance
  useEffect(() => {
    if (!scriptLoaded || !mapContainerRef.current || !window.google?.maps || useFallbackMap || !apiKey) return;

    if (!mapInstanceRef.current) {
      const map = new window.google.maps.Map(mapContainerRef.current, {
        center: defaultCenter,
        zoom: 13,
        mapTypeControl: true,
        streetViewControl: true,
        fullscreenControl: false,
        styles: [
          {
            featureType: 'poi',
            elementType: 'labels',
            stylers: [{ visibility: 'on' }]
          }
        ]
      });

      directionsServiceRef.current = new window.google.maps.DirectionsService();
      directionsRendererRef.current = new window.google.maps.DirectionsRenderer({
        map,
        suppressMarkers: false,
        polylineOptions: {
          strokeColor: mode === 'walking' ? '#7c3aed' : '#0d946e', // Purple for walk, Emerald teal for drive
          strokeWeight: 5,
          strokeOpacity: 0.85
        }
      });

      trafficLayerRef.current = new window.google.maps.TrafficLayer();
      mapInstanceRef.current = map;
    }
  }, [scriptLoaded, useFallbackMap, apiKey]);

  // 3. Traffic Layer Toggle
  useEffect(() => {
    if (!trafficLayerRef.current || !mapInstanceRef.current) return;
    trafficLayerRef.current.setMap(showTraffic ? mapInstanceRef.current : null);
  }, [showTraffic]);

  // 3b. Render User Current Location Pin on Google Map
  useEffect(() => {
    if (!mapInstanceRef.current || !window.google?.maps) return;

    if (userMarkerRef.current) {
      userMarkerRef.current.setMap(null);
      userMarkerRef.current = null;
    }

    if (userLocation && typeof userLocation.lat === 'number' && typeof userLocation.lng === 'number') {
      userMarkerRef.current = new window.google.maps.Marker({
        position: { lat: userLocation.lat, lng: userLocation.lng },
        map: mapInstanceRef.current,
        title: 'Your Current Location',
        zIndex: 9999,
        icon: {
          path: window.google.maps.SymbolPath.CIRCLE,
          scale: 9,
          fillColor: '#2563eb', // Royal Blue GPS dot
          fillOpacity: 1,
          strokeColor: '#ffffff',
          strokeWeight: 3
        }
      });
    }
  }, [userLocation, scriptLoaded, useFallbackMap]);

  // 4. Calculate Preferred Route via Google DirectionsService
  useEffect(() => {
    if (!scriptLoaded || !directionsServiceRef.current || !directionsRendererRef.current || useFallbackMap || !apiKey) return;

    // A) If routing directly from User's Current Location to a selected destination
    if (routeFromUser && userLocation && activeUserRouteStop?.coordinates) {
      setRouteLoading(true);
      setRouteError(null);

      const origin = { lat: userLocation.lat, lng: userLocation.lng };
      const destination = { 
        lat: activeUserRouteStop.coordinates.lat, 
        lng: activeUserRouteStop.coordinates.lng 
      };

      const travelMode = mode === 'walking' 
        ? window.google.maps.TravelMode.WALKING 
        : window.google.maps.TravelMode.DRIVING;

      directionsRendererRef.current.setOptions({
        polylineOptions: {
          strokeColor: '#2563eb', // Vibrant blue for route from current location
          strokeWeight: 6,
          strokeOpacity: 0.9
        }
      });

      directionsServiceRef.current.route(
        {
          origin,
          destination,
          travelMode
        },
        (result, status) => {
          setRouteLoading(false);
          if (status === window.google.maps.DirectionsStatus.OK && result) {
            directionsRendererRef.current.setDirections(result);

            if (onRouteComputed && result.routes && result.routes[0]) {
              const route = result.routes[0];
              const leg = route.legs[0];
              if (leg) {
                onRouteComputed({
                  legs: [{
                    from_place: 'My Current Location',
                    to_place: activeUserRouteStop.name,
                    distance_text: leg.distance?.text || '',
                    duration_text: leg.duration?.text || '',
                    distance_km: leg.distance?.value ? Number((leg.distance.value / 1000).toFixed(1)) : 0,
                    duration_minutes: leg.duration?.value ? Math.round(leg.duration.value / 60) : 0,
                    steps: (leg.steps || []).map(st => ({
                      instructions: st.instructions ? st.instructions.replace(/<[^>]*>?/gm, '') : '',
                      distance: st.distance?.text || '',
                      duration: st.duration?.text || ''
                    }))
                  }],
                  total_distance_km: leg.distance?.value ? Number((leg.distance.value / 1000).toFixed(1)) : 0,
                  total_duration_minutes: leg.duration?.value ? Math.round(leg.duration.value / 60) : 0,
                  raw_result: result
                });
              }
            }
          } else {
            setRouteError(`Could not route from current location: ${status}`);
          }
        }
      );
      return;
    }

    // B) Standard Day Itinerary Sequence Routing
    const validStops = stops.filter(s => s && s.coordinates && typeof s.coordinates.lat === 'number');

    if (validStops.length === 0) {
      directionsRendererRef.current.setDirections({ routes: [] });
      if (mapInstanceRef.current) mapInstanceRef.current.setCenter(defaultCenter);
      return;
    }

    if (validStops.length === 1) {
      const singlePos = { lat: validStops[0].coordinates.lat, lng: validStops[0].coordinates.lng };
      if (mapInstanceRef.current) {
        mapInstanceRef.current.setCenter(singlePos);
        mapInstanceRef.current.setZoom(15);
      }
      directionsRendererRef.current.setDirections({ routes: [] });
      return;
    }

    setRouteLoading(true);
    setRouteError(null);

    const origin = { lat: validStops[0].coordinates.lat, lng: validStops[0].coordinates.lng };
    const destination = { lat: validStops[validStops.length - 1].coordinates.lat, lng: validStops[validStops.length - 1].coordinates.lng };
    const waypoints = validStops.slice(1, -1).map(s => ({
      location: { lat: s.coordinates.lat, lng: s.coordinates.lng },
      stopover: true
    }));

    const travelMode = mode === 'walking' 
      ? window.google.maps.TravelMode.WALKING 
      : window.google.maps.TravelMode.DRIVING;

    directionsRendererRef.current.setOptions({
      polylineOptions: {
        strokeColor: mode === 'walking' ? '#7c3aed' : '#0d946e',
        strokeWeight: 5,
        strokeOpacity: 0.85
      }
    });

    directionsServiceRef.current.route(
      {
        origin,
        destination,
        waypoints,
        travelMode,
        optimizeWaypoints: false
      },
      (result, status) => {
        setRouteLoading(false);
        if (status === window.google.maps.DirectionsStatus.OK && result) {
          directionsRendererRef.current.setDirections(result);

          if (onRouteComputed && result.routes && result.routes[0]) {
            const route = result.routes[0];
            const legsData = route.legs.map((leg, idx) => ({
              from_place: validStops[idx]?.name || 'Origin',
              to_place: validStops[idx + 1]?.name || 'Destination',
              distance_text: leg.distance?.text || '',
              duration_text: leg.duration?.text || '',
              distance_km: leg.distance?.value ? Number((leg.distance.value / 1000).toFixed(1)) : 0,
              duration_minutes: leg.duration?.value ? Math.round(leg.duration.value / 60) : 0,
              steps: (leg.steps || []).map(step => ({
                instructions: step.instructions ? step.instructions.replace(/<[^>]*>?/gm, '') : '',
                distance: step.distance?.text || '',
                duration: step.duration?.text || ''
              }))
            }));

            const totalDistKm = legsData.reduce((acc, l) => acc + l.distance_km, 0);
            const totalDurMin = legsData.reduce((acc, l) => acc + l.duration_minutes, 0);

            onRouteComputed({
              legs: legsData,
              total_distance_km: Number(totalDistKm.toFixed(1)),
              total_duration_minutes: totalDurMin,
              raw_result: result
            });
          }
        } else {
          setRouteError(`Notice: Google Directions status is ${status}.`);
        }
      }
    );
  }, [scriptLoaded, stops, mode, useFallbackMap, routeFromUser, userLocation, activeUserRouteStop, apiKey]);

  // 5. Focus selected stop
  useEffect(() => {
    if (selectedStopIndex !== null && stops[selectedStopIndex]?.coordinates && mapInstanceRef.current) {
      const coord = stops[selectedStopIndex].coordinates;
      mapInstanceRef.current.panTo({ lat: coord.lat, lng: coord.lng });
      mapInstanceRef.current.setZoom(16);
    }
  }, [selectedStopIndex, stops]);

  const handleSaveUserKey = (e) => {
    e.preventDefault();
    if (!keyInput.trim()) return;
    sessionStorage.setItem('voyantra_google_maps_key', keyInput.trim());
    setApiKey(keyInput.trim());
    setUseFallbackMap(false);
    setShowKeyInput(false);
    setKeyInput('');
  };

  // =========================================================================
  // CASE 1: Seamless In-App Interactive Map (OpenStreetMap Engine)
  // Automatically renders when no Google key is set, or user toggles fallback
  // =========================================================================
  if (!apiKey || useFallbackMap) {
    return (
      <div className="relative w-full h-full flex flex-col rounded-2xl overflow-hidden border border-slate-200 shadow-md">
        {/* Top Control Ribbon */}
        <div className="px-3.5 py-2 bg-white/95 backdrop-blur-md border-b border-slate-200 flex flex-wrap items-center justify-between gap-2 z-10 shrink-0">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shrink-0" />
            <span className="text-xs font-bold text-slate-800 font-logo">
              In-App Interactive Map
            </span>
            <span className="px-2 py-0.5 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 text-[10px] font-bold uppercase tracking-wider font-sans">
              OpenStreetMap (Zero Key • Free)
            </span>
          </div>

          <div className="flex items-center gap-2">
            {apiKey ? (
              <button
                onClick={() => setUseFallbackMap(false)}
                className="px-2.5 py-1 rounded-lg bg-brand-700 hover:bg-brand-800 text-white text-[11px] font-bold font-logo transition-all cursor-pointer flex items-center gap-1 shadow-2xs"
              >
                <span>Switch to Google Maps</span>
              </button>
            ) : (
              <button
                onClick={() => setShowKeyInput(prev => !prev)}
                className="px-2.5 py-1 rounded-lg bg-amber-50 hover:bg-amber-100 text-amber-900 border border-amber-300 text-[11px] font-bold font-logo transition-all cursor-pointer flex items-center gap-1"
              >
                <Key className="w-3 h-3 text-amber-700" />
                <span>{showKeyInput ? 'Hide Key Input' : 'Have a Google Maps Key?'}</span>
              </button>
            )}
          </div>
        </div>

        {/* Expandable Key Input Dropdown */}
        {showKeyInput && !apiKey && (
          <div className="p-3 bg-amber-50/95 border-b border-amber-200 z-10 shrink-0 text-xs animate-fadeIn">
            <form onSubmit={handleSaveUserKey} className="flex items-center gap-2">
              <input
                type="text"
                value={keyInput}
                onChange={(e) => setKeyInput(e.target.value)}
                placeholder="Paste AIzaSy... Google Maps API Key to enable Google Satellite & Traffic"
                className="flex-1 px-3 py-1.5 rounded-lg bg-white border border-amber-300 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-amber-400"
              />
              <button
                type="submit"
                className="px-3 py-1.5 rounded-lg bg-terracotta hover:bg-terracotta/90 text-white font-bold text-xs font-logo cursor-pointer shrink-0 shadow-2xs"
              >
                Enable Google Maps
              </button>
              <button
                type="button"
                onClick={() => setShowKeyInput(false)}
                className="p-1.5 text-slate-400 hover:text-slate-600 cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </form>
          </div>
        )}

        {/* In-App MapView Canvas */}
        <div className="flex-1 w-full min-h-0 relative">
          <MapView 
            places={stops}
            height="100%"
            transitMode={mode}
            userLocation={userLocation}
            routeLegs={osmRouteData.legs}
          />
        </div>
      </div>
    );
  }

  // =========================================================================
  // CASE 2: Official Google Maps JavaScript API Engine
  // =========================================================================
  return (
    <div className="relative w-full h-full flex flex-col rounded-2xl overflow-hidden border border-slate-200 shadow-md">
      {/* Top Engine Ribbon with One-Click OpenStreetMap Switcher */}
      <div className="px-3.5 py-2 bg-white/95 backdrop-blur-md border-b border-slate-200 flex flex-wrap items-center justify-between gap-2 z-10 shrink-0">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-blue-600 animate-pulse shrink-0" />
          <span className="text-xs font-bold text-slate-800 font-logo">
            In-App Google Maps
          </span>
          <span className="px-2 py-0.5 rounded-full bg-blue-50 border border-blue-200 text-blue-800 text-[10px] font-bold uppercase tracking-wider font-sans">
            Directions API Active
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setUseFallbackMap(true)}
            className="px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-[11px] font-bold font-logo transition-all cursor-pointer flex items-center gap-1 border border-slate-200"
            title="Switch to free OpenStreetMap rendering"
          >
            <Compass className="w-3 h-3 text-emerald-600" />
            <span>Switch to OpenStreetMap</span>
          </button>
        </div>
      </div>

      {/* Route Loading Indicator */}
      {routeLoading && (
        <div className="absolute top-12 left-1/2 -translate-x-1/2 z-10 bg-slate-900/80 backdrop-blur-md px-3.5 py-1.5 rounded-full text-white text-xs font-medium flex items-center gap-2 shadow-lg border border-white/20">
          <Loader2 className="w-3.5 h-3.5 animate-spin text-amber-300" />
          <span>Calculating Google Directions route...</span>
        </div>
      )}

      {/* Script Loading / Error Banner */}
      {scriptError && (
        <div className="p-3 bg-rose-50 border-b border-rose-200 text-xs text-rose-800 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{scriptError}</span>
          </div>
          <button
            onClick={() => setUseFallbackMap(true)}
            className="font-bold underline text-rose-900 ml-2 cursor-pointer"
          >
            Switch to OpenStreetMap
          </button>
        </div>
      )}

      {/* Main Google Maps Canvas */}
      <div 
        ref={mapContainerRef} 
        className="flex-1 w-full bg-slate-100 min-h-[350px]" 
      />

      {/* Google Maps Legend & Mode Chip */}
      <div className="absolute bottom-4 left-4 z-10 bg-white/95 backdrop-blur-md p-2.5 rounded-xl border border-slate-200 shadow-lg text-xs space-y-1 font-sans">
        <div className="flex items-center gap-2 font-bold text-slate-900 font-logo text-[11px]">
          <Navigation className="w-3.5 h-3.5 text-brand-600" />
          <span>Google Maps Directions</span>
        </div>
        <div className="flex items-center gap-2 text-slate-600 text-[11px]">
          <span className={`w-3.5 h-1 rounded-full ${mode === 'walking' ? 'bg-purple-600' : 'bg-emerald-600'}`} />
          <span>{mode === 'walking' ? 'Walking Route (Pedestrian)' : 'Driving Route (Road Network)'}</span>
        </div>
        {showTraffic && (
          <div className="flex items-center gap-1.5 text-emerald-700 text-[10px] font-semibold">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span>Live Traffic Layer Active</span>
          </div>
        )}
      </div>
    </div>
  );
}
