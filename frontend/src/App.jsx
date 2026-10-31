import React, { useState } from 'react';
import { Navbar } from './components/Navbar';
import { ExplorePage } from './pages/ExplorePage';
import { PlannerPage } from './pages/PlannerPage';
import { SavedBasketPage } from './pages/SavedBasketPage';
import { HotelsPage } from './pages/HotelsPage';
import { MapPage } from './pages/MapPage';
import { ProfilePage } from './pages/ProfilePage';
import { AdminPortal } from './components/AdminPortal';
import { SignUpPage } from './pages/SignUpPage';
import { PreferencesProvider } from './context/PreferencesContext';
import { AuthProvider } from './context/AuthContext';

export function App() {
  const [activeTab, setActiveTab] = useState('explore');

  const renderActivePage = () => {
    switch (activeTab) {
      case 'explore':
        return <ExplorePage setActiveTab={setActiveTab} />;
      case 'planner':
        return <PlannerPage setActiveTab={setActiveTab} />;
      case 'basket':
        return <SavedBasketPage setActiveTab={setActiveTab} />;
      case 'hotels':
        return <HotelsPage />;
      case 'map':
        return <MapPage setActiveTab={setActiveTab} />;
      case 'profile':
        return <ProfilePage />;
      case 'admin':
        return <AdminPortal />;
      case 'signup':
        return <SignUpPage setActiveTab={setActiveTab} />;
      default:
        return <ExplorePage setActiveTab={setActiveTab} />;
    }
  };

  return (
    <AuthProvider>
      <PreferencesProvider>
        <div className="min-h-screen bg-slate-50 flex flex-col font-sans selection:bg-brand-500 selection:text-white">
          {/* Top Navbar */}
          <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

          {/* Main Content View: pt-0 on Explore so Hero background extends behind glassy navbar, pt-16 on other pages. No bottom padding on planner for full-height single-page view */}
          <main className={`flex-1 ${activeTab === 'planner' ? 'pt-16 pb-0 overflow-hidden' : activeTab === 'explore' ? 'pt-0 pb-16' : 'pt-16 pb-16'}`}>
            {renderActivePage()}
          </main>

          {/* Global Footer (hidden on single-page Planner view for pure full-screen experience) */}
          {activeTab !== 'planner' && (
            <footer className="border-t border-sandstone bg-white py-10 text-slate-500 text-xs">
              <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-6">
                <div className="flex flex-col sm:flex-row items-center gap-3 text-center sm:text-left">
                  <img 
                    src="/images/logo/voyantra-logo-horizontal-crop.png" 
                    alt="Voyantra Logo" 
                    className="h-8 w-auto object-contain cursor-pointer hover:opacity-90 transition-opacity"
                    onClick={() => setActiveTab('explore')}
                  />
                  <span className="hidden sm:inline text-slate-300">•</span>
                  <span className="text-slate-600 font-medium">Personalized Tourist Trip-Planning Platform (Pondicherry & Chennai)</span>
                </div>
                <div className="flex items-center gap-4 text-slate-400 text-[11px]">
                  <span>MongoDB & OSM Grounded</span>
                  <span>•</span>
                  <span>Academic Mini-Project</span>
                </div>
              </div>
            </footer>
          )}
        </div>
      </PreferencesProvider>
    </AuthProvider>
  );
}

export default App;
