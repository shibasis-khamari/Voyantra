import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Volume2, X, Sparkles, AlertCircle, RefreshCw } from 'lucide-react';
import { playTextToSpeech, stopTextToSpeech } from './VoiceInputButton';

export function LiveVoiceModal({
  isOpen,
  onClose,
  language = 'en',
  onSendMessage,
  isProcessing = false
}) {
  const [sessionState, setSessionState] = useState('idle'); // 'idle' | 'listening' | 'thinking' | 'speaking'
  const [currentTranscript, setCurrentTranscript] = useState('');
  const [latestAssistantText, setLatestAssistantText] = useState('');
  const [errorNotice, setErrorNotice] = useState(null);

  const recognitionRef = useRef(null);
  const isSpeakingRef = useRef(false);

  const getLangCode = (l) => {
    if (l === 'hi') return 'hi-IN';
    if (l === 'ta') return 'ta-IN';
    return 'en-IN';
  };

  // Start continuous listening loop
  const startListening = () => {
    stopTextToSpeech();
    isSpeakingRef.current = false;
    setSessionState('listening');
    setErrorNotice(null);

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setErrorNotice("Speech recognition is not supported in this browser.");
      setSessionState('idle');
      return;
    }

    try {
      if (recognitionRef.current) {
        try { recognitionRef.current.abort(); } catch (_) {}
      }

      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = getLangCode(language);

      recognition.onstart = () => {
        setSessionState('listening');
      };

      recognition.onresult = (event) => {
        // If assistant was speaking, any user voice interrupts immediately
        if (isSpeakingRef.current) {
          stopTextToSpeech();
          isSpeakingRef.current = false;
        }

        let fullText = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          fullText += event.results[i][0].transcript;
        }

        if (fullText.trim()) {
          setCurrentTranscript(fullText);
        }
      };

      recognition.onerror = (e) => {
        console.warn('[LiveVoice] speech error:', e.error);
        if (e.error === 'not-allowed') {
          setErrorNotice("Microphone access denied. Please allow microphone permissions.");
        }
      };

      recognition.onend = () => {
        // Restart if still in live voice mode and not thinking
        if (sessionState === 'listening') {
          try { recognition.start(); } catch (_) {}
        }
      };

      recognition.start();
      recognitionRef.current = recognition;
    } catch (err) {
      console.warn('[LiveVoice] init failed:', err);
      setErrorNotice(err.message);
    }
  };

  const stopListening = () => {
    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch (_) {}
    }
  };

  // When live session opens
  useEffect(() => {
    if (isOpen) {
      startListening();
    } else {
      stopListening();
      stopTextToSpeech();
      isSpeakingRef.current = false;
      setSessionState('idle');
    }
    return () => {
      stopListening();
      stopTextToSpeech();
      isSpeakingRef.current = false;
    };
  }, [isOpen]);

  // Handle user completing an utterance
  const handleSendLiveUtterance = async () => {
    const text = currentTranscript.trim();
    if (!text || sessionState === 'thinking') return;

    stopListening();
    setSessionState('thinking');
    setCurrentTranscript('');

    try {
      const response = await onSendMessage(text, 'live_voice');
      if (response && response.reply_message) {
        setLatestAssistantText(response.reply_message);
        setSessionState('speaking');
        isSpeakingRef.current = true;

        // Speak aloud
        playTextToSpeech(response.reply_message, language);

        // Resume listening automatically when speech ends
        const estimatedDurationMs = Math.min(Math.max(response.reply_message.length * 60, 2000), 12000);
        setTimeout(() => {
          if (isOpen && sessionState !== 'thinking') {
            isSpeakingRef.current = false;
            startListening();
          }
        }, estimatedDurationMs);
      } else {
        startListening();
      }
    } catch (e) {
      setErrorNotice(e.message);
      startListening();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-2xl animate-fadeIn">
      {/* Container */}
      <div className="relative w-full max-w-lg bg-slate-900/90 border border-white/20 rounded-3xl p-6 sm:p-8 text-white shadow-2xl flex flex-col items-center text-center space-y-6">
        
        {/* Close / Exit Button */}
        <button
          onClick={() => {
            stopListening();
            stopTextToSpeech();
            onClose();
          }}
          className="absolute top-4 right-4 p-2 rounded-full bg-white/10 hover:bg-white/20 text-slate-300 hover:text-white transition-colors cursor-pointer"
          title="Exit Live Voice Mode"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Top Header Badge */}
        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-[#FCD34D]/20 border border-[#FCD34D]/40 text-[#FCD34D] text-xs font-bold uppercase tracking-wider">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Live Conversation Mode</span>
        </div>

        {/* State Headline */}
        <div>
          <h2 className="text-xl sm:text-2xl font-black tracking-tight">
            {sessionState === 'listening' && "I'm listening..."}
            {sessionState === 'thinking' && "Analyzing travel request..."}
            {sessionState === 'speaking' && "Voyantra Concierge speaking"}
            {sessionState === 'idle' && "Connecting..."}
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Hands-free two-way voice • Speak naturally in English, Hindi, or Tamil
          </p>
        </div>

        {/* Dynamic Voice Visualizer Orb */}
        <div className="relative flex items-center justify-center my-4">
          {/* Outer Pulsing Rings */}
          <div className={`absolute w-44 h-44 rounded-full transition-all duration-700 ${
            sessionState === 'listening' ? 'bg-emerald-500/20 animate-ping' :
            sessionState === 'thinking' ? 'bg-[#FCD34D]/20 animate-pulse' :
            sessionState === 'speaking' ? 'bg-terracotta/30 animate-pulse' :
            'bg-white/5'
          }`} />

          <div className={`absolute w-36 h-36 rounded-full transition-all duration-500 ${
            sessionState === 'listening' ? 'bg-emerald-500/30' :
            sessionState === 'thinking' ? 'bg-[#FCD34D]/30' :
            sessionState === 'speaking' ? 'bg-terracotta/40' :
            'bg-white/10'
          }`} />

          {/* Center Core Button */}
          <div className={`relative w-28 h-28 rounded-full flex items-center justify-center shadow-2xl transition-all ${
            sessionState === 'listening' ? 'bg-emerald-500 ring-8 ring-emerald-500/40 shadow-emerald-500/50' :
            sessionState === 'thinking' ? 'bg-amber-500 ring-8 ring-amber-500/40 shadow-amber-500/50' :
            sessionState === 'speaking' ? 'bg-terracotta ring-8 ring-terracotta/40 shadow-terracotta/50' :
            'bg-slate-800'
          }`}>
            {sessionState === 'speaking' ? (
              <Volume2 className="w-12 h-12 text-white animate-bounce" />
            ) : sessionState === 'thinking' ? (
              <RefreshCw className="w-10 h-10 text-white animate-spin" />
            ) : (
              <Mic className="w-12 h-12 text-white" />
            )}
          </div>
        </div>

        {/* Live Subtitles & Captions */}
        <div className="w-full min-h-[70px] max-h-[110px] overflow-y-auto px-4 py-3 rounded-2xl bg-white/5 border border-white/10 text-xs sm:text-sm text-slate-200">
          {currentTranscript ? (
            <p className="italic text-emerald-300 font-medium">"{currentTranscript}"</p>
          ) : latestAssistantText ? (
            <p className="text-slate-300 line-clamp-3 leading-relaxed">{latestAssistantText}</p>
          ) : (
            <p className="text-slate-500 italic">Say "Plan a 2-day beach trip" or ask any travel question...</p>
          )}
        </div>

        {/* Error message */}
        {errorNotice && (
          <div className="flex items-center gap-2 text-rose-400 text-xs bg-rose-500/10 px-3 py-1.5 rounded-xl border border-rose-500/20">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorNotice}</span>
          </div>
        )}

        {/* Controls Bar */}
        <div className="flex items-center gap-3 w-full justify-center">
          {sessionState === 'listening' && currentTranscript.trim() && (
            <button
              onClick={handleSendLiveUtterance}
              className="px-5 py-2.5 rounded-2xl bg-[#FCD34D] hover:bg-amber-300 text-slate-950 text-xs font-bold transition-all cursor-pointer shadow-lg"
            >
              Send Request →
            </button>
          )}

          {sessionState === 'speaking' && (
            <button
              onClick={() => {
                stopTextToSpeech();
                isSpeakingRef.current = false;
                startListening();
              }}
              className="px-4 py-2 rounded-2xl bg-white/20 hover:bg-white/30 text-white text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5"
            >
              <Mic className="w-3.5 h-3.5" />
              <span>Tap to Interrupt</span>
            </button>
          )}

          <button
            onClick={() => {
              stopListening();
              stopTextToSpeech();
              onClose();
            }}
            className="px-4 py-2 rounded-2xl bg-white/10 hover:bg-white/15 text-slate-300 hover:text-white text-xs font-semibold border border-white/20 transition-all cursor-pointer"
          >
            Switch to Text
          </button>
        </div>
      </div>
    </div>
  );
}
