"""
Voyantra 2.0 Short-Term Context & Reference Resolution Service
Resolves pronouns ("it", "that place", "the hotel you mentioned") across conversation turns.
"""
from typing import List, Dict, Any, Optional
import re

class ContextService:
    def resolve_references(
        self,
        current_message: str,
        recent_messages: List[Dict[str, Any]],
        recent_places: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyzes current message for pronouns and contextual references,
        resolving them against recent conversation history.
        """
        msg_clean = (current_message or "").strip()
        msg_lower = msg_clean.lower()
        
        resolved_entity = None
        has_pronoun_reference = False

        # Pronoun patterns
        pronoun_triggers = [
            r"\bis it\b", r"\babout it\b", r"\bto it\b", r"\bthat place\b", 
            r"\bthe beach\b", r"\bthat beach\b", r"\bthe temple\b", r"\bthat temple\b",
            r"\bthe hotel\b", r"\bthat hotel\b", r"\bthe second one\b", r"\bthe first one\b",
            r"\badd it\b", r"\bremove it\b", r"\bvisit it\b"
        ]

        for pattern in pronoun_triggers:
            if re.search(pattern, msg_lower):
                has_pronoun_reference = True
                break

        # If a pronoun reference exists, search previous turns for named places
        if has_pronoun_reference and recent_messages:
            # Check most recent assistant messages for place names
            for m in reversed(recent_messages[-4:]):
                content = m.get("content", "")
                # Find quoted or bolded names in assistant message
                bold_matches = re.findall(r'\*\*([^*]+)\*\*', content)
                if bold_matches:
                    resolved_entity = bold_matches[0]
                    break

        if not resolved_entity and recent_places and len(recent_places) > 0 and has_pronoun_reference:
            resolved_entity = recent_places[0]

        return {
            "has_reference": has_pronoun_reference,
            "resolved_entity": resolved_entity,
            "augmented_query": f"{msg_clean} (Referring to: {resolved_entity})" if resolved_entity else msg_clean
        }

context_service = ContextService()
