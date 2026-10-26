import React, { useState } from 'react';
import { 
  User, 
  Mail, 
  Lock, 
  ShieldCheck, 
  Compass, 
  Sparkles, 
  CheckCircle2, 
  AlertCircle, 
  ArrowRight,
  Eye,
  EyeOff
} from 'lucide-react';
import { VoyantraAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';

export function SignUpPage({ setActiveTab, onOpenLoginModal }) {
  const { login } = useAuth();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [role, setRole] = useState('user'); // 'user' | 'admin'
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const handleRegister = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (!name.trim()) {
      setError('Please enter your full name.');
      return;
    }

    if (!email.trim() || !email.includes('@')) {
      setError('Please provide a valid email address.');
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters long.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match. Please re-enter.');
      return;
    }

    setLoading(true);

    try {
      const res = await VoyantraAPI.register({
        name: name.trim(),
        email: email.trim().toLowerCase(),
        password,
        role
      });

      login(res.user, res.access_token);
      setSuccess(`Welcome to Voyantra, ${res.user.name}! Your ${role === 'admin' ? 'Administrator' : 'Traveler'} account is active.`);

      setTimeout(() => {
        if (role === 'admin') {
          setActiveTab('admin');
        } else {
          setActiveTab('planner');
        }
      }, 1500);
    } catch (err) {
      setError(err.message || 'Registration failed. An account with this email may already exist.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="bg-white rounded-3xl shadow-xl border border-sandstone overflow-hidden grid grid-cols-1 lg:grid-cols-12">
        
        {/* Left Side: Brand & Visuals */}
        <div className="lg:col-span-5 bg-gradient-to-br from-brand-900 via-slate-900 to-terracotta p-8 sm:p-10 text-white flex flex-col justify-between relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute bottom-0 left-0 w-64 h-64 bg-terracotta/20 rounded-full blur-3xl pointer-events-none" />

          <div className="relative z-10 space-y-6">
            <div className="flex items-center gap-3 cursor-pointer" onClick={() => setActiveTab('explore')}>
              <div className="w-11 h-11 rounded-2xl bg-white/10 backdrop-blur-md flex items-center justify-center border border-white/20 text-white shadow-md">
                <Compass className="w-6 h-6 text-sandstone" />
              </div>
              <span className="font-serif text-2xl font-bold tracking-tight text-white">Voyantra</span>
            </div>

            <div className="space-y-2">
              <h1 className="text-2xl sm:text-3xl font-serif font-bold leading-tight">
                Craft Your Journey Across Pondicherry & Chennai
              </h1>
              <p className="text-xs text-slate-300 leading-relaxed">
                Join our AI-powered travel concierge to generate custom itineraries, discover coastal heritage, and monitor crowd forecasts.
              </p>
            </div>

            <div className="space-y-3 pt-2">
              <div className="flex items-center gap-3 text-xs text-slate-200 bg-white/5 border border-white/10 p-3 rounded-2xl backdrop-blur-xs">
                <div className="w-7 h-7 rounded-lg bg-terracotta/30 flex items-center justify-center shrink-0 text-white">
                  <Sparkles className="w-4 h-4 text-amber-300" />
                </div>
                <span>Conversational AI Concierge grounded in verified catalog data</span>
              </div>

              <div className="flex items-center gap-3 text-xs text-slate-200 bg-white/5 border border-white/10 p-3 rounded-2xl backdrop-blur-xs">
                <div className="w-7 h-7 rounded-lg bg-brand-500/30 flex items-center justify-center shrink-0 text-white">
                  <Compass className="w-4 h-4 text-brand-300" />
                </div>
                <span>Demographic & dietary filtering (Vegetarian, Vegan, Jain)</span>
              </div>

              <div className="flex items-center gap-3 text-xs text-slate-200 bg-white/5 border border-white/10 p-3 rounded-2xl backdrop-blur-xs">
                <div className="w-7 h-7 rounded-lg bg-emerald-500/30 flex items-center justify-center shrink-0 text-white">
                  <ShieldCheck className="w-4 h-4 text-emerald-300" />
                </div>
                <span>Role-based access with dual Traveler and Admin privileges</span>
              </div>
            </div>
          </div>

          <div className="relative z-10 pt-8 border-t border-white/10 text-[11px] text-slate-400">
            <span>Already registered? </span>
            <button
              onClick={() => onOpenLoginModal ? onOpenLoginModal() : setActiveTab('explore')}
              className="text-amber-300 hover:text-white font-bold underline transition-colors"
            >
              Sign In to Your Account
            </button>
          </div>
        </div>

        {/* Right Side: Sign Up Form */}
        <div className="lg:col-span-7 p-8 sm:p-10 space-y-6">
          <div>
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold text-slate-900">Create an Account</h2>
              <span className="text-xs font-semibold px-2.5 py-1 bg-brand-50 text-brand-700 border border-brand-200 rounded-full">
                Quick Setup
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Sign up as a Traveler or Administrator to access all Voyantra planning tools.
            </p>
          </div>

          {/* Role Choice */}
          <div className="space-y-2">
            <label className="block text-xs font-bold text-slate-700">Select Account Role</label>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setRole('user')}
                className={`flex items-center justify-center gap-2 p-3 rounded-2xl border text-xs font-bold transition-all ${
                  role === 'user'
                    ? 'border-brand-600 bg-brand-50/70 text-brand-900 shadow-sm ring-1 ring-brand-600'
                    : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
                }`}
              >
                <User className="w-4 h-4 text-brand-600" />
                <span>Traveler</span>
              </button>

              <button
                type="button"
                onClick={() => setRole('admin')}
                className={`flex items-center justify-center gap-2 p-3 rounded-2xl border text-xs font-bold transition-all ${
                  role === 'admin'
                    ? 'border-amber-500 bg-amber-50/70 text-amber-900 shadow-sm ring-1 ring-amber-500'
                    : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'
                }`}
              >
                <ShieldCheck className="w-4 h-4 text-amber-600" />
                <span>Administrator</span>
              </button>
            </div>
          </div>

          {error && (
            <div className="p-3.5 bg-red-50 border border-red-200 rounded-2xl text-red-700 text-xs font-medium flex items-center gap-2.5 animate-in fade-in">
              <AlertCircle className="w-4 h-4 shrink-0 text-red-600" />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="p-3.5 bg-emerald-50 border border-emerald-200 rounded-2xl text-emerald-800 text-xs font-medium flex items-center gap-2.5 animate-in fade-in">
              <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
              <span>{success}</span>
            </div>
          )}

          <form onSubmit={handleRegister} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Full Name</label>
              <div className="relative">
                <User className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g., Jean Dupont or Ananya Sharma"
                  className="w-full pl-10 pr-3.5 py-2.5 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Email Address</label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@example.com"
                  className="w-full pl-10 pr-3.5 py-2.5 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Password</label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Min. 6 chars"
                    className="w-full pl-10 pr-9 py-2.5 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-2.5 top-2.5 text-slate-400 hover:text-slate-600 p-1"
                  >
                    {showPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Confirm Password</label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Repeat password"
                    className="w-full pl-10 pr-3.5 py-2.5 rounded-xl border border-slate-300 text-xs font-medium focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
                  />
                </div>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className={`w-full py-3 rounded-xl text-xs font-bold text-white shadow-md transition-all flex items-center justify-center gap-2 ${
                role === 'admin'
                  ? 'bg-amber-600 hover:bg-amber-700 shadow-amber-600/20'
                  : 'bg-brand-600 hover:bg-brand-700 shadow-brand-600/20'
              } disabled:opacity-50`}
            >
              {loading ? (
                <span>Creating Account...</span>
              ) : (
                <>
                  <span>Create {role === 'admin' ? 'Administrator' : 'Traveler'} Account</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          <div className="pt-2 text-center text-xs text-slate-500">
            <span>By registering, you agree to Voyantra's cultural respect decorum and terms of service.</span>
          </div>
        </div>

      </div>
    </div>
  );
}