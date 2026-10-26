import React, { useState, useEffect } from 'react';
import { 
  X, 
  User, 
  ShieldCheck, 
  Mail, 
  Lock, 
  Sparkles, 
  CheckCircle2, 
  AlertCircle,
  UserPlus,
  LogIn
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { VoyantraAPI } from '../services/api';

export function LoginModal({ isOpen, onClose, initialMode = 'login' }) {
  const { login } = useAuth();
  const [authMode, setAuthMode] = useState(initialMode); // 'login' | 'signup'
  const [activeTab, setActiveTab] = useState('user'); // 'user' | 'admin'
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  useEffect(() => {
    if (isOpen) {
      setAuthMode(initialMode);
      setError(null);
      setSuccess(null);
    }
  }, [isOpen, initialMode]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e?.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    if (authMode === 'signup') {
      if (!name.trim()) {
        setError('Please enter your name.');
        setLoading(false);
        return;
      }
      if (password.length < 6) {
        setError('Password must be at least 6 characters.');
        setLoading(false);
        return;
      }
      if (password !== confirmPassword) {
        setError('Passwords do not match.');
        setLoading(false);
        return;
      }

      try {
        const res = await VoyantraAPI.register({
          name: name.trim(),
          email: email.trim().toLowerCase(),
          password,
          role: activeTab
        });

        login(res.user, res.access_token);
        setSuccess(`Account created! Logged in as ${res.user.role === 'admin' ? 'Administrator' : 'Traveler'}.`);
        setTimeout(() => {
          setSuccess(null);
          onClose();
        }, 1200);
      } catch (err) {
        setError(err.message || 'Registration failed. An account with this email may already exist.');
      } finally {
        setLoading(false);
      }
    } else {
      // Login mode
      try {
        const res = await VoyantraAPI.login({
          email: email.trim().toLowerCase(),
          password,
          role: activeTab
        });

        login(res.user, res.access_token);
        setSuccess(`Successfully logged in as ${res.user.role === 'admin' ? 'Administrator' : 'Traveler'}!`);
        setTimeout(() => {
          setSuccess(null);
          onClose();
        }, 1200);
      } catch (err) {
        setError(err.message || 'Login failed. Please check your credentials.');
      } finally {
        setLoading(false);
      }
    }
  };

  const fillDemoUser = () => {
    setAuthMode('login');
    setActiveTab('user');
    setEmail('user@voyantra.com');
    setPassword('user123');
  };

  const fillDemoAdmin = () => {
    setAuthMode('login');
    setActiveTab('admin');
    setEmail('admin@voyantra.com');
    setPassword('admin123');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
      <div className="bg-white rounded-3xl shadow-2xl max-w-md w-full overflow-hidden border border-slate-100 animate-in fade-in zoom-in duration-200">
        
        {/* Modal Header */}
        <div className="bg-gradient-to-r from-slate-900 via-brand-900 to-brand-800 p-6 text-white relative">
          <button 
            onClick={onClose}
            className="absolute top-4 right-4 p-1 rounded-full text-slate-300 hover:text-white hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
          
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-white/10 backdrop-blur flex items-center justify-center text-brand-300 border border-white/20">
              <Sparkles className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold">
                {authMode === 'signup' ? 'Create Voyantra Account' : 'Voyantra Account Access'}
              </h2>
              <p className="text-xs text-slate-300">
                {authMode === 'signup' ? 'Join to save itineraries & preferences' : 'Login to access traveler preferences & admin settings'}
              </p>
            </div>
          </div>

          {/* Mode Switcher (Log In / Sign Up) */}
          <div className="flex bg-black/30 p-1 rounded-xl mt-5 border border-white/10">
            <button
              onClick={() => { setAuthMode('login'); setError(null); }}
              className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
                authMode === 'login'
                  ? 'bg-white text-slate-900 shadow-md'
                  : 'text-slate-300 hover:text-white'
              }`}
            >
              <LogIn className="w-3.5 h-3.5" />
              <span>Log In</span>
            </button>

            <button
              onClick={() => { setAuthMode('signup'); setError(null); }}
              className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
                authMode === 'signup'
                  ? 'bg-amber-400 text-slate-950 shadow-md'
                  : 'text-slate-300 hover:text-white'
              }`}
            >
              <UserPlus className="w-3.5 h-3.5" />
              <span>Sign Up</span>
            </button>
          </div>

          {/* Role Switcher Tabs */}
          <div className="flex gap-2 mt-3">
            <button
              onClick={() => { setActiveTab('user'); setError(null); }}
              className={`flex-1 py-1.5 rounded-lg text-xs font-semibold border transition-all flex items-center justify-center gap-1.5 ${
                activeTab === 'user'
                  ? 'bg-white/20 border-white/40 text-white font-bold'
                  : 'bg-white/5 border-transparent text-slate-300 hover:text-white'
              }`}
            >
              <User className="w-3.5 h-3.5" />
              <span>Traveler</span>
            </button>

            <button
              onClick={() => { setActiveTab('admin'); setError(null); }}
              className={`flex-1 py-1.5 rounded-lg text-xs font-semibold border transition-all flex items-center justify-center gap-1.5 ${
                activeTab === 'admin'
                  ? 'bg-amber-400/20 border-amber-400/40 text-amber-300 font-bold'
                  : 'bg-white/5 border-transparent text-slate-300 hover:text-white'
              }`}
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Administrator</span>
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-4">

          {/* Demo Quick Fill Banners (Only in login mode) */}
          {authMode === 'login' && (
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-3">
              <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2 flex items-center justify-between">
                <span>Quick Demo Accounts</span>
                <span className="text-[10px] text-teal-600 font-semibold bg-teal-50 px-1.5 py-0.5 rounded">MongoDB Synced</span>
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={fillDemoUser}
                  className="flex-1 py-1.5 px-2 bg-white hover:bg-brand-50 border border-slate-200 rounded-lg text-[11px] font-bold text-slate-700 hover:text-brand-700 text-center transition-colors shadow-2xs"
                >
                  👤 Traveler Demo
                </button>
                <button
                  type="button"
                  onClick={fillDemoAdmin}
                  className="flex-1 py-1.5 px-2 bg-amber-50 hover:bg-amber-100 border border-amber-200 rounded-lg text-[11px] font-bold text-amber-900 text-center transition-colors shadow-2xs"
                >
                  🛡️ Admin Demo
                </button>
              </div>
            </div>
          )}

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-xl text-red-700 text-xs font-medium flex items-center gap-2 animate-in fade-in">
              <AlertCircle className="w-4 h-4 shrink-0 text-red-600" />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 text-xs font-medium flex items-center gap-2 animate-in fade-in">
              <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
              <span>{success}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-3">
            {authMode === 'signup' && (
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Full Name</label>
                <div className="relative">
                  <User className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g. Ramesh Kumar"
                    className="w-full pl-9 pr-3 py-2 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
                  />
                </div>
              </div>
            )}

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                {activeTab === 'admin' ? 'Admin Email' : 'Email Address'}
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder={activeTab === 'admin' ? 'admin@voyantra.com' : 'user@voyantra.com'}
                  className="w-full pl-9 pr-3 py-2 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={authMode === 'signup' ? 'Min. 6 characters' : '••••••••'}
                  className="w-full pl-9 pr-3 py-2 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
                />
              </div>
            </div>

            {authMode === 'signup' && (
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Confirm Password</label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  <input
                    type="password"
                    required
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Confirm password"
                    className="w-full pl-9 pr-3 py-2 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
                  />
                </div>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className={`w-full py-2.5 rounded-xl text-xs font-bold text-white shadow-md transition-all ${
                activeTab === 'admin'
                  ? 'bg-amber-600 hover:bg-amber-700 shadow-amber-600/20'
                  : 'bg-brand-600 hover:bg-brand-700 shadow-brand-600/20'
              } disabled:opacity-50`}
            >
              {loading
                ? 'Processing...'
                : authMode === 'signup'
                ? `Create ${activeTab === 'admin' ? 'Administrator' : 'Traveler'} Account`
                : `Log In as ${activeTab === 'admin' ? 'Administrator' : 'Traveler'}`}
            </button>
          </form>

          {/* Toggle bottom link */}
          <div className="text-center pt-2">
            {authMode === 'login' ? (
              <p className="text-xs text-slate-500">
                Don't have an account?{' '}
                <button
                  type="button"
                  onClick={() => { setAuthMode('signup'); setError(null); }}
                  className="text-brand-600 hover:text-brand-800 font-bold underline"
                >
                  Sign Up now
                </button>
              </p>
            ) : (
              <p className="text-xs text-slate-500">
                Already registered?{' '}
                <button
                  type="button"
                  onClick={() => { setAuthMode('login'); setError(null); }}
                  className="text-brand-600 hover:text-brand-800 font-bold underline"
                >
                  Log In
                </button>
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}