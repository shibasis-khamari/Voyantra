import React, { useState, useRef, useEffect } from 'react';
import { Globe, ChevronDown, Check } from 'lucide-react';

export const LANGUAGES = [
  { code: 'auto', label: 'Auto Detect', native: 'Auto', flag: '🌐' },
  { code: 'en', label: 'English', native: 'English', flag: '🇬🇧' },
  { code: 'hi', label: 'Hindi', native: 'हिन्दी', flag: '🇮🇳' },
  { code: 'ta', label: 'Tamil', native: 'தமிழ்', flag: '🇮🇳' }
];

export function LanguageSelector({ selectedLanguage, onSelectLanguage, className = '' }) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  const activeLang = LANGUAGES.find(l => l.code === (selectedLanguage || 'auto')) || LANGUAGES[0];

  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div className={`relative inline-block text-left ${className}`} ref={dropdownRef}>
      <button
        type="button"
        onClick={() => setIsOpen(prev => !prev)}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/10 hover:bg-white/20 border border-white/20 text-white text-xs font-semibold backdrop-blur-md transition-all cursor-pointer shadow-xs"
        title="Select AI Chat & Voice Language"
        aria-expanded={isOpen}
      >
        <span className="text-xs">{activeLang.flag}</span>
        <span className="max-w-[70px] sm:max-w-[100px] truncate">{activeLang.native}</span>
        <ChevronDown className={`w-3 h-3 text-slate-300 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-1.5 w-48 rounded-2xl bg-slate-900/95 backdrop-blur-xl border border-white/15 shadow-2xl py-1 z-50 text-white animate-fadeIn">
          <div className="px-3 py-1.5 border-b border-white/10 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
            Language / भाषा / மொழி
          </div>
          {LANGUAGES.map(lang => {
            const isSelected = (selectedLanguage || 'auto') === lang.code;
            return (
              <button
                key={lang.code}
                type="button"
                onClick={() => {
                  onSelectLanguage(lang.code === 'auto' ? null : lang.code);
                  setIsOpen(false);
                }}
                className={`w-full flex items-center justify-between px-3 py-2 text-xs font-medium hover:bg-white/10 transition-colors cursor-pointer ${
                  isSelected ? 'text-[#FCD34D] font-bold bg-white/5' : 'text-slate-200'
                }`}
              >
                <div className="flex items-center gap-2">
                  <span>{lang.flag}</span>
                  <span>{lang.label}</span>
                  <span className="text-[10px] text-slate-400">({lang.native})</span>
                </div>
                {isSelected && <Check className="w-3.5 h-3.5 text-[#FCD34D]" />}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
