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
from ...core.dependencies import get_current_user, get_user_id

router = APIRouter(prefix="/chat", tags=["Voyantra 2.0 Conversational AI"])

def _conversation_owner(conversation_id: str) -> Optional[str]:
    """Returns the owning user_id of a conversation, or None if it doesn't exist / no DB."""
    col = db_manager.get_collection("conversations")
    if col is None:
        return None
    doc = col.find_one({"id": conversation_id}, {"user_id": 1})
    return doc.get("user_id") if doc else None


def _require_owned_conversation(conversation_id: str, user_id: str) -> None:
    """404 (not 403) when missing or owned by someone else, so ids can't be probed."""
    col = db_manager.get_collection("conversations")
    if col is None:
        return
    if _conversation_owner(conversation_id) != user_id:
        raise HTTPException(status_code=404, detail="Conversation not found")


@router.post("/message", response_model=ChatTurnResponse)
def handle_chat_message(req: ChatTurnRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Processes a conversational user message across English, Hindi, or Tamil."""
    uid = get_user_id(current_user)
    if req.conversation_id:
        owner = _conversation_owner(req.conversation_id)
        if owner is not None and owner != uid:
            raise HTTPException(status_code=404, detail="Conversation not found")
    return orchestrator.process_turn(req, user_id=uid)

@router.get("/conversations", response_model=List[ConversationSummary])
def list_conversations(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Lists saved conversation sessions for the signed-in user."""
    user_id = get_user_id(current_user)
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
def get_conversation(conversation_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Loads all turns from a previous conversation owned by the signed-in user."""
    _require_owned_conversation(conversation_id, get_user_id(current_user))
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
def delete_conversation(conversation_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """Deletes a conversation (and its messages) owned by the signed-in user."""
    _require_owned_conversation(conversation_id, get_user_id(current_user))
    conv_col = db_manager.get_collection("conversations")
    msg_col = db_manager.get_collection("messages")
    if conv_col is not None:
        conv_col.delete_one({"id": conversation_id})
    if msg_col is not None:
        msg_col.delete_many({"conversation_id": conversation_id})
    return {"status": "success", "message": f"Conversation {conversation_id} deleted"}

@router.get("/memory", response_model=UserMemoryProfile)
def get_memory(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Retrieves the signed-in user's memory profile with consented preferences."""
    return memory_service.get_user_memory(get_user_id(current_user))

@router.put("/memory", response_model=UserMemoryProfile)
def update_memory(updates: Dict[str, Any], current_user: Dict[str, Any] = Depends(get_current_user)):
    """Updates the signed-in user's memory profile with strict opt-in consent enforcement."""
    return memory_service.update_user_memory(get_user_id(current_user), updates)

@router.delete("/memory")
def clear_memory(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Permanently clears all remembered preferences for the signed-in user."""
    success = memory_service.clear_user_memory(get_user_id(current_user))
    return {"status": "success", "cleared": success}

@router.post("/transcribe")
async def transcribe_speech(
    file: Optional[UploadFile] = File(None),
    language: Optional[str] = Form("en"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Fallback speech-to-text audio transcription endpoint."""
    audio_data = await file.read() if file else b""
    return voice_service.transcribe_audio(audio_data, file.filename if file else "audio.wav", language)

@router.post("/synthesize")
def synthesize_speech(
    text: str = Query(..., min_length=1),
    language: str = Query("en"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Produces speech synthesis metadata for playback."""
    return voice_service.synthesize_speech(text, language)
