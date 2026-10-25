import React, { useState, useEffect } from 'react';
import { ShieldCheck, Database, MapPin, Users, Activity, CheckCircle, RefreshCw, Server, AlertTriangle } from 'lucide-react';
import { VoyantraAPI } from '../services/api';

export function AdminPortal() {
  const [cities, setCities] = useState([]);
  const [placesCount, setPlacesCount] = useState({ pondicherry: 0, chennai: 0 });
  const [dbStatus, setDbStatus] = useState({ connected: true, type: 'MongoDB (voyantra_db)' });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const cList = await VoyantraAPI.getCities();
      setCities(cList);
      
      const pPondy = await VoyantraAPI.getPlaces({ city_id: 'pondicherry' });
      const pChennai = await VoyantraAPI.getPlaces({ city_id: 'chennai' });
      setPlacesCount({
        pondicherry: pPondy.length,
        chennai: pChennai.length
      });
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      
      {/* Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-amber-950 to-slate-900 rounded-2xl p-6 text-white shadow-xl border border-amber-500/20 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-amber-500/20 border border-amber-500/30 flex items-center justify-center text-amber-400">
            <ShieldCheck className="w-7 h-7" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold">Voyantra Administrator Portal</h1>
              <span className="px-2 py-0.5 bg-amber-400 text-slate-950 font-bold text-[10px] uppercase tracking-wider rounded-md">
                Admin Privilege
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-1">
              System monitoring, MongoDB data verification, and place repository management.
            </p>
          </div>
        </div>

        <button
          onClick={loadData}
          className="flex items-center gap-2 px-3.5 py-2 bg-white/10 hover:bg-white/20 border border-white/20 rounded-xl text-xs font-bold transition-colors"
        >
          <RefreshCw className="w-4 h-4 text-amber-400" />
          <span>Refresh Database Stats</span>
        </button>
      </div>

      {/* Grid Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-teal-50 text-teal-700 flex items-center justify-center">
            <Database className="w-6 h-6" />
          </div>
          <div>
            <div className="text-xs font-bold text-slate-500">Database Engine</div>
            <div className="text-sm font-extrabold text-slate-900">MongoDB</div>
            <div className="text-[11px] font-bold text-emerald-600 flex items-center gap-1 mt-0.5">
              <CheckCircle className="w-3 h-3" />
              <span>voyantra_db Online</span>
            </div>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-brand-50 text-brand-700 flex items-center justify-center">
            <MapPin className="w-6 h-6" />
          </div>
          <div>
            <div className="text-xs font-bold text-slate-500">Active Destinations</div>
            <div className="text-sm font-extrabold text-slate-900">Pondicherry & Chennai</div>
            <div className="text-[11px] font-medium text-slate-500 mt-0.5">
              {placesCount.pondicherry + placesCount.chennai} Total Places Loaded
            </div>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-700 flex items-center justify-center">
            <Users className="w-6 h-6" />
          </div>
          <div>
            <div className="text-xs font-bold text-slate-500">User Roles</div>
            <div className="text-sm font-extrabold text-slate-900">Traveler & Admin</div>
            <div className="text-[11px] font-bold text-amber-700 mt-0.5">Role-Based Access</div>
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-purple-50 text-purple-700 flex items-center justify-center">
            <Server className="w-6 h-6" />
          </div>
          <div>
            <div className="text-xs font-bold text-slate-500">FastAPI Backend</div>
            <div className="text-sm font-extrabold text-slate-900">Python 3.14 (Async)</div>
            <div className="text-[11px] font-bold text-emerald-600 flex items-center gap-1 mt-0.5">
              <CheckCircle className="w-3 h-3" />
              <span>Status Healthy</span>
            </div>
          </div>
        </div>

      </div>

      {/* City & Collection Details Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Database className="w-5 h-5 text-brand-600" />
            MongoDB Collection Repositories
          </h2>
          <span className="text-xs font-semibold text-slate-500">Strictly Scope-Bound</span>
        </div>

        <div className="divide-y divide-slate-100">
          <div className="p-4 sm:p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 hover:bg-slate-50 transition-colors">
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-slate-900 text-sm">Pondicherry Places Dataset</span>
                <span className="px-2 py-0.5 bg-brand-100 text-brand-800 text-[10px] font-bold rounded">Pilot City</span>
              </div>
              <p className="text-xs text-slate-500 mt-1">French Colonial Quarter, Promenade Beach, Matrimandir & Cafes</p>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs font-extrabold text-slate-800 bg-slate-100 px-3 py-1.5 rounded-lg border border-slate-200">
                {placesCount.pondicherry} Places Loaded
              </span>
            </div>
          </div>

          <div className="p-4 sm:p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 hover:bg-slate-50 transition-colors">
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-slate-900 text-sm">Chennai Places Dataset</span>
                <span className="px-2 py-0.5 bg-teal-100 text-teal-800 text-[10px] font-bold rounded">Metropolitan</span>
              </div>
              <p className="text-xs text-slate-500 mt-1">Marina Beach, Kapaleeshwarar Temple, Fort St. George & San Thome</p>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs font-extrabold text-slate-800 bg-slate-100 px-3 py-1.5 rounded-lg border border-slate-200">
                {placesCount.chennai} Places Loaded
              </span>
            </div>
          </div>
        </div>
      </div>

    </div>
  );
}
