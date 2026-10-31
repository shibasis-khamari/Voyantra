import React, { useState, useEffect } from 'react';
import { Brain, X, ShieldAlert, Check, Trash2, Save, Loader2, Sparkles } from 'lucide-react';
import { VoyantraAPI } from '../../services/api';

export function MemorySettingsModal({ isOpen, onClose, onMemoryUpdated }) {
  const [profile, setProfile] = useState({
    is_memory_enabled: true,
    preferred_language: 'en',
    travel_pace: 'balanced',
    budget_tier: 'moderate',
    dietary_preference: 'all',
    sensitive_cultural_opt_in: false,
    sensitive_cultural_preferences: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadMemory();
    }
  }, [isOpen]);

  const loadMemory = async () => {
    setIsLoading(true);
    try {
      const data = await VoyantraAPI.getMemoryProfile();
      if (data) {
        setProfile(prev => ({
          ...prev,
          ...data,
          sensitive_cultural_opt_in: Boolean(data.sensitive_cultural_opt_in),
          sensitive_cultural_preferences: data.sensitive_cultural_preferences || ''
        }));
      }
    } catch (e) {
      console.warn("Failed to load memory:", e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const updated = await VoyantraAPI.updateMemoryProfile({
        is_memory_enabled: profile.is_memory_enabled,
        preferred_language: profile.preferred_language,
        travel_pace: profile.travel_pace,
        budget_tier: profile.budget_tier,
        dietary_preference: profile.dietary_preference,
        sensitive_cultural_opt_in: profile.sensitive_cultural_opt_in,
        sensitive_cultural_preferences: profile.sensitive_cultural_preferences
      });
      setSaveSuccess(true);
      if (onMemoryUpdated) onMemoryUpdated(updated);
      setTimeout(() => setSaveSuccess(false), 2500);
    } catch (e) {
      alert("Failed to save memory profile: " + e.message);
    } finally {
      setIsSaving(false);
    }
  };

  const handleClear = async () => {
    if (!window.confirm("Permanently erase all AI remembered preferences?")) return;
    setIsSaving(true);
    try {
      await VoyantraAPI.clearMemoryProfile();
      setProfile({
        is_memory_enabled: true,
        preferred_language: 'en',
        travel_pace: 'balanced',
        budget_tier: 'moderate',
        dietary_preference: 'all',
        sensitive_cultural_opt_in: false,
        sensitive_cultural_preferences: ''
      });
      setSaveSuccess(true);
      if (onMemoryUpdated) onMemoryUpdated(null);
      setTimeout(() => setSaveSuccess(false), 2000);
    } catch (e) {
      alert("Failed to clear memory: " + e.message);
    } finally {
      setIsSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/75 backdrop-blur-md animate-fadeIn">
      <div className="relative w-full max-w-lg bg-slate-900 border border-white/15 rounded-3xl text-white shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        
        {/* Header */}
        <div className="p-5 border-b border-white/10 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-white/10 flex items-center justify-center">
              <Brain className="w-4 h-4 text-[#FCD34D]" />
            </div>
            <div>
              <h3 className="font-extrabold text-sm sm:text-base text-white">AI Memory & Preferences</h3>
              <p className="text-[10px] text-slate-400">Consented personalized travel memory</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-full hover:bg-white/10 text-slate-400 hover:text-white transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Form Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {isLoading ? (
            <div className="text-center py-10 text-xs text-slate-400">
              Loading preferences...
            </div>
          ) : (
            <>
              {/* Enable Memory Toggle */}
              <div className="flex items-center justify-between p-3.5 rounded-2xl bg-white/5 border border-white/10">
                <div>
                  <div className="text-xs font-bold text-white">Enable Long-Term Travel Memory</div>
                  <div className="text-[11px] text-slate-400">Allow AI to recall your pace, diet, and style across sessions.</div>
                </div>
                <button
                  type="button"
                  onClick={() => setProfile(p => ({ ...p, is_memory_enabled: !p.is_memory_enabled }))}
                  className={`w-11 h-6 rounded-full transition-colors relative cursor-pointer ${
                    profile.is_memory_enabled ? 'bg-[#FCD34D]' : 'bg-slate-700'
                  }`}
                >
                  <span className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-slate-950 transition-transform ${
                    profile.is_memory_enabled ? 'translate-x-5' : 'translate-x-0'
                  }`} />
                </button>
              </div>

              {/* Travel Pace & Budget */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] font-bold text-slate-300 block mb-1">Travel Pace</label>
                  <select
                    value={profile.travel_pace || 'balanced'}
                    onChange={(e) => setProfile(p => ({ ...p, travel_pace: e.target.value }))}
                    className="w-full px-3 py-2 rounded-xl bg-white/10 border border-white/15 text-xs text-white outline-none [&>option]:bg-slate-900"
                  >
                    <option value="relaxed">🌴 Relaxed (Leisurely)</option>
                    <option value="balanced">⚖️ Balanced (Recommended)</option>
                    <option value="packed">⚡ Packed (Max Coverage)</option>
                  </select>
                </div>

                <div>
                  <label className="text-[11px] font-bold text-slate-300 block mb-1">Budget Tier</label>
                  <select
                    value={profile.budget_tier || 'moderate'}
                    onChange={(e) => setProfile(p => ({ ...p, budget_tier: e.target.value }))}
                    className="w-full px-3 py-2 rounded-xl bg-white/10 border border-white/15 text-xs text-white outline-none [&>option]:bg-slate-900"
                  >
                    <option value="budget">💰 Budget Conscious</option>
                    <option value="moderate">💳 Moderate / Standard</option>
                    <option value="luxury">✨ Luxury & Premium</option>
                  </select>
                </div>
              </div>

              {/* Dietary Preferences */}
              <div>
                <label className="text-[11px] font-bold text-slate-300 block mb-1">Dietary Preference</label>
                <select
                  value={profile.dietary_preference || 'all'}
                  onChange={(e) => setProfile(p => ({ ...p, dietary_preference: e.target.value }))}
                  className="w-full px-3 py-2 rounded-xl bg-white/10 border border-white/15 text-xs text-white outline-none [&>option]:bg-slate-900"
                >
                  <option value="all">🍽️ All Cuisines (No restrictions)</option>
                  <option value="vegetarian">🥗 Pure Vegetarian</option>
                  <option value="vegan">🌱 Vegan</option>
                  <option value="halal">🥩 Halal Certified</option>
                  <option value="jain">🙏 Jain Vegetarian</option>
                </select>
              </div>

              {/* Sensitive Cultural / Religious Preferences (Strict Opt-In) */}
              <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 space-y-3">
                <div className="flex items-start gap-2.5">
                  <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                  <div>
                    <h4 className="text-xs font-bold text-amber-300">
                      Sensitive Cultural & Religious Memory (Strict Opt-In)
                    </h4>
                    <p className="text-[10px] text-slate-300 leading-relaxed mt-0.5">
                      Explicit consent is required to remember religious observances, temple etiquette preferences, or prayer schedules.
                    </p>
                  </div>
                </div>

                <label className="flex items-center gap-2 cursor-pointer text-xs font-semibold text-slate-200">
                  <input
                    type="checkbox"
                    checked={profile.sensitive_cultural_opt_in}
                    onChange={(e) => setProfile(p => ({ ...p, sensitive_cultural_opt_in: e.target.checked }))}
                    className="rounded border-white/20 text-[#FCD34D] focus:ring-0 cursor-pointer"
                  />
                  <span>I explicitly consent to store sensitive cultural preferences</span>
                </label>

                {profile.sensitive_cultural_opt_in && (
                  <div className="pt-1 animate-fadeIn">
                    <textarea
                      rows={2}
                      value={profile.sensitive_cultural_preferences || ''}
                      onChange={(e) => setProfile(p => ({ ...p, sensitive_cultural_preferences: e.target.value }))}
                      placeholder="e.g. Prefer temple visits during morning darshan; avoid non-veg areas; respect footwear and dress codes"
                      className="w-full p-2.5 rounded-xl bg-black/30 border border-white/20 text-xs text-white outline-none resize-none placeholder-slate-500"
                    />
                  </div>
                )}
              </div>
            </>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t border-white/10 flex items-center justify-between bg-black/20">
          <button
            type="button"
            onClick={handleClear}
            disabled={isSaving}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-rose-400 hover:text-rose-300 hover:bg-rose-500/10 text-xs font-bold transition-all cursor-pointer"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Clear Memory</span>
          </button>

          <div className="flex items-center gap-2">
            {saveSuccess && (
              <span className="text-xs text-emerald-400 font-bold flex items-center gap-1">
                <Check className="w-3.5 h-3.5" /> Saved!
              </span>
            )}
            <button
              type="button"
              onClick={handleSave}
              disabled={isSaving}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-[#FCD34D] hover:bg-amber-300 text-slate-950 text-xs font-bold transition-all cursor-pointer shadow-md"
            >
              {isSaving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
              <span>Save Preferences</span>
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
