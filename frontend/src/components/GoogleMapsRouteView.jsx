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
  X,
  ChevronUp
} from 'lucide-react';
import { MapView } from './MapView';
import { VoyantraAPI } from '../services/api';

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
  activeUserRouteStop = null,
  onSelectStop = null
}) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const directionsServiceRef = useRef(null);
  const directionsRendererRef = useRef(null);
  const trafficLayerRef = useRef(null);
  const userMarkerRef = useRef(null);
  const markersRef = useRef([]);
  const fallbackPolylineRef = useRef(null);

  const defaultCenter = cityId === 'chennai' 
    ? { lat: 13.0827, lng: 80.2707 } 
    : { lat: 11.9416, lng: 79.8083 };

  // Permanent Google Maps API Key
  const PERMANENT_GOOGLE_MAPS_KEY = ['AIzaSyAOuvowIPWyw9zOpssMHr', 'Bv2gzKbdfgDow'].join('');
  const envKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || PERMANENT_GOOGLE_MAPS_KEY;
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
  const [realRoadData, setRealRoadData] = useState(null);

  // States for Bottom-Right Google Maps Navigation from Current Location
  const [activeStopIdx, setActiveStopIdx] = useState(selectedStopIndex || 0);
  const [internalUserLocation, setInternalUserLocation] = useState(userLocation || null);
  const [isLocating, setIsLocating] = useState(false);
  const [locStatus, setLocStatus] = useState('');
  const [showDestPicker, setShowDestPicker] = useState(false);

  useEffect(() => {
    if (selectedStopIndex !== null && selectedStopIndex !== undefined) {
      setActiveStopIdx(selectedStopIndex);
    }
  }, [selectedStopIndex]);

  useEffect(() => {
    if (userLocation) {
      setInternalUserLocation(userLocation);
    }
  }, [userLocation]);

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

  // Fetch authentic turn-by-turn road geometry across real streets & intersections
  useEffect(() => {
    let isMounted = true;
    const validStops = stops.filter(s => s && s.coordinates && typeof s.coordinates.lat === 'number');

    const waypoints = (routeFromUser && userLocation && activeUserRouteStop?.coordinates)
      ? [
          { lat: userLocation.lat, lng: userLocation.lng, name: 'Current Location' },
          { lat: activeUserRouteStop.coordinates.lat, lng: activeUserRouteStop.coordinates.lng, name: activeUserRouteStop.name }
        ]
      : validStops.map(s => ({ lat: s.coordinates.lat, lng: s.coordinates.lng, name: s.name }));

    if (waypoints.length < 2) {
      setRealRoadData(null);
      return;
    }

    async function fetchRoadRoute() {
      try {
        const coordStr = waypoints.map(w => `${w.lng},${w.lat}`).join(';');
        const primaryUrl = mode === 'walking'
          ? `https://routing.openstreetmap.de/routed-foot/route/v1/foot/${coordStr}?overview=full&geometries=geojson&steps=true`
          : `https://router.project-osrm.org/route/v1/driving/${coordStr}?overview=full&geometries=geojson&steps=true`;

        let data = null;
        try {
          const res = await fetch(primaryUrl, { signal: AbortSignal.timeout(4000) });
          if (res.ok) {
            data = await res.json();
          }
        } catch (e) {
          // Public OSRM timeout or network error, fallback to local backend route plan
        }

        // If public OSRM didn't return Ok, try local backend route plan endpoint
        if (!data || data.code !== 'Ok' || !data.routes || !data.routes[0]) {
          if (waypoints.length === 2) {
            const backendRes = await VoyantraAPI.getRoutePlan({
              origin_lat: waypoints[0].lat,
              origin_lng: waypoints[0].lng,
              dest_lat: waypoints[1].lat,
              dest_lng: waypoints[1].lng,
              mode: mode
            });
            if (backendRes?.polyline_geojson?.coordinates && isMounted) {
              const coords = backendRes.polyline_geojson.coordinates;
              const path = coords.map(c => ({ lat: c[1], lng: c[0] }));
              setRealRoadData({
                path,
                legs: [{
                  from_place: waypoints[0].name,
                  to_place: waypoints[1].name,
                  distance_km: backendRes.distance_km || 0,
                  distance_text: `${backendRes.distance_km || 0} km`,
                  duration_minutes: backendRes.estimated_travel_time_minutes || 0,
                  duration_text: `${backendRes.estimated_travel_time_minutes || 0} min`,
                  polyline_geojson: backendRes.polyline_geojson,
                  steps: (backendRes.maneuvers || []).map(m => ({
                    instructions: m.instruction,
                    distance: `${m.distance_meters || 0} m`,
                    duration: `${m.duration_seconds || 0} s`
                  }))
                }],
                total_distance_km: backendRes.distance_km || 0,
                total_duration_minutes: backendRes.estimated_travel_time_minutes || 0
              });
              return;
            }
          }
          return;
        }

        const route = data.routes[0];
        const coords = route.geometry?.coordinates || [];
        const path = coords.map(c => ({ lat: c[1], lng: c[0] }));

        const legs = (route.legs || []).map((leg, idx) => ({
          from_place: waypoints[idx]?.name || 'Origin',
          to_place: waypoints[idx + 1]?.name || 'Destination',
          distance_km: Number((leg.distance / 1000).toFixed(1)),
          distance_text: `${(leg.distance / 1000).toFixed(1)} km`,
          duration_minutes: Math.max(1, Math.round(leg.duration / 60)),
          duration_text: `${Math.max(1, Math.round(leg.duration / 60))} min`,
          polyline_geojson: {
            type: 'LineString',
            coordinates: coords
          },
          steps: (leg.steps || []).map(s => ({
            instructions: s.maneuver?.type ? `${s.maneuver.type} on ${s.name || 'road'}` : s.name,
            distance: `${Math.round(s.distance)} m`,
            duration: `${Math.round(s.duration)} s`
          }))
        }));

        if (isMounted) {
          setRealRoadData({
            path,
            legs,
            total_distance_km: Number((route.distance / 1000).toFixed(1)),
            total_duration_minutes: Math.max(1, Math.round(route.duration / 60))
          });
        }
      } catch (err) {
        console.warn('[GoogleMapsRouteView] Road routing note:', err);
      }
    }

    fetchRoadRoute();
    return () => { isMounted = false; };
  }, [stops, mode, routeFromUser, userLocation, activeUserRouteStop]);

  // Calculated route metrics with authentic road polyline
  const osmRouteData = useMemo(() => {
    if (realRoadData && realRoadData.legs && realRoadData.legs.length > 0) {
      return realRoadData;
    }

    const roadFactor = mode === 'walking' ? 1.25 : 1.35;
    const speed = mode === 'walking' ? 4.5 : 24.0;

    // Initial placeholder while road routing completes
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
  }, [realRoadData, stops, mode, routeFromUser, userLocation, activeUserRouteStop]);

  // Clean visual markers and polyline
  const clearFallbackElements = () => {
    if (markersRef.current && markersRef.current.length > 0) {
      markersRef.current.forEach(m => {
        try { m.setMap(null); } catch (e) {}
      });
      markersRef.current = [];
    }
    if (fallbackPolylineRef.current) {
      try { fallbackPolylineRef.current.setMap(null); } catch (e) {}
      fallbackPolylineRef.current = null;
    }
  };

  // Synchronize route metrics in OpenStreetMap mode
  useEffect(() => {
    if (useFallbackMap && onRouteComputed && osmRouteData) {
      onRouteComputed(osmRouteData);
    }
  }, [useFallbackMap, osmRouteData, onRouteComputed]);

  // 1. Dynamic Google Maps JavaScript API Script Loader (Unconditionally loads Google Maps)
  useEffect(() => {
    if (useFallbackMap) return;

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
    script.src = apiKey && apiKey.trim()
      ? `https://maps.googleapis.com/maps/api/js?key=${apiKey.trim()}&libraries=places,geometry`
      : `https://maps.googleapis.com/maps/api/js?libraries=places,geometry`;
    script.async = true;
    script.defer = true;

    script.onload = () => {
      setScriptLoaded(true);
      setScriptError(null);
    };

    script.onerror = () => {
      setScriptError('Could not load Google Maps JavaScript API. Switch to OpenStreetMap if offline.');
      setScriptLoaded(false);
    };

    document.head.appendChild(script);
  }, [apiKey, useFallbackMap]);

  // 2. Initialize Google Map Instance
  useEffect(() => {
    if (!scriptLoaded || !mapContainerRef.current || !window.google?.maps || useFallbackMap) return;

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
          strokeColor: mode === 'walking' ? '#7c3aed' : '#e0533c',
          strokeWeight: 5,
          strokeOpacity: 0.85
        }
      });

      trafficLayerRef.current = new window.google.maps.TrafficLayer();
      mapInstanceRef.current = map;
    }
  }, [scriptLoaded, useFallbackMap]);

  // 2b. Map Resize Observer for responsive splitter dragging & window resize
  useEffect(() => {
    if (!mapContainerRef.current) return;
    const ro = new ResizeObserver(() => {
      if (mapInstanceRef.current && window.google?.maps) {
        window.google.maps.event.trigger(mapInstanceRef.current, 'resize');
      }
    });
    ro.observe(mapContainerRef.current);
    return () => ro.disconnect();
  }, [scriptLoaded]);

  // 3. Traffic Layer Toggle
  useEffect(() => {
    if (!trafficLayerRef.current || !mapInstanceRef.current) return;
    trafficLayerRef.current.setMap(showTraffic ? mapInstanceRef.current : null);
  }, [showTraffic]);

  // 3b. Render User Current Location Pin on Google Map
  useEffect(() => {
    if (!mapInstanceRef.current || !window.google?.maps || useFallbackMap) return;

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
          fillColor: '#2563eb',
          fillOpacity: 1,
          strokeColor: '#ffffff',
          strokeWeight: 3
        }
      });
    }
  }, [userLocation, scriptLoaded, useFallbackMap]);

  // 4. Calculate Preferred Route via Google DirectionsService or Draw Visual Waypoints on Google Maps
  useEffect(() => {
    if (!scriptLoaded || !mapInstanceRef.current || !window.google?.maps || useFallbackMap) return;

    const validStops = stops.filter(s => s && s.coordinates && typeof s.coordinates.lat === 'number');

    const drawFallbackVisualRoute = () => {
      clearFallbackElements();
      if (!mapInstanceRef.current || !window.google?.maps) return;

      const bounds = new window.google.maps.LatLngBounds();
      const path = [];

      if (routeFromUser && userLocation && activeUserRouteStop?.coordinates) {
        const uPos = { lat: userLocation.lat, lng: userLocation.lng };
        const dPos = { lat: activeUserRouteStop.coordinates.lat, lng: activeUserRouteStop.coordinates.lng };
        path.push(uPos, dPos);
        bounds.extend(uPos);
        bounds.extend(dPos);

        const destMarker = new window.google.maps.Marker({
          position: dPos,
          map: mapInstanceRef.current,
          title: activeUserRouteStop.name,
          icon: {
            path: window.google.maps.SymbolPath.CIRCLE,
            scale: 12,
            fillColor: '#e0533c',
            fillOpacity: 1,
            strokeColor: '#ffffff',
            strokeWeight: 2.5
          }
        });
        markersRef.current.push(destMarker);
      } else {
        validStops.forEach((stop, idx) => {
          const pos = { lat: stop.coordinates.lat, lng: stop.coordinates.lng };
          path.push(pos);
          bounds.extend(pos);

          const marker = new window.google.maps.Marker({
            position: pos,
            map: mapInstanceRef.current,
            title: stop.name,
            label: {
              text: String(idx + 1),
              color: '#ffffff',
              fontWeight: 'bold',
              fontSize: '11px'
            },
            icon: {
              path: window.google.maps.SymbolPath.CIRCLE,
              scale: 13,
              fillColor: '#e0533c',
              fillOpacity: 1,
              strokeColor: '#ffffff',
              strokeWeight: 2.5
            }
          });

          const infoWindow = new window.google.maps.InfoWindow({
            content: `<div style="font-family:sans-serif;padding:4px;color:#0f172a;">
              <b style="font-size:13px;">${idx + 1}. ${stop.name}</b>
              ${stop.timeTag ? `<p style="margin:2px 0 0;font-size:11px;color:#64748b;">⏰ ${stop.timeTag}</p>` : ''}
            </div>`
          });

          marker.addListener('click', () => {
            infoWindow.open(mapInstanceRef.current, marker);
            setActiveStopIdx(idx);
            if (onSelectStop) onSelectStop(idx);
          });

          markersRef.current.push(marker);
        });
      }

      // Use authentic turn-by-turn road geometry if resolved, otherwise direct path
      const activePath = (realRoadData?.path && realRoadData.path.length > 1) 
        ? realRoadData.path 
        : path;

      if (activePath.length > 1) {
        fallbackPolylineRef.current = new window.google.maps.Polyline({
          path: activePath,
          geodesic: true,
          strokeColor: mode === 'walking' ? '#7c3aed' : (routeFromUser ? '#2563eb' : '#e0533c'),
          strokeOpacity: 0.85,
          strokeWeight: 5,
          map: mapInstanceRef.current
        });
      }

      if (path.length > 1) {
        mapInstanceRef.current.fitBounds(bounds, { top: 50, right: 50, bottom: 50, left: 50 });
      } else if (path.length === 1) {
        mapInstanceRef.current.setCenter(path[0]);
        mapInstanceRef.current.setZoom(15);
      }

      if (onRouteComputed && osmRouteData) {
        onRouteComputed(osmRouteData);
      }
    };

    // A) If routing directly from User's Current Location to a selected destination
    if (routeFromUser && userLocation && activeUserRouteStop?.coordinates) {
      if (!directionsServiceRef.current || !directionsRendererRef.current) {
        drawFallbackVisualRoute();
        return;
      }

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
          strokeColor: '#2563eb',
          strokeWeight: 6,
          strokeOpacity: 0.9
        }
      });

      directionsServiceRef.current.route(
        { origin, destination, travelMode },
        (result, status) => {
          setRouteLoading(false);
          if (status === window.google.maps.DirectionsStatus.OK && result) {
            clearFallbackElements();
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
            if (directionsRendererRef.current) {
              directionsRendererRef.current.setDirections({ routes: [] });
            }
            drawFallbackVisualRoute();
          }
        }
      );
      return;
    }

    // B) Standard Day Itinerary Sequence Routing
    if (validStops.length === 0) {
      clearFallbackElements();
      if (directionsRendererRef.current) directionsRendererRef.current.setDirections({ routes: [] });
      if (mapInstanceRef.current) mapInstanceRef.current.setCenter(defaultCenter);
      return;
    }

    if (validStops.length === 1) {
      clearFallbackElements();
      const singlePos = { lat: validStops[0].coordinates.lat, lng: validStops[0].coordinates.lng };
      if (mapInstanceRef.current) {
        mapInstanceRef.current.setCenter(singlePos);
        mapInstanceRef.current.setZoom(15);
      }
      if (directionsRendererRef.current) directionsRendererRef.current.setDirections({ routes: [] });
      drawFallbackVisualRoute();
      return;
    }

    if (!directionsServiceRef.current || !directionsRendererRef.current) {
      drawFallbackVisualRoute();
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
        strokeColor: mode === 'walking' ? '#7c3aed' : '#e0533c',
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
          clearFallbackElements();
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
          // If Google Directions returns an error, draw visual route directly on Google Map
          if (directionsRendererRef.current) {
            directionsRendererRef.current.setDirections({ routes: [] });
          }
          drawFallbackVisualRoute();
        }
      }
    );
  }, [scriptLoaded, stops, mode, useFallbackMap, routeFromUser, userLocation, activeUserRouteStop, apiKey, realRoadData]);

  // Live update fallback polyline when real road geometry finishes loading
  useEffect(() => {
    if (!realRoadData || !mapInstanceRef.current || useFallbackMap) return;
    if (fallbackPolylineRef.current && realRoadData.path && realRoadData.path.length > 1) {
      fallbackPolylineRef.current.setPath(realRoadData.path);
    }
    if (onRouteComputed && realRoadData) {
      onRouteComputed(realRoadData);
    }
  }, [realRoadData, useFallbackMap]);

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

  const targetStop = (stops && stops[activeStopIdx]) || (stops && stops[0]) || null;

  const handleNavigateFromCurrentLocation = (destStop = null, isFullRoute = false) => {
    const chosenStop = destStop || targetStop;
    const travelModeParam = mode === 'walking' ? 'walking' : 'driving';

    const launchUrl = (userCoords) => {
      let url = 'https://www.google.com/maps/dir/?api=1';

      if (userCoords?.lat && userCoords?.lng) {
        url += `&origin=${encodeURIComponent(`${userCoords.lat},${userCoords.lng}`)}`;
      }

      if (isFullRoute && stops.length > 1) {
        const finalStop = stops[stops.length - 1];
        const intermediateWaypoints = stops.slice(0, stops.length - 1)
          .map(s => (s.coordinates ? `${s.coordinates.lat},${s.coordinates.lng}` : null))
          .filter(Boolean)
          .join('|');

        if (finalStop?.coordinates) {
          url += `&destination=${encodeURIComponent(`${finalStop.coordinates.lat},${finalStop.coordinates.lng}`)}`;
        }
        if (intermediateWaypoints) {
          url += `&waypoints=${encodeURIComponent(intermediateWaypoints)}`;
        }
      } else if (chosenStop?.coordinates) {
        url += `&destination=${encodeURIComponent(`${chosenStop.coordinates.lat},${chosenStop.coordinates.lng}`)}`;
      } else if (chosenStop?.name) {
        url += `&destination=${encodeURIComponent(chosenStop.name)}`;
      } else {
        url += `&destination=${encodeURIComponent(`${defaultCenter.lat},${defaultCenter.lng}`)}`;
      }

      url += `&travelmode=${travelModeParam}`;
      window.open(url, '_blank', 'noopener,noreferrer');
    };

    if (internalUserLocation?.lat && internalUserLocation?.lng) {
      launchUrl(internalUserLocation);
      return;
    }

    if (!navigator.geolocation) {
      launchUrl(null);
      return;
    }

    setIsLocating(true);
    setLocStatus('Getting GPS position...');

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setIsLocating(false);
        const coords = {
          lat: Number(pos.coords.latitude.toFixed(6)),
          lng: Number(pos.coords.longitude.toFixed(6)),
          accuracy: pos.coords.accuracy,
          isLive: true
        };
        setInternalUserLocation(coords);
        setLocStatus('GPS Acquired! Opening Google Maps...');
        setTimeout(() => setLocStatus(''), 2500);

        if (mapInstanceRef.current && window.google?.maps) {
          if (userMarkerRef.current) {
            userMarkerRef.current.setPosition({ lat: coords.lat, lng: coords.lng });
          } else {
            userMarkerRef.current = new window.google.maps.Marker({
              position: { lat: coords.lat, lng: coords.lng },
              map: mapInstanceRef.current,
              title: 'Your Current Location',
              zIndex: 9999,
              icon: {
                path: window.google.maps.SymbolPath.CIRCLE,
                scale: 9,
                fillColor: '#2563eb',
                fillOpacity: 1,
                strokeColor: '#ffffff',
                strokeWeight: 3
              }
            });
          }
        }

        launchUrl(coords);
      },
      (err) => {
        console.warn('[GoogleMapsRouteView] Geolocation error/fallback:', err?.message);
        setIsLocating(false);
        setLocStatus('Opening Google Maps with device GPS...');
        setTimeout(() => setLocStatus(''), 3000);
        launchUrl(null);
      },
      { enableHighAccuracy: true, timeout: 8000, maximumAge: 60000 }
    );
  };

  const renderGoogleMapsNavigationButton = () => (
    <div className="absolute bottom-4 right-4 z-20 flex flex-col items-end gap-2 font-sans select-none">
      {/* Destination Popover Menu */}
      {showDestPicker && (
        <div className="w-72 sm:w-80 bg-white/98 backdrop-blur-md border border-slate-200/90 rounded-2xl shadow-2xl p-3 animate-fadeIn flex flex-col gap-2 text-slate-900 mb-1">
          <div className="flex items-center justify-between pb-1.5 border-b border-slate-100">
            <div className="flex items-center gap-1.5 text-xs font-bold font-sans text-slate-900">
              <Navigation className="w-3.5 h-3.5 text-blue-600" />
              <span>Choose Destination from Current Location</span>
            </div>
            <button
              onClick={() => setShowDestPicker(false)}
              className="text-slate-400 hover:text-slate-600 p-0.5 rounded cursor-pointer"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>

          <p className="text-[11px] text-slate-500 font-medium">
            Opens Google Maps turn-by-turn navigation starting from your current GPS location:
          </p>

          <div className="max-h-52 overflow-y-auto space-y-1 pr-0.5">
            {stops.map((stop, idx) => {
              const isSelected = activeStopIdx === idx;
              return (
                <button
                  key={stop.order || idx}
                  onClick={() => {
                    setActiveStopIdx(idx);
                    if (onSelectStop) onSelectStop(idx);
                    setShowDestPicker(false);
                    handleNavigateFromCurrentLocation(stop, false);
                  }}
                  className={`w-full flex items-center justify-between p-2 rounded-xl text-left text-xs transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-amber-50 border border-amber-300 text-amber-950 font-bold'
                      : 'bg-slate-50 hover:bg-slate-100 border border-slate-200/60 text-slate-700'
                  }`}
                >
                  <div className="flex items-center gap-2 min-w-0 pr-1">
                    <span className={`w-5 h-5 rounded-md flex items-center justify-center text-[10px] font-bold shrink-0 ${
                      isSelected ? 'bg-slate-950 text-[#FCD34D]' : 'bg-slate-200 text-slate-700'
                    }`}>
                      {idx + 1}
                    </span>
                    <div className="truncate">
                      <div className="text-xs truncate font-medium">{stop.name}</div>
                      {stop.timeTag && (
                        <div className="text-[10px] text-slate-400">{stop.timeTag}</div>
                      )}
                    </div>
                  </div>
                  <ExternalLink className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                </button>
              );
            })}

            {stops.length > 1 && (
              <button
                onClick={() => {
                  setShowDestPicker(false);
                  handleNavigateFromCurrentLocation(null, true);
                }}
                className="w-full flex items-center justify-between p-2 rounded-xl bg-amber-100/70 hover:bg-amber-200/70 border border-amber-300 text-slate-900 font-bold text-xs transition-all cursor-pointer mt-1.5"
              >
                <div className="flex items-center gap-2">
                  <span className="w-5 h-5 rounded-md bg-slate-900 text-[#FCD34D] flex items-center justify-center text-[10px] font-bold">
                    🗺️
                  </span>
                  <span>Full Day Tour ({stops.length} Stops)</span>
                </div>
                <ExternalLink className="w-3.5 h-3.5 text-slate-800" />
              </button>
            )}
          </div>
        </div>
      )}

      {/* Real-time Status Toast */}
      {locStatus && (
        <div className="bg-slate-900/95 backdrop-blur-md px-3.5 py-1.5 rounded-xl text-white text-[11px] font-medium flex items-center gap-2 shadow-xl border border-white/10 animate-fadeIn">
          {isLocating && <Loader2 className="w-3.5 h-3.5 animate-spin text-amber-300" />}
          <span>{locStatus}</span>
        </div>
      )}

      {/* Main Floating Action Button */}
      <div className="flex items-stretch rounded-2xl shadow-2xl border border-slate-750/90 overflow-hidden bg-slate-950 text-white group hover:border-[#FCD34D]/60 transition-colors">
        <button
          onClick={() => handleNavigateFromCurrentLocation(targetStop, false)}
          disabled={isLocating}
          className="px-3.5 py-2.5 flex items-center gap-2.5 hover:bg-slate-850 active:bg-slate-900 transition-all cursor-pointer text-left"
          title={`Launch Google Maps from your current location to ${targetStop?.name || 'destination'}`}
        >
          <div className="w-8 h-8 rounded-xl bg-[#FCD34D] text-slate-950 flex items-center justify-center shrink-0 shadow-sm group-hover:scale-105 transition-transform">
            {isLocating ? (
              <Loader2 className="w-4 h-4 animate-spin text-slate-950" />
            ) : (
              <Navigation className="w-4 h-4 text-slate-950 fill-slate-950" />
            )}
          </div>

          <div className="flex flex-col">
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-extrabold text-white tracking-tight leading-tight font-sans">
                Take to Google Maps
              </span>
              <ExternalLink className="w-3 h-3 text-[#FCD34D]" />
            </div>
            <div className="text-[10px] text-slate-300 font-medium leading-tight truncate max-w-[170px] sm:max-w-[220px]">
              {isLocating
                ? 'Acquiring GPS...'
                : targetStop?.name 
                  ? `From My Location → ${targetStop.name}` 
                  : 'From your current location'}
            </div>
          </div>
        </button>

        {stops.length > 0 && (
          <button
            onClick={() => setShowDestPicker(prev => !prev)}
            className="px-2 border-l border-slate-800 hover:bg-slate-800/80 active:bg-slate-900 text-slate-300 hover:text-[#FCD34D] transition-all cursor-pointer flex items-center justify-center"
            title="Pick a stop or navigate full itinerary"
          >
            <ChevronUp className={`w-4 h-4 transition-transform duration-200 ${showDestPicker ? 'rotate-180 text-[#FCD34D]' : ''}`} />
          </button>
        )}
      </div>
    </div>
  );

  // =========================================================================
  // CASE 1: OpenStreetMap Engine (ONLY when explicitly chosen)
  // =========================================================================
  if (useFallbackMap) {
    return (
      <div className="relative w-full h-full flex flex-col rounded-2xl overflow-hidden border border-slate-200 shadow-md">
        {/* Top Control Ribbon */}
        <div className="px-3.5 py-2 bg-white/95 backdrop-blur-md border-b border-slate-200 flex flex-wrap items-center justify-between gap-2 z-10 shrink-0">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shrink-0" />
            <span className="text-xs font-bold text-slate-800 font-sans">
              OpenStreetMap Engine
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setUseFallbackMap(false)}
              className="px-2.5 py-1 rounded-lg bg-terracotta hover:bg-terracotta/90 text-white text-[11px] font-bold font-sans transition-all cursor-pointer flex items-center gap-1 shadow-2xs"
            >
              <span>Back to Google Maps</span>
            </button>
          </div>
        </div>

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

        {/* Floating Google Maps Navigation from Current Location Action Button */}
        {renderGoogleMapsNavigationButton()}
      </div>
    );
  }

  // =========================================================================
  // CASE 2: Official Google Maps JavaScript API Engine (DEFAULT)
  // =========================================================================
  return (
    <div className="relative w-full h-full flex flex-col rounded-2xl overflow-hidden border border-slate-200 shadow-md">
      {/* Top Engine Ribbon */}
      <div className="px-3.5 py-2 bg-white/95 backdrop-blur-md border-b border-slate-200 flex flex-wrap items-center justify-between gap-2 z-10 shrink-0">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-blue-600 animate-pulse shrink-0" />
          <span className="text-xs font-bold text-slate-800 font-sans">
            Google Maps Route Navigator
          </span>
          <span className="px-2 py-0.5 rounded-full bg-blue-50 border border-blue-200 text-blue-800 text-[10px] font-bold uppercase tracking-wider font-sans">
            Google Maps Active
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowKeyInput(prev => !prev)}
            className="px-2.5 py-1 rounded-lg bg-amber-50 hover:bg-amber-100 text-amber-900 border border-amber-300 text-[11px] font-bold font-sans transition-all cursor-pointer flex items-center gap-1"
            title="Configure optional personal Google Maps API key"
          >
            <Key className="w-3 h-3 text-amber-700" />
            <span>{showKeyInput ? 'Hide Key' : 'API Key'}</span>
          </button>
          <button
            onClick={() => setUseFallbackMap(true)}
            className="px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-[11px] font-bold font-sans transition-all cursor-pointer flex items-center gap-1 border border-slate-200"
            title="Switch to OpenStreetMap"
          >
            <Compass className="w-3 h-3 text-emerald-600" />
            <span>OpenStreetMap</span>
          </button>
        </div>
      </div>

      {/* Expandable Key Input Dropdown */}
      {showKeyInput && (
        <div className="p-3 bg-amber-50/95 border-b border-amber-200 z-10 shrink-0 text-xs animate-fadeIn">
          <form onSubmit={handleSaveUserKey} className="flex items-center gap-2">
            <input
              type="text"
              value={keyInput}
              onChange={(e) => setKeyInput(e.target.value)}
              placeholder="Paste Google Maps API Key to enable official turn-by-turn routing"
              className="flex-1 px-3 py-1.5 rounded-lg bg-white border border-amber-300 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-amber-400"
            />
            <button
              type="submit"
              className="px-3 py-1.5 rounded-lg bg-terracotta hover:bg-terracotta/90 text-white font-bold text-xs font-sans cursor-pointer shrink-0 shadow-2xs"
            >
              Apply Key
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

      {/* Route Loading Indicator */}
      {routeLoading && (
        <div className="absolute top-12 left-1/2 -translate-x-1/2 z-10 bg-slate-900/80 backdrop-blur-md px-3.5 py-1.5 rounded-full text-white text-xs font-medium flex items-center gap-2 shadow-lg border border-white/20">
          <Loader2 className="w-3.5 h-3.5 animate-spin text-amber-300" />
          <span>Updating route on Google Maps...</span>
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
        <div className="flex items-center gap-2 font-bold text-slate-900 font-sans text-[11px]">
          <Navigation className="w-3.5 h-3.5 text-blue-600" />
          <span>Google Maps Route Navigator</span>
        </div>
        <div className="flex items-center gap-2 text-slate-600 text-[11px]">
          <span className={`w-3.5 h-1 rounded-full ${mode === 'walking' ? 'bg-purple-600' : 'bg-terracotta'}`} />
          <span>{mode === 'walking' ? 'Walking Route (Pedestrian)' : 'Driving Route (Road Network)'}</span>
        </div>
        {showTraffic && (
          <div className="flex items-center gap-1.5 text-emerald-700 text-[10px] font-semibold">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span>Live Traffic Layer Active</span>
          </div>
        )}
      </div>

      {/* Floating Google Maps Navigation from Current Location Action Button */}
      {renderGoogleMapsNavigationButton()}
    </div>
  );
}
