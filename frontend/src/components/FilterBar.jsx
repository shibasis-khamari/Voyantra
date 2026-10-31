import React from 'react';
import { Search, SlidersHorizontal, Sparkles, Filter, X } from 'lucide-react';
import { CATEGORIES, BUDGET_TIERS, AGE_GROUPS, DIETARY_OPTIONS } from '../types/constants';

export function FilterBar({
  search,
  setSearch,
  cityFilter = 'all',
  setCityFilter,
  selectedCategory,
  setSelectedCategory,
  selectedBudget,
  setSelectedBudget,
  selectedDietary,
  setSelectedDietary,
  selectedAgeGroup,
  setSelectedAgeGroup,
  onReset
}) {
  const hasActiveFilters = search || cityFilter !== 'all' || selectedCategory !== 'all' || selectedBudget !== '' || selectedDietary !== 'all';

  return (
    <div className="bg-white rounded-3xl p-4 sm:p-5 border border-sandstone shadow-2xs space-y-4">
      {/* Top Search & Filter Bar */}
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-between">
        {/* Search Input */}
        <div className="relative w-full sm:w-96">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search Pondicherry, Chennai, Marina, French Quarter..."
            className="w-full pl-10 pr-4 py-2.5 rounded-full border border-sandstone bg-sandstone-canvas focus:bg-white focus:border-brand-700 text-xs font-semibold outline-none transition-all placeholder:text-slate-400"
          />
          {search && (
            <button
              onClick={() => setSearch('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Quick Selectors */}
        <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto justify-start sm:justify-end">
          {/* City Segmented Toggle (Pondicherry, Chennai, All) */}
          {setCityFilter && (
            <div className="flex items-center p-0.5 rounded-full bg-slate-100 border border-slate-200 text-xs font-semibold">
              <button
                type="button"
                onClick={() => setCityFilter('all')}
                className={`px-3 py-1.5 rounded-full transition-all cursor-pointer ${
                  cityFilter === 'all'
                    ? 'bg-white text-slate-950 font-bold shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                All Destinations
              </button>
              <button
                type="button"
                onClick={() => setCityFilter('pondicherry')}
                className={`px-3 py-1.5 rounded-full transition-all cursor-pointer ${
                  cityFilter === 'pondicherry'
                    ? 'bg-white text-slate-950 font-bold shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Pondicherry
              </button>
              <button
                type="button"
                onClick={() => setCityFilter('chennai')}
                className={`px-3 py-1.5 rounded-full transition-all cursor-pointer ${
                  cityFilter === 'chennai'
                    ? 'bg-white text-slate-950 font-bold shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Chennai
              </button>
            </div>
          )}
          {/* Budget Selector */}
          <select
            value={selectedBudget}
            onChange={(e) => setSelectedBudget(e.target.value)}
            className="px-3.5 py-2 text-xs font-bold rounded-full border border-sandstone bg-sandstone-light text-brand-700 hover:border-brand-700 outline-none cursor-pointer"
          >
            <option value="">All Budgets</option>
            {BUDGET_TIERS.map(b => (
              <option key={b.id} value={b.id}>{b.label}</option>
            ))}
          </select>

          {/* Dietary Selector */}
          <select
            value={selectedDietary}
            onChange={(e) => setSelectedDietary(e.target.value)}
            className="px-3.5 py-2 text-xs font-bold rounded-full border border-sandstone bg-sandstone-light text-brand-700 hover:border-brand-700 outline-none cursor-pointer"
          >
            {DIETARY_OPTIONS.map(d => (
              <option key={d.id} value={d.id}>{d.label}</option>
            ))}
          </select>

          {/* Age Group Simulator */}
          <select
            value={selectedAgeGroup}
            onChange={(e) => setSelectedAgeGroup(e.target.value)}
            className="px-3.5 py-2 text-xs font-bold rounded-full border border-terracotta/30 bg-terracotta/10 text-terracotta hover:bg-terracotta/20 outline-none cursor-pointer"
            title="Simulate recommendations for different age profiles"
          >
            {AGE_GROUPS.map(a => (
              <option key={a.id} value={a.id}>Age: {a.shortLabel} yrs</option>
            ))}
          </select>

          {hasActiveFilters && (
            <button
              onClick={onReset}
              className="px-3 py-2 text-xs font-bold text-rose-600 hover:bg-rose-50 rounded-full transition-colors"
            >
              Reset
            </button>
          )}
        </div>
      </div>

      {/* Category Pills Carousel */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 pt-1 scrollbar-none">
        {CATEGORIES.map(cat => {
          const isActive = selectedCategory === cat.id;
          return (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={`shrink-0 px-4 py-1.5 rounded-full text-xs font-bold transition-all ${
                isActive
                  ? 'bg-brand-700 text-sandstone-canvas shadow-xs'
                  : 'bg-sandstone-light hover:bg-sandstone text-slate-700 border border-sandstone/60'
              }`}
            >
              {cat.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
