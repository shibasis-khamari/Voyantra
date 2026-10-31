"""
Voyantra 2.0 Geographic Scope & Policy Service
Centralizes all destination-support rules across the application.
"""
from typing import Tuple, Dict, Any, Optional
import re

SUPPORTED_FULL_DESTINATIONS = {
    "pondicherry": {
        "slug": "pondicherry",
        "display_name": "Pondicherry",
        "aliases": ["pondy", "puducherry", "pondicherry", "white town"],
        "coordinates": {"lat": 11.9416, "lng": 79.8083},
        "has_local_catalog": True,
        "supports_itinerary": True
    },
    "chennai": {
        "slug": "chennai",
        "display_name": "Chennai",
        "aliases": ["chennai", "madras", "mylapore"],
        "coordinates": {"lat": 13.0827, "lng": 80.2707},
        "has_local_catalog": True,
        "supports_itinerary": True
    }
}

class DestinationService:
    def __init__(self):
        self.supported = SUPPORTED_FULL_DESTINATIONS

    def detect_destination(self, text: str, default: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
        """
        Detects destination from natural language query.
        Returns (city_slug, display_name).
        Can return 'both' for combined Pondicherry & Chennai queries.
        """
        t = (text or "").lower()
        has_pondy = any(re.search(rf"\b{re.escape(alias)}\b", t) for alias in self.supported["pondicherry"]["aliases"])
        has_chennai = any(re.search(rf"\b{re.escape(alias)}\b", t) for alias in self.supported["chennai"]["aliases"])

        if has_pondy and has_chennai:
            return "both", "Pondicherry & Chennai"
        if has_pondy:
            return "pondicherry", "Pondicherry"
        if has_chennai:
            return "chennai", "Chennai"

        if default:
            d = default.lower().strip()
            if d in ["both", "all", "any"]:
                return "both", "Pondicherry & Chennai"
            if d in self.supported:
                return self.supported[d]["slug"], self.supported[d]["display_name"]

        return None, None

    def supports_full_planning(self, city_slug: Optional[str]) -> bool:
        """Checks if city supports end-to-end local discovery & itinerary generation."""
        if not city_slug:
            return False
        slug = city_slug.lower()
        return slug in self.supported or slug in ["both", "all"]

    def get_unsupported_destination_message(self, requested_destination: str, lang: str = "en") -> str:
        """Polite and transparent limitation message for destinations outside Pondicherry & Chennai."""
        dest = requested_destination.title()
        if lang == "hi":
            return (
                f"मैं {dest} के इतिहास, संस्कृति और सामान्य जानकारी के बारे में खुशी से बता सकता हूँ। "
                f"हालाँकि, वोयंत्रा (Voyantra) का विस्तृत स्थानीय यात्रा-नियोजन (Itinerary Planning) और होटल व स्थल खोज "
                f"वर्तमान में केवल **पुडुचेरी (Pondicherry)** और **चेन्नई (Chennai)** के लिए उपलब्ध है। "
                f"क्या आप इन दोनों तटीय शहरों के लिए कोई योजना बनाना चाहेंगे?"
            )
        elif lang == "ta":
            return (
                f"{dest} பற்றிய பொதுவான தகவல்கள் மற்றும் வரலாற்றை என்னால் விளக்க முடியும். "
                f"ஆயினும், வாயாந்திராவின் (Voyantra) விரிவான உள்ளூர் பயணத் திட்டமிடல் மற்றும் இடங்கள் ஆய்வு "
                f"தற்போது **பாண்டிச்சேரி (Pondicherry)** மற்றும் **சென்னை (Chennai)** ஆகிய இடங்களுக்கு மட்டுமே கிடைக்கிறது. "
                f"இந்த நகரங்களுக்கான பயணத்திட்டத்தை உருவாக்க விரும்புகிறீர்களா?"
            )
        return (
            f"I can share general history, culture, and visitor insights about {dest}. "
            f"However, Voyantra's end-to-end local discovery, hotel recommendations, and personalized itinerary planning "
            f"are currently focused on **Pondicherry** and **Chennai**. "
            f"Would you like me to curate a personalized itinerary for Pondicherry, Chennai, or a combined coastal trip?"
        )

destination_service = DestinationService()
