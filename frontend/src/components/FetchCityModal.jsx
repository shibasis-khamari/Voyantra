import React, { useState } from 'react';
import { X, Globe, DownloadCloud, CheckCircle2, AlertCircle, Loader2, MapPin } from 'lucide-react';
import { VoyantraAPI } from '../services/api';

export function FetchCityModal({ isOpen, onClose, onCityIngested }) {
  const [cityName, setCityName] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleFetch = async (e) => {
    e.preventDefault();
    if (!cityName.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await VoyantraAPI.fetchCityFromInternet(cityName.trim());
      setResult(res);
      if (onCityIngested) {
        onCityIngested(res.city_id);
      }
    } catch (err) {
      setError(err.message || 'Failed to fetch city data from internet.');
    } finally {
      setLoading(false);
    }
  };

  const quickCities = ['Goa', 'Jaipur', 'Kochi', 'Manali', 'Ooty', 'Varanasi'];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-fadeIn">
      <div className="bg-white rounded-3xl max-w-lg w-full p-6 sm:p-8 shadow-2xl border border-slate-100 relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-full text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 rounded-2xl bg-teal-50 text-teal-600 flex items-center justify-center border border-teal-200">
            <Globe className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-900">Direct Internet Ingestion</h2>
            <p className="text-xs text-slate-500">Reads live POIs from OpenStreetMap & Wikipedia</p>
          </div>
        </div>

        <form onSubmit={handleFetch} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              Enter Any City Name
            </label>
            <div className="relative">
              <MapPin className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                value={cityName}
                onChange={(e) => setCityName(e.target.value)}
                placeholder="e.g. Goa, Jaipur, Kochi, Manali..."
                disabled={loading}
                className="w-full pl-10 pr-4 py-3 rounded-xl border border-slate-200 bg-slate-50 focus:bg-white focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20 text-sm outline-none transition-all"
              />
            </div>
          </div>

          {/* Quick city tags */}
          <div>
            <span className="text-[11px] text-slate-400 font-medium">Quick suggestions:</span>
            <div className="flex flex-wrap gap-1.5 mt-1.5">
              {quickCities.map(c => (
                <button
                  type="button"
                  key={c}
                  onClick={() => setCityName(c)}
                  className="px-2.5 py-1 rounded-lg text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium transition-colors"
                >
                  {c}
                </button>
              ))}
            </div>
          </div>

          {/* Status feedback */}
          {loading && (
            <div className="p-4 rounded-xl bg-teal-50 border border-teal-200 flex items-center gap-3 text-xs text-teal-800">
              <Loader2 className="w-5 h-5 text-teal-600 animate-spin shrink-0" />
              <div>
                <strong className="block">Contacting OpenStreetMap & Wikipedia...</strong>
                Extracting coordinates, attractions, beaches, and cafes.
              </div>
            </div>
          )}

          {error && (
            <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 flex items-start gap-2.5 text-xs text-rose-800">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {result && result.success && (
            <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 space-y-1.5 text-xs text-emerald-900">
              <div className="flex items-center gap-1.5 font-bold text-sm text-emerald-800">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                Successfully Ingested {result.city_name}!
              </div>
              <p>Found & saved <strong>{result.total_ingested} destinations</strong> into the database.</p>
            </div>
          )}

          <div className="flex items-center gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 py-3 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold transition-colors"
            >
              Close
            </button>
            <button
              type="submit"
              disabled={loading || !cityName.trim()}
              className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white text-xs font-bold transition-colors shadow-md"
            >
              <DownloadCloud className="w-4 h-4" />
              {loading ? 'Ingesting...' : 'Fetch & Save to DB'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
