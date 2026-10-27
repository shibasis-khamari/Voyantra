import React, { useState, useEffect, useRef } from 'react';
import { Compass, MapPin, Sparkles, Hotel, Map, User, Luggage, LogIn, LogOut, ShieldCheck } from 'lucide-react';
import { usePreferences } from '../context/PreferencesContext';
import { useAuth } from '../context/AuthContext';
import { VoyantraAPI } from '../services/api';
import { LoginModal } from './LoginModal';

export function Navbar({ activeTab, setActiveTab }) {
  const { tripPlan, selectedCity, setSelectedCity } = usePreferences();
  const { user, logout, isAdmin } = useAuth();
  const [cities, setCities] = useState([]);
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const userMenuRef = useRef(null);

  useEffect(() => {
    loadCities();
  }, []);

  // Close dropdown on click outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target)) {
        setUserMenuOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const loadCities = async () => {
    const list = await VoyantraAPI.getCities();
    setCities(list);
  };

  const navItems = [
    { id: 'explore', label: 'Explore', icon: Compass },
    { id: 'planner', label: 'Planner', icon: Sparkles },
    { id: 'hotels', label: 'Hotels', icon: Hotel },
    { id: 'map', label: 'Map', icon: Map },
    { id: 'profile', label: 'Preferences', icon: User }
  ];

  if (isAdmin) {
    navItems.push({ id: 'admin', label: 'Admin', icon: ShieldCheck });
  }

  return (
    <>
      <header className="fixed top-0 left-0 right-0 z-50 backdrop-blur-xl bg-slate-950/40 border-b border-white/10 shadow-[0_4px_30px_rgba(0,0,0,0.15)] transition-all duration-300">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            
            {/* Left: Brand Logo & Manual City Selector */}
            <div className="flex items-center gap-3">
              <div 
                onClick={() => setActiveTab('explore')}
                className="flex items-center gap-2.5 cursor-pointer group"
              >
                <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-700 to-terracotta flex items-center justify-center text-white shadow-md shadow-brand-900/30 group-hover:scale-105 transition-transform">
                  <Compass className="w-5 h-5 text-white" />
                </div>
                <span className="font-serif text-2xl font-bold tracking-tight text-white drop-shadow-xs group-hover:text-amber-300 transition-colors">
                  Voyantra
                </span>
              </div>

              {/* Manual City Selector Pill (Restricted to Pondicherry & Chennai) */}
              <div className="flex items-center gap-1.5 bg-white/10 hover:bg-white/15 border border-white/15 px-3 py-1.5 rounded-full backdrop-blur-md transition-colors text-white">
                <MapPin className="w-3.5 h-3.5 text-amber-300 shrink-0" />
                <select
                  value={selectedCity}
                  onChange={(e) => setSelectedCity(e.target.value)}
                  className="bg-transparent text-xs font-semibold text-white outline-none cursor-pointer font-sans [&>option]:bg-slate-900 [&>option]:text-white"
                  title="Select destination city manually"
                >
                  {cities.map(c => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Center: Organized & Minimal Nav Dock */}
            <nav className="hidden md:flex items-center gap-1 bg-white/5 border border-white/10 px-2 py-1 rounded-full backdrop-blur-md">
              {navItems.map(item => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => setActiveTab(item.id)}
                    className={`flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all duration-200 cursor-pointer ${
                      isActive 
                        ? 'text-white bg-white/15 border border-white/20 shadow-xs' 
                        : 'text-slate-300 hover:text-white hover:bg-white/10'
                    }`}
                  >
                    <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-amber-300' : 'text-slate-400'}`} />
                    <span>{item.label}</span>
                  </button>
                );
              })}
            </nav>

            {/* Right: Consolidated Auth Button / Circular Avatar & Trip Basket */}
            <div className="flex items-center gap-2.5">
              {user ? (
                /* Logged In: Circular Avatar with Sleek Dropdown */
                <div className="relative" ref={userMenuRef}>
                  <button
                    onClick={() => setUserMenuOpen(!userMenuOpen)}
                    title={user.name}
                    className="w-8 h-8 rounded-full bg-gradient-to-tr from-terracotta to-amber-400 text-slate-950 font-bold text-xs flex items-center justify-center ring-2 ring-white/20 hover:ring-amber-300 shadow-md transition-all cursor-pointer select-none"
                  >
                    {user.name?.charAt(0)?.toUpperCase() || 'U'}
                  </button>

                  {userMenuOpen && (
                    <div className="absolute right-0 mt-2 w-48 rounded-2xl bg-slate-900/95 border border-white/15 shadow-2xl backdrop-blur-xl p-2 text-white text-xs space-y-1 animate-in fade-in zoom-in-95 duration-150 z-50">
                      <div className="px-3 py-2 border-b border-white/10 space-y-0.5">
                        <div className="font-bold text-white truncate">{user.name}</div>
                        <div className="text-[10px] text-amber-300 uppercase tracking-wider font-semibold">
                          {user.role === 'admin' ? 'Administrator' : 'Traveler'}
                        </div>
                      </div>

                      <button
                        onClick={() => { setActiveTab('profile'); setUserMenuOpen(false); }}
                        className="w-full text-left px-3 py-2 rounded-xl hover:bg-white/10 flex items-center gap-2 text-slate-200 hover:text-white transition-colors cursor-pointer"
                      >
                        <User className="w-3.5 h-3.5 text-slate-400" />
                        <span>My Preferences</span>
                      </button>

                      {isAdmin && (
                        <button
                          onClick={() => { setActiveTab('admin'); setUserMenuOpen(false); }}
                          className="w-full text-left px-3 py-2 rounded-xl hover:bg-white/10 flex items-center gap-2 text-amber-300 hover:text-amber-200 transition-colors cursor-pointer"
                        >
                          <ShieldCheck className="w-3.5 h-3.5 text-amber-400" />
                          <span>Admin Portal</span>
                        </button>
                      )}

                      <button
                        onClick={() => { logout(); setUserMenuOpen(false); }}
                        className="w-full text-left px-3 py-2 rounded-xl hover:bg-red-500/20 text-red-300 hover:text-red-200 flex items-center gap-2 transition-colors cursor-pointer"
                      >
                        <LogOut className="w-3.5 h-3.5 text-red-400" />
                        <span>Log Out</span>
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                /* Logged Out: Single Consolidated Sign In / Sign Up Button */
                <button
                  onClick={() => setIsLoginModalOpen(true)}
                  className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-white/10 hover:bg-white/20 text-white border border-white/20 text-xs font-semibold transition-all backdrop-blur-md cursor-pointer hover:border-white/30 shadow-xs"
                >
                  <LogIn className="w-3.5 h-3.5 text-amber-300" />
                  <span>Log In</span>
                </button>
              )}

              {/* Trip Plan Basket Pill */}
              <button
                onClick={() => setActiveTab('planner')}
                className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/10 hover:bg-white/20 border border-white/20 text-white text-xs font-semibold transition-all backdrop-blur-md cursor-pointer shadow-xs"
                title="Open Trip Basket"
              >
                <Luggage className="w-3.5 h-3.5 text-amber-300" />
                <span className="hidden sm:inline">Basket</span>
                <span className="w-4 h-4 rounded-full bg-terracotta text-white flex items-center justify-center text-[10px] font-bold">
                  {tripPlan.length}
                </span>
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Tab Bar */}
        <div className="md:hidden flex border-t border-white/10 overflow-x-auto px-2 py-1.5 gap-1 bg-slate-950/85 backdrop-blur-xl">
          {navItems.map(item => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex-1 min-w-[65px] py-1.5 flex flex-col items-center gap-1 rounded-xl text-[10px] transition-colors ${
                  isActive ? 'text-amber-300 font-bold bg-white/10' : 'text-slate-400 hover:text-white'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      </header>

      {/* Unified Login & Sign Up Modal */}
      <LoginModal 
        isOpen={isLoginModalOpen}
        onClose={() => setIsLoginModalOpen(false)}
        initialMode="login"
      />
    </>
  );
}
