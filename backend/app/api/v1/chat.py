"""
Voyantra 2.0 Unified Conversation & Voice Router
Endpoints:
- POST /api/v1/chat/message (Unified turn handler)
- GET  /api/v1/chat/conversations (List user chats)
- GET  /api/v1/chat/conversations/{id} (Load chat turns)
- DELETE /api/v1/chat/conversations/{id} (Delete chat)
- GET  /api/v1/chat/memory (Get consented memory)
- PUT  /api/v1/chat/memory (Update consented memory)
- DELETE /api/v1/chat/memory (Clear memory)
- POST /api/v1/chat/transcribe (Speech-to-text fallback)
- POST /api/v1/chat/synthesize (Text-to-speech fallback)
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Query
from typing import List, Optional, Dict, Any

from ...schemas.chat import (
    ChatTurnRequest, ChatTurnResponse, ConversationSummary,
    ChatMessage, UserMemoryProfile
)
from ...services.conversation.orchestrator import orchestrator
from ...services.conversation.memory_service import memory_service
from ...services.conversation.voice_service import voice_service
from ...core.database import db_manager

router = APIRouter(prefix="/chat", tags=["Voyantra 2.0 Conversational AI"])

@router.post("/message", response_model=ChatTurnResponse)
def handle_chat_message(req: ChatTurnRequest):
    """Processes a conversational user message across English, Hindi, or Tamil."""
    return orchestrator.process_turn(req, user_id="demo_user")

@router.get("/conversations", response_model=List[ConversationSummary])
def list_conversations(user_id: Optional[str] = "demo_user"):
    """Lists saved conversation sessions for the user."""
    col = db_manager.get_collection("conversations")
    results = []
    if col is not None:
        docs = list(col.find({"user_id": user_id}).sort("updated_at", -1).limit(20))
        for d in docs:
            results.append(ConversationSummary(
                id=d.get("id"),
                title=d.get("title", "Conversation"),
                created_at=d.get("created_at", ""),
                updated_at=d.get("updated_at", ""),
                preview=d.get("title", ""),
                language=d.get("language", "en")
            ))
    return results

@router.get("/conversations/{conversation_id}")
def get_conversation(conversation_id: str):
    """Loads all turns from a previous conversation."""
    col = db_manager.get_collection("messages")
    turns = []
    if col is not None:
        docs = list(col.find({"conversation_id": conversation_id}).sort("timestamp", 1))
        for d in docs:
            turns.append({
                "id": str(d.get("_id", "")),
                "role": d.get("role"),
                "content": d.get("content"),
                "language": d.get("language", "en"),
                "timestamp": d.get("timestamp")
            })
    return {"conversation_id": conversation_id, "messages": turns}

@router.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: str):
    """Deletes a conversation and its messages."""
    conv_col = db_manager.get_collection("conversations")
    msg_col = db_manager.get_collection("messages")
    if conv_col is not None:
        conv_col.delete_one({"id": conversation_id})
    if msg_col is not None:
        msg_col.delete_many({"conversation_id": conversation_id})
    return {"status": "success", "message": f"Conversation {conversation_id} deleted"}

@router.get("/memory", response_model=UserMemoryProfile)
def get_memory(user_id: Optional[str] = "demo_user"):
    """Retrieves user memory profile with consented preferences."""
    return memory_service.get_user_memory(user_id)

@router.put("/memory", response_model=UserMemoryProfile)
def update_memory(updates: Dict[str, Any], user_id: Optional[str] = "demo_user"):
    """Updates user memory profile with strict opt-in consent enforcement."""
    return memory_service.update_user_memory(user_id, updates)

@router.delete("/memory")
def clear_memory(user_id: Optional[str] = "demo_user"):
    """Permanently clears all remembered preferences for the user."""
    success = memory_service.clear_user_memory(user_id)
    return {"status": "success", "cleared": success}

@router.post("/transcribe")
async def transcribe_speech(
    file: Optional[UploadFile] = File(None),
    language: Optional[str] = Form("en")
):
    """Fallback speech-to-text audio transcription endpoint."""
    audio_data = await file.read() if file else b""
    return voice_service.transcribe_audio(audio_data, file.filename if file else "audio.wav", language)

@router.post("/synthesize")
def synthesize_speech(
    text: str = Query(..., min_length=1),
    language: str = Query("en")
):
    """Produces speech synthesis metadata for playback."""
    return voice_service.synthesize_speech(text, language)
