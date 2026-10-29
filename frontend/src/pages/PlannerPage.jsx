import React, { useState, useEffect, useRef } from 'react';
import { 
  Sparkles, Sliders, Luggage, IndianRupee, Clock, Trash2, Edit3, Check, RefreshCw, Plus, GripVertical, Move,
  ArrowRight, CheckCircle2, Navigation, Send, Compass, Lightbulb, Loader2, Calendar,
  Zap, Lock, Unlock, Car, Footprints, AlertTriangle, MapPin, Map as MapIcon, ChevronDown,
  Pencil, MoreHorizontal
} from 'lucide-react';
import { PlaceCard } from '../components/PlaceCard';
import { PlaceModal } from '../components/PlaceModal';
import { FestivalAdvisoryBanner } from '../components/FestivalAdvisoryBanner';
import { TransitLegCard } from '../components/TransitLegCard';
import { VoyantraAPI } from '../services/api';
import { usePreferences } from '../context/PreferencesContext';
import { AGE_GROUPS, DIETARY_OPTIONS, BUDGET_TIERS } from '../types/constants';
import { PageHero } from '../components/PageHero';

function parseBold(str) {
  const parts = str.split(/(\*\*.*?\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i} className="font-bold text-slate-900">{part.slice(2, -2)}</strong>;
    }
    return part;
  });
}

function FormattedMessage({ text }) {
  if (!text) return null;
  const lines = text.split('\n');
  return (
    <div className="space-y-1.5 leading-relaxed text-xs sm:text-sm">
      {lines.map((line, idx) => {
        const trimmed = line.trim();
        if (!trimmed) return <div key={idx} className="h-1" />;
        if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
          return (
            <div key={idx} className="flex items-start gap-2 ml-1 text-slate-700">
              <span className="text-[#FCD34D] font-bold">•</span>
              <span>{parseBold(trimmed.substring(2))}</span>
            </div>
          );
        }
        return (
          <p key={idx} className="text-slate-800">
            {parseBold(trimmed)}
          </p>
        );
      })}
    </div>
  );
}

