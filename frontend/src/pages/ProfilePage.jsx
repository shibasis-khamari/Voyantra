import React from 'react';
import { User, ShieldCheck, Heart, Trash2, CheckCircle2 } from 'lucide-react';
import { usePreferences } from '../context/PreferencesContext';
import { AGE_GROUPS, DIETARY_OPTIONS, BUDGET_TIERS } from '../types/constants';

export function ProfilePage() {
  const {
    ageGroup,
    setAgeGroup,
    dietaryPreference,
    setDietaryPreference,
    budgetTier,
    setBudgetTier,
    favorites,
    toggleFavorite
  } = usePreferences();

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200 shadow-xs flex items-center gap-5">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-brand-600 to-teal-400 text-white flex items-center justify-center font-bold text-2xl shadow-lg shadow-brand-500/20">
          <User className="w-8 h-8" />
        </div>
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900">Personalization Profile</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Manage your demographic & dietary preferences. Stored transparently and strictly self-declared.
          </p>
        </div>
      </div>

      {/* Settings Form */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200 shadow-xs space-y-8">
        {/* Privacy Note Alert */}
        <div className="p-4 rounded-2xl bg-teal-50 border border-teal-200 flex items-start gap-3">
          <ShieldCheck className="w-5 h-5 text-teal-600 shrink-0 mt-0.5" />
          <div className="text-xs text-teal-900 leading-relaxed">
            <strong>Privacy & Ethics Assurance:</strong> Religious and dietary preferences are 100% optional, opt-in, and strictly self-declared. They are never inferred from user names, IP addresses, or regions.
          </div>
        </div>

        {/* Age Group */}
        <div className="space-y-3">
          <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
            1. Age Demographic Bracket
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {AGE_GROUPS.map(a => {
              const isSelected = ageGroup === a.id;
              return (
                <div
                  key={a.id}
                  onClick={() => setAgeGroup(a.id)}
                  className={`p-4 rounded-2xl border cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-brand-50 border-brand-500 ring-2 ring-brand-500/20'
                      : 'bg-slate-50 border-slate-200 hover:bg-slate-100'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sm text-slate-900">{a.label}</span>
                    {isSelected && <CheckCircle2 className="w-4 h-4 text-brand-600" />}
                  </div>
                  <p className="text-xs text-slate-500 mt-1">{a.desc}</p>
                </div>
              );
            })}
          </div>
        </div>

        {/* Dietary Preferences */}
        <div className="space-y-3">
          <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
            2. Dietary & Faith Preference (Opt-in)
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {DIETARY_OPTIONS.map(d => {
              const isSelected = dietaryPreference === d.id;
              return (
                <div
                  key={d.id}
                  onClick={() => setDietaryPreference(d.id)}
                  className={`p-4 rounded-2xl border cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-brand-50 border-brand-500 ring-2 ring-brand-500/20'
                      : 'bg-slate-50 border-slate-200 hover:bg-slate-100'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sm text-slate-900">{d.label}</span>
                    {isSelected && <CheckCircle2 className="w-4 h-4 text-brand-600" />}
                  </div>
                  <p className="text-xs text-slate-500 mt-1">{d.desc}</p>
                </div>
              );
            })}
          </div>
        </div>

        {/* Budget Tier */}
        <div className="space-y-3">
          <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
            3. Default Budget Preference
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {BUDGET_TIERS.map(b => {
              const isSelected = budgetTier === b.id;
              return (
                <div
                  key={b.id}
                  onClick={() => setBudgetTier(b.id)}
                  className={`p-4 rounded-2xl border cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-brand-50 border-brand-500 ring-2 ring-brand-500/20'
                      : 'bg-slate-50 border-slate-200 hover:bg-slate-100'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sm text-slate-900">{b.label}</span>
                    {isSelected && <CheckCircle2 className="w-4 h-4 text-brand-600" />}
                  </div>
                  <p className="text-xs text-slate-500 mt-1">{b.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
