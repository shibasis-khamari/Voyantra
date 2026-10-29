import React, { useState, useEffect } from 'react';
import { HotelCard } from '../components/HotelCard';
import { VoyantraAPI } from '../services/api';
import { Hotel, IndianRupee, SlidersHorizontal, MapPin } from 'lucide-react';
import { BUDGET_TIERS } from '../types/constants';
import { PageHero } from '../components/PageHero';

export function HotelsPage() {
  const [hotels, setHotels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedBudget, setSelectedBudget] = useState('');
  const [maxPrice, setMaxPrice] = useState(15000);

  const [backendError, setBackendError] = useState(null);

  useEffect(() => {
    loadHotels();
  }, [selectedBudget, maxPrice]);

  const loadHotels = async () => {
    setLoading(true);
    try {
      const data = await VoyantraAPI.getHotels({
        budget: selectedBudget,
        max_price: maxPrice
      });
      setHotels(data);
      setBackendError(null);
    } catch (e) {
      setBackendError(e.message);
      setHotels([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Backend Disconnected Notice */}
      {backendError && (
        <div className="p-5 rounded-2xl bg-rose-50 border-2 border-rose-300 text-rose-900 space-y-2 shadow-md animate-fadeIn">
          <div className="flex items-center gap-2 font-black text-rose-800 text-sm uppercase tracking-wider">
            <span className="px-2 py-0.5 rounded bg-rose-200 text-rose-900 font-extrabold text-[11px]">
              ⚠️ BACKEND DISCONNECTED
            </span>
          </div>
          <p className="text-xs text-rose-900 leading-relaxed font-medium">
            {backendError}
          </p>
          <div className="p-2.5 rounded-lg bg-rose-100/90 font-mono text-[11px] text-rose-950 font-bold">
            Start Server Command: cd E:\Voyantra\backend && python run.py
          </div>
        </div>
      )}
      {/* Page header */}
      <PageHero
        eyebrow="Handpicked stays"
        title="Find a stay that fits your journey"
        description="Compare coastal hotels and heritage stays by budget, location, and comfort."
        image="/images/rohit-durbha-3GpBMD609o4-unsplash.jpg"
      />

      {/* Filter Controls */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Filter Budget:</span>
          <div className="flex gap-1.5">
            <button
              onClick={() => setSelectedBudget('')}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                selectedBudget === '' ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              All Tiers
            </button>
            {BUDGET_TIERS.map(b => (
              <button
                key={b.id}
                onClick={() => setSelectedBudget(b.id)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                  selectedBudget === b.id ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                }`}
              >
                {b.label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-3 text-xs">
          <span className="text-slate-500 font-medium">Max Price: <strong className="text-slate-900">₹{maxPrice.toLocaleString()}</strong></span>
          <input
            type="range"
            min="500"
            max="16000"
            step="500"
            value={maxPrice}
            onChange={(e) => setMaxPrice(Number(e.target.value))}
            className="accent-indigo-600 cursor-pointer"
          />
        </div>
      </div>

      {/* Hotels Grid */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 animate-pulse">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-72 bg-slate-200 rounded-2xl"></div>
          ))}
        </div>
      ) : hotels.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {hotels.map(hotel => (
            <HotelCard key={hotel.id} hotel={hotel} />
          ))}
        </div>
      ) : (
        <div className="text-center py-12 bg-white rounded-2xl border border-slate-200 p-6">
          <p className="text-sm text-slate-500 font-medium">No hotels found within this price range.</p>
        </div>
      )}
    </div>
  );
}