export function PlannerPage({ setActiveTab }) {
  const { 
    selectedCity,
    setSelectedCity,
    ageGroup, 
    setAgeGroup, 
    dietaryPreference, 
    setDietaryPreference, 
    budgetTier, 
    setBudgetTier,
    tripPlan,
    addToTripPlan,
    removeFromTripPlan,
    clearTripPlan,
    activeItinerary: globalItinerary,
    setActiveItinerary: setGlobalItinerary
  } = usePreferences();

  const [recommendations, setRecommendations] = useState([]);
  const [loadingRecs, setLoadingRecs] = useState(true);
  const [activeModalItem, setActiveModalItem] = useState(null);

  // Phase 2 State: Prompt, Preset Suggestions & AI Itinerary
  const [promptText, setPromptText] = useState('');
  const [durationDays, setDurationDays] = useState(1);
  const [presetSuggestions, setPresetSuggestions] = useState([]);
  const [selectedPresetId, setSelectedPresetId] = useState('');
  const [aiItinerary, setAiItinerary] = useState(() => globalItinerary || null);
  const [availableAlternatives, setAvailableAlternatives] = useState([]);
  const [loadingAi, setLoadingAi] = useState(false);
  const [editingSlot, setEditingSlot] = useState(null);
  const [editingSlotData, setEditingSlotData] = useState(null);

  // Helper to extract duration from conversational text (defaults to 1 if not mentioned)
  const extractDurationFromText = (text) => {
    if (!text) return 1;
    const lower = text.toLowerCase();
    const digitMatch = lower.match(/\b([1-7])\s*-?\s*days?\b/);
    if (digitMatch) return parseInt(digitMatch[1], 10);
    if (/\b(one|1)\s*-?\s*days?\b/.test(lower)) return 1;
    if (/\b(two|2)\s*-?\s*days?\b/.test(lower) || /\bweekend\b/.test(lower)) return 2;
    if (/\b(three|3)\s*-?\s*days?\b/.test(lower)) return 3;
    if (/\b(four|4)\s*-?\s*days?\b/.test(lower)) return 4;
    if (/\b(five|5)\s*-?\s*days?\b/.test(lower)) return 5;
    if (/\b(six|6)\s*-?\s*days?\b/.test(lower)) return 6;
    if (/\b(seven|7)\s*-?\s*days?\b/.test(lower) || /\bweek\b/.test(lower)) return 7;
    return 1; // Default to 1 day if user doesn't mention number of days
  };
  
  // Drag & Drop State
  const [draggedCard, setDraggedCard] = useState(null);
  const [dragOverTarget, setDragOverTarget] = useState(null);
  
  // AI Conversational Chatbox & Itinerary State
  const [chatMessages, setChatMessages] = useState([
    {
      id: 'welcome-msg',
      sender: 'ai',
      text: "Hello! 👋 I'm your **Voyantra AI Concierge**.\n\nAsk me about hotels, dining, top attractions, comparisons, or custom itineraries for destinations across India and anywhere in the world.",
      timestamp: 'Just now',
      suggested_followups: [
        "Suggest the best hotels in Mumbai",
        "What are the best places to visit in Tokyo?",
        "Find affordable resorts in Bali",
        "Plan a 7-day trip to Himachal Pradesh"
      ]
    }
  ]);
  const [chatInputText, setChatInputText] = useState('');
  const [isRefining, setIsRefining] = useState(false);
  const chatEndRef = useRef(null);

  // Phase 4 State: TSP Day Optimization & Navigation
  const [dayOptimizations, setDayOptimizations] = useState({});
  const [optimizingDay, setOptimizingDay] = useState(null);
  const [lockedSlots, setLockedSlots] = useState({});
  const [transitModes, setTransitModes] = useState({});
  const [showDayMap, setShowDayMap] = useState({});

  const itineraryRef = useRef(null);
  const [backendError, setBackendError] = useState(null);

  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatMessages, isRefining]);

  useEffect(() => {
    fetchRecommendations();
    loadPresetSuggestions();
  }, [ageGroup, dietaryPreference, budgetTier, selectedCity]);

  const loadPresetSuggestions = async () => {
    try {
      const suggs = await VoyantraAPI.getPresetSuggestions();
      setPresetSuggestions(suggs);
      setBackendError(null);
    } catch (e) {
      setBackendError(e.message);
    }
  };

  const fetchRecommendations = async () => {
    setLoadingRecs(true);
    try {
      const data = await VoyantraAPI.getPersonalizedRecommendations({
        city_id: selectedCity,
        age_group: ageGroup,
        dietary_preference: dietaryPreference,
        budget_tier: budgetTier
      });
      setRecommendations(data.ranked_places || []);
      setBackendError(null);
    } catch (e) {
      setBackendError(e.message);
    } finally {
      setLoadingRecs(false);
    }
  };

  // Unified AI Travel Concierge Message Handler (Greetings, Q&A, Places & Flexible Itinerary)
  const handleSendMessage = async (textToSend = null) => {
    const text = (textToSend || chatInputText).trim();
    if (!text || isRefining) return;

    // Automatically detect duration from text or default to 1 day
    const detectedDays = extractDurationFromText(text);
    setDurationDays(detectedDays);

    const timeNow = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const userMsg = {
      id: `usr-${Date.now()}`,
      sender: 'user',
      text: text,
      timestamp: timeNow
    };

    setChatMessages(prev => [...prev, userMsg]);
    setChatInputText('');
    setIsRefining(true);
    setBackendError(null);

    try {
      const history = chatMessages.map(m => ({
        role: m.sender === 'user' ? 'user' : 'assistant',
        content: m.text
      }));

      const res = await VoyantraAPI.chatWithAi({
        city_id: selectedCity,
        message: text,
        conversation_history: history,
        current_itinerary: aiItinerary,
        age_group: ageGroup,
        dietary_preference: dietaryPreference,
        duration_days: detectedDays
      });

      if (res) {
        const aiMsg = {
          id: `ai-${Date.now()}`,
          sender: 'ai',
          text: res.reply_message,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          intent: res.intent,
          recommended_places: res.recommended_places || [],
          suggested_followups: res.suggested_followups || [],
          hasItinerary: Boolean(res.itinerary)
        };
        setChatMessages(prev => [...prev, aiMsg]);

        if (res.city_id && setSelectedCity && res.city_id.toLowerCase() !== selectedCity?.toLowerCase()) {
          setSelectedCity(res.city_id);
        }

        if (res.itinerary) {
          setAiItinerary(res.itinerary);
          setGlobalItinerary(res.itinerary);
          setTimeout(() => {
            itineraryRef.current?.scrollIntoView({ behavior: 'smooth' });
          }, 350);
        }
      }
    } catch (e) {
      console.error("Chat error:", e);
      const errorMsg = {
        id: `err-${Date.now()}`,
        sender: 'ai',
        text: `Sorry, I encountered an issue: ${e.message}. Please check if the backend server is running.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setChatMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsRefining(false);
    }
  };

  const selectPreset = (sugg) => {
    if (!sugg) return;
    setSelectedPresetId(sugg.id);
    handleSendMessage(sugg.prompt);
  };

  // Phase 4 Day Optimization & Route Calculation Helpers
  const findCoordinatesForPlace = (placeName) => {
    if (!placeName) return { lat: 11.9416, lng: 79.8083 };
    const norm = placeName.toLowerCase().trim();
    const found = recommendations.find(r => 
      r.place && r.place.name && (r.place.name.toLowerCase().includes(norm) || norm.includes(r.place.name.toLowerCase()))
    );
    if (found?.place?.coordinates?.lat && found?.place?.coordinates?.lng) {
      return { lat: found.place.coordinates.lat, lng: found.place.coordinates.lng };
    }
    if (selectedCity === 'chennai') {
      return { lat: 13.0827, lng: 80.2707 };
    }
    return { lat: 11.9416, lng: 79.8083 };
  };

  const handleOptimizeDay = async (dayIdx, overrideMode = null) => {
    if (!aiItinerary || !aiItinerary.days || !aiItinerary.days[dayIdx]) return;
    const day = aiItinerary.days[dayIdx];
    const mode = overrideMode || transitModes[dayIdx] || 'driving';

    setOptimizingDay(dayIdx);
    setBackendError(null);

    try {
      const slotKeys = Object.keys(day).filter(k => !['day_number', 'theme'].includes(k) && !!day[k]);
      if (slotKeys.length === 0) {
        setBackendError("No places to optimize for this day.");
        return;
      }
      const slots = slotKeys.map((k) => {
        const rawSlot = day[k];
        const name = typeof rawSlot === 'string' ? rawSlot : (rawSlot.place_name || 'Destination');
        const coords = findCoordinatesForPlace(name);

        let anchor = null;
        if (k === 'morning') anchor = 'morning';
        else if (k === 'afternoon') anchor = 'afternoon';
        else if (k === 'evening') anchor = 'sunset';

        const slotId = `d${dayIdx}_${k}`;
        const isLocked = !!lockedSlots[slotId];

        return {
          slot_id: slotId,
          place_name: name,
          coordinates: coords,
          time_anchor: anchor,
          is_locked: isLocked,
          visit_duration_minutes: 60,
          opening_hours: { is_verified: false }
        };
      });

      const res = await VoyantraAPI.optimizeDaySchedule({
        day_number: day.day_number || (dayIdx + 1),
        city_id: selectedCity || 'pondicherry',
        mode,
        travel_date: '2026-11-15',
        slots
      });

      setDayOptimizations(prev => ({
        ...prev,
        [dayIdx]: res
      }));
    } catch (err) {
      setBackendError(`Optimization failed: ${err.message}`);
    } finally {
      setOptimizingDay(null);
    }
  };

  const toggleLockSlot = (slotId) => {
    setLockedSlots(prev => ({
      ...prev,
      [slotId]: !prev[slotId]
    }));
  };

  const handleToggleTransitMode = (dayIdx) => {
    const currentMode = transitModes[dayIdx] || 'driving';
    const newMode = currentMode === 'driving' ? 'walking' : 'driving';
    setTransitModes(prev => ({ ...prev, [dayIdx]: newMode }));
    handleOptimizeDay(dayIdx, newMode);
  };

  // DRAG AND DROP HANDLERS
  const handleDragStart = (e, dayIdx, slotKey, slotData) => {
    setDraggedCard({ dayIdx, slotKey, slotData });
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', JSON.stringify({ dayIdx, slotKey }));
  };

  const handleDragOver = (e, dayIdx, slotKey) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    if (!dragOverTarget || dragOverTarget.dayIdx !== dayIdx || dragOverTarget.slotKey !== slotKey) {
      setDragOverTarget({ dayIdx, slotKey });
    }
  };

  const handleDrop = (e, targetDayIdx, targetSlotKey) => {
    e.preventDefault();
    setDragOverTarget(null);
    if (!draggedCard || !aiItinerary) return;

    const { dayIdx: fromDayIdx, slotKey: fromSlotKey, slotData: fromData } = draggedCard;
    if (fromDayIdx === targetDayIdx && fromSlotKey === targetSlotKey) return;

    const updatedDays = [...aiItinerary.days];
    const targetData = updatedDays[targetDayIdx][targetSlotKey];

    // Swap items between slots across days or within same day
    updatedDays[targetDayIdx][targetSlotKey] = { ...fromData };

    if (targetData) {
      updatedDays[fromDayIdx][fromSlotKey] = { ...targetData };
    } else {
      delete updatedDays[fromDayIdx][fromSlotKey];
    }

    setAiItinerary({ ...aiItinerary, days: updatedDays });
    setDraggedCard(null);
  };

  const handleDropDirect = (fromDayIdx, fromSlotKey, targetDayIdx, targetSlotKey) => {
    if (!aiItinerary) return;
    const updatedDays = [...aiItinerary.days];
    const fromData = updatedDays[fromDayIdx]?.[fromSlotKey];
    const targetData = updatedDays[targetDayIdx]?.[targetSlotKey];
    if (!fromData) return;

    updatedDays[targetDayIdx][targetSlotKey] = { ...fromData };
    if (targetData) {
      updatedDays[fromDayIdx][fromSlotKey] = { ...targetData };
    } else {
      delete updatedDays[fromDayIdx][fromSlotKey];
    }
    setAiItinerary({ ...aiItinerary, days: updatedDays });
  };

  const handleSaveSlotChanges = (dayIdx, slotKey) => {
    if (!editingSlotData || !aiItinerary) return;
    const { place_name, notes, duration } = editingSlotData;
    
    setAiItinerary(prev => {
      if (!prev || !prev.days) return prev;
      const newDays = [...prev.days];
      const day = { ...newDays[dayIdx] };
      const oldSlot = day[slotKey] || {};
      day[slotKey] = {
        ...oldSlot,
        place_name: (place_name || '').trim(),
        activity_note: (notes || '').trim(),
        est_time: (duration || '').trim()
      };
      newDays[dayIdx] = day;
      const updated = { ...prev, days: newDays };
      setGlobalItinerary(updated);
      return updated;
    });
    setEditingSlotData(null);
  };

  // ITINERARY CUSTOMIZATION HANDLERS
  const handleSwapPlace = (dayIdx, timeSlot, newPlaceName) => {
    if (!aiItinerary) return;
    const updatedDays = [...aiItinerary.days];
    if (updatedDays[dayIdx] && updatedDays[dayIdx][timeSlot]) {
      updatedDays[dayIdx][timeSlot].place_name = newPlaceName;
    }
    setAiItinerary({ ...aiItinerary, days: updatedDays });
    setEditingSlot(null);
  };

  const handleEditNoteOrTime = (dayIdx, timeSlot, field, value) => {
    if (!aiItinerary) return;
    const updatedDays = [...aiItinerary.days];
    if (updatedDays[dayIdx] && updatedDays[dayIdx][timeSlot]) {
      updatedDays[dayIdx][timeSlot][field] = value;
    }
    setAiItinerary({ ...aiItinerary, days: updatedDays });
  };

  const handleRemoveSlot = (dayIdx, timeSlot) => {
    if (!aiItinerary) return;
    const updatedDays = [...aiItinerary.days];
    if (updatedDays[dayIdx]) {
      delete updatedDays[dayIdx][timeSlot];
    }
    setAiItinerary({ ...aiItinerary, days: updatedDays });
  };

  const handleAddSlotToDay = (dayIdx) => {
    if (!aiItinerary) return;
    const updatedDays = [...aiItinerary.days];
    const defaultPlace = availableAlternatives[0]?.name || "Local Landmark Walk";
    const slotCount = Object.keys(updatedDays[dayIdx]).filter(k => k.startsWith('custom_')).length + 1;
    const slotKey = `custom_${slotCount}`;
    updatedDays[dayIdx][slotKey] = {
      place_name: defaultPlace,
      activity_note: "Custom user visiting activity slot.",
      est_time: "Flexible Time"
    };
    setAiItinerary({ ...aiItinerary, days: updatedDays });
  };

  const handleAddAllToBasket = () => {
    if (!aiItinerary) return;
    aiItinerary.days.forEach(d => {
      Object.keys(d).forEach(slotKey => {
        if (['day_number', 'theme'].includes(slotKey)) return;
        const slot = d[slotKey];
        if (slot && slot.place_name) {
          const matchRec = recommendations.find(r => r.place.name.toLowerCase() === slot.place_name.toLowerCase());
          if (matchRec) {
            addToTripPlan(matchRec.place);
          }
        }
      });
    });
  };

  // Calculate basket totals
  const totalCost = tripPlan.reduce((acc, item) => acc + (item.estimated_cost_inr || 0), 0);
  const totalMinutes = tripPlan.reduce((acc, item) => acc + (item.duration_minutes || 0), 0);
  const totalHours = (totalMinutes / 60).toFixed(1);

  const selectedPreset = presetSuggestions.find(s => s.id === selectedPresetId);

  return (
    <div className="relative min-h-screen">
      {/* Fixed Window Background Image (Prominently Visible Coastal View) */}
      <div 
        className="fixed inset-0 z-0 overflow-hidden pointer-events-none select-none"
        aria-hidden="true"
      >
        <img
          src="/images/luisa-linkous-L03SoHMhbz8-unsplash.jpg"
          alt="Scenic Coastal Horizon"
          className="w-full h-full object-cover object-center fixed scale-105 filter brightness-[0.98] contrast-[1.04] saturate-[1.12]"
        />
        {/* Soft Luminous Atmospheric Veils for True Glass Refraction */}
        <div className="absolute inset-0 bg-slate-950/20" />
        <div className="absolute inset-0 bg-gradient-to-b from-slate-950/35 via-transparent to-slate-950/45" />
      </div>

      {/* Main Page Content Layer */}
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Phase 3 Festival Advisory Banner */}
        <FestivalAdvisoryBanner selectedCity={selectedCity} />

        {/* Backend Disconnected Notice */}
        {backendError && (
          <div className="p-4 rounded-2xl bg-rose-50/90 backdrop-blur-md border border-rose-300 text-rose-900 space-y-2 shadow-md animate-fadeIn">
            <div className="flex items-center gap-2 font-black text-rose-800 text-xs uppercase tracking-wider">
              <span className="px-2 py-0.5 rounded bg-rose-200 text-rose-900 font-extrabold text-[10px]">
                ⚠️ BACKEND DISCONNECTED
              </span>
            </div>
            <p className="text-xs text-rose-900 leading-relaxed font-medium">
              {backendError}
            </p>
            <div className="p-2 rounded-lg bg-rose-100/90 font-mono text-[11px] text-rose-950 font-bold">
              Start Server Command: cd E:\Voyantra\backend && python run.py
            </div>
          </div>
        )}

        {/* Minimal Glass Preset Options Dropdown */}
        <div className="p-4 sm:p-5 rounded-3xl bg-white/70 backdrop-blur-xl border border-white/50 shadow-xl space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-white/40 pb-2.5">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-[#FCD34D]/25 border border-[#FCD34D]/50 flex items-center justify-center text-slate-950 shrink-0 shadow-2xs">
                <Sparkles className="w-4 h-4 text-amber-700" />
              </div>
              <div>
                <h3 className="text-sm sm:text-base font-bold font-sans text-slate-900 leading-tight">
                  Curated Travel Presets
                </h3>
                <p className="text-xs text-slate-600 font-sans">
                  Select a template to instantly generate your tailored coastal route
                </p>
              </div>
            </div>
            
            <span className="self-start sm:self-center px-2.5 py-1 rounded-full bg-white/60 border border-white/50 text-[11px] font-bold text-slate-700 font-sans">
              {presetSuggestions.length} Presets Available
            </span>
          </div>

          {/* Dropdown Selector & Quick Action */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2.5">
            <div className="relative flex-1">
              <select
                value={selectedPresetId}
                onChange={(e) => {
                  const newId = e.target.value;
                  setSelectedPresetId(newId);
                  const found = presetSuggestions.find(s => s.id === newId);
                  if (found) {
                    selectPreset(found);
                  }
                }}
                className="w-full appearance-none px-4 py-2.5 pr-10 rounded-2xl bg-white/80 hover:bg-white border border-white/60 focus:border-[#FCD34D] focus:ring-2 focus:ring-[#FCD34D]/30 text-xs sm:text-sm font-semibold text-slate-900 transition-all cursor-pointer shadow-xs outline-none"
              >
                <option value="">✨ Select a Curated Travel Preset (Click to Generate)...</option>
                {presetSuggestions.map((sugg) => (
                  <option key={sugg.id} value={sugg.id}>
                    {sugg.icon} {sugg.title} — [{sugg.category?.toUpperCase()}]
                  </option>
                ))}
              </select>
              <div className="pointer-events-none absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-500">
                <ChevronDown className="w-4 h-4" />
              </div>
            </div>

            {selectedPreset && (
              <button
                onClick={() => selectPreset(selectedPreset)}
                disabled={loadingAi}
                className="px-5 py-2.5 rounded-2xl bg-[#FCD34D] hover:bg-amber-400 text-slate-950 font-bold text-xs sm:text-sm font-sans shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2 cursor-pointer shrink-0 disabled:opacity-50"
              >
                {loadingAi ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin text-slate-950" />
                    <span>Generating...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 text-amber-900" />
                    <span>Re-Generate Preset</span>
                  </>
                )}
              </button>
            )}
          </div>

          {/* Active Preset Pill */}
          {selectedPreset && (
            <div className="p-3 rounded-2xl bg-white/60 backdrop-blur-md border border-white/50 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2.5 text-xs animate-fadeIn">
              <div className="flex items-center gap-2.5 min-w-0">
                <span className="text-xl p-1 rounded-xl bg-white/80 border border-white/60 shrink-0">
                  {selectedPreset.icon}
                </span>
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-900 font-sans">{selectedPreset.title}</span>
                    <span className="px-2 py-0.5 rounded-full bg-[#FCD34D]/25 border border-[#FCD34D]/50 text-slate-900 text-[10px] font-bold uppercase tracking-wider font-sans">
                      {selectedPreset.category}
                    </span>
                  </div>
                  <p className="text-slate-600 italic text-[11px] truncate mt-0.5">
                    "{selectedPreset.prompt}"
                  </p>
                </div>
              </div>
              <button
                onClick={() => setChatInputText(selectedPreset.prompt)}
                className="text-[11px] font-bold text-amber-800 hover:text-amber-950 hover:underline shrink-0 whitespace-nowrap self-end sm:self-center cursor-pointer"
                title="Paste prompt into chat input to customize before sending"
              >
                Customize in Chat ✎
              </button>
            </div>
          )}
        </div>

      {/* Interactive AI Travel Concierge Chatbox (Frosted Glass Finish) */}
      <div className="bg-white/70 backdrop-blur-xl rounded-3xl border border-white/50 shadow-2xl overflow-hidden space-y-0">
        {/* Chatbox Header */}
        <div className="bg-slate-900/90 backdrop-blur-xl p-4 sm:p-5 text-white flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-white/10 backdrop-blur-md border border-white/20 flex items-center justify-center shadow-inner">
              <img 
                src="/images/logo/voyantra-icon-nobg-crop.png" 
                alt="Voyantra AI" 
                className="w-7 h-7 object-contain drop-shadow-xs" 
              />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-extrabold text-sm sm:text-base tracking-tight text-white font-sans">Voyantra AI Concierge</h3>
                <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-[#FCD34D]/20 text-[#FCD34D] border border-[#FCD34D]/40 text-[10px] font-bold">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#FCD34D] animate-ping"></span>
                  Live
                </span>
              </div>
              <p className="text-[11px] text-slate-300 font-sans">
                Natural conversational trip curation & local recommendations
              </p>
            </div>
          </div>

        </div>

        {/* Conversation Stream */}
        <div className="p-4 sm:p-6 space-y-4 max-h-[460px] overflow-y-auto bg-slate-900/5 backdrop-blur-xs">
          {chatMessages.map((msg) => (
            <div
              key={msg.id}
              className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'} space-y-2 animate-fadeIn`}
            >
              <div
                className={`max-w-[90%] sm:max-w-[80%] p-4 rounded-2xl text-xs sm:text-sm shadow-sm ${
                  msg.sender === 'user'
                    ? 'bg-gradient-to-r from-terracotta to-orange-500 text-white rounded-br-none shadow-md font-sans'
                    : 'bg-white/80 backdrop-blur-md border border-white/60 text-slate-900 rounded-bl-none shadow-sm'
                }`}
              >
                {msg.sender === 'user' ? (
                  <p className="font-medium leading-relaxed whitespace-pre-wrap">{msg.text}</p>
                ) : (
                  <FormattedMessage text={msg.text} />
                )}
                
                <span className={`text-[9px] mt-2 block font-medium ${msg.sender === 'user' ? 'text-amber-100 text-right' : 'text-slate-400'}`}>
                  {msg.timestamp}
                </span>
              </div>

              {/* Recommended Place Mini Cards (if returned) */}
              {msg.recommended_places && msg.recommended_places.length > 0 && (
                <div className="w-full max-w-[90%] sm:max-w-[80%] grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-1">
                  {msg.recommended_places.map((place) => (
                    <div
                      key={place.id}
                      className="p-3 rounded-2xl bg-white/80 backdrop-blur-md border border-white/60 shadow-xs flex flex-col justify-between gap-2 hover:border-[#FCD34D] transition-all"
                    >
                      <div>
                        <div className="flex items-center justify-between gap-1">
                          <span className="font-bold text-xs text-slate-900 line-clamp-1">{place.name}</span>
                          <span className="px-1.5 py-0.5 rounded text-[9px] font-bold uppercase bg-[#FCD34D]/25 text-slate-950 border border-[#FCD34D]/50">
                            {place.category}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-600 mt-0.5">
                          Cost: <strong className="text-slate-900">₹{place.estimated_cost_inr}</strong> • {place.duration_minutes} mins
                        </p>
                        {place.highlights && place.highlights.length > 0 && (
                          <p className="text-[10px] text-amber-800 mt-1 line-clamp-1">
                            ✨ {place.highlights[0]}
                          </p>
                        )}
                      </div>
                      <button
                        onClick={() => addToTripPlan(place)}
                        className="w-full py-1.5 rounded-xl bg-[#FCD34D]/25 hover:bg-[#FCD34D]/40 text-slate-950 text-[10px] font-bold border border-[#FCD34D]/50 transition-colors cursor-pointer"
                      >
                        + Add to Trip Plan
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Itinerary Ready Action Banner */}
              {msg.hasItinerary && (
                <div className="w-full max-w-[90%] sm:max-w-[80%] p-3.5 rounded-2xl bg-white/85 backdrop-blur-md border border-[#FCD34D]/60 text-slate-900 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-md">
                  <div className="flex items-center gap-2.5">
                    <span className="text-xl">🗺️</span>
                    <div>
                      <span className="font-bold text-xs text-slate-900 font-sans">Itinerary & Route Ready</span>
                      <p className="text-[10px] text-slate-600">Explore verified itinerary & timeline or open the interactive map</p>
                    </div>
                  </div>
                  <div className="flex flex-wrap items-center gap-2 self-start sm:self-auto shrink-0">
                    <button
                      onClick={() => {
                        setGlobalItinerary(aiItinerary);
                        if (setActiveTab) setActiveTab('map');
                      }}
                      className="px-3.5 py-1.5 rounded-xl bg-[#FCD34D] hover:bg-amber-300 text-slate-950 text-[11px] font-black font-sans shadow-xs flex items-center gap-1.5 transition-all cursor-pointer"
                    >
                      <Compass className="w-3.5 h-3.5 text-slate-950" />
                      <span>View Map & Details →</span>
                    </button>
                    <button
                      onClick={() => itineraryRef.current?.scrollIntoView({ behavior: 'smooth' })}
                      className="px-3 py-1.5 rounded-xl bg-white/80 border border-slate-300 hover:bg-white text-slate-800 text-[11px] font-bold font-sans shadow-2xs flex items-center gap-1 transition-all cursor-pointer"
                    >
                      <span>Timeline</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              )}

              {/* Contextual Suggested Followups */}
              {msg.suggested_followups && msg.suggested_followups.length > 0 && (
                <div className="flex flex-wrap gap-1.5 pt-1 pl-1">
                  {msg.suggested_followups.map((fup, i) => (
                    <button
                      key={i}
                      onClick={() => handleSendMessage(fup)}
                      disabled={isRefining}
                      className="px-2.5 py-1 rounded-full bg-white/80 backdrop-blur-sm hover:bg-[#FCD34D]/25 hover:text-slate-950 text-slate-700 text-[10px] sm:text-[11px] font-bold border border-white/60 hover:border-[#FCD34D] transition-all shadow-2xs disabled:opacity-50 cursor-pointer"
                    >
                      💡 {fup}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}

          {isRefining && (
            <div className="flex items-start gap-2.5 animate-fadeIn">
              <div className="w-7 h-7 rounded-full bg-slate-900 p-1 flex items-center justify-center shadow-xs border border-[#FCD34D]/40">
                <img 
                  src="/images/logo/voyantra-icon-nobg-crop.png" 
                  alt="Voyantra" 
                  className="w-full h-full object-contain" 
                />
              </div>
              <div className="p-3.5 rounded-2xl bg-white/80 backdrop-blur-md border border-white/60 text-xs text-slate-900 font-bold flex items-center gap-2 shadow-xs">
                <Loader2 className="w-3.5 h-3.5 text-terracotta animate-spin" />
                <span>Voyantra Concierge is typing...</span>
              </div>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* Chat Input Bar */}
        <div className="p-3 sm:p-4 bg-white/70 backdrop-blur-xl border-t border-white/40">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="flex items-center gap-2"
          >
            <input
              type="text"
              value={chatInputText}
              onChange={(e) => setChatInputText(e.target.value)}
              placeholder="Ask a question or request a custom schedule (e.g. 'Best cafes in Pondy', 'Plan a 2-day relaxed trip')..."
              disabled={isRefining}
              className="flex-1 px-4 py-2.5 rounded-2xl border border-white/60 bg-white/80 focus:bg-white focus:border-[#FCD34D] focus:ring-2 focus:ring-[#FCD34D]/30 text-xs sm:text-sm font-medium outline-none transition-all placeholder-slate-400"
            />
            <button
              type="submit"
              disabled={isRefining || !chatInputText.trim()}
              className="px-5 py-2.5 rounded-2xl bg-terracotta hover:bg-terracotta/90 disabled:opacity-50 text-white text-xs sm:text-sm font-bold flex items-center gap-2 shadow-md transition-all shrink-0 cursor-pointer"
            >
              {isRefining ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              <span className="hidden sm:inline">Send</span>
            </button>
          </form>
        </div>
      </div>

      {/* Target Ref Anchor for Window Scroll */}
      <div ref={itineraryRef} />

      {/* Generated AI Day-by-Day Itinerary Result View (Frosted Glass Finish) */}
      {aiItinerary && !loadingAi && (
        <div className="bg-white/70 backdrop-blur-xl rounded-3xl p-6 border border-white/50 shadow-2xl space-y-6 animate-fadeIn">
          {/* Source Notice Banner */}
          {aiItinerary.source === 'fallback' && (
            <div className="p-3.5 rounded-2xl bg-amber-50/90 border border-amber-300 text-amber-900 text-xs flex items-center justify-between gap-2 shadow-2xs">
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded-md bg-amber-200 text-amber-900 font-extrabold text-[10px] uppercase">
                  Offline Planner
                </span>
                <span className="font-medium text-amber-950">
                  Generated by the offline planner ({aiItinerary.fallback_reason || 'offline model'})
                </span>
              </div>
            </div>
          )}

          {/* Top Chips Row */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="px-3.5 py-1 rounded-full bg-[#eee9e2] text-slate-800 text-xs font-semibold font-sans">
              {aiItinerary.days?.length || 1} days
            </span>
            <span className="px-3.5 py-1 rounded-full bg-[#eee9e2] text-slate-800 text-xs font-semibold font-sans">
              Family-friendly
            </span>
            <span className="px-3.5 py-1 rounded-full bg-[#eee9e2] text-slate-800 text-xs font-semibold font-sans">
              Est. budget ₹{aiItinerary.total_estimated_budget_inr}
            </span>
          </div>

          {/* Title & Subtitle */}
          <div className="space-y-1">
            <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight leading-tight font-sans">
              {aiItinerary.itinerary_title}
            </h2>
            <p className="text-xs sm:text-sm text-slate-600 max-w-2xl leading-relaxed font-sans">
              {aiItinerary.summary}
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap items-center gap-3 pt-1">
            <button
              onClick={() => {
                setGlobalItinerary(aiItinerary);
                if (setActiveTab) setActiveTab('map');
              }}
              className="px-5 py-2.5 rounded-xl bg-[#0f172a] hover:bg-slate-800 text-white text-xs sm:text-sm font-bold font-sans flex items-center gap-2 shadow-md cursor-pointer transition-all border border-slate-700"
            >
              <Compass className="w-4 h-4 text-[#FCD34D]" />
              <span>View Map & Details</span>
            </button>

            <button
              onClick={handleAddAllToBasket}
              className="px-5 py-2.5 rounded-xl bg-white hover:bg-slate-50 text-slate-800 border border-slate-200/90 text-xs sm:text-sm font-bold font-sans flex items-center gap-2 shadow-2xs cursor-pointer transition-all"
            >
              <Luggage className="w-4 h-4 text-slate-700" />
              <span>Save to basket</span>
            </button>
          </div>

          {/* Instructional Subtext */}
          <p className="text-xs text-slate-500 font-sans">
            Drag the handle on any stop to reorder it or move it to another day. Use the pencil to edit.
          </p>

          {/* AI Location Feasibility & Unavailability Clarity Advisory */}
          {aiItinerary.unavailability_notice && (
            <div className="p-4 rounded-2xl bg-amber-50 border-2 border-amber-300/80 text-amber-900 text-xs space-y-1.5 shadow-sm">
              <div className="flex items-center gap-2 font-black text-amber-800 text-xs uppercase tracking-wider">
                <span className="px-2 py-0.5 rounded-md bg-amber-200 text-amber-900 font-extrabold text-[10px]">
                  ⚠️ AI REALITY CHECK & FEASIBILITY ADVISORY
                </span>
              </div>
              <p className="font-medium leading-relaxed text-amber-950">
                {aiItinerary.unavailability_notice}
              </p>
            </div>
          )}

          {/* Days Timeline with Image 1 Card Finish */}
          <div className="space-y-6 pt-2">
            {aiItinerary.days.map((day, dayIdx) => {
              const isOptimizing = optimizingDay === dayIdx;
              const slotKeys = Object.keys(day).filter(k => !['day_number', 'theme'].includes(k) && !!day[k]);
              const orderWeights = { morning: 1, afternoon: 2, evening: 3 };
              slotKeys.sort((a, b) => (orderWeights[a] || 4) - (orderWeights[b] || 4));

              const isDraggingFromOtherDay = draggedCard && draggedCard.dayIdx !== dayIdx;

              return (
                <div 
                  key={day.day_number || dayIdx} 
                  className="bg-[#f5f1eb] rounded-3xl p-6 sm:p-7 border border-[#e8dfd5] space-y-4 shadow-2xs transition-all"
                >
                  {/* Day Header */}
                  <div className="flex flex-wrap items-center justify-between gap-3 pb-2 border-b border-[#e5dcd1]">
                    <div className="flex items-center gap-2.5">
                      <span className="w-6 h-6 rounded-full bg-slate-900 text-[#FCD34D] flex items-center justify-center text-xs font-black font-sans shrink-0">
                        {day.day_number}
                      </span>
                      <h3 className="text-sm sm:text-base font-extrabold text-slate-900 uppercase tracking-wider font-sans">
                        Day {day.day_number}: {day.theme}
                      </h3>
                    </div>

                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => handleOptimizeDay(dayIdx)}
                        disabled={isOptimizing}
                        className="bg-white hover:bg-slate-50 border border-slate-200/90 text-slate-800 px-3.5 py-1.5 rounded-xl text-xs font-bold shadow-2xs flex items-center gap-1.5 cursor-pointer transition-all"
                      >
                        {isOptimizing ? (
                          <>
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            <span>Optimizing...</span>
                          </>
                        ) : (
                          <>
                            <Zap className="w-3.5 h-3.5 text-amber-700 fill-[#FCD34D]" />
                            <span>Optimize route</span>
                          </>
                        )}
                      </button>

                      <button
                        onClick={() => handleAddSlotToDay(dayIdx)}
                        className="text-xs font-bold text-slate-700 hover:text-slate-950 flex items-center gap-1 cursor-pointer transition-colors"
                      >
                        <Plus className="w-3.5 h-3.5" />
                        <span>Add slot</span>
                      </button>
                    </div>
                  </div>

                  {/* Drop zone indicator when dragging between days */}
                  {isDraggingFromOtherDay && (
                    <div 
                      onDragOver={(e) => {
                        e.preventDefault();
                        e.dataTransfer.dropEffect = 'move';
                      }}
                      onDrop={(e) => {
                        e.preventDefault();
                        if (draggedCard) {
                          handleDropDirect(draggedCard.dayIdx, draggedCard.slotKey, dayIdx, 'morning');
                          setDraggedCard(null);
                        }
                      }}
                      className="border-2 border-dashed border-[#c2410c]/80 bg-[#c2410c]/5 rounded-2xl p-4 text-center text-xs font-bold text-[#c2410c] animate-fadeIn transition-all"
                    >
                      Drop here to add to Day {day.day_number} morning
                    </div>
                  )}

                  {/* Vertical Stack of Stop Cards (Image 1 Style) */}
                  <div className="space-y-3">
                    {slotKeys.map((slotKey) => {
                      const rawSlot = day[slotKey];
                      if (!rawSlot) return null;
                      const slot = typeof rawSlot === 'string' ? { place_name: rawSlot, activity_note: '', est_time: '' } : rawSlot;

                      const isThisEditing = editingSlotData?.dayIdx === dayIdx && editingSlotData?.slotKey === slotKey;
                      const isThisDragging = draggedCard?.dayIdx === dayIdx && draggedCard?.slotKey === slotKey;
                      const timeLabel = slotKey.toUpperCase();
                      const durationDisplay = slot.duration_minutes ? `${(slot.duration_minutes / 60).toFixed(1)} hrs` : (slot.est_time || (slotKey === 'evening' ? '2 hrs' : '2.5 hrs'));

                      if (isThisEditing) {
                        return (
                          /* INLINE EDITING STOP FORM (Image 1) */
                          <div key={slotKey} className="bg-white rounded-2xl p-5 border border-slate-300 shadow-sm space-y-4 animate-fadeIn">
                            <div className="text-xs font-bold text-terracotta tracking-wider uppercase font-sans">
                              Editing Stop
                            </div>

                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                              <div>
                                <label className="text-[11px] font-bold text-slate-700 block mb-1">Place name</label>
                                <input
                                  type="text"
                                  value={editingSlotData.place_name}
                                  onChange={(e) => setEditingSlotData(prev => ({ ...prev, place_name: e.target.value }))}
                                  className="w-full px-3.5 py-2 rounded-xl border border-slate-200 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#c2410c]"
                                />
                              </div>
                              <div>
                                <label className="text-[11px] font-bold text-slate-700 block mb-1">Time of day</label>
                                <input
                                  type="text"
                                  value={editingSlotData.timeOfDay}
                                  onChange={(e) => setEditingSlotData(prev => ({ ...prev, timeOfDay: e.target.value }))}
                                  className="w-full px-3.5 py-2 rounded-xl border border-slate-200 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#c2410c]"
                                />
                              </div>
                              <div>
                                <label className="text-[11px] font-bold text-slate-700 block mb-1">Duration</label>
                                <input
                                  type="text"
                                  value={editingSlotData.duration}
                                  onChange={(e) => setEditingSlotData(prev => ({ ...prev, duration: e.target.value }))}
                                  className="w-full px-3.5 py-2 rounded-xl border border-slate-200 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#c2410c]"
                                />
                              </div>
                            </div>

                            <div>
                              <label className="text-[11px] font-bold text-slate-700 block mb-1">Notes</label>
                              <textarea
                                rows={3}
                                value={editingSlotData.notes}
                                onChange={(e) => setEditingSlotData(prev => ({ ...prev, notes: e.target.value }))}
                                className="w-full px-3.5 py-2 rounded-xl border border-slate-200 text-xs text-slate-900 focus:outline-none focus:ring-2 focus:ring-[#c2410c] resize-none"
                              />
                            </div>

                            <div className="flex items-center justify-between pt-2 border-t border-slate-100">
                              <button
                                type="button"
                                onClick={() => {
                                  handleRemoveSlot(dayIdx, slotKey);
                                  setEditingSlotData(null);
                                }}
                                className="text-xs font-bold text-rose-600 hover:text-rose-700 cursor-pointer"
                              >
                                Delete stop
                              </button>
                              <div className="flex items-center gap-2">
                                <button
                                  type="button"
                                  onClick={() => setEditingSlotData(null)}
                                  className="px-4 py-2 rounded-xl border border-slate-200 text-xs font-bold text-slate-700 hover:bg-slate-50 cursor-pointer"
                                >
                                  Cancel
                                </button>
                                <button
                                  type="button"
                                  onClick={() => {
                                    handleSaveSlotChanges(dayIdx, slotKey);
                                  }}
                                  className="px-4 py-2 rounded-xl bg-[#0f172a] hover:bg-slate-800 text-white text-xs font-bold cursor-pointer shadow-xs"
                                >
                                  Save changes
                                </button>
                              </div>
                            </div>
                          </div>
                        );
                      }

                      return (
                        /* STANDARD WHITE STOP CARD (Image 1) */
                        <div
                          key={slotKey}
                          draggable
                          onDragStart={(e) => handleDragStart(e, dayIdx, slotKey, slot)}
                          onDragOver={(e) => handleDragOver(e, dayIdx, slotKey)}
                          onDrop={(e) => handleDrop(e, dayIdx, slotKey)}
                          className={`bg-white rounded-2xl p-4 sm:p-5 border shadow-xs flex items-start gap-3.5 transition-all group ${
                            isThisDragging 
                              ? 'border-[#c2410c] shadow-md ring-2 ring-[#c2410c]/30' 
                              : 'border-slate-200/80 hover:border-slate-300'
                          }`}
                        >
                          {/* Left Drag Handle */}
                          <div className="shrink-0 pt-0.5 cursor-grab active:cursor-grabbing text-slate-400 group-hover:text-slate-600">
                            <GripVertical className="w-4 h-4" />
                          </div>

                          {/* Middle Content */}
                          <div className="flex-1 min-w-0">
                            <div className="flex flex-wrap items-center gap-2 text-[10px] sm:text-[11px] font-bold uppercase tracking-wider text-slate-500 font-sans">
                              <span>{timeLabel} · {durationDisplay}</span>
                              {isThisDragging && (
                                <span className="px-2.5 py-0.5 rounded-full bg-terracotta text-white text-[10px] font-bold uppercase font-sans">
                                  MOVING TO DAY {dayIdx === 0 ? 2 : 1}
                                </span>
                              )}
                            </div>

                            <div className="font-bold text-slate-900 text-sm sm:text-base mt-0.5 font-sans">
                              {slot.place_name || 'Destination'}
                            </div>

                            <p className="text-xs text-slate-600 mt-0.5 leading-relaxed font-sans">
                              {slot.activity_note || 'Explore authentic heritage, cultural sights, and coastal relaxation.'}
                            </p>
                          </div>

                          {/* Right Action Icons (Pencil & 3 Dots) */}
                          <div className="flex items-center gap-1 shrink-0 pt-0.5">
                            <button
                              type="button"
                              onClick={() => {
                                setEditingSlotData({
                                  dayIdx,
                                  slotKey,
                                  place_name: slot.place_name || '',
                                  timeOfDay: slotKey === 'morning' ? 'Morning' : slotKey === 'afternoon' ? 'Afternoon' : 'Evening',
                                  duration: durationDisplay,
                                  notes: slot.activity_note || ''
                                });
                              }}
                              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors cursor-pointer"
                              title="Edit stop"
                            >
                              <Pencil className="w-4 h-4" />
                            </button>
                            <button
                              type="button"
                              onClick={() => {
                                const targetDay = dayIdx === 0 ? 1 : 0;
                                if (aiItinerary.days?.[targetDay]) {
                                  handleDropDirect(dayIdx, slotKey, targetDay, slotKey);
                                }
                              }}
                              className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors cursor-pointer"
                              title="Move to other day"
                            >
                              <MoreHorizontal className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Travel Tips & Belief Decorum Advisory */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {aiItinerary.travel_tips && (
              <div className="p-4 rounded-2xl bg-white/70 backdrop-blur-md border border-white/50 text-xs space-y-1 shadow-xs">
                <span className="font-bold text-slate-900 uppercase tracking-wider font-sans">💡 Local Travel Tips:</span>
                <ul className="list-disc list-inside space-y-0.5 text-slate-700">
                  {aiItinerary.travel_tips.map((tip, idx) => (
                    <li key={idx}>{tip}</li>
                  ))}
                </ul>
              </div>
            )}

            {aiItinerary.belief_and_etiquette_advisory && (
              <div className="p-4 rounded-2xl bg-white/70 backdrop-blur-md border border-white/50 text-xs space-y-1 shadow-xs">
                <span className="font-bold text-slate-900 uppercase tracking-wider font-sans">📜 Etiquette & Decorum:</span>
                <p className="text-slate-700 leading-relaxed mt-1">
                  {aiItinerary.belief_and_etiquette_advisory}
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Control Panel + Live Trip Basket */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left: Preferences Tuning Panel */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white/70 backdrop-blur-xl rounded-2xl p-6 border border-white/50 shadow-xl space-y-5">
            <div className="flex items-center gap-2 pb-3 border-b border-sandstone">
              <Sliders className="w-5 h-5 text-terracotta" />
              <h2 className="text-base font-bold text-slate-800 font-sans">Preferences & Profile Filters</h2>
            </div>

            {/* 1. Age Group Selector */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2 font-sans">
                1. Select Age Bracket
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {AGE_GROUPS.map(a => (
                  <button
                    key={a.id}
                    onClick={() => setAgeGroup(a.id)}
                    className={`p-3 rounded-xl text-left border transition-all cursor-pointer ${
                      ageGroup === a.id
                        ? 'bg-[#FCD34D]/25 border-[#FCD34D] ring-2 ring-[#FCD34D]/40 text-slate-950 font-bold shadow-xs'
                        : 'bg-white/60 border-white/60 hover:bg-white/80 text-slate-800 font-medium'
                    }`}
                  >
                    <div className="text-sm font-sans">{a.shortLabel} yrs</div>
                    <div className="text-[10px] text-slate-500 font-normal mt-0.5 line-clamp-1">{a.label.split('(')[1]?.replace(')', '')}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* 2. Dietary Preference */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2 font-sans">
                2. Dietary Filter (Opt-In)
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                {DIETARY_OPTIONS.map(d => (
                  <button
                    key={d.id}
                    onClick={() => setDietaryPreference(d.id)}
                    className={`p-2.5 rounded-xl text-left border text-xs transition-all cursor-pointer ${
                      dietaryPreference === d.id
                        ? 'bg-[#FCD34D]/25 border-[#FCD34D] ring-2 ring-[#FCD34D]/40 text-slate-950 font-bold shadow-xs'
                        : 'bg-white/60 border-white/60 hover:bg-white/80 text-slate-800'
                    }`}
                  >
                    <div>{d.label}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* 3. Budget Tier */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2 font-sans">
                3. Budget Level
              </label>
              <div className="grid grid-cols-3 gap-2">
                {BUDGET_TIERS.map(b => (
                  <button
                    key={b.id}
                    onClick={() => setBudgetTier(b.id)}
                    className={`p-2.5 rounded-xl text-center border text-xs transition-all cursor-pointer ${
                      budgetTier === b.id
                        ? 'bg-[#FCD34D]/25 border-[#FCD34D] ring-2 ring-[#FCD34D]/40 text-slate-950 font-bold shadow-xs'
                        : 'bg-white/60 border-white/60 hover:bg-white/80 text-slate-800'
                    }`}
                  >
                    <div className="font-bold text-sm">{b.symbol}</div>
                    <div>{b.label.split(' ')[0]}</div>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Ranked Recommendations Grid */}
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3.5 rounded-2xl bg-white/70 backdrop-blur-xl border border-white/50 shadow-md">
              <h2 className="text-base sm:text-lg font-extrabold text-slate-900 flex items-center gap-2 font-sans">
                <Sparkles className="w-5 h-5 text-amber-700" />
                Ranked Recommendations ({recommendations.length} Places)
              </h2>
              <span className="text-xs text-slate-500 font-sans">Sorted by match score</span>
            </div>

            {loadingRecs ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 animate-pulse">
                {[1, 2, 3, 4].map(i => (
                  <div key={i} className="h-72 bg-slate-200 rounded-2xl"></div>
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                {recommendations.map(item => (
                  <PlaceCard
                    key={item.place.id}
                    place={item.place}
                    matchScore={item.match_score}
                    matchReasons={item.match_reasons}
                    onSelect={() => setActiveModalItem(item)}
                  />
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right: Trip Basket & Itinerary Preview */}
        <div className="space-y-6">
          <div className="bg-white/70 backdrop-blur-xl rounded-2xl p-6 border border-white/50 shadow-xl sticky top-24 space-y-6">
            <div className="flex items-center justify-between pb-3 border-b border-sandstone">
              <div className="flex items-center gap-2">
                <Luggage className="w-5 h-5 text-terracotta" />
                <h3 className="font-bold text-slate-900 font-sans">Your Trip Basket</h3>
              </div>
              {tripPlan.length > 0 && (
                <button
                  onClick={clearTripPlan}
                  className="text-xs text-rose-600 hover:text-rose-700 font-medium flex items-center gap-1 cursor-pointer"
                >
                  <Trash2 className="w-3.5 h-3.5" /> Clear
                </button>
              )}
            </div>

            {/* Trip Stats */}
            <div className="grid grid-cols-2 gap-3 p-3 bg-white/60 backdrop-blur-md rounded-xl border border-white/60 text-center">
              <div>
                <div className="text-[11px] text-slate-500 font-medium font-sans">Total Activity Cost</div>
                <div className="text-base font-extrabold text-slate-900 flex items-center justify-center gap-0.5 mt-0.5 font-sans">
                  <IndianRupee className="w-4 h-4 text-terracotta" />
                  {totalCost === 0 ? 'Free' : `₹${totalCost}`}
                </div>
              </div>
              <div>
                <div className="text-[11px] text-slate-500 font-medium font-sans">Est. Time Needed</div>
                <div className="text-base font-extrabold text-slate-900 flex items-center justify-center gap-1 mt-0.5 font-sans">
                  <Clock className="w-4 h-4 text-slate-700" />
                  ~{totalHours} hrs
                </div>
              </div>
            </div>

            {/* Selected Items List */}
            {tripPlan.length === 0 ? (
              <div className="py-8 text-center space-y-2">
                <div className="w-10 h-10 rounded-full bg-white/80 border border-white/60 flex items-center justify-center mx-auto text-slate-400">
                  <Luggage className="w-5 h-5 text-slate-400" />
                </div>
                <p className="text-xs text-slate-700 font-medium">Your basket is empty.</p>
                <p className="text-[11px] text-slate-500">Click "+ Add to Trip" on any destination to build your schedule.</p>
              </div>
            ) : (
              <div className="space-y-2.5 max-h-96 overflow-y-auto pr-1">
                {tripPlan.map((place, idx) => (
                  <div 
                    key={place.id}
                    className="flex items-center justify-between p-3 rounded-xl bg-white/75 backdrop-blur-sm border border-white/60 text-xs shadow-2xs"
                  >
                    <div className="flex items-center gap-2.5 overflow-hidden">
                      <span className="w-5 h-5 rounded-full bg-slate-900 text-[#FCD34D] font-bold flex items-center justify-center shrink-0 text-[10px] font-sans">
                        {idx + 1}
                      </span>
                      <div className="truncate">
                        <div className="font-bold text-slate-900 truncate">{place.name}</div>
                        <div className="text-slate-500 text-[10px]">~{place.duration_minutes} mins • {place.estimated_cost_inr === 0 ? 'Free' : `₹${place.estimated_cost_inr}`}</div>
                      </div>
                    </div>

                    <button
                      onClick={() => removeFromTripPlan(place.id)}
                      className="text-slate-400 hover:text-rose-500 p-1 transition-colors cursor-pointer"
                      title="Remove"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* OpenStreetMap & OSRM Routing Legal Attribution */}
      <div className="pt-6 pb-2 text-center text-[11px] text-slate-400 border-t border-slate-100 flex items-center justify-center gap-1.5">
        <span>Map data &copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer" className="underline hover:text-slate-600">OpenStreetMap</a> contributors (ODbL)</span>
        <span>•</span>
        <span>Routing engine &copy; <a href="http://project-osrm.org/" target="_blank" rel="noreferrer" className="underline hover:text-slate-600">OSRM</a></span>
      </div>

      {/* Place Modal */}
      {activeModalItem && (
        <PlaceModal
          place={activeModalItem.place}
          matchInfo={activeModalItem}
          onClose={() => setActiveModalItem(null)}
        />
      )}


      </div>
    </div>
  );
}
