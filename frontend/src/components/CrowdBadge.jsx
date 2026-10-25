import React, { useState, useEffect, useRef } from 'react';
import { Users, Info, X, Clock, AlertTriangle, TrendingUp, Sparkles, ShieldAlert, MapPin, Zap, Database } from 'lucide-react';
import { VoyantraAPI } from '../services/api';
import { CrowdReportModal } from './CrowdReportModal';

export function CrowdBadge({ placeId, placeName, cityId = 'pondicherry', tendency = 'medium', className = '' }) {
  const [showPopover, setShowPopover] = useState(false);
  const [crowdData, setCrowdData] = useState(null);
  const [liveStatus, setLiveStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showReportModal, setShowReportModal] = useState(false);

  const popoverRef = useRef(null);
  const level = tendency.toLowerCase();

  const fetchAnalytics = async () => {
    if (!placeId) return;
    setLoading(true);
    try {
      const [estRes, liveRes] = await Promise.all([
        VoyantraAPI.getPlaceCrowdEstimate(placeId, cityId),
        VoyantraAPI.getLiveCrowdStatus(placeId, cityId)
      ]);
      if (estRes) setCrowdData(estRes);
      if (liveRes) setLiveStatus(liveRes);
    } catch (e) {
      console.error('Error fetching crowd analytics:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = (e) => {
    e.stopPropagation();
    if (!showPopover && !crowdData) {
      fetchAnalytics();
    }
    setShowPopover(!showPopover);
  };

  // Close popover when clicking outside or pressing Escape
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (popoverRef.current && !popoverRef.current.contains(event.target)) {
        setShowPopover(false);
      }
    };
    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        setShowPopover(false);
      }
    };

    if (showPopover) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [showPopover]);

  let badgeColor = "bg-amber-500/10 text-amber-800 border-amber-500/20";
  let dotColor = "bg-amber-500";
  let labelText = "Moderate Crowd";

  if (level === 'low') {
    badgeColor = "bg-emerald-500/10 text-emerald-800 border-emerald-500/20";
    dotColor = "bg-emerald-500 animate-pulse";
    labelText = "Serene / Low Crowd";
  } else if (level === 'high') {
    badgeColor = "bg-rose-500/10 text-rose-800 border-rose-500/20";
    dotColor = "bg-rose-500 animate-pulse";
    labelText = "Bustling / High Footfall";
  } else if (level === 'peak') {
    badgeColor = "bg-purple-500/15 text-purple-900 border-purple-500/30";
    dotColor = "bg-purple-600 animate-ping";
    labelText = "Peak Festival Surge";
  }

  // Real-time confidence badge color
  const getConfidenceStyle = (confidence) => {
    if (confidence === 'HIGH') return 'bg-emerald-100 text-emerald-800 border-emerald-300';
    if (confidence === 'MEDIUM') return 'bg-amber-100 text-amber-800 border-amber-300';
    return 'bg-slate-100 text-slate-700 border-slate-200';
  };

  const isChennai = cityId?.toLowerCase().includes('chennai');
  const provenanceText = isChennai
    ? 'Seasonality: Tamil Nadu Tourism Dept (2022–2024 District 3302 Records)'
    : 'Seasonality: MoT 2014 survey data, rough prior';

  return (
    <>
      <div className="relative inline-block" ref={popoverRef}>
        <button
          onClick={handleToggle}
          title="Click for Real-Time & Historical Crowd Analytics"
          className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border backdrop-blur-xs hover:scale-105 transition-all cursor-pointer ${badgeColor} ${className}`}
        >
          <span className={`w-2 h-2 rounded-full ${dotColor}`} />
          <span>{labelText}</span>
          <Info className="w-3 h-3 opacity-60 ml-0.5" />
        </button>

        {/* Interactive Crowd Analytics & Live Crowdsourcing Popover */}
        {showPopover && (
          <div 
            onClick={(e) => e.stopPropagation()}
            className="absolute left-0 bottom-full mb-2 z-[70] w-80 sm:w-88 p-4 rounded-3xl bg-white border border-slate-200 shadow-2xl space-y-3 animate-fadeIn text-left text-slate-800"
          >
            {/* Header */}
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <div className="flex items-center gap-1.5 font-bold text-xs text-slate-900">
                <Users className="w-4 h-4 text-brand-600" />
                <span>Crowd Density Intelligence</span>
              </div>
              <button 
                onClick={() => setShowPopover(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>

            {loading ? (
              <div className="text-center py-4 space-y-1">
                <div className="w-5 h-5 mx-auto border-2 border-brand-500 border-t-transparent rounded-full animate-spin"></div>
                <p className="text-[11px] text-slate-400">Computing live footfall & historical patterns...</p>
              </div>
            ) : (
              <div className="space-y-3 text-xs">
                {/* Live Footfall Badge & Surge Alert (Phase 5) */}
                {liveStatus && (
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
                        <span className="font-extrabold text-[11px] text-slate-800 uppercase tracking-wide">
                          Live Blended Status
                        </span>
                      </div>
                      <span 
                        title={liveStatus.confidence_badge}
                        className={`text-[10px] font-extrabold px-2 py-0.5 rounded-full border ${getConfidenceStyle(liveStatus.confidence_level || 'LOW')}`}
                      >
                        {liveStatus.confidence_level || 'LOW'} CONFIDENCE
                      </span>
                    </div>

                    {/* Surge Anomaly Banner */}
                    {liveStatus.is_surge && (
                      <div className="p-2 rounded-2xl bg-rose-50 border border-rose-300 text-rose-900 text-[11px] font-medium flex items-start gap-1.5 animate-pulse">
                        <Zap className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                        <div>
                          <span className="font-extrabold text-rose-800">Unusual Live Surge: </span>
                          <span>{liveStatus.anomaly_alert || 'Human reports show sharp increase over expected baseline!'}</span>
                        </div>
                      </div>
                    )}

                    {liveStatus.active_reports_count > 0 && (
                      <div className="text-[10px] text-slate-500 flex items-center justify-between bg-slate-50 px-2 py-1 rounded-xl">
                        <span>👥 {liveStatus.active_reports_count} verified {liveStatus.active_reports_count === 1 ? 'report' : 'reports'}</span>
                        <span className="font-bold text-brand-600">Blended: {liveStatus.blended_density_pct}%</span>
                      </div>
                    )}

                    {liveStatus.last_reported_time && (
                      <div className="text-[9px] text-slate-400 text-right pr-1">
                        Latest report at {liveStatus.last_reported_time}
                      </div>
                    )}
                  </div>
                )}

                {/* Density Progress Bar */}
                {crowdData && (
                  <div className="space-y-1">
                    <div className="flex items-center justify-between text-[11px] font-bold">
                      <span className="text-slate-600">Density Index:</span>
                      <span className="text-brand-800 font-extrabold">
                        {liveStatus && liveStatus.active_reports_count > 0 ? liveStatus.blended_density_pct : crowdData.crowd_density_pct}% Capacity
                      </span>
                    </div>
                    <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden border border-slate-200">
                      <div 
                        className={`h-full rounded-full transition-all duration-500 ${
                          (liveStatus?.blended_density_pct || crowdData.crowd_density_pct) > 75 
                            ? 'bg-gradient-to-r from-rose-500 to-purple-600' 
                            : (liveStatus?.blended_density_pct || crowdData.crowd_density_pct) > 50 
                            ? 'bg-gradient-to-r from-amber-400 to-rose-400' 
                            : 'bg-gradient-to-r from-emerald-400 to-teal-500'
                        }`}
                        style={{ width: `${liveStatus?.blended_density_pct || crowdData.crowd_density_pct}%` }}
                      />
                    </div>
                  </div>
                )}

                {/* 1-Tap Footfall Report Button */}
                {placeId && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setShowReportModal(true);
                    }}
                    className="w-full py-2 px-3 rounded-2xl bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-700 hover:to-indigo-700 text-white font-bold text-xs shadow-xs hover:shadow-md transition-all flex items-center justify-center gap-1.5 cursor-pointer"
                  >
                    <MapPin className="w-3.5 h-3.5" />
                    <span>Report Live Footfall (On-Site)</span>
                  </button>
                )}

                {/* Quiet Visiting Window */}
                {crowdData?.quiet_window && (
                  <div className="p-2 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-900 text-[11px] font-bold flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                    <span>Best Visiting Window: {crowdData.quiet_window}</span>
                  </div>
                )}

                {/* Festival Warning Alert */}
                {crowdData?.festival_alert && (
                  <div className="p-2 rounded-xl bg-amber-50 border border-amber-300 text-amber-950 text-[11px] font-medium space-y-0.5">
                    <div className="flex items-center gap-1 text-amber-900 font-extrabold">
                      <ShieldAlert className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                      <span>{crowdData.festival_alert.name}</span>
                    </div>
                    <p className="text-[10px] text-amber-900/90 leading-tight">
                      {crowdData.festival_alert.advisory_level}
                    </p>
                  </div>
                )}

                {/* Drivers Breakdown */}
                {crowdData?.drivers && crowdData.drivers.length > 0 && (
                  <div className="space-y-1">
                    <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Crowd Drivers:</div>
                    <ul className="list-disc list-inside text-[11px] text-slate-600 space-y-0.5">
                      {crowdData.drivers.map((d, i) => (
                        <li key={i} className="line-clamp-1">{d}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Hourly Trend Bar Chart */}
                {crowdData?.hourly_curve && (
                  <div className="space-y-1.5 pt-1">
                    <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center justify-between">
                      <span>Hourly Crowd Curve (6 AM - 10 PM):</span>
                    </div>
                    <div className="flex items-end gap-1 h-12 pt-2 border-b border-slate-100">
                      {crowdData.hourly_curve.filter(h => h.hour % 2 === 0).map((h, i) => (
                        <div key={i} className="flex-1 flex flex-col items-center gap-1 group/bar">
                          <div 
                            title={`${h.time_label}: ${h.density_pct}% crowd`}
                            className={`w-full rounded-t transition-all ${
                              h.density_pct > 75 ? 'bg-rose-500' : h.density_pct > 50 ? 'bg-amber-400' : 'bg-emerald-400'
                            }`}
                            style={{ height: `${(h.density_pct / 100) * 36}px` }}
                          />
                          <span className="text-[8px] text-slate-400 font-mono">{h.hour}h</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Phase 6: Provenance Footer */}
                <div className="pt-2 border-t border-slate-100 flex items-center gap-1.5 text-[10px] text-slate-400">
                  <Database className="w-3 h-3 text-slate-400 shrink-0" />
                  <span className="leading-tight">{provenanceText}</span>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Geofenced Footfall Reporting Modal */}
      {showReportModal && (
        <CrowdReportModal
          placeId={placeId}
          placeName={placeName}
          cityId={cityId}
          isOpen={showReportModal}
          onClose={() => setShowReportModal(false)}
          onSuccess={() => {
            fetchAnalytics();
          }}
        />
      )}
    </>
  );
}
