"""
Voyantra 2.0 Multilingual Language Service
Supports English (en), Hindi (hi), and Tamil (ta) with automatic detection,
context continuity, and proper name preservation.
"""
from typing import Optional, Literal
import re

SupportedLanguage = Literal["en", "hi", "ta"]

SUPPORTED_LANGUAGES = {
    "en": {"code": "en", "name": "English", "native_name": "English", "bcp47": "en-IN"},
    "hi": {"code": "hi", "name": "Hindi", "native_name": "हिन्दी", "bcp47": "hi-IN"},
    "ta": {"code": "ta", "name": "Tamil", "native_name": "தமிழ்", "bcp47": "ta-IN"}
}

class LanguageService:
    def __init__(self):
        self.supported = SUPPORTED_LANGUAGES

    def detect_language(self, text: str, fallback: str = "en") -> str:
        """
        Detects whether input text is English, Hindi, or Tamil.
        Uses character script analysis (Devanagari / Tamil / Latin).
        """
        if not text or not text.strip():
            return fallback

        t = text.strip()

        # Count character frequencies by script
        devanagari_count = len(re.findall(r'[\u0900-\u097F]', t))
        tamil_count = len(re.findall(r'[\u0B80-\u0BFF]', t))
        latin_count = len(re.findall(r'[a-zA-Z]', t))

        total_script_chars = devanagari_count + tamil_count + latin_count

        if total_script_chars == 0:
            return fallback

        # If Tamil script represents more than 15% of script characters
        if tamil_count / total_script_chars > 0.15:
            return "ta"

        # If Devanagari script represents more than 15% of script characters
        if devanagari_count / total_script_chars > 0.15:
            return "hi"

        # Fallback to Latin / English
        return "en"

    def normalize_language_code(self, lang_input: Optional[str], default: str = "en") -> str:
        """Ensures language is strictly one of 'en', 'hi', or 'ta'."""
        if not lang_input:
            return default
        code = lang_input.strip().lower()
        if code in ["hi", "hindi", "hin"]:
            return "hi"
        if code in ["ta", "tamil", "tam"]:
            return "ta"
        if code in ["en", "english", "eng"]:
            return "en"
        return default

    def get_system_language_instruction(self, lang: str) -> str:
        """Prompt instruction directing the model to answer in the detected or selected language."""
        if lang == "hi":
            return (
                "भाषा निर्देश: उपयोगकर्ता से हिन्दी (Devanagari script) में स्वाभाविक और विनम्र रूप से बात करें। "
                "स्थानों, होटलों और प्रसिद्ध आकर्षणों के मूल अंग्रेजी/स्थानीय नाम भी साथ में स्पष्ट रखें ताकि नेविगेशन आसान रहे।"
            )
        elif lang == "ta":
            return (
                "மொழி வழிகாட்டுதல்: பயனருடன் தமிழில் (Tamil script) இயல்பாகவும் மரியாதையுடனும் உரையாடவும். "
                "இடங்கள், ஹோட்டல்கள் மற்றும் சுற்றுலா தலங்களின் பெயர்களை எளிதாக அடையாளம் காணும் வகையில் ஆங்கிலம்/உள்ளூர் வடிவிலும் குறிப்பிடவும்."
            )
        return (
            "LANGUAGE INSTRUCTION: Respond in natural, warm, and sophisticated English. "
            "Keep place and destination names clear and recognizable."
        )

language_service = LanguageService()
