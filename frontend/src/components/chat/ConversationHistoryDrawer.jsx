import React, { useState, useEffect } from 'react';
import { History, X, Plus, Trash2, MessageSquare, Clock, Globe } from 'lucide-react';
import { VoyantraAPI } from '../../services/api';

export function ConversationHistoryDrawer({
  isOpen,
  onClose,
  activeConversationId,
  onSelectConversation,
  onNewConversation
}) {
  const [conversations, setConversations] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [deletingId, setDeletingId] = useState(null);

  const loadConversations = async () => {
    setIsLoading(true);
    try {
      const data = await VoyantraAPI.getConversations();
      setConversations(data || []);
    } catch (e) {
      console.warn("Failed to load conversation history:", e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadConversations();
    }
  }, [isOpen]);

  const handleDelete = async (e, convId) => {
    e.stopPropagation();
    if (!window.confirm("Are you sure you want to delete this chat history?")) return;
    setDeletingId(convId);
    try {
      await VoyantraAPI.deleteConversation(convId);
      setConversations(prev => prev.filter(c => c.id !== convId));
      if (activeConversationId === convId) {
        onNewConversation();
      }
    } catch (e) {
      alert("Failed to delete conversation: " + e.message);
    } finally {
      setDeletingId(null);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/60 backdrop-blur-xs animate-fadeIn">
      {/* Backdrop click to close */}
      <div className="flex-1" onClick={onClose} />

      {/* Drawer content */}
      <div className="w-full max-w-sm sm:max-w-md bg-slate-900 border-l border-white/10 text-white h-full flex flex-col shadow-2xl animate-slideLeft">
        
        {/* Header */}
        <div className="p-4 sm:p-5 border-b border-white/10 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-white/10 flex items-center justify-center">
              <History className="w-4 h-4 text-[#FCD34D]" />
            </div>
            <div>
              <h3 className="font-extrabold text-sm text-white">Chat History</h3>
              <p className="text-[10px] text-slate-400">Past itineraries & conversations</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-full hover:bg-white/10 text-slate-400 hover:text-white transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* New Chat Button */}
        <div className="p-4 border-b border-white/10">
          <button
            onClick={() => {
              onNewConversation();
              onClose();
            }}
            className="w-full py-2.5 px-4 rounded-2xl bg-[#FCD34D] hover:bg-amber-300 text-slate-950 text-xs font-bold flex items-center justify-center gap-2 transition-all cursor-pointer shadow-md"
          >
            <Plus className="w-4 h-4" />
            <span>Start New Conversation</span>
          </button>
        </div>

        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {isLoading ? (
            <div className="text-center py-10 text-xs text-slate-400">
              Loading saved chats...
            </div>
          ) : conversations.length === 0 ? (
            <div className="text-center py-12 px-4 space-y-2 text-slate-400">
              <MessageSquare className="w-8 h-8 mx-auto text-slate-600 stroke-[1.5]" />
              <p className="text-xs font-medium">No previous conversations found.</p>
              <p className="text-[11px] text-slate-500">Your chats with Voyantra AI Concierge will appear here automatically.</p>
            </div>
          ) : (
            conversations.map((conv) => {
              const isActive = activeConversationId === conv.id;
              return (
                <div
                  key={conv.id}
                  onClick={() => {
                    onSelectConversation(conv.id);
                    onClose();
                  }}
                  className={`group p-3.5 rounded-2xl border transition-all cursor-pointer flex items-start justify-between gap-3 ${
                    isActive
                      ? 'bg-white/15 border-[#FCD34D]/60 shadow-md ring-1 ring-[#FCD34D]/30'
                      : 'bg-white/5 hover:bg-white/10 border-white/10'
                  }`}
                >
                  <div className="flex-1 min-w-0 space-y-1">
                    <div className="flex items-center gap-1.5">
                      <span className="text-[9px] uppercase px-1.5 py-0.5 rounded bg-white/10 text-slate-300 font-bold">
                        {conv.language || 'en'}
                      </span>
                      <h4 className="font-bold text-xs text-slate-200 group-hover:text-white truncate">
                        {conv.title || "Travel Plan"}
                      </h4>
                    </div>

                    <div className="flex items-center gap-2 text-[10px] text-slate-400">
                      <Clock className="w-3 h-3" />
                      <span>{conv.updated_at ? new Date(conv.updated_at).toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : 'Recent'}</span>
                    </div>
                  </div>

                  <button
                    onClick={(e) => handleDelete(e, conv.id)}
                    disabled={deletingId === conv.id}
                    className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-white/10 transition-colors cursor-pointer shrink-0 opacity-80 group-hover:opacity-100"
                    title="Delete Conversation"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
