"""
Language Configuration for Speech-to-Speech Pipeline
Supports 15+ languages with Azure Speech and Translator codes
"""

# Language mappings: Azure Speech-to-Text language codes
SPEECH_LANGUAGES = {
    "en": "en-US",      # English (US)
    "es": "es-ES",      # Spanish (Spain)
    "fr": "fr-FR",      # French (France)
    "de": "de-DE",      # German
    "it": "it-IT",      # Italian
    "pt": "pt-BR",      # Portuguese (Brazil)
    "ru": "ru-RU",      # Russian
    "ja": "ja-JP",      # Japanese
    "ko": "ko-KR",      # Korean
    "zh": "zh-CN",      # Chinese (Simplified)
    "hi": "hi-IN",      # Hindi
    "te": "te-IN",      # Telugu
    "ta": "ta-IN",      # Tamil
    "ar": "ar-SA",      # Arabic
    "nl": "nl-NL",      # Dutch
    "pl": "pl-PL",      # Polish
    "tr": "tr-TR",      # Turkish
    "sv": "sv-SE",      # Swedish
    "th": "th-TH",      # Thai
    "vi": "vi-VN",      # Vietnamese
}

# Language names for display
LANGUAGE_NAMES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "ja": "Japanese",
    "ko": "Korean",
    "zh": "Chinese",
    "hi": "Hindi",
    "te": "Telugu",
    "ta": "Tamil",
    "ar": "Arabic",
    "nl": "Dutch",
    "pl": "Polish",
    "tr": "Turkish",
    "sv": "Swedish",
    "th": "Thai",
    "vi": "Vietnamese",
}

# Azure TTS Voice mappings (Neural voices)
TTS_VOICES = {
    "en": "en-US-JennyNeural",
    "es": "es-ES-ElviraNeural",
    "fr": "fr-FR-DeniseNeural",
    "de": "de-DE-KatjaNeural",
    "it": "it-IT-ElsaNeural",
    "pt": "pt-BR-FranciscaNeural",
    "ru": "ru-RU-SvetlanaNeural",
    "ja": "ja-JP-NanamiNeural",
    "ko": "ko-KR-SunHiNeural",
    "zh": "zh-CN-XiaoxiaoNeural",
    "hi": "hi-IN-SwaraNeural",
    "te": "te-IN-MohanNeural",
    "ta": "ta-IN-PallaviNeural",
    "ar": "ar-SA-ZariyahNeural",
    "nl": "nl-NL-FennaNeural",
    "pl": "pl-PL-AgnieszkaNeural",
    "tr": "tr-TR-EmelNeural",
    "sv": "sv-SE-SofieNeural",
    "th": "th-TH-PremwadeeNeural",
    "vi": "vi-VN-HoaiMyNeural",
}

# Default target languages (can be customized)
DEFAULT_TARGET_LANGUAGES = ["hi", "te", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh", "ar", "nl", "pl", "tr"]

# Supported languages list (for UI dropdowns)
SUPPORTED_LANGUAGES = list(LANGUAGE_NAMES.keys())

def get_speech_language_code(lang_code: str) -> str:
    """Get Azure Speech language code from 2-letter code."""
    return SPEECH_LANGUAGES.get(lang_code, "en-US")

def get_language_name(lang_code: str) -> str:
    """Get language display name from 2-letter code."""
    return LANGUAGE_NAMES.get(lang_code, "Unknown")

def get_tts_voice(lang_code: str) -> str:
    """Get Azure TTS voice name from 2-letter code."""
    return TTS_VOICES.get(lang_code, "en-US-JennyNeural")

def get_all_languages() -> dict:
    """Get all language information."""
    return {
        code: {
            "name": LANGUAGE_NAMES[code],
            "speech_code": SPEECH_LANGUAGES[code],
            "tts_voice": TTS_VOICES[code]
        }
        for code in SUPPORTED_LANGUAGES
    }

