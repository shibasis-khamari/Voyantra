import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import { DEFAULT_COORDINATES } from '../types/constants';

// Fix default leaflet icons in Vite
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Custom Category Markers
const createCustomIcon = (category) => {
  let color = '#0d9488'; // teal default
  if (category === 'heritage') color = '#ca8a04';
  if (category === 'spiritual') color = '#9333ea';
  if (category === 'food' || category === 'cafe') color = '#ea580c';

  return L.divIcon({
    className: 'custom-leaflet-marker',
    html: `
      <div style="
        background-color: ${color};
        width: 28px;
        height: 28px;
        border-radius: 50% 50% 50% 0;
        transform: rotate(-45deg);
        border: 2px solid white;
        box-shadow: 0 3px 8px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
      ">
        <div style="
          width: 8px;
          height: 8px;
          background: white;
          border-radius: 50%;
        "></div>
      </div>
    `,
    iconSize: [28, 28],
    iconAnchor: [14, 28],
    popupAnchor: [0, -28],
  });
};

export function MapView({ 
  places = [], 
  selectedPlace = null, 
  onSelectPlace = null, 
  height = '420px',
  routeLegs = [],
  transitMode = 'driving'
}) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersRef = useRef([]);
  const polylinesRef = useRef([]);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      // Initialize map centered on Pondicherry
      const map = L.map(mapContainerRef.current).setView(
        [DEFAULT_COORDINATES.lat, DEFAULT_COORDINATES.lng],
        DEFAULT_COORDINATES.zoom
      );

      // OpenStreetMap Free Tile Layer with ODbL & OSRM / FOSSGIS Attribution
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap contributors (ODbL)</a> | Routing by &copy; <a href="https://routing.openstreetmap.de/about.html" target="_blank" rel="noreferrer">OSRM via FOSSGIS routing service</a>',
        maxZoom: 18,
      }).addTo(map);

      mapInstanceRef.current = map;
    }

    const map = mapInstanceRef.current;

    // Clear old markers
    markersRef.current.forEach(m => map.removeLayer(m));
    markersRef.current = [];

    // Add new place markers
    const group = [];
    places.forEach(p => {
      if (p.coordinates && p.coordinates.lat && p.coordinates.lng) {
        const marker = L.marker([p.coordinates.lat, p.coordinates.lng], {
          icon: createCustomIcon(p.category)
        }).addTo(map);

        const osrmUrl = `https://www.openstreetmap.org/directions?engine=fossgis_osrm_car&route=%3B${p.coordinates.lat}%2C${p.coordinates.lng}`;

        const popupContent = `
          <div style="font-family: 'Plus Jakarta Sans', sans-serif; min-width: 180px;">
            <div style="font-size: 10px; font-weight: bold; text-transform: uppercase; color: #0d9488; margin-bottom: 2px;">
              ${p.category}
            </div>
            <strong style="font-size: 14px; color: #0f172a; display: block; margin-bottom: 4px;">${p.name}</strong>
            <p style="font-size: 11px; color: #64748b; margin: 0 0 6px 0;">${p.sub_category || p.address}</p>
            <div style="display: flex; gap: 4px;">
              <a href="${osrmUrl}" target="_blank" rel="noopener noreferrer" style="
                display: inline-block;
                background: #0d9488;
                color: white;
                font-size: 11px;
                font-weight: 600;
                padding: 4px 8px;
                border-radius: 6px;
                text-decoration: none;
              ">
                OSRM Route ↗
              </a>
            </div>
          </div>
        `;

        marker.bindPopup(popupContent);
        marker.on('click', () => {
          if (onSelectPlace) onSelectPlace(p);
        });

        markersRef.current.push(marker);
        group.push([p.coordinates.lat, p.coordinates.lng]);
      }
    });

    // -------------------------------------------------------------------------
    // Render Turn-by-Turn Route Polylines (Phase 4: Navigation Overlay)
    // -------------------------------------------------------------------------
    polylinesRef.current.forEach(p => map.removeLayer(p));
    polylinesRef.current = [];

    if (routeLegs && routeLegs.length > 0) {
      routeLegs.forEach((leg, idx) => {
        const coords = leg.polyline_geojson?.coordinates;
        if (coords && coords.length > 0) {
          // GeoJSON is [lon, lat] -> Leaflet requires [lat, lon]
          const latLngs = coords.map(pt => [pt[1], pt[0]]);
          
          let color = '#0d9488'; // Brand teal for driving
          let dashArray = null;
          if (leg.closure_affected) {
            color = '#f59e0b'; // Amber warning for festival closure detours
          } else if (transitMode === 'walking') {
            color = '#8b5cf6'; // Violet dashed for walking
            dashArray = '6, 8';
          }

          const line = L.polyline(latLngs, {
            color,
            weight: 4,
            opacity: 0.85,
            dashArray
          }).addTo(map);

          line.bindPopup(`
            <div style="font-size: 12px; font-family: sans-serif;">
              <strong>Leg ${idx + 1}: ${leg.from_place} &rarr; ${leg.to_place}</strong><br/>
              Distance: ${leg.distance_km} km | Est. Travel: ~${leg.duration_minutes} min<br/>
              <span style="font-size: 10px; color: #64748b;">${leg.is_approximate ? '(Approximate travel time)' : 'Live network route'}</span>
              ${leg.closure_affected ? '<br/><span style="color: #b45309; font-weight: bold;">⚠️ Procession road closure detected</span>' : ''}
            </div>
          `);

          polylinesRef.current.push(line);
          latLngs.forEach(pt => group.push(pt));
        }
      });
    }

    if (group.length > 0) {
      map.fitBounds(group, { padding: [40, 40], maxZoom: 14 });
    }

    return () => {
      // Map cleanup on unmount
    };
  }, [places, routeLegs, transitMode]);

  // Pan to selected place
  useEffect(() => {
    if (selectedPlace && mapInstanceRef.current) {
      mapInstanceRef.current.setView(
        [selectedPlace.coordinates.lat, selectedPlace.coordinates.lng],
        15,
        { animate: true }
      );
    }
  }, [selectedPlace]);

  return (
    <div className="w-full rounded-2xl overflow-hidden shadow-md border border-slate-200 relative">
      <div ref={mapContainerRef} style={{ height }} className="w-full bg-slate-100" />
      {/* Map Legend */}
      <div className="absolute bottom-3 left-3 z-[400] bg-white/95 backdrop-blur-md p-2.5 rounded-xl border border-slate-200 shadow-md text-xs space-y-1">
        <div className="font-bold text-slate-800 text-[11px] mb-1">Voyantra Route & Pins</div>
        <div className="flex items-center gap-2 text-slate-600">
          <span className="w-4 h-1 bg-teal-600 rounded-full"></span> Driving Route (OSRM)
        </div>
        <div className="flex items-center gap-2 text-slate-600">
          <span className="w-4 h-1 border-t-2 border-dashed border-purple-600"></span> Walking Route (FOSSGIS)
        </div>
        <div className="flex items-center gap-2 text-slate-600">
          <span className="w-4 h-1 bg-amber-500 rounded-full"></span> Festival Closure Detour
        </div>
      </div>
    </div>
  );
}
