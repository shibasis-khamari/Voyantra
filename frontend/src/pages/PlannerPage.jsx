import React, { useState, useEffect, useRef } from 'react';
import { 
  Sparkles, Luggage, IndianRupee, Clock, Trash2, Check, RefreshCw, Plus, GripVertical,
  ArrowRight, CheckCircle2, Compass, Send, Loader2, Zap, Pencil, MoreHorizontal,
  ChevronDown, X, PanelRightClose, PanelRightOpen, MapPin, SlidersHorizontal, MessageSquare,
  History, Brain, Radio, Volume2, VolumeX
} from 'lucide-react';
import { PlaceModal } from '../components/PlaceModal';
import { VoyantraAPI } from '../services/api';
import { usePreferences } from '../context/PreferencesContext';

// Voyantra 2.0 Chat Components
import { LanguageSelector } from '../components/chat/LanguageSelector';
import { VoiceInputButton, playTextToSpeech, stopTextToSpeech } from '../components/chat/VoiceInputButton';
import { LiveVoiceModal } from '../components/chat/LiveVoiceModal';
import { ConversationHistoryDrawer } from '../components/chat/ConversationHistoryDrawer';
import { MemorySettingsModal } from '../components/chat/MemorySettingsModal';
import { ItineraryAlternativesPicker } from '../components/chat/ItineraryAlternativesPicker';
import { RichCardList } from '../components/chat/RichCardList';

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
    dietaryPreference, 
    budgetTier, 
    tripPlan,
    addToTripPlan,
    activeItinerary: globalItinerary,
    setActiveItinerary: setGlobalItinerary
  } = usePreferences();

  // Recommendations state for place details lookups
  const [recommendations, setRecommendations] = useState([]);
  const [activeModalItem, setActiveModalItem] = useState(null);

  // AI & Preset Suggestions State
  const [presetSuggestions, setPresetSuggestions] = useState([]);
  const [selectedPresetId, setSelectedPresetId] = useState('');
  const [aiItinerary, setAiItinerary] = useState(() => globalItinerary || null);
  const [activeAlternativeId, setActiveAlternativeId] = useState('alt-relaxed');
  const [editingSlotData, setEditingSlotData] = useState(null);
  const [basketToast, setBasketToast] = useState(null);

  // Voyantra 2.0 Multilingual & Voice State
  const [conversationId, setConversationId] = useState(null);
  const [selectedLanguage, setSelectedLanguage] = useState(null); // null = auto detect; 'en' | 'hi' | 'ta'
  const [isLiveVoiceOpen, setIsLiveVoiceOpen] = useState(false);
  const [isHistoryDrawerOpen, setIsHistoryDrawerOpen] = useState(false);
  const [isMemoryModalOpen, setIsMemoryModalOpen] = useState(false);
  const [audioReadAloud, setAudioReadAloud] = useState(false);

  // Mobile View Switcher: 'chat' | 'itinerary'
  const [mobileTab, setMobileTab] = useState('chat');

  // Drag & Drop State
  const [draggedCard, setDraggedCard] = useState(null);
  const [dragOverTarget, setDragOverTarget] = useState(null);
  
  // AI Conversational Chatbox State
  const [chatMessages, setChatMessages] = useState([
    {
      id: 'welcome-msg',
      sender: 'ai',
      text: "Hello! 👋 I'm your **Voyantra AI Travel Concierge**.\n\nI offer full travel intelligence for **Pondicherry & Chennai**, plus worldwide knowledge. You can talk to me in **English**, **हिन्दी (Hindi)**, or **தமிழ் (Tamil)** using text, Push-to-Talk, or Live Voice.\n\nAsk me about sights, boutique stays, authentic food, or request a complete multi-day itinerary!",
      timestamp: 'Just now',
      language: 'en',
      suggested_followups: [
        "Plan a 2-day trip to Pondicherry & Chennai",
        "पुडुचेरी में सबसे अच्छे समुद्र तट कौन से हैं?",
        "சென்னையில் உள்ள சிறந்த பாரம்பரிய இடங்கள் எவை?",
        "Top vegetarian dining in Mylapore & White Town"
      ]
    }
  ]);
  const [chatInputText, setChatInputText] = useState('');
  const [isRefining, setIsRefining] = useState(false);
  const chatEndRef = useRef(null);

  // Route Optimization State
  const [optimizingDay, setOptimizingDay] = useState(null);
  const [lockedSlots, setLockedSlots] = useState({});
  const [transitModes, setTransitModes] = useState({});
  const [backendError, setBackendError] = useState(null);

  // Auto-scroll chat to bottom
  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatMessages, isRefining]);

  // Load presets & recommendations on mount
  useEffect(() => {
    loadPresetSuggestions();
    loadPlacesForLookup();
  }, [selectedCity]);

  const loadPresetSuggestions = async () => {
    try {
      const suggs = await VoyantraAPI.getPresetSuggestions();
      setPresetSuggestions(suggs || []);
    } catch (e) {
      console.warn("Failed to load preset suggestions:", e.message);
    }
  };

  const loadPlacesForLookup = async () => {
    try {
      const places = await VoyantraAPI.getPlaces({ city_id: 'all' });
      setRecommendations(places || []);
    } catch (e) {
      console.warn("Failed to load places for lookup:", e.message);
    }
  };

  // Helper to extract duration from conversational text
  const extractDurationFromText = (text) => {
    if (!text) return 2;
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
    return 2;
  };

  // Send message to AI Concierge (Unified Voyantra 2.0 /api/v1/chat/message)
  const handleSendMessage = async (textToSend = null, voiceMode = 'text') => {
    const text = (textToSend || chatInputText).trim();
    if (!text || isRefining) return null;

    const detectedDays = extractDurationFromText(text);

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
      const res = await VoyantraAPI.sendChatMessage({
        message: text,
        conversation_id: conversationId,
        language: selectedLanguage,
        voice_mode: voiceMode,
        current_itinerary: aiItinerary,
        user_preferences: {
          age_group: ageGroup,
          dietary_preference: dietaryPreference,
          budget_tier: budgetTier
        },
        duration_days: detectedDays
      });

      if (res) {
        if (res.conversation_id) {
          setConversationId(res.conversation_id);
        }

        const aiMsg = {
          id: `ai-${Date.now()}`,
          sender: 'ai',
          text: res.reply_message,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          language: res.language || 'en',
          intent: res.intent,
          places: res.places || [],
          hotels: res.hotels || [],
          restaurants: res.restaurants || [],
          suggested_followups: res.suggested_followups || [],
          hasItinerary: Boolean(res.itinerary)
        };
        setChatMessages(prev => [...prev, aiMsg]);

        // If audio read-aloud is active and not live_voice mode (live voice manages its own speech)
        if (audioReadAloud && voiceMode !== 'live_voice' && res.reply_message) {
          playTextToSpeech(res.reply_message, res.language || 'en');
        }

        if (res.itinerary) {
          setAiItinerary(res.itinerary);
          setGlobalItinerary(res.itinerary);
          if (res.itinerary.active_alternative_id) {
            setActiveAlternativeId(res.itinerary.active_alternative_id);
          }
          // Auto switch to itinerary on mobile view
          setMobileTab('itinerary');
        }

        return res;
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
      setBackendError(e.message);
      return null;
    } finally {
      setIsRefining(false);
    }
  };

  const selectPreset = (sugg) => {
    if (!sugg) return;
    setSelectedPresetId(sugg.id);
    handleSendMessage(sugg.prompt);
  };

  // Alternative Selection Handler
  const handleSelectAlternative = (altId) => {
    if (!aiItinerary || !aiItinerary.alternatives) return;
    const selectedAlt = aiItinerary.alternatives.find(a => a.id === altId);
    if (!selectedAlt) return;

    setActiveAlternativeId(altId);
    const updatedItinerary = {
      ...aiItinerary,
      active_alternative_id: altId,
      days: selectedAlt.days,
      total_estimated_budget_inr: selectedAlt.total_estimated_budget_inr,
      summary: selectedAlt.summary
    };
    setAiItinerary(updatedItinerary);
    setGlobalItinerary(updatedItinerary);
  };

  // Resume past conversation session
  const handleSelectConversation = async (convId) => {
    try {
      setIsRefining(true);
      const data = await VoyantraAPI.getConversation(convId);
      if (data && data.messages) {
        setConversationId(convId);
        const mapped = data.messages.map((m, idx) => ({
          id: m.id || `msg-${idx}`,
          sender: m.role === 'user' ? 'user' : 'ai',
          text: m.content,
          timestamp: m.timestamp ? new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Earlier',
          language: m.language || 'en'
        }));
        setChatMessages(mapped.length > 0 ? mapped : chatMessages);
      }
    } catch (e) {
      alert("Could not load conversation: " + e.message);
    } finally {
      setIsRefining(false);
    }
  };

  // Start fresh conversation session
  const handleNewConversation = () => {
    setConversationId(null);
    setChatMessages([
      {
        id: 'welcome-fresh',
        sender: 'ai',
        text: "Started a new conversation session. ✨ What would you like to explore next?",
        timestamp: 'Just now',
        language: 'en',
        suggested_followups: [
          "Plan a weekend getaway to Pondicherry",
          "What are the best seafood restaurants in Chennai?",
          "Heritage walk in White Town"
        ]
      }
    ]);
  };

  // Generic Add to Basket helper for Place, Hotel, or Restaurant
  const handleAddCardToBasket = (item, type = 'place') => {
    let placeObj = null;
    if (type === 'hotel') {
      placeObj = {
        id: item.id || `hotel-${Date.now()}`,
        name: item.name,
        description: `Boutique Accommodation (${item.budget_tier}) - ₹${item.price_per_night_inr}/night. ${item.amenities?.join(', ') || ''}`,
        category: 'hotel',
        city_id: item.city_id || 'pondicherry',
        estimated_cost_inr: item.price_per_night_inr || 0,
        duration_minutes: 480
      };
    } else if (type === 'restaurant') {
      placeObj = {
        id: item.id || `rest-${Date.now()}`,
        name: item.name,
        description: `Dining (${item.category}) - ${item.dietary_options?.join(', ') || 'Authentic dishes'}`,
        category: 'restaurant',
        city_id: item.city_id || 'pondicherry',
        estimated_cost_inr: item.estimated_cost_inr || 350,
        duration_minutes: 60
      };
    } else {
      placeObj = {
        id: item.id || `place-${Date.now()}`,
        name: item.name,
        description: item.highlights?.join(' • ') || item.address || 'Curated attraction',
        category: item.category || 'culture',
        city_id: item.city_id || 'pondicherry',
        estimated_cost_inr: item.estimated_cost_inr || 0,
        duration_minutes: item.duration_minutes || 60
      };
    }

    addToTripPlan(placeObj);
    setBasketToast(`Added "${item.name}" to Basket!`);
    setTimeout(() => setBasketToast(null), 3000);
  };

  // Day Optimization Helper
  const findCoordinatesForPlace = (placeName) => {
    if (!placeName) return { lat: 11.9416, lng: 79.8083 };
    const norm = placeName.toLowerCase().trim();
    const found = recommendations.find(p => 
      p.name && (p.name.toLowerCase().includes(norm) || norm.includes(p.name.toLowerCase()))
    );
    if (found?.coordinates?.lat && found?.coordinates?.lng) {
      return { lat: found.coordinates.lat, lng: found.coordinates.lng };
    }
    if (norm.includes('chennai') || norm.includes('marina') || norm.includes('mylapore')) {
      return { lat: 13.0827, lng: 80.2707 };
    }
    return { lat: 11.9416, lng: 79.8083 };
  };

  const handleOptimizeDay = async (dayIdx) => {
    if (!aiItinerary || !aiItinerary.days || !aiItinerary.days[dayIdx]) return;
    const day = aiItinerary.days[dayIdx];
    const mode = transitModes[dayIdx] || 'driving';

    setOptimizingDay(dayIdx);
    setBackendError(null);

    try {
      const slotKeys = Object.keys(day).filter(k => !['day_number', 'theme'].includes(k) && !!day[k]);
      if (slotKeys.length === 0) return;

      const slots = slotKeys.map((k) => {
        const rawSlot = day[k];
        const name = typeof rawSlot === 'string' ? rawSlot : (rawSlot.place_name || 'Destination');
        const coords = findCoordinatesForPlace(name);
        const slotId = `d${dayIdx}_${k}`;

        return {
          slot_id: slotId,
          place_name: name,
          coordinates: coords,
          time_anchor: k === 'morning' ? 'morning' : k === 'afternoon' ? 'afternoon' : 'sunset',
          is_locked: !!lockedSlots[slotId],
          visit_duration_minutes: 60,
          opening_hours: { is_verified: false }
        };
      });

      await VoyantraAPI.optimizeDaySchedule({
        day_number: day.day_number || (dayIdx + 1),
        city_id: 'all',
        mode,
        travel_date: '2026-11-15',
        slots
      });
    } catch (err) {
      console.warn("Optimization notice:", err.message);
    } finally {
      setOptimizingDay(null);
    }
  };

  // Drag and Drop
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

    updatedDays[targetDayIdx][targetSlotKey] = { ...fromData };

    if (targetData) {
      updatedDays[fromDayIdx][fromSlotKey] = { ...targetData };
    } else {
      delete updatedDays[fromDayIdx][fromSlotKey];
    }

    const updated = { ...aiItinerary, days: updatedDays };
    setAiItinerary(updated);
    setGlobalItinerary(updated);
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
    const updated = { ...aiItinerary, days: updatedDays };
    setAiItinerary(updated);
    setGlobalItinerary(updated);
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

  const handleRemoveSlot = (dayIdx, timeSlot) => {
    if (!aiItinerary) return;
    const updatedDays = [...aiItinerary.days];
    if (updatedDays[dayIdx]) {
      delete updatedDays[dayIdx][timeSlot];
    }
    const updated = { ...aiItinerary, days: updatedDays };
    setAiItinerary(updated);
    setGlobalItinerary(updated);
  };

  const handleAddSlotToDay = (dayIdx) => {
    if (!aiItinerary) return;
    const updatedDays = [...aiItinerary.days];
    const slotCount = Object.keys(updatedDays[dayIdx]).filter(k => k.startsWith('custom_')).length + 1;
    const slotKey = `custom_${slotCount}`;
    updatedDays[dayIdx][slotKey] = {
      place_name: "Local Sightseeing & Leisure",
      activity_note: "Custom stop added by traveler.",
      est_time: "Flexible Time"
    };
    const updated = { ...aiItinerary, days: updatedDays };
    setAiItinerary(updated);
    setGlobalItinerary(updated);
  };

  const handleAddAllToBasket = () => {
    if (!aiItinerary) return;
    let addedCount = 0;
    aiItinerary.days.forEach(d => {
      Object.keys(d).forEach(slotKey => {
        if (['day_number', 'theme'].includes(slotKey)) return;
        const slot = d[slotKey];
        if (slot && slot.place_name) {
          const matchedPlace = recommendations.find(p => p.name?.toLowerCase() === slot.place_name?.toLowerCase());
          const placeToAdd = matchedPlace || {
            id: `itin-stop-${Date.now()}-${Math.random().toString(36).substr(2, 4)}`,
            name: slot.place_name,
            description: slot.activity_note || "Stop from AI Generated Itinerary",
            category: "culture",
            city_id: slot.place_name.toLowerCase().includes('chennai') ? 'chennai' : 'pondicherry',
            estimated_cost_inr: 0,
            duration_minutes: 60
          };
          addToTripPlan(placeToAdd);
          addedCount++;
        }
      });
    });

    setBasketToast(`Saved ${addedCount} destinations to your Trip Basket!`);
    setTimeout(() => setBasketToast(null), 3500);
  };

  return (
    <div className="relative h-[calc(100vh-4rem)] w-full overflow-hidden flex flex-col font-sans select-none">
      {/* Background Horizon Backdrop */}
      <div 
        className="fixed inset-0 z-0 overflow-hidden pointer-events-none select-none"
        aria-hidden="true"
      >
        <img
          src="/images/luisa-linkous-L03SoHMhbz8-unsplash.jpg"
          alt="Scenic Coastal View"
          className="w-full h-full object-cover object-center fixed scale-105 filter brightness-[0.96] contrast-[1.04] saturate-[1.1]"
        />
        <div className="absolute inset-0 bg-slate-950/30" />
        <div className="absolute inset-0 bg-gradient-to-b from-slate-950/40 via-transparent to-slate-950/45" />
      </div>

      {/* Top Single-Page Command Bar */}
      <div className="relative z-20 h-14 px-3 sm:px-6 bg-slate-950/85 backdrop-blur-xl border-b border-white/10 flex items-center justify-between gap-2 text-white shrink-0">
        
        {/* Left: AI Concierge Brand & Status */}
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-white/10 border border-white/20 flex items-center justify-center shadow-xs">
            <Sparkles className="w-4 h-4 text-[#FCD34D]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-xs sm:text-sm tracking-tight text-white">Voyantra AI Concierge</span>
              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full bg-[#FCD34D]/20 text-[#FCD34D] border border-[#FCD34D]/40 text-[9px] font-bold">
                <span className="w-1.5 h-1.5 rounded-full bg-[#FCD34D] animate-ping" />
                Live 2.0
              </span>
            </div>
            <p className="text-[10px] text-slate-300 hidden sm:block">
              Multilingual Travel Intelligence • Pondicherry & Chennai
            </p>
          </div>
        </div>

        {/* Center / Right: Quick Controls, Voice Mode, Memory & History */}
        <div className="flex items-center gap-1.5 sm:gap-2">
          
          {/* Language Selector (en, hi, ta, auto) */}
          <LanguageSelector
            selectedLanguage={selectedLanguage}
            onSelectLanguage={(lang) => setSelectedLanguage(lang)}
          />

          {/* Live Voice Opt-In Button */}
          <button
            onClick={() => setIsLiveVoiceOpen(true)}
            className="flex items-center gap-1 px-2.5 sm:px-3 py-1.5 rounded-full bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-400/40 text-emerald-300 text-xs font-bold transition-all cursor-pointer shadow-xs"
            title="Launch Hands-Free Live Voice Mode"
          >
            <Radio className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
            <span className="hidden sm:inline">Live Voice</span>
          </button>

          {/* AI Memory Settings Button */}
          <button
            onClick={() => setIsMemoryModalOpen(true)}
            className="p-1.5 sm:px-2.5 sm:py-1.5 rounded-full bg-white/10 hover:bg-white/20 border border-white/20 text-slate-200 hover:text-white text-xs font-semibold flex items-center gap-1 transition-all cursor-pointer"
            title="Manage AI Memory & Cultural Preferences"
          >
            <Brain className="w-3.5 h-3.5 text-[#FCD34D]" />
            <span className="hidden md:inline">Memory</span>
          </button>

          {/* Chat History Drawer Button */}
          <button
            onClick={() => setIsHistoryDrawerOpen(true)}
            className="p-1.5 sm:px-2.5 sm:py-1.5 rounded-full bg-white/10 hover:bg-white/20 border border-white/20 text-slate-200 hover:text-white text-xs font-semibold flex items-center gap-1 transition-all cursor-pointer"
            title="View Past Chat Sessions"
          >
            <History className="w-3.5 h-3.5 text-indigo-300" />
            <span className="hidden md:inline">History</span>
          </button>

          {/* Preset Selector Dropdown */}
          <div className="relative hidden lg:block">
            <select
              value={selectedPresetId}
              onChange={(e) => {
                const id = e.target.value;
                setSelectedPresetId(id);
                const found = presetSuggestions.find(s => s.id === id);
                if (found) selectPreset(found);
              }}
              className="appearance-none bg-white/10 hover:bg-white/15 border border-white/20 px-3 py-1.5 pr-7 rounded-full text-xs font-semibold text-white outline-none cursor-pointer max-w-[180px] truncate [&>option]:bg-slate-900 [&>option]:text-white"
            >
              <option value="">✨ Curated Presets...</option>
              {presetSuggestions.map(s => (
                <option key={s.id} value={s.id}>
                  {s.icon} {s.title}
                </option>
              ))}
            </select>
            <div className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-300">
              <ChevronDown className="w-3 h-3" />
            </div>
          </div>

          {/* Mobile Tab Toggle */}
          {aiItinerary && (
            <div className="md:hidden flex items-center bg-white/10 border border-white/20 rounded-full p-0.5 text-xs font-bold">
              <button
                onClick={() => setMobileTab('chat')}
                className={`px-2.5 py-1 rounded-full transition-all cursor-pointer ${
                  mobileTab === 'chat' ? 'bg-[#FCD34D] text-slate-950 shadow-xs' : 'text-slate-300 hover:text-white'
                }`}
              >
                Chat
              </button>
              <button
                onClick={() => setMobileTab('itinerary')}
                className={`px-2.5 py-1 rounded-full transition-all cursor-pointer ${
                  mobileTab === 'itinerary' ? 'bg-[#FCD34D] text-slate-950 shadow-xs' : 'text-slate-300 hover:text-white'
                }`}
              >
                Itinerary
              </button>
            </div>
          )}

          {/* Close Itinerary (Return to Full Chat) */}
          {aiItinerary && (
            <button
              onClick={() => {
                setAiItinerary(null);
                setGlobalItinerary(null);
                setMobileTab('chat');
              }}
              className="hidden sm:flex items-center gap-1 px-2.5 py-1.5 rounded-full bg-white/10 hover:bg-white/20 border border-white/20 text-slate-200 hover:text-white text-xs font-medium cursor-pointer transition-all"
              title="Close itinerary to return to full-screen AI chat"
            >
              <PanelRightClose className="w-3.5 h-3.5 text-slate-400" />
              <span>Full Chat</span>
            </button>
          )}

          {/* Saved Basket Link */}
          <button
            onClick={() => setActiveTab('basket')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/10 hover:bg-white/20 border border-white/20 text-white text-xs font-semibold cursor-pointer transition-all"
            title="Open Saved Basket"
          >
            <Luggage className="w-3.5 h-3.5 text-amber-300" />
            <span className="hidden md:inline">Basket</span>
            <span className="w-4 h-4 rounded-full bg-terracotta text-white flex items-center justify-center text-[10px] font-bold">
              {tripPlan.length}
            </span>
          </button>
        </div>
      </div>

      {/* Basket Added Toast Notice */}
      {basketToast && (
        <div className="absolute top-16 right-4 z-50 p-3 rounded-2xl bg-slate-900/95 border border-[#FCD34D]/60 text-white shadow-2xl flex items-center gap-2.5 text-xs font-semibold animate-fadeIn">
          <CheckCircle2 className="w-4 h-4 text-[#FCD34D] shrink-0" />
          <span>{basketToast}</span>
          <button
            onClick={() => setActiveTab('basket')}
            className="ml-2 px-2 py-0.5 rounded-lg bg-[#FCD34D] text-slate-950 font-bold text-[10px] hover:bg-amber-300 transition-colors cursor-pointer"
          >
            View Basket →
          </button>
        </div>
      )}

      {/* Main Single-Page Body Container */}
      <div className="relative z-10 flex-1 min-h-0 flex overflow-hidden">
        
        {/* =================================================================== */}
        {/* LEFT / FULL-WIDTH PANEL: Conversational AI Concierge Chatbox       */}
        {/* Covers 100% width when no itinerary; ~45% width when itinerary ready */}
        {/* =================================================================== */}
        <div 
          className={`flex flex-col h-full bg-white/75 backdrop-blur-xl transition-all duration-300 ${
            aiItinerary 
              ? `${mobileTab === 'chat' ? 'flex' : 'hidden'} md:flex md:w-[48%] lg:w-[44%] border-r border-white/30` 
              : 'w-full'
          }`}
        >
          {/* Chat Messages Stream */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
            
            {/* Minimal Welcome Hero Card inside Chat Stream */}
            <div className="p-4 sm:p-5 rounded-3xl bg-white/80 border border-white/70 shadow-sm space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs font-bold text-slate-700">
                  <Sparkles className="w-4 h-4 text-amber-600" />
                  <span>Voyantra Conversational Travel AI</span>
                </div>
                <div className="text-[10px] font-bold text-slate-500">
                  🇮🇳 EN • हिन्दी • தமிழ்
                </div>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">
                Discover places, verified boutique hotels, and dining in **Pondicherry & Chennai**, or get intelligent answers for destinations worldwide.
              </p>
              
              {/* Quick Multilingual Prompt Suggestions */}
              <div className="flex flex-wrap gap-1.5 pt-1">
                {[
                  "2-day trip to Pondicherry & Chennai",
                  "पुडुचेरी के प्रमुख आकर्षण",
                  "மயிலாப்பூர் கபாலீஸ்வரர் கோவில் நேரம்",
                  "Quiet boutique hotels with ocean view"
                ].map((prompt, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSendMessage(prompt)}
                    className="px-2.5 py-1 rounded-full bg-slate-100 hover:bg-[#FCD34D]/30 border border-slate-200 text-slate-700 hover:text-slate-950 text-[11px] font-semibold transition-all cursor-pointer shadow-2xs"
                  >
                    💡 {prompt}
                  </button>
                ))}
              </div>
            </div>

            {/* Conversation Messages */}
            {chatMessages.map((msg) => (
              <div
                key={msg.id}
                className={`flex flex-col ${msg.sender === 'user' ? 'items-end' : 'items-start'} space-y-2 animate-fadeIn`}
              >
                <div
                  className={`max-w-[92%] sm:max-w-[88%] p-4 rounded-2xl text-xs sm:text-sm shadow-sm ${
                    msg.sender === 'user'
                      ? 'bg-gradient-to-r from-terracotta to-orange-500 text-white rounded-br-none shadow-md font-sans'
                      : 'bg-white/95 backdrop-blur-md border border-white/80 text-slate-900 rounded-bl-none shadow-sm'
                  }`}
                >
                  {msg.sender === 'user' ? (
                    <p className="font-medium leading-relaxed whitespace-pre-wrap">{msg.text}</p>
                  ) : (
                    <>
                      <FormattedMessage text={msg.text} />
                      
                      {/* Audio Read-out Speaker button on AI messages */}
                      <div className="flex items-center justify-between pt-2 mt-2 border-t border-slate-100 text-[10px] text-slate-400">
                        <span className="uppercase font-bold text-[9px] tracking-wider text-slate-500">
                          {msg.language ? `${msg.language.toUpperCase()} • ` : ''}{msg.timestamp}
                        </span>
                        <button
                          type="button"
                          onClick={() => playTextToSpeech(msg.text, msg.language || 'en')}
                          className="flex items-center gap-1 hover:text-slate-900 text-slate-500 transition-colors cursor-pointer"
                          title="Listen to this message"
                        >
                          <Volume2 className="w-3 h-3 text-slate-600" />
                          <span>Listen</span>
                        </button>
                      </div>
                    </>
                  )}
                </div>

                {/* Rich Discovery Cards (Places, Hotels, Restaurants) */}
                {msg.sender === 'ai' && (
                  <RichCardList
                    places={msg.places}
                    hotels={msg.hotels}
                    restaurants={msg.restaurants}
                    onAddToBasket={(item, type) => handleAddCardToBasket(item, type)}
                    onOpenDetails={(place) => setActiveModalItem({ place })}
                  />
                )}

                {/* Contextual Followup Chips */}
                {msg.suggested_followups && msg.suggested_followups.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 pt-1 pl-1">
                    {msg.suggested_followups.map((fup, i) => (
                      <button
                        key={i}
                        onClick={() => handleSendMessage(fup)}
                        disabled={isRefining}
                        className="px-2.5 py-1 rounded-full bg-white/90 hover:bg-[#FCD34D]/30 hover:text-slate-950 text-slate-700 text-[10px] sm:text-[11px] font-bold border border-white/70 transition-all shadow-2xs disabled:opacity-50 cursor-pointer"
                      >
                        💡 {fup}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}

            {/* AI Typing Indicator */}
            {isRefining && (
              <div className="flex items-start gap-2.5 animate-fadeIn">
                <div className="w-7 h-7 rounded-full bg-slate-900 p-1 flex items-center justify-center shadow-xs border border-[#FCD34D]/40">
                  <Sparkles className="w-3.5 h-3.5 text-[#FCD34D]" />
                </div>
                <div className="p-3.5 rounded-2xl bg-white/90 backdrop-blur-md border border-white/70 text-xs text-slate-900 font-bold flex items-center gap-2 shadow-xs">
                  <Loader2 className="w-3.5 h-3.5 text-terracotta animate-spin" />
                  <span>Voyantra Concierge is thinking...</span>
                </div>
              </div>
            )}

            <div ref={chatEndRef} />
          </div>

          {/* Chat Input Bar Pinned at Bottom */}
          <div className="p-3 sm:p-4 bg-white/85 backdrop-blur-xl border-t border-white/40 shrink-0">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
              className="flex items-center gap-2"
            >
              {/* Push-to-Talk Voice Input Button */}
              <VoiceInputButton
                language={selectedLanguage || 'en'}
                onTranscriptReady={(transcript) => {
                  setChatInputText(transcript);
                  handleSendMessage(transcript);
                }}
                disabled={isRefining}
              />

              {/* Text Input Box */}
              <input
                type="text"
                value={chatInputText}
                onChange={(e) => setChatInputText(e.target.value)}
                placeholder={
                  selectedLanguage === 'hi' 
                    ? "पुडुचेरी, चेन्नई या किसी भी स्थान के बारे में पूछें..."
                    : selectedLanguage === 'ta'
                    ? "புதுச்சேரி, சென்னை அல்லது பயணத் திட்டம் பற்றி கேட்கவும்..."
                    : "Ask about Chennai, Pondicherry, or request an itinerary..."
                }
                disabled={isRefining}
                className="flex-1 px-4 py-2.5 rounded-2xl border border-white/80 bg-white/95 focus:bg-white focus:border-[#FCD34D] focus:ring-2 focus:ring-[#FCD34D]/30 text-xs sm:text-sm font-medium outline-none transition-all placeholder-slate-400 shadow-inner"
              />

              {/* Audio Read-Aloud Toggle Button */}
              <button
                type="button"
                onClick={() => setAudioReadAloud(prev => !prev)}
                className={`p-2.5 rounded-2xl border transition-all cursor-pointer hidden sm:flex items-center justify-center ${
                  audioReadAloud
                    ? 'bg-[#FCD34D]/25 border-[#FCD34D] text-slate-950 font-bold'
                    : 'bg-white hover:bg-slate-100 border-slate-200 text-slate-500'
                }`}
                title={audioReadAloud ? "Voice Read-Out: ON" : "Voice Read-Out: OFF"}
              >
                {audioReadAloud ? <Volume2 className="w-4 h-4 text-slate-900" /> : <VolumeX className="w-4 h-4 text-slate-400" />}
              </button>

              {/* Send Button */}
              <button
                type="submit"
                disabled={isRefining || !chatInputText.trim()}
                className="px-4 sm:px-5 py-2.5 rounded-2xl bg-terracotta hover:bg-terracotta/90 disabled:opacity-50 text-white text-xs sm:text-sm font-bold flex items-center gap-1.5 shadow-md transition-all shrink-0 cursor-pointer"
              >
                {isRefining ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                <span className="hidden sm:inline">Send</span>
              </button>
            </form>
          </div>
        </div>

        {/* =================================================================== */}
        {/* RIGHT PANEL: Generated Itinerary View                             */}
        {/* Displays on right side when itinerary exists; independent scroll   */}
        {/* =================================================================== */}
        {aiItinerary && (
          <div 
            className={`flex-1 h-full flex flex-col bg-slate-50/95 backdrop-blur-xl transition-all duration-300 overflow-hidden ${
              mobileTab === 'itinerary' ? 'flex' : 'hidden md:flex'
            }`}
          >
            {/* Itinerary Header Bar */}
            <div className="p-4 sm:p-5 bg-white/95 backdrop-blur-md border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shrink-0 shadow-xs">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="px-2.5 py-0.5 rounded-full bg-[#FCD34D]/25 border border-[#FCD34D]/50 text-slate-950 text-[10px] font-extrabold uppercase tracking-wider">
                    {aiItinerary.days?.length || 1} Days Route
                  </span>
                  <span className="px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 text-[10px] font-bold">
                    Est. Budget ₹{aiItinerary.total_estimated_budget_inr || 0}
                  </span>
                </div>
                <h2 className="text-base sm:text-lg font-black text-slate-900 tracking-tight mt-1 line-clamp-1">
                  {aiItinerary.itinerary_title || "Custom Coastal Itinerary"}
                </h2>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2 shrink-0">
                <button
                  onClick={() => {
                    setGlobalItinerary(aiItinerary);
                    if (setActiveTab) setActiveTab('map');
                  }}
                  className="px-3.5 py-2 rounded-xl bg-slate-950 hover:bg-slate-900 text-white text-xs font-bold flex items-center gap-1.5 shadow-sm transition-all cursor-pointer"
                  title="View Route & Sights on Interactive Map"
                >
                  <Compass className="w-3.5 h-3.5 text-[#FCD34D]" />
                  <span>View Map</span>
                </button>

                <button
                  onClick={handleAddAllToBasket}
                  className="px-3.5 py-2 rounded-xl bg-[#FCD34D] hover:bg-amber-400 text-slate-950 text-xs font-bold flex items-center gap-1.5 shadow-sm transition-all cursor-pointer"
                  title="Save all destinations to trip basket"
                >
                  <Luggage className="w-3.5 h-3.5" />
                  <span>Save to Basket</span>
                </button>
              </div>
            </div>

            {/* Itinerary Scrollable Content */}
            <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-5">
              
              {/* Multi-Alternative Itinerary Switcher Tabs */}
              {aiItinerary.alternatives && aiItinerary.alternatives.length > 0 && (
                <ItineraryAlternativesPicker
                  alternatives={aiItinerary.alternatives}
                  activeAlternativeId={activeAlternativeId}
                  onSelectAlternative={handleSelectAlternative}
                />
              )}

              {/* Summary note */}
              {aiItinerary.summary && (
                <div className="p-3.5 rounded-2xl bg-white/80 border border-slate-200 text-xs text-slate-700 leading-relaxed shadow-2xs">
                  <span className="font-bold text-slate-900">Summary: </span>
                  {aiItinerary.summary}
                </div>
              )}

              {/* Feasibility / Limitation Advisory Notice */}
              {aiItinerary.unavailability_notice && (
                <div className="p-3.5 rounded-2xl bg-amber-50 border border-amber-300 text-amber-950 text-xs space-y-1 shadow-2xs">
                  <div className="font-bold text-amber-900 uppercase tracking-wider text-[10px]">
                    ⚠️ Destination Advisory
                  </div>
                  <p className="leading-relaxed">{aiItinerary.unavailability_notice}</p>
                </div>
              )}

              {/* Day-by-Day Timeline */}
              <div className="space-y-5">
                {aiItinerary.days.map((day, dayIdx) => {
                  const isOptimizing = optimizingDay === dayIdx;
                  const slotKeys = Object.keys(day).filter(k => !['day_number', 'theme'].includes(k) && !!day[k]);
                  const orderWeights = { morning: 1, afternoon: 2, evening: 3 };
                  slotKeys.sort((a, b) => (orderWeights[a] || 4) - (orderWeights[b] || 4));

                  const isDraggingFromOtherDay = draggedCard && draggedCard.dayIdx !== dayIdx;

                  return (
                    <div 
                      key={day.day_number || dayIdx} 
                      className="bg-white rounded-3xl p-5 border border-slate-200 shadow-sm space-y-4 transition-all"
                    >
                      {/* Day Header */}
                      <div className="flex flex-wrap items-center justify-between gap-3 pb-2.5 border-b border-slate-100">
                        <div className="flex items-center gap-2">
                          <span className="w-6 h-6 rounded-full bg-slate-950 text-[#FCD34D] flex items-center justify-center text-xs font-black shrink-0">
                            {day.day_number || dayIdx + 1}
                          </span>
                          <h3 className="text-xs sm:text-sm font-extrabold text-slate-900 uppercase tracking-wider">
                            Day {day.day_number || dayIdx + 1}: {day.theme}
                          </h3>
                        </div>

                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleOptimizeDay(dayIdx)}
                            disabled={isOptimizing}
                            className="bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-800 px-3 py-1 rounded-xl text-xs font-bold shadow-2xs flex items-center gap-1 cursor-pointer transition-all disabled:opacity-50"
                          >
                            {isOptimizing ? (
                              <>
                                <Loader2 className="w-3 h-3 animate-spin" />
                                <span>Optimizing...</span>
                              </>
                            ) : (
                              <>
                                <Zap className="w-3 h-3 text-amber-700 fill-[#FCD34D]" />
                                <span>Optimize</span>
                              </>
                            )}
                          </button>

                          <button
                            onClick={() => handleAddSlotToDay(dayIdx)}
                            className="text-xs font-bold text-slate-600 hover:text-slate-950 flex items-center gap-1 cursor-pointer transition-colors"
                          >
                            <Plus className="w-3.5 h-3.5" />
                            <span>Add stop</span>
                          </button>
                        </div>
                      </div>

                      {/* Drop Indicator */}
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
                          className="border-2 border-dashed border-[#c2410c]/80 bg-[#c2410c]/5 rounded-2xl p-3 text-center text-xs font-bold text-[#c2410c] animate-fadeIn transition-all"
                        >
                          Drop here to move to Day {day.day_number || dayIdx + 1}
                        </div>
                      )}

                      {/* Vertical Stack of Stop Cards */}
                      <div className="space-y-2.5">
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
                              /* Inline Editing Form */
                              <div key={slotKey} className="bg-slate-50 rounded-2xl p-4 border border-slate-300 space-y-3 animate-fadeIn">
                                <div className="text-[11px] font-bold text-terracotta uppercase">
                                  Editing Stop
                                </div>
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                                  <div>
                                    <label className="text-[10px] font-bold text-slate-700 block mb-0.5">Place Name</label>
                                    <input
                                      type="text"
                                      value={editingSlotData.place_name}
                                      onChange={(e) => setEditingSlotData(prev => ({ ...prev, place_name: e.target.value }))}
                                      className="w-full px-3 py-1.5 rounded-xl border border-slate-200 text-xs text-slate-900 bg-white outline-none"
                                    />
                                  </div>
                                  <div>
                                    <label className="text-[10px] font-bold text-slate-700 block mb-0.5">Duration</label>
                                    <input
                                      type="text"
                                      value={editingSlotData.duration}
                                      onChange={(e) => setEditingSlotData(prev => ({ ...prev, duration: e.target.value }))}
                                      className="w-full px-3 py-1.5 rounded-xl border border-slate-200 text-xs text-slate-900 bg-white outline-none"
                                    />
                                  </div>
                                </div>
                                <div>
                                  <label className="text-[10px] font-bold text-slate-700 block mb-0.5">Notes</label>
                                  <textarea
                                    rows={2}
                                    value={editingSlotData.notes}
                                    onChange={(e) => setEditingSlotData(prev => ({ ...prev, notes: e.target.value }))}
                                    className="w-full px-3 py-1.5 rounded-xl border border-slate-200 text-xs text-slate-900 bg-white outline-none resize-none"
                                  />
                                </div>
                                <div className="flex items-center justify-between pt-1 border-t border-slate-200">
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
                                      className="px-3 py-1 rounded-xl border border-slate-200 text-xs font-bold text-slate-700 hover:bg-slate-100 cursor-pointer"
                                    >
                                      Cancel
                                    </button>
                                    <button
                                      type="button"
                                      onClick={() => handleSaveSlotChanges(dayIdx, slotKey)}
                                      className="px-3 py-1 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold cursor-pointer"
                                    >
                                      Save
                                    </button>
                                  </div>
                                </div>
                              </div>
                            );
                          }

                          return (
                            /* Stop Card */
                            <div
                              key={slotKey}
                              draggable
                              onDragStart={(e) => handleDragStart(e, dayIdx, slotKey, slot)}
                              onDragOver={(e) => handleDragOver(e, dayIdx, slotKey)}
                              onDrop={(e) => handleDrop(e, dayIdx, slotKey)}
                              className={`bg-slate-50 hover:bg-white rounded-2xl p-3.5 border transition-all flex items-start gap-3 group ${
                                isThisDragging 
                                   ? 'border-[#c2410c] shadow-md ring-2 ring-[#c2410c]/30' 
                                  : 'border-slate-200/80 hover:border-slate-300 shadow-2xs'
                              }`}
                            >
                              <div className="shrink-0 pt-0.5 cursor-grab active:cursor-grabbing text-slate-400 group-hover:text-slate-600">
                                <GripVertical className="w-4 h-4" />
                              </div>

                              <div className="flex-1 min-w-0">
                                <div className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                                  <span>{timeLabel} · {durationDisplay}</span>
                                </div>

                                <div className="font-extrabold text-slate-900 text-xs sm:text-sm mt-0.5">
                                  {slot.place_name || 'Destination'}
                                </div>

                                <p className="text-xs text-slate-600 mt-0.5 line-clamp-2 leading-relaxed">
                                  {slot.activity_note || 'Explore heritage, coastal scenery, and dining.'}
                                </p>
                              </div>

                              <div className="flex items-center gap-1 shrink-0">
                                <button
                                  type="button"
                                  onClick={() => {
                                    setEditingSlotData({
                                      dayIdx,
                                      slotKey,
                                      place_name: slot.place_name || '',
                                      duration: durationDisplay,
                                      notes: slot.activity_note || ''
                                    });
                                  }}
                                  className="p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200 transition-colors cursor-pointer"
                                  title="Edit stop"
                                >
                                  <Pencil className="w-3.5 h-3.5" />
                                </button>
                                <button
                                  type="button"
                                  onClick={() => {
                                    const targetDay = dayIdx === 0 ? 1 : 0;
                                    if (aiItinerary.days?.[targetDay]) {
                                      handleDropDirect(dayIdx, slotKey, targetDay, slotKey);
                                    }
                                  }}
                                  className="p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-200 transition-colors cursor-pointer"
                                  title="Move to other day"
                                >
                                  <MoreHorizontal className="w-3.5 h-3.5" />
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

              {/* Local Travel Tips & Etiquette */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                {aiItinerary.travel_tips && (
                  <div className="p-3.5 rounded-2xl bg-white border border-slate-200 text-xs space-y-1 shadow-2xs">
                    <span className="font-bold text-slate-900 uppercase tracking-wider text-[11px]">💡 Local Travel Tips:</span>
                    <ul className="list-disc list-inside space-y-0.5 text-slate-700 text-[11px]">
                      {aiItinerary.travel_tips.map((tip, idx) => (
                        <li key={idx}>{tip}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {aiItinerary.belief_and_etiquette_advisory && (
                  <div className="p-3.5 rounded-2xl bg-white border border-slate-200 text-xs space-y-1 shadow-2xs">
                    <span className="font-bold text-slate-900 uppercase tracking-wider text-[11px]">📜 Etiquette & Decorum:</span>
                    <p className="text-slate-700 leading-relaxed text-[11px] mt-0.5">
                      {aiItinerary.belief_and_etiquette_advisory}
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

      </div>

      {/* Place Details Modal */}
      {activeModalItem && (
        <PlaceModal
          place={activeModalItem.place}
          matchInfo={activeModalItem}
          onClose={() => setActiveModalItem(null)}
        />
      )}

      {/* Voyantra 2.0 Live Voice Full-Screen Modal */}
      <LiveVoiceModal
        isOpen={isLiveVoiceOpen}
        onClose={() => setIsLiveVoiceOpen(false)}
        language={selectedLanguage || 'en'}
        onSendMessage={(text, mode) => handleSendMessage(text, mode)}
        isProcessing={isRefining}
      />

      {/* Voyantra 2.0 Conversation History Drawer */}
      <ConversationHistoryDrawer
        isOpen={isHistoryDrawerOpen}
        onClose={() => setIsHistoryDrawerOpen(false)}
        activeConversationId={conversationId}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
      />

      {/* Voyantra 2.0 User Memory & Sensitive Preferences Modal */}
      <MemorySettingsModal
        isOpen={isMemoryModalOpen}
        onClose={() => setIsMemoryModalOpen(false)}
        onMemoryUpdated={(profile) => {
          if (profile?.preferred_language) {
            setSelectedLanguage(profile.preferred_language);
          }
        }}
      />
    </div>
  );
}

export default PlannerPage;
