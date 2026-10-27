import React, { useState } from 'react';
import { Navbar } from './components/Navbar';
import { ExplorePage } from './pages/ExplorePage';
import { PlannerPage } from './pages/PlannerPage';
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
        return <PlannerPage />;
      case 'hotels':
        return <HotelsPage />;
      case 'map':
        return <MapPage />;
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

          {/* Main Content View */}
          <main className="flex-1 pb-16">
            {renderActivePage()}
          </main>

          {/* Global Footer */}
          <footer className="border-t border-slate-200 bg-white py-8 text-slate-500 text-xs">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-2">
                <span className="font-bold text-slate-800">Voyantra</span>
                <span>• Personalized Tourist Trip-Planning Platform (Pondicherry & Chennai)</span>
              </div>
              <div className="flex items-center gap-4 text-slate-400">
                <span>MongoDB & OSM Powered</span>
                <span>•</span>
                <span>Academic Mini-Project</span>
              </div>
            </div>
          </footer>
        </div>
      </PreferencesProvider>
    </AuthProvider>
  );
}

export default App;
