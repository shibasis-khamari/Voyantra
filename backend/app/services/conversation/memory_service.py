"""
Voyantra 2.0 Optional Long-Term Memory Service
Stores consented user preferences in MongoDB collection 'user_preferences'.
Enforces strict consent boundaries and privacy safeguards:
- Sensitive preferences (e.g., religious/cultural observances) require explicit opt-in.
- Never infers sensitive traits from user identity, name, or location.
- Provides complete user controls to view, edit, disable, or delete preferences.
"""
from typing import Dict, Any, Optional
from datetime import datetime
from ...core.database import db_manager
from ...schemas.chat import UserMemoryProfile

class MemoryService:
    def __init__(self):
        self._memory_cache: Dict[str, Dict[str, Any]] = {}

    def get_user_memory(self, user_id: str) -> UserMemoryProfile:
        """Retrieves user memory profile, with fallback defaults."""
        col = db_manager.get_collection("user_preferences")
        if col is not None:
            doc = col.find_one({"user_id": user_id})
            if doc:
                doc.pop("_id", None)
                doc.pop("user_id", None)
                return UserMemoryProfile(**doc)

        cached = self._memory_cache.get(user_id)
        if cached:
            return UserMemoryProfile(**cached)

        # Default profile
        return UserMemoryProfile()

    def update_user_memory(self, user_id: str, updates: Dict[str, Any]) -> UserMemoryProfile:
        """Updates user memory profile with strict consent validation."""
        current = self.get_user_memory(user_id).model_dump()
        
        # Guard sensitive preferences against unsolicited persistence
        if "sensitive_cultural_preferences" in updates:
            # Requires explicit opt-in flag
            if not updates.get("sensitive_cultural_opt_in") and not current.get("sensitive_cultural_opt_in"):
                updates.pop("sensitive_cultural_preferences", None)

        current.update(updates)
        current["updated_at"] = datetime.now().isoformat()
        if not current.get("created_at"):
            current["created_at"] = current["updated_at"]

        col = db_manager.get_collection("user_preferences")
        if col is not None:
            col.update_one(
                {"user_id": user_id},
                {"$set": {"user_id": user_id, **current}},
                upsert=True
            )
        else:
            self._memory_cache[user_id] = current

        return UserMemoryProfile(**current)

    def clear_user_memory(self, user_id: str) -> bool:
        """Permanently clears all saved long-term preferences for the user."""
        col = db_manager.get_collection("user_preferences")
        if col is not None:
            col.delete_one({"user_id": user_id})
        self._memory_cache.pop(user_id, None)
        return True

    def set_memory_enabled(self, user_id: str, enabled: bool) -> UserMemoryProfile:
        """Toggles long-term memory active state."""
        return self.update_user_memory(user_id, {"is_memory_enabled": enabled})

memory_service = MemoryService()
