import React, { useState, useEffect } from 'react';
import { Compass, MapPin, Sparkles, Hotel, Map, User, Luggage, LogIn, LogOut, ShieldCheck, Navigation, UserPlus } from 'lucide-react';
import { usePreferences } from '../context/PreferencesContext';
import { useAuth } from '../context/AuthContext';
import { VoyantraAPI } from '../services/api';
import { LoginModal } from './LoginModal';

export function Navbar({ activeTab, setActiveTab }) {
  const { tripPlan, selectedCity, setSelectedCity, detectCurrentLocation, locationNotice } = usePreferences();
  const { user, logout, isAdmin } = useAuth();
  const [cities, setCities] = useState([]);
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
  const [loginModalMode, setLoginModalMode] = useState('login');

  useEffect(() => {
    loadCities();
  }, []);

  const loadCities = async () => {
    const list = await VoyantraAPI.getCities();
    setCities(list);
  };

  const navItems = [
    { id: 'explore', label: 'Explore Places', icon: Compass },
    { id: 'planner', label: 'Personalized Planner', icon: Sparkles, badge: 'AI & Filters' },
    { id: 'hotels', label: 'Hotels', icon: Hotel },
    { id: 'map', label: 'Interactive Map', icon: Map },
    { id: 'profile', label: 'My Preferences', icon: User }
  ];

  if (isAdmin) {
    navItems.push({ id: 'admin', label: 'Admin Portal', icon: ShieldCheck, badge: 'Admin' });
  }

  return (
    <>
      <header className="sticky top-0 z-40 bg-[#FAF8F5]/90 backdrop-blur-md border-b border-sandstone shadow-2xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo & City Selector */}
            <div className="flex items-center gap-3">
              <div 
                onClick={() => setActiveTab('explore')}
                className="flex items-center gap-2.5 cursor-pointer group"
              >
                <div className="w-10 h-10 rounded-xl bg-brand-700 flex items-center justify-center text-white shadow-md shadow-brand-700/20 group-hover:bg-terracotta transition-colors">
                  <Compass className="w-5 h-5 text-sandstone-canvas" />
                </div>
                <div>
                  <span className="font-serif text-2xl font-bold tracking-tight text-brand-700 group-hover:text-terracotta transition-colors">
                    Voyantra
                  </span>
                </div>
              </div>

              {/* City Switcher (Restricted to Chennai & Pondicherry) */}
              <div className="flex items-center gap-1.5 bg-sandstone-light p-1 px-2.5 rounded-full border border-sandstone">
                <MapPin className="w-3.5 h-3.5 text-terracotta" />
                <select
                  value={selectedCity}
                  onChange={(e) => setSelectedCity(e.target.value)}
                  className="bg-transparent text-xs font-bold text-brand-700 outline-none pr-1 cursor-pointer font-sans"
                >
                  {cities.map(c => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
                <button
                  onClick={() => detectCurrentLocation(true)}
                  title="Detect my current location with GPS"
                  className="p-1 rounded-full text-brand-700 hover:text-terracotta hover:bg-sandstone transition-colors flex items-center gap-1 text-[10px] font-bold"
                >
                  <Navigation className="w-3 h-3 text-terracotta animate-pulse" />
                  <span className="hidden sm:inline">GPS</span>
                </button>
              </div>
            </div>

            {/* Navigation Links */}
            <nav className="hidden md:flex items-center gap-1">
              {navItems.map(item => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => setActiveTab(item.id)}
                    className={`relative flex items-center gap-2 px-3.5 py-2 rounded-full text-xs font-bold transition-all ${
                      isActive 
                        ? 'text-terracotta bg-terracotta/10 border border-terracotta/20 shadow-2xs' 
                        : 'text-slate-600 hover:text-brand-700 hover:bg-sandstone-light'
                    }`}
                  >
                    <Icon className={`w-4 h-4 ${isActive ? 'text-terracotta' : 'text-slate-400'}`} />
                    {item.label}
                    {item.badge && (
                      <span className={`text-[9px] uppercase font-bold tracking-widest px-1.5 py-0.5 rounded-full ${
                        item.badge === 'Admin' ? 'bg-amber-100 text-amber-900' : 'bg-terracotta/15 text-terracotta'
                      }`}>
                        {item.badge}
                      </span>
                    )}
                  </button>
                );
              })}
            </nav>

            {/* User Auth Controls & Trip Plan Counter */}
            <div className="flex items-center gap-2">
              {user ? (
                <div className="flex items-center gap-2">
                  <div className="hidden sm:flex items-center gap-2 bg-slate-100 border border-slate-200 px-2.5 py-1 rounded-xl">
                    <div className="w-6 h-6 rounded-full bg-brand-600 text-white font-bold text-xs flex items-center justify-center">
                      {user.name.charAt(0)}
                    </div>
                    <div className="flex flex-col">
                      <span className="text-[11px] font-bold text-slate-800 leading-tight">{user.name}</span>
                      <span className="text-[9px] font-semibold text-slate-500 uppercase">{user.role}</span>
                    </div>
                  </div>

                  <button
                    onClick={logout}
                    title="Log Out"
                    className="p-2 text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-xl transition-colors"
                  >
                    <LogOut className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <div className="flex items-center gap-1.5">
                  <button
                    onClick={() => { setLoginModalMode('login'); setIsLoginModalOpen(true); }}
                    className="flex items-center gap-1 px-2.5 sm:px-3 py-1.5 bg-brand-50 hover:bg-brand-100 text-brand-700 border border-brand-200 rounded-xl text-xs font-bold transition-colors"
                  >
                    <LogIn className="w-3.5 h-3.5" />
                    <span>Log In</span>
                  </button>

                  <button
                    onClick={() => setActiveTab('signup')}
                    className="flex items-center gap-1 px-2.5 sm:px-3 py-1.5 bg-terracotta hover:bg-terracotta/90 text-white rounded-xl text-xs font-bold transition-colors shadow-xs"
                  >
                    <UserPlus className="w-3.5 h-3.5" />
                    <span className="hidden sm:inline">Sign Up</span>
                  </button>
                </div>
              )}

              <button
                onClick={() => setActiveTab('planner')}
                className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-brand-700 text-white text-xs sm:text-sm font-medium transition-colors shadow-sm"
              >
                <Luggage className="w-4 h-4 text-brand-300" />
                <span className="hidden sm:inline">Trip Basket</span>
                <span className="ml-1 w-5 h-5 rounded-full bg-brand-500 text-white flex items-center justify-center text-xs font-bold">
                  {tripPlan.length}
                </span>
              </button>
            </div>
          </div>
        </div>

        {/* Mobile Tab Bar */}
        <div className="md:hidden flex border-t border-slate-100 overflow-x-auto px-2 py-1.5 gap-1 bg-white">
          {navItems.map(item => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex-1 min-w-[70px] py-1.5 flex flex-col items-center gap-1 rounded-lg text-[11px] ${
                  isActive ? 'text-brand-700 font-semibold bg-brand-50' : 'text-slate-500'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{item.label.split(' ')[0]}</span>
              </button>
            );
          })}
        </div>

        {/* Location Notice Banner */}
        {locationNotice && (
          <div className="bg-brand-700 text-white text-[11px] font-bold py-1 px-4 text-center flex items-center justify-center gap-2 animate-fadeIn">
            <span>{locationNotice}</span>
          </div>
        )}
      </header>

      {/* Login & Registration Auth Modal */}
      <LoginModal 
        isOpen={isLoginModalOpen}
        onClose={() => setIsLoginModalOpen(false)}
        initialMode={loginModalMode}
      />
    </>
  );
}
