import React, { useState, useEffect, useRef } from 'react';
import { 
  Sparkles, Sliders, Luggage, IndianRupee, Clock, Trash2, Edit3, Check, RefreshCw, Plus, GripVertical, Move,
  ArrowRight, CheckCircle2, Navigation, Send, Compass, Lightbulb, Loader2, Calendar,
  Zap, Lock, Unlock, Car, Footprints, AlertTriangle, MapPin, Map as MapIcon
} from 'lucide-react';
import { PlaceCard } from '../components/PlaceCard';
import { PlaceModal } from '../components/PlaceModal';
import { FestivalAdvisoryBanner } from '../components/FestivalAdvisoryBanner';
import { TransitLegCard } from '../components/TransitLegCard';
import { MapView } from '../components/MapView';
import { VoyantraAPI } from '../services/api';
import { usePreferences } from '../context/PreferencesContext';
import { AGE_GROUPS, DIETARY_OPTIONS, BUDGET_TIERS } from '../types/constants';

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
              <span className="text-teal-600 font-bold">•</span>
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

export function PlannerPage() {
  const { 
    selectedCity,
    ageGroup, 
    setAgeGroup, 
    dietaryPreference, 
    setDietaryPreference, 
    budgetTier, 
    setBudgetTier,
    tripPlan,
    addToTripPlan,
    removeFromTripPlan,
    clearTripPlan
  } = usePreferences();

  const [recommendations, setRecommendations] = useState([]);
  const [loadingRecs, setLoadingRecs] = useState(true);
  const [activeModalItem, setActiveModalItem] = useState(null);

  // Phase 2 State: Prompt, Preset Suggestions & AI Itinerary
  const [promptText, setPromptText] = useState('');
  const [durationDays, setDurationDays] = useState(2);
  const [presetSuggestions, setPresetSuggestions] = useState([]);
  const [aiItinerary, setAiItinerary] = useState(null);
  const [availableAlternatives, setAvailableAlternatives] = useState([]);
  const [loadingAi, setLoadingAi] = useState(false);
  const [editingSlot, setEditingSlot] = useState(null);
  
  // Drag & Drop State
  const [draggedCard, setDraggedCard] = useState(null);
  const [dragOverTarget, setDragOverTarget] = useState(null);
  
  // AI Conversational Chatbox & Itinerary State
  const [chatMessages, setChatMessages] = useState([
    {
      id: 'welcome-msg',
      sender: 'ai',
      text: "Hello! 👋 I'm your **Voyantra AI Travel Concierge**.\n\nYou can chat with me naturally like a local guide — ask for restaurant recommendations, heritage landmarks, beach sunset timings, or ask me to craft a custom multi-day itinerary for any duration or time of day!",
      timestamp: 'Just now',
      suggested_followups: [
        "Plan a 2-day relaxed trip",
        "Best cafes & breakfast in White Town",
        "What can I do tomorrow morning?",
        "Temples, ashrams & dress codes"
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
        duration_days: durationDays
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

        if (res.itinerary) {
          setAiItinerary(res.itinerary);
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

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Phase 3 Festival Advisory Banner */}
      <FestivalAdvisoryBanner selectedCity={selectedCity} />

      {/* Backend Disconnected Notice */}
      {backendError && (
        <div className="p-5 rounded-2xl bg-rose-50 border-2 border-rose-300 text-rose-900 space-y-2 shadow-md animate-fadeIn">
          <div className="flex items-center gap-2 font-black text-rose-800 text-sm uppercase tracking-wider">
            <span className="px-2 py-0.5 rounded bg-rose-200 text-rose-900 font-extrabold text-[11px]">
              ⚠️ BACKEND DISCONNECTED
            </span>
          </div>
          <p className="text-xs text-rose-900 leading-relaxed font-medium">
            {backendError}
          </p>
          <div className="p-2.5 rounded-lg bg-rose-100/90 font-mono text-[11px] text-rose-950 font-bold">
            Start Server Command: cd E:\Voyantra\backend && python run.py
          </div>
        </div>
      )}

      {/* Preset Suggestion Options Carousel */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 text-slate-800 text-sm font-bold">
          <Lightbulb className="w-4 h-4 text-amber-500" />
          <span>Preset Suggestions & Travel Templates (Click to Generate):</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {presetSuggestions.map((sugg) => (
            <button
              key={sugg.id}
              onClick={() => selectPreset(sugg)}
              className="p-4 rounded-2xl bg-white border border-slate-200 hover:border-brand-500 hover:bg-brand-50/50 text-left transition-all group shadow-2xs flex items-start gap-3"
            >
              <span className="text-2xl p-2 rounded-xl bg-slate-100 group-hover:bg-brand-100 shrink-0">
                {sugg.icon}
              </span>
              <div>
                <h4 className="font-bold text-xs sm:text-sm text-slate-900 group-hover:text-brand-700 transition-colors">
                  {sugg.title}
                </h4>
                <p className="text-xs text-slate-500 mt-1 line-clamp-2 leading-relaxed">
                  "{sugg.prompt}"
                </p>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Interactive AI Travel Concierge Chatbox */}
      <div className="bg-white rounded-3xl border border-teal-200/90 shadow-sm overflow-hidden space-y-0">
        {/* Chatbox Header */}
        <div className="bg-gradient-to-r from-teal-800 via-teal-700 to-emerald-800 p-4 sm:p-5 text-white flex flex-col sm:flex-row sm:items-center justify-between gap-3">
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
                <h3 className="font-extrabold text-sm sm:text-base tracking-tight text-white">Voyantra AI Travel Concierge</h3>
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-400/20 text-emerald-200 border border-emerald-400/30 text-[10px] font-bold">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping"></span>
                  Gemini 3.5 Flash Lite Live
                </span>
              </div>
              <p className="text-[11px] text-teal-100/80">
                Ask for custom itineraries, restaurant recommendations, temple decorum, or beach timings!
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 self-end sm:self-center">
            <span className="text-[11px] font-bold text-teal-200 uppercase tracking-wider">Duration:</span>
            <select
              value={durationDays}
              onChange={(e) => setDurationDays(Number(e.target.value))}
              className="px-3 py-1.5 rounded-xl border border-white/20 font-bold text-teal-900 bg-white/95 text-xs outline-none cursor-pointer shadow-sm"
            >
              <option value={1}>1 Day Plan</option>
              <option value={2}>2 Days Weekend</option>
              <option value={3}>3 Days Vacation</option>
              <option value={4}>4 Days Holiday</option>
              <option value={5}>5 Days Getaway</option>
            </select>
          </div>
        </div>

        {/* Conversation Stream */}
        <div className="p-4 sm:p-6 space-y-4 max-h-[460px] overflow-y-auto bg-slate-50/50">
          {chatMessages.map((msg) => (
            <div
              key={msg.id}
              className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'} space-y-2 animate-fadeIn`}
            >
              <div
                className={`max-w-[90%] sm:max-w-[80%] p-4 rounded-2xl text-xs sm:text-sm shadow-xs ${
                  msg.sender === 'user'
                    ? 'bg-brand-600 text-white rounded-br-none shadow-brand-600/20'
                    : 'bg-white border border-teal-100 text-slate-800 rounded-bl-none shadow-sm'
                }`}
              >
                {msg.sender === 'user' ? (
                  <p className="font-medium leading-relaxed whitespace-pre-wrap">{msg.text}</p>
                ) : (
                  <FormattedMessage text={msg.text} />
                )}
                
                <span className={`text-[9px] mt-2 block font-medium ${msg.sender === 'user' ? 'text-brand-200 text-right' : 'text-slate-400'}`}>
                  {msg.timestamp}
                </span>
              </div>

              {/* Recommended Place Mini Cards (if returned) */}
              {msg.recommended_places && msg.recommended_places.length > 0 && (
                <div className="w-full max-w-[90%] sm:max-w-[80%] grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-1">
                  {msg.recommended_places.map((place) => (
                    <div
                      key={place.id}
                      className="p-3 rounded-xl bg-white border border-teal-200/80 shadow-2xs flex flex-col justify-between gap-2 hover:border-teal-400 transition-all"
                    >
                      <div>
                        <div className="flex items-center justify-between gap-1">
                          <span className="font-bold text-xs text-slate-900 line-clamp-1">{place.name}</span>
                          <span className="px-1.5 py-0.5 rounded text-[9px] font-bold uppercase bg-teal-50 text-teal-800 border border-teal-200">
                            {place.category}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-500 mt-0.5">
                          Est. Cost: <strong className="text-slate-700">₹{place.estimated_cost_inr}</strong> • {place.duration_minutes} mins
                        </p>
                        {place.highlights && place.highlights.length > 0 && (
                          <p className="text-[10px] text-teal-700 mt-1 line-clamp-1">
                            ✨ {place.highlights[0]}
                          </p>
                        )}
                      </div>
                      <button
                        onClick={() => addToTripPlan(place)}
                        className="w-full py-1 rounded-lg bg-teal-50 hover:bg-teal-100 text-teal-800 text-[10px] font-bold border border-teal-200 transition-colors cursor-pointer"
                      >
                        + Add to Trip Plan
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Itinerary Ready Action Banner */}
              {msg.hasItinerary && (
                <div className="w-full max-w-[90%] sm:max-w-[80%] p-3 rounded-xl bg-gradient-to-r from-teal-50 to-emerald-50 border border-teal-300 text-teal-900 flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">🗺️</span>
                    <div>
                      <span className="font-bold text-xs">Itinerary Generated!</span>
                      <p className="text-[10px] text-teal-700">Explore Day-by-Day schedule and map below</p>
                    </div>
                  </div>
                  <button
                    onClick={() => itineraryRef.current?.scrollIntoView({ behavior: 'smooth' })}
                    className="px-3 py-1 rounded-lg bg-teal-700 hover:bg-teal-800 text-white text-[11px] font-bold shadow-xs flex items-center gap-1 transition-all cursor-pointer"
                  >
                    <span>View Plan</span>
                    <ArrowRight className="w-3 h-3" />
                  </button>
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
                      className="px-2.5 py-1 rounded-full bg-white hover:bg-teal-50 hover:text-teal-800 text-slate-600 text-[10px] sm:text-[11px] font-bold border border-slate-200 hover:border-teal-300 transition-all shadow-2xs disabled:opacity-50 cursor-pointer"
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
              <div className="w-7 h-7 rounded-full bg-teal-800 p-1 flex items-center justify-center shadow-xs">
                <img 
                  src="/images/logo/voyantra-icon-nobg-crop.png" 
                  alt="Voyantra" 
                  className="w-full h-full object-contain" 
                />
              </div>
              <div className="p-3.5 rounded-2xl bg-white border border-teal-200 text-xs text-teal-900 font-bold flex items-center gap-2 shadow-xs">
                <Loader2 className="w-3.5 h-3.5 text-teal-600 animate-spin" />
                <span>Voyantra Concierge is typing...</span>
              </div>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>

        {/* Chat Input Bar */}
        <div className="p-3 sm:p-4 bg-white border-t border-slate-100">
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
              placeholder="Ask a question, say hello, or plan an itinerary (e.g. 'Hello!', 'Best cafes in Pondy', 'Plan a 2-day trip')..."
              disabled={isRefining}
              className="flex-1 px-4 py-3 rounded-2xl border border-slate-200 bg-slate-50 focus:bg-white focus:border-teal-600 focus:ring-2 focus:ring-teal-600/15 text-xs sm:text-sm font-medium outline-none transition-all"
            />
            <button
              type="submit"
              disabled={isRefining || !chatInputText.trim()}
              className="px-5 py-3 rounded-2xl bg-teal-700 hover:bg-teal-800 disabled:opacity-50 text-white text-xs sm:text-sm font-bold flex items-center gap-2 shadow-sm transition-all shrink-0 cursor-pointer"
            >
              {isRefining ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              <span className="hidden sm:inline">Send</span>
            </button>
          </form>
        </div>
      </div>

      {/* Target Ref Anchor for Window Scroll */}
      <div ref={itineraryRef} />

      {/* Generated AI Day-by-Day Itinerary Result View (DRAG & DROP + EDITABLE) */}
      {aiItinerary && !loadingAi && (
        <div className="bg-gradient-to-br from-white via-teal-50/30 to-emerald-50/20 rounded-3xl p-6 border border-teal-200 shadow-md space-y-6 animate-fadeIn">
          {/* Source Notice Banner */}
          {aiItinerary.source === 'fallback' && (
            <div className="p-3.5 rounded-2xl bg-amber-50 border border-amber-300 text-amber-900 text-xs flex items-center justify-between gap-2 shadow-2xs">
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

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-teal-100">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-teal-100 text-teal-800 text-xs font-bold">
                  <Move className="w-3.5 h-3.5" /> Drag & Drop Interactive Plan
                </div>
                {aiItinerary.source === 'gemini' ? (
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-xs font-bold">
                    <Sparkles className="w-3 h-3 text-emerald-600" /> Google Gemini RAG
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 text-xs font-semibold">
                    Offline Model
                  </span>
                )}
              </div>
              <h2 className="text-2xl font-extrabold text-slate-900">{aiItinerary.itinerary_title}</h2>
              <p className="text-xs text-slate-600 mt-0.5">{aiItinerary.summary} • <span className="font-semibold text-teal-700">Drag any card between Day 1 & Day 2 to customize your schedule!</span></p>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={handleAddAllToBasket}
                className="px-3.5 py-2 rounded-xl bg-teal-700 hover:bg-teal-800 text-white text-xs font-bold flex items-center gap-1.5 shadow-sm transition-all"
              >
                <Luggage className="w-4 h-4" /> Save Plan to Basket
              </button>
              <div className="text-right">
                <span className="text-[11px] text-slate-400">Est. Budget</span>
                <div className="text-xl font-black text-teal-700 flex items-center justify-end">
                  <IndianRupee className="w-4 h-4" /> {aiItinerary.total_estimated_budget_inr}
                </div>
              </div>
            </div>
          </div>

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

          {/* Days Timeline with DRAG & DROP Cards and TSP Order Optimization */}
          <div className="space-y-6">
            {aiItinerary.days.map((day, dayIdx) => {
              const optData = dayOptimizations[dayIdx];
              const isOptimizing = optimizingDay === dayIdx;
              const currentMode = transitModes[dayIdx] || 'driving';
              const isShowingMap = !!showDayMap[dayIdx];

              // Collect places for MapView
              const dayPlaces = recommendations
                .filter(r => r.place)
                .slice(0, 6)
                .map(r => r.place);

              return (
                <div 
                  key={day.day_number} 
                  className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs space-y-4"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-slate-100">
                    <span className="text-sm font-extrabold text-brand-700 uppercase tracking-wider flex items-center gap-2">
                      <span className="w-6 h-6 rounded-full bg-brand-600 text-white flex items-center justify-center text-xs">
                        {day.day_number}
                      </span>
                      Day {day.day_number}: {day.theme}
                    </span>

                    <div className="flex items-center gap-2">
                      {/* ⚡ Optimize Order Trigger Button (Phase 4 Task 7) */}
                      <button
                        onClick={() => handleOptimizeDay(dayIdx)}
                        disabled={isOptimizing}
                        className="text-xs text-teal-800 hover:text-teal-900 font-bold flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-teal-100 hover:bg-teal-200 border border-teal-300 transition-all shadow-2xs"
                      >
                        {isOptimizing ? (
                          <>
                            <Loader2 className="w-3.5 h-3.5 animate-spin" /> Optimizing TSP...
                          </>
                        ) : (
                          <>
                            <Zap className="w-3.5 h-3.5 text-teal-600 fill-teal-500" /> ⚡ Optimize Route & Order
                          </>
                        )}
                      </button>

                      {/* Toggle Route Map on Leaflet */}
                      {optData && (
                        <button
                          onClick={() => setShowDayMap(prev => ({ ...prev, [dayIdx]: !prev[dayIdx] }))}
                          className="text-xs text-slate-700 hover:text-slate-900 font-semibold flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 border border-slate-200 transition-all"
                        >
                          <MapIcon className="w-3.5 h-3.5 text-teal-600" />
                          {isShowingMap ? 'Hide Route Map' : 'View Route Map'}
                        </button>
                      )}

                      <button
                        onClick={() => handleAddSlotToDay(dayIdx)}
                        className="text-xs text-brand-700 hover:text-brand-800 font-bold flex items-center gap-1 px-2.5 py-1 rounded-lg bg-brand-50 border border-brand-200"
                      >
                        <Plus className="w-3.5 h-3.5" /> Add Visiting Slot
                      </button>
                    </div>
                  </div>

                  {/* OPTIMIZATION METRICS BANNER (When Day is Optimized) */}
                  {optData && (
                    <div className="p-3 rounded-xl bg-teal-50/70 border border-teal-200 flex flex-wrap items-center justify-between gap-3 text-xs animate-fadeIn">
                      <div className="flex items-center gap-3">
                        <span className="font-extrabold text-teal-900 flex items-center gap-1">
                          <CheckCircle2 className="w-4 h-4 text-teal-600" /> Optimized Sequence:
                        </span>
                        <span className="text-slate-700 font-medium">
                          🚗 ~{optData.total_travel_time_minutes} min travel ({optData.total_travel_distance_km} km)
                        </span>
                        <span className="text-slate-400">•</span>
                        <span className="text-slate-700 font-medium">
                          ⏱️ ~{optData.total_visit_time_minutes} min sightseeing
                        </span>
                        {optData.is_approximate && (
                          <span className="text-[10px] text-slate-500 italic">
                            (Approximate travel time)
                          </span>
                        )}
                      </div>

                      {/* Mode Switcher */}
                      <div className="flex items-center gap-1">
                        <span className="text-[11px] text-slate-500 mr-1">Mode:</span>
                        <button
                          onClick={() => handleToggleTransitMode(dayIdx)}
                          className="px-2 py-1 rounded-lg bg-white border border-teal-300 font-semibold text-teal-800 hover:bg-teal-50 flex items-center gap-1 shadow-2xs transition-all"
                        >
                          {currentMode === 'driving' ? (
                            <>
                              <Car className="w-3.5 h-3.5" /> Driving (Switch to Walk)
                            </>
                          ) : (
                            <>
                              <Footprints className="w-3.5 h-3.5" /> Walking (Switch to Drive)
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  )}

                  {/* ROUTE MAP OVERLAY ON LEAFLET (Phase 4 Task 6) */}
                  {optData && isShowingMap && (
                    <div className="rounded-xl overflow-hidden border border-teal-200 shadow-xs animate-fadeIn">
                      <MapView 
                        height="300px" 
                        places={dayPlaces} 
                        routeLegs={optData.transit_legs} 
                        transitMode={currentMode} 
                      />
                    </div>
                  )}

                  {/* SEQUENTIAL OPTIMIZED TIMELINE WITH TRANSIT LEGS */}
                  {optData ? (
                    <div className="space-y-3">
                      {optData.optimized_slots.map((s, idx) => {
                        const isLocked = !!lockedSlots[s.slot_id];
                        return (
                          <React.Fragment key={s.slot_id || idx}>
                            <div className="p-3.5 rounded-xl border bg-white border-teal-200/90 shadow-2xs space-y-2 relative transition-all">
                              <div className="flex items-center justify-between pb-1 border-b border-slate-100">
                                <div className="flex items-center gap-2">
                                  <span className="w-5 h-5 rounded-full bg-teal-700 text-white flex items-center justify-center font-bold text-[11px]">
                                    {s.order}
                                  </span>
                                  <span className="font-extrabold text-slate-900 text-xs">{s.place_name}</span>
                                  {s.time_anchor && (
                                    <span className="px-2 py-0.5 rounded-full bg-teal-100 text-teal-800 text-[10px] font-bold uppercase tracking-wider">
                                      {s.time_anchor === 'sunset' ? '🌅 Sunset Anchor' : s.time_anchor}
                                    </span>
                                  )}
                                </div>

                                <div className="flex items-center gap-2">
                                  <div className="px-2 py-0.5 rounded-md bg-slate-100 font-mono text-[11px] font-bold text-slate-700">
                                    {s.start_time} - {s.end_time}
                                  </div>
                                  {/* Lock Toggle */}
                                  <button
                                    onClick={() => toggleLockSlot(s.slot_id)}
                                    title={isLocked ? 'Stop position is locked' : 'Click to lock stop in position'}
                                    className={`p-1 rounded-md border text-xs flex items-center gap-1 transition-all ${
                                      isLocked 
                                        ? 'bg-amber-100 border-amber-300 text-amber-800 font-bold' 
                                        : 'bg-slate-50 border-slate-200 text-slate-500 hover:text-slate-700'
                                    }`}
                                  >
                                    {isLocked ? <Lock className="w-3 h-3 text-amber-700" /> : <Unlock className="w-3 h-3" />}
                                    <span className="text-[10px]">{isLocked ? 'Locked' : 'Lock'}</span>
                                  </button>
                                </div>
                              </div>

                              {/* Unverified Opening Hours Warning Chip */}
                              {s.hours_warning && (
                                <div className="px-2.5 py-1 rounded-lg bg-amber-50 border border-amber-200 text-amber-900 text-[11px] flex items-center gap-1.5">
                                  <AlertTriangle className="w-3 h-3 text-amber-600 shrink-0" />
                                  <span>{s.hours_warning}</span>
                                </div>
                              )}
                            </div>

                            {/* Transit Leg Connector between consecutive stops */}
                            {idx < optData.optimized_slots.length - 1 && (
                              <TransitLegCard 
                                leg={optData.transit_legs[idx]} 
                                mode={currentMode}
                                onToggleMode={() => handleToggleTransitMode(dayIdx)}
                              />
                            )}
                          </React.Fragment>
                        );
                      })}

                      {/* OSRM / FOSSGIS & OpenStreetMap Attribution Footer */}
                      <div className="pt-3 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2 text-[10px] text-slate-400">
                        <span>
                          Routing by <a href="https://routing.openstreetmap.de/about.html" target="_blank" rel="noreferrer" className="underline hover:text-slate-600">OSRM via FOSSGIS routing service</a>
                        </span>
                        <span>
                          Map data © <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer" className="underline hover:text-slate-600">OpenStreetMap contributors (ODbL)</a>
                        </span>
                      </div>
                    </div>
                  ) : (
                    /* STANDARD GRID BEFORE OPTIMIZATION */
                    <div className="space-y-2">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                        {Object.keys(day).filter(k => !['day_number', 'theme'].includes(k)).map((slotKey) => {
                          const rawSlot = day[slotKey];
                          if (!rawSlot) return null;
                          const slot = typeof rawSlot === 'string' ? { place_name: rawSlot, activity_note: '', est_time: '' } : rawSlot;

                          const isEditing = editingSlot?.dayIdx === dayIdx && editingSlot?.slotKey === slotKey;
                          const isOver = dragOverTarget?.dayIdx === dayIdx && dragOverTarget?.slotKey === slotKey;
                          const slotTitle = slotKey.startsWith('custom_') ? `➕ Custom Slot` : slotKey === 'morning' ? '🌅 Morning' : slotKey === 'afternoon' ? '☀️ Afternoon' : '🌙 Evening';

                          return (
                            <div 
                              key={slotKey} 
                              draggable={!isEditing}
                              onDragStart={(e) => handleDragStart(e, dayIdx, slotKey, slot)}
                              onDragOver={(e) => handleDragOver(e, dayIdx, slotKey)}
                              onDrop={(e) => handleDrop(e, dayIdx, slotKey)}
                              className={`p-3.5 rounded-xl border space-y-2 relative transition-all cursor-grab active:cursor-grabbing ${
                                isOver 
                                  ? 'border-2 border-dashed border-teal-500 bg-teal-50/80 shadow-md ring-4 ring-teal-500/20' 
                                  : 'bg-slate-50 border-slate-200 hover:border-brand-400 hover:bg-white hover:shadow-xs'
                              }`}
                            >
                              <div className="flex items-center justify-between pb-1 border-b border-slate-200/60">
                                <div className="flex items-center gap-1.5">
                                  <GripVertical className="w-3.5 h-3.5 text-slate-400 shrink-0 cursor-grab" />
                                  <span className="text-[10px] uppercase font-bold text-slate-700">{slotTitle}</span>
                                </div>
                                <div className="flex items-center gap-1">
                                  <button
                                    onClick={() => setEditingSlot(isEditing ? null : { dayIdx, slotKey })}
                                    className="p-1 rounded text-slate-400 hover:text-brand-600 hover:bg-slate-200 transition-all"
                                    title="Edit or Swap Place"
                                  >
                                    <Edit3 className="w-3.5 h-3.5" />
                                  </button>
                                  <button
                                    onClick={() => handleRemoveSlot(dayIdx, slotKey)}
                                    className="p-1 rounded text-slate-400 hover:text-rose-600 hover:bg-slate-200 transition-all"
                                    title="Remove Slot"
                                  >
                                    <Trash2 className="w-3.5 h-3.5" />
                                  </button>
                                </div>
                              </div>

                              {/* EDIT & SWAP MODE */}
                              {isEditing ? (
                                <div className="space-y-2 bg-white p-2.5 rounded-lg border border-brand-300 shadow-2xs">
                                  <div>
                                    <label className="text-[10px] font-bold text-slate-500 block mb-0.5">Swap Destination:</label>
                                    <select
                                      value={slot.place_name || ''}
                                      onChange={(e) => handleSwapPlace(dayIdx, slotKey, e.target.value)}
                                      className="w-full text-xs font-bold p-1 rounded border border-slate-200 bg-slate-50 outline-none"
                                    >
                                      <option value={slot.place_name || ''}>{slot.place_name || 'Selected Place'} (Current)</option>
                                      {availableAlternatives.map((alt) => (
                                        <option key={alt.id} value={alt.name}>
                                          {alt.name} ({alt.sub_category || alt.category})
                                        </option>
                                      ))}
                                    </select>
                                  </div>

                                  <div>
                                    <label className="text-[10px] font-bold text-slate-500 block mb-0.5">Visiting Time:</label>
                                    <input
                                      type="text"
                                      value={slot.est_time || ''}
                                      onChange={(e) => handleEditNoteOrTime(dayIdx, slotKey, 'est_time', e.target.value)}
                                      className="w-full text-xs p-1 rounded border border-slate-200 bg-slate-50 outline-none"
                                    />
                                  </div>

                                  <div>
                                    <label className="text-[10px] font-bold text-slate-500 block mb-0.5">Custom Notes:</label>
                                    <input
                                      type="text"
                                      value={slot.activity_note || ''}
                                      onChange={(e) => handleEditNoteOrTime(dayIdx, slotKey, 'activity_note', e.target.value)}
                                      className="w-full text-xs p-1 rounded border border-slate-200 bg-slate-50 outline-none"
                                    />
                                  </div>

                                  <button
                                    onClick={() => setEditingSlot(null)}
                                    className="w-full py-1 bg-brand-600 text-white rounded text-[11px] font-bold flex items-center justify-center gap-1"
                                  >
                                    <Check className="w-3.5 h-3.5" /> Done Editing
                                  </button>
                                </div>
                              ) : (
                                /* DISPLAY MODE WITH DRAG FEEDBACK */
                                <>
                                  <div className="font-bold text-slate-900 text-sm flex items-center justify-between">
                                    <span>{slot.place_name || 'Destination'}</span>
                                    <span className="text-[10px] text-slate-400 font-normal">({slot.est_time || 'Flexible'})</span>
                                  </div>
                                  <p className="text-slate-600 leading-relaxed text-[11px]">{slot.activity_note}</p>
                                  {/* Mobile touch quick reordering */}
                                  {aiItinerary.days && aiItinerary.days.length > 1 && (
                                    <div className="flex items-center gap-1.5 pt-1 md:hidden">
                                      <button
                                        type="button"
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          const targetDayIdx = dayIdx === 0 ? 1 : 0;
                                          handleDropDirect(dayIdx, slotKey, targetDayIdx, slotKey);
                                        }}
                                        className="text-[10px] text-teal-700 bg-teal-50 hover:bg-teal-100 px-2 py-0.5 rounded-md font-medium border border-teal-200"
                                      >
                                        ↔ Swap with Day {dayIdx === 0 ? 2 : 1}
                                      </button>
                                    </div>
                                  )}
                                </>
                              )}
                            </div>
                          );
                        })}
                      </div>
                      <p className="text-[11px] text-slate-500 pt-1 text-center font-medium">
                        💡 Click <span className="font-bold text-teal-700">"⚡ Optimize Route & Order"</span> above to calculate inter-stop travel times and view turn-by-turn routes on the map!
                      </p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Travel Tips & Belief Decorum Advisory */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {aiItinerary.travel_tips && (
              <div className="p-4 rounded-xl bg-white border border-teal-200 text-xs space-y-1">
                <span className="font-bold text-teal-800 uppercase tracking-wider">💡 Local Travel Tips:</span>
                <ul className="list-disc list-inside space-y-0.5 text-slate-600">
                  {aiItinerary.travel_tips.map((tip, idx) => (
                    <li key={idx}>{tip}</li>
                  ))}
                </ul>
              </div>
            )}

            {aiItinerary.belief_and_etiquette_advisory && (
              <div className="p-4 rounded-xl bg-purple-50/80 border border-purple-200 text-xs space-y-1">
                <span className="font-bold text-purple-900 uppercase tracking-wider">📜 Religious, Belief & Etiquette Advisory:</span>
                <p className="text-purple-900/90 leading-relaxed mt-1">
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
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-xs space-y-5">
            <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
              <Sliders className="w-5 h-5 text-brand-600" />
              <h2 className="text-base font-bold text-slate-800">Demographic & Dietary Filter Tuning</h2>
            </div>

            {/* 1. Age Group Selector */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                1. Select Age Bracket
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {AGE_GROUPS.map(a => (
                  <button
                    key={a.id}
                    onClick={() => setAgeGroup(a.id)}
                    className={`p-3 rounded-xl text-left border transition-all ${
                      ageGroup === a.id
                        ? 'bg-brand-50 border-brand-500 ring-2 ring-brand-500/20 text-brand-900 font-bold shadow-xs'
                        : 'bg-slate-50 border-slate-200 hover:bg-slate-100 text-slate-700 font-medium'
                    }`}
                  >
                    <div className="text-sm">{a.shortLabel} yrs</div>
                    <div className="text-[10px] text-slate-500 font-normal mt-0.5 line-clamp-1">{a.label.split('(')[1]?.replace(')', '')}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* 2. Dietary Preference */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                2. Self-Declared Dietary Filter (Opt-In)
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                {DIETARY_OPTIONS.map(d => (
                  <button
                    key={d.id}
                    onClick={() => setDietaryPreference(d.id)}
                    className={`p-2.5 rounded-xl text-left border text-xs transition-all ${
                      dietaryPreference === d.id
                        ? 'bg-brand-50 border-brand-500 ring-2 ring-brand-500/20 text-brand-900 font-bold'
                        : 'bg-slate-50 border-slate-200 hover:bg-slate-100 text-slate-700'
                    }`}
                  >
                    <div>{d.label}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* 3. Budget Tier */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                3. Budget Level
              </label>
              <div className="grid grid-cols-3 gap-2">
                {BUDGET_TIERS.map(b => (
                  <button
                    key={b.id}
                    onClick={() => setBudgetTier(b.id)}
                    className={`p-2.5 rounded-xl text-center border text-xs transition-all ${
                      budgetTier === b.id
                        ? 'bg-brand-50 border-brand-500 ring-2 ring-brand-500/20 text-brand-900 font-bold'
                        : 'bg-slate-50 border-slate-200 hover:bg-slate-100 text-slate-700'
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
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-extrabold text-slate-900 flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-brand-600" />
                Ranked Destinations for Profile ({recommendations.length} Places)
              </h2>
              <span className="text-xs text-slate-500">Sorted by match score</span>
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
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-xs sticky top-24 space-y-6">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Luggage className="w-5 h-5 text-brand-600" />
                <h3 className="font-bold text-slate-900">Your Trip Basket</h3>
              </div>
              {tripPlan.length > 0 && (
                <button
                  onClick={clearTripPlan}
                  className="text-xs text-rose-600 hover:text-rose-700 font-medium flex items-center gap-1"
                >
                  <Trash2 className="w-3.5 h-3.5" /> Clear
                </button>
              )}
            </div>

            {/* Trip Stats */}
            <div className="grid grid-cols-2 gap-3 p-3 bg-slate-50 rounded-xl border border-slate-100 text-center">
              <div>
                <div className="text-[11px] text-slate-400">Total Activity Cost</div>
                <div className="text-base font-extrabold text-slate-900 flex items-center justify-center gap-0.5 mt-0.5">
                  <IndianRupee className="w-4 h-4 text-slate-600" />
                  {totalCost === 0 ? 'Free' : `₹${totalCost}`}
                </div>
              </div>
              <div>
                <div className="text-[11px] text-slate-400">Est. Time Needed</div>
                <div className="text-base font-extrabold text-slate-900 flex items-center justify-center gap-1 mt-0.5">
                  <Clock className="w-4 h-4 text-slate-600" />
                  ~{totalHours} hrs
                </div>
              </div>
            </div>

            {/* Selected Items List */}
            {tripPlan.length === 0 ? (
              <div className="py-8 text-center space-y-2">
                <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center mx-auto text-slate-400">
                  <Luggage className="w-5 h-5" />
                </div>
                <p className="text-xs text-slate-500 font-medium">Your basket is empty.</p>
                <p className="text-[11px] text-slate-400">Click "+ Add to Trip" on any card to build your custom schedule.</p>
              </div>
            ) : (
              <div className="space-y-2.5 max-h-96 overflow-y-auto pr-1">
                {tripPlan.map((place, idx) => (
                  <div 
                    key={place.id}
                    className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-200/80 text-xs"
                  >
                    <div className="flex items-center gap-2.5 overflow-hidden">
                      <span className="w-5 h-5 rounded-full bg-brand-100 text-brand-800 font-bold flex items-center justify-center shrink-0 text-[10px]">
                        {idx + 1}
                      </span>
                      <div className="truncate">
                        <div className="font-bold text-slate-800 truncate">{place.name}</div>
                        <div className="text-slate-400 text-[10px]">~{place.duration_minutes} mins • {place.estimated_cost_inr === 0 ? 'Free' : `₹${place.estimated_cost_inr}`}</div>
                      </div>
                    </div>

                    <button
                      onClick={() => removeFromTripPlan(place.id)}
                      className="text-slate-400 hover:text-rose-500 p-1 transition-colors"
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
  );
}
