import React, { useState } from 'react';
import { createPortal } from 'react-dom';
import { X, MapPin, CheckCircle2, AlertTriangle, ShieldCheck, Users, Clock, Sparkles } from 'lucide-react';
import { VoyantraAPI } from '../services/api';

const CROWD_OPTIONS = [
  {
    level: 'serene',
    title: 'Serene / Peaceful',
    desc: 'Plenty of space, no queues (< 25% capacity)',
    color: 'border-emerald-500 bg-emerald-50 text-emerald-900',
    activeRing: 'ring-2 ring-emerald-500 bg-emerald-100/60',
    emoji: '🟢'
  },
  {
    level: 'moderate',
    title: 'Moderate Flow',
    desc: 'Normal activity, comfortable moving (~50% capacity)',
    color: 'border-amber-400 bg-amber-50 text-amber-900',
    activeRing: 'ring-2 ring-amber-500 bg-amber-100/60',
    emoji: '🟡'
  },
  {
    level: 'bustling',
    title: 'Bustling & Busy',
    desc: 'Crowded corridors, minor queues (~75% capacity)',
    color: 'border-orange-500 bg-orange-50 text-orange-900',
    activeRing: 'ring-2 ring-orange-500 bg-orange-100/60',
    emoji: '🔴'
  },
  {
    level: 'overcrowded',
    title: 'Peak Surge / Overcrowded',
    desc: 'Shoulder-to-shoulder, heavy wait times (> 90% capacity)',
    color: 'border-purple-500 bg-purple-50 text-purple-900',
    activeRing: 'ring-2 ring-purple-500 bg-purple-100/60',
    emoji: '🟣'
  }
];

export function CrowdReportModal({
  placeId,
  placeName = 'this location',
  cityId = 'pondicherry',
  isOpen,
  onClose,
  onSuccess
}) {
  const [selectedLevel, setSelectedLevel] = useState('moderate');
  const [waitTime, setWaitTime] = useState(0);
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [locating, setLocating] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg(null);
    setSuccessMsg(null);

    if (!navigator.geolocation) {
      setErrorMsg('Geolocation is not supported by your browser. Physical on-site presence (<= 200m) is required.');
      return;
    }

    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        setLocating(false);
        const { latitude, longitude } = pos.coords;

        setSubmitting(true);
        try {
          const payload = {
            place_id: placeId,
            city_id: cityId,
            crowd_level: selectedLevel,
            user_lat: latitude,
            user_lng: longitude
          };

          const res = await VoyantraAPI.submitCrowdReport(payload);
          setSuccessMsg(res.message || 'Report submitted! Thank you for contributing.');
          if (onSuccess) {
            onSuccess(res);
          }
          setTimeout(() => {
            onClose();
          }, 1800);
        } catch (err) {
          const raw = err.message || '';
          if (raw.includes('User is') && raw.includes('away')) {
            setErrorMsg(raw);
          } else if (raw.includes('Rate limit') || raw.includes('15 minutes')) {
            setErrorMsg('Cooldown active: You can only report once every 15 minutes for this venue.');
          } else {
            setErrorMsg(raw || 'Failed to submit report. Please try again.');
          }
        } finally {
          setSubmitting(false);
        }
      },
      (geoErr) => {
        setLocating(false);
        if (geoErr.code === geoErr.PERMISSION_DENIED) {
          setErrorMsg('Location access was denied. Please allow location access to verify you are on-site (within 200m).');
        } else {
          setErrorMsg('Unable to retrieve your physical location: ' + geoErr.message);
        }
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    );
  };

  return createPortal(
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-fadeIn">
      <div 
        className="relative w-full max-w-md bg-white rounded-3xl shadow-2xl border border-slate-100 overflow-hidden text-slate-800 transition-all"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="p-5 pb-4 bg-gradient-to-r from-brand-600 to-indigo-700 text-white">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="p-2 rounded-xl bg-white/10 backdrop-blur-xs">
                <Users className="w-5 h-5 text-white" />
              </span>
              <div>
                <h3 className="font-bold text-base leading-tight">Report Live Footfall</h3>
                <p className="text-xs text-white/80 line-clamp-1">{placeName}</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 rounded-full text-white/80 hover:text-white hover:bg-white/20 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="mt-3 flex items-center gap-1.5 text-[11px] text-white/90 bg-white/10 px-2.5 py-1.5 rounded-xl">
            <ShieldCheck className="w-4 h-4 text-emerald-300 shrink-0" />
            <span>Geofence verification active: Must be on-site (within 200m)</span>
          </div>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          {/* Level Picker */}
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-2">
              Current Crowd Sensation:
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {CROWD_OPTIONS.map((opt) => (
                <button
                  type="button"
                  key={opt.level}
                  onClick={() => setSelectedLevel(opt.level)}
                  className={`p-3 rounded-2xl border text-left transition-all flex flex-col justify-between ${opt.color} ${
                    selectedLevel === opt.level ? `${opt.activeRing} shadow-sm font-semibold` : 'opacity-85 hover:opacity-100'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold flex items-center gap-1.5">
                      <span>{opt.emoji}</span>
                      <span>{opt.title}</span>
                    </span>
                    {selectedLevel === opt.level && (
                      <CheckCircle2 className="w-4 h-4 text-slate-700 shrink-0" />
                    )}
                  </div>
                  <p className="text-[10px] mt-1 text-slate-600 leading-tight">
                    {opt.desc}
                  </p>
                </button>
              ))}
            </div>
          </div>

          {/* Wait Time & Notes */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1 flex items-center gap-1">
                <Clock className="w-3.5 h-3.5 text-slate-400" />
                <span>Estimated Wait (min):</span>
              </label>
              <input
                type="number"
                min="0"
                max="240"
                value={waitTime}
                onChange={(e) => setWaitTime(e.target.value)}
                placeholder="0"
                className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1 flex items-center gap-1">
                <Sparkles className="w-3.5 h-3.5 text-slate-400" />
                <span>Quick Note (optional):</span>
              </label>
              <input
                type="text"
                maxLength={100}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="e.g. entry line moving fast"
                className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>
          </div>

          {/* Error & Success Alerts */}
          {errorMsg && (
            <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-start gap-2 animate-fadeIn">
              <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <div className="space-y-0.5">
                <span className="font-bold">Verification Notice:</span>
                <p className="text-[11px] leading-tight text-rose-700">{errorMsg}</p>
              </div>
            </div>
          )}

          {successMsg && (
            <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center gap-2 animate-fadeIn">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              <span className="font-semibold text-[11px]">{successMsg}</span>
            </div>
          )}

          {/* Submit Action */}
          <div className="pt-2 flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting || locating}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || locating}
              className="px-5 py-2.5 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-700 hover:to-indigo-700 shadow-md hover:shadow-lg transition-all flex items-center gap-1.5 disabled:opacity-60 cursor-pointer"
            >
              {locating ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Checking Geofence...</span>
                </>
              ) : submitting ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Submitting...</span>
                </>
              ) : (
                <>
                  <MapPin className="w-3.5 h-3.5" />
                  <span>Verify Location & Submit</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>,
    document.body
  );
}
