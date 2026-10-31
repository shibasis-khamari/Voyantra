import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Volume2, VolumeX, Loader2, Square } from 'lucide-react';

/**
 * Push-to-Talk Voice Input Button with Web Speech API integration.
 * Supports en-IN, hi-IN, and ta-IN Indian speech recognition models.
 */
export function VoiceInputButton({
  language = 'en',
  onTranscriptReady,
  disabled = false,
  className = ''
}) {
  const [isListening, setIsListening] = useState(false);
  const [interimTranscript, setInterimTranscript] = useState('');
  const [speechSupported, setSpeechSupported] = useState(true);
  const recognitionRef = useRef(null);

  // Map app language code to BCP-47 SpeechRecognition tag
  const getRecognitionLang = (langCode) => {
    switch (langCode) {
      case 'hi': return 'hi-IN';
      case 'ta': return 'ta-IN';
      case 'en':
      default: return 'en-IN';
    }
  };

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setSpeechSupported(false);
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = getRecognitionLang(language);

      recognition.onstart = () => {
        setIsListening(true);
        setInterimTranscript('');
      };

      recognition.onresult = (event) => {
        let currentText = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          currentText += event.results[i][0].transcript;
        }
        setInterimTranscript(currentText);
      };

      recognition.onerror = (event) => {
        console.warn('[VoiceInput] Speech recognition notice:', event.error);
        setIsListening(false);
        setInterimTranscript('');
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
    } catch (e) {
      console.warn('[VoiceInput] Init failed:', e);
      setSpeechSupported(false);
    }

    return () => {
      if (recognitionRef.current) {
        try { recognitionRef.current.abort(); } catch (_) {}
      }
    };
  }, [language]);

  const toggleListening = () => {
    if (disabled) return;
    if (!speechSupported) {
      alert("Speech recognition is not supported in this browser. Please use Chrome, Edge, or Safari.");
      return;
    }

    if (isListening) {
      if (recognitionRef.current) {
        try { recognitionRef.current.stop(); } catch (_) {}
      }
      setIsListening(false);
      if (interimTranscript.trim() && onTranscriptReady) {
        onTranscriptReady(interimTranscript.trim());
      }
      setInterimTranscript('');
    } else {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.lang = getRecognitionLang(language);
          recognitionRef.current.start();
        } catch (e) {
          console.warn('[VoiceInput] Start error:', e);
        }
      }
    }
  };

  return (
    <div className={`relative flex items-center ${className}`}>
      {/* Listening Waveform / Floating Chip */}
      {isListening && (
        <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900/95 text-white text-[11px] font-bold shadow-xl border border-red-500/40 whitespace-nowrap animate-bounce z-50">
          <span className="w-2 h-2 rounded-full bg-red-500 animate-ping shrink-0" />
          <span>{interimTranscript || "Listening... Speak now"}</span>
        </div>
      )}

      <button
        type="button"
        onClick={toggleListening}
        disabled={disabled}
        title={isListening ? "Stop Recording (Click to send)" : "Push-to-Talk (Speech Input)"}
        className={`p-2.5 rounded-2xl border transition-all cursor-pointer flex items-center justify-center shrink-0 ${
          isListening
            ? 'bg-red-500 hover:bg-red-600 text-white border-red-400 ring-4 ring-red-400/30 animate-pulse'
            : 'bg-white hover:bg-slate-100 text-slate-700 hover:text-slate-950 border-slate-200 shadow-2xs'
        }`}
      >
        {isListening ? (
          <Square className="w-4 h-4 fill-white" />
        ) : (
          <Mic className="w-4 h-4 text-slate-600 hover:text-terracotta transition-colors" />
        )}
      </button>
    </div>
  );
}

/**
 * Text-to-speech helper to read out assistant messages aloud
 */
export function playTextToSpeech(text, language = 'en') {
  if (!('speechSynthesis' in window)) return;
  try {
    window.speechSynthesis.cancel(); // Stop any ongoing speech
    const utterance = new SpeechSynthesisUtterance(text);
    switch (language) {
      case 'hi':
        utterance.lang = 'hi-IN';
        break;
      case 'ta':
        utterance.lang = 'ta-IN';
        break;
      case 'en':
      default:
        utterance.lang = 'en-IN';
        break;
    }
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    window.speechSynthesis.speak(utterance);
  } catch (e) {
    console.warn('[TTS] playback notice:', e);
  }
}

export function stopTextToSpeech() {
  if ('speechSynthesis' in window) {
    try { window.speechSynthesis.cancel(); } catch (_) {}
  }
}
