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

# Azure TTS Voice mappings (Neural voices) grouped by gender for easy switching
# Voice names are common Azure voices; update if your region uses different names.
TTS_VOICES = {
    "en": {"female": "en-US-JennyNeural", "male": "en-US-GuyNeural"},
    "es": {"female": "es-ES-ElviraNeural", "male": "es-ES-AlvaroNeural"},
    "fr": {"female": "fr-FR-DeniseNeural", "male": "fr-FR-HenriNeural"},
    "de": {"female": "de-DE-KatjaNeural", "male": "de-DE-ConradNeural"},
    "it": {"female": "it-IT-ElsaNeural", "male": "it-IT-DiegoNeural"},
    "pt": {"female": "pt-BR-FranciscaNeural", "male": "pt-BR-AntonioNeural"},
    "ru": {"female": "ru-RU-SvetlanaNeural", "male": "ru-RU-DmitryNeural"},
    "ja": {"female": "ja-JP-NanamiNeural", "male": "ja-JP-KeitaNeural"},
    "ko": {"female": "ko-KR-SunHiNeural", "male": "ko-KR-InJoonNeural"},
    "zh": {"female": "zh-CN-XiaoxiaoNeural", "male": "zh-CN-YunyangNeural"},
    "hi": {"female": "hi-IN-SwaraNeural", "male": "hi-IN-MadhurNeural"},
    "te": {"female": "te-IN-ShrutiNeural", "male": "te-IN-MohanNeural"},
    "ta": {"female": "ta-IN-PallaviNeural", "male": "ta-IN-ValluvarNeural"},
    "ar": {"female": "ar-SA-ZariyahNeural", "male": "ar-SA-HamedNeural"},
    "nl": {"female": "nl-NL-FennaNeural", "male": "nl-NL-MaartenNeural"},
    "pl": {"female": "pl-PL-AgnieszkaNeural", "male": "pl-PL-MarekNeural"},
    "tr": {"female": "tr-TR-EmelNeural", "male": "tr-TR-AhmetNeural"},
    "sv": {"female": "sv-SE-SofieNeural", "male": "sv-SE-MattiasNeural"},
    "th": {"female": "th-TH-PremwadeeNeural", "male": "th-TH-NiwatNeural"},
    "vi": {"female": "vi-VN-HoaiMyNeural", "male": "vi-VN-NamMinhNeural"},
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

def get_tts_voice(lang_code: str, gender: str = "female") -> str:
    """Get Azure TTS voice name from 2-letter code and preferred gender."""
    voices = TTS_VOICES.get(lang_code)
    if isinstance(voices, dict):
        # try requested gender, then fallback to the other, then English female
        return voices.get(gender) or voices.get("female") or voices.get("male") or "en-US-JennyNeural"
    # backward compatibility if mapping is ever a string
    return voices or "en-US-JennyNeural"

def get_all_languages() -> dict:
    """Get all language information."""
    return {
        code: {
            "name": LANGUAGE_NAMES[code],
            "speech_code": SPEECH_LANGUAGES[code],
            "tts_voice": get_tts_voice(code),
            "tts_voice_male": get_tts_voice(code, "male"),
            "tts_voice_female": get_tts_voice(code, "female"),
        }
        for code in SUPPORTED_LANGUAGES
    }
