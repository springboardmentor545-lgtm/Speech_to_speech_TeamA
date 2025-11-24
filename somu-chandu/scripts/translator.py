"""
Milestone 2: Translation Module
Azure Translator integration for translating STT transcripts
"""

import os
import json
import time
from typing import List, Dict, Optional
from dotenv import load_dotenv
import requests

try:
    from language_config import DEFAULT_TARGET_LANGUAGES
except ImportError:
    DEFAULT_TARGET_LANGUAGES = ["hi", "te", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh", "ar", "nl", "pl", "tr"]

load_dotenv()

TRANSLATOR_KEY = os.getenv("AZURE_TRANSLATOR_KEY")
TRANSLATOR_REGION = os.getenv("AZURE_TRANSLATOR_REGION") or os.getenv("AZURE_REGION")
TRANSLATOR_ENDPOINT = "https://api.cognitive.microsofttranslator.com"

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "translations")


def translate_text(
    text: str,
    target_languages: List[str] = None,
    source_language: Optional[str] = None
) -> Dict[str, any]:
    if target_languages is None:
        target_languages = DEFAULT_TARGET_LANGUAGES
    """
    Translate text to one or multiple target languages using Azure Translator.
    
    Args:
        text: Input text to translate
        target_languages: List of target language codes (e.g., ["hi", "te", "es"])
        source_language: Source language code (auto-detect if None)
    
    Returns:
        Dictionary with translations and metadata:
        {
            "original_text": str,
            "source_language": str,
            "translations": {
                "hi": "translated text",
                "te": "translated text"
            },
            "timestamp": str,
            "success": bool,
            "error": Optional[str]
        }
    """
    if not TRANSLATOR_KEY or not TRANSLATOR_REGION:
        return {
            "original_text": text,
            "source_language": None,
            "translations": {},
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "success": False,
            "error": "Missing Azure Translator credentials. Add AZURE_TRANSLATOR_KEY and AZURE_TRANSLATOR_REGION to .env"
        }
    
    if not text or not text.strip():
        return {
            "original_text": text,
            "source_language": None,
            "translations": {},
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "success": False,
            "error": "Empty text provided"
        }
    
    try:
        # Prepare API request
        endpoint = f"{TRANSLATOR_ENDPOINT}/translate"
        params = {
            "api-version": "3.0",
            "to": target_languages
        }
        
        if source_language:
            params["from"] = source_language
        
        headers = {
            "Ocp-Apim-Subscription-Key": TRANSLATOR_KEY,
            "Ocp-Apim-Subscription-Region": TRANSLATOR_REGION,
            "Content-Type": "application/json"
        }
        
        body = [{"text": text}]
        
        # Make API call
        response = requests.post(endpoint, params=params, headers=headers, json=body, timeout=10)
        response.raise_for_status()
        
        result = response.json()[0]
        
        # Extract translations
        translations = {}
        detected_language = result.get("detectedLanguage", {}).get("language", source_language or "unknown")
        
        for translation in result.get("translations", []):
            lang = translation.get("to")
            translated_text = translation.get("text", "")
            translations[lang] = translated_text
        
        return {
            "original_text": text,
            "source_language": detected_language,
            "translations": translations,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "success": True,
            "error": None
        }
    
    except requests.exceptions.RequestException as e:
        return {
            "original_text": text,
            "source_language": None,
            "translations": {},
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "success": False,
            "error": f"API request failed: {str(e)}"
        }
    except Exception as e:
        return {
            "original_text": text,
            "source_language": None,
            "translations": {},
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "success": False,
            "error": f"Translation error: {str(e)}"
        }


def translate_with_retry(
    text: str,
    target_languages: List[str] = None,
    source_language: Optional[str] = None,
    max_retries: int = 3,
    retry_delay: float = 1.0
) -> Dict[str, any]:
    if target_languages is None:
        target_languages = DEFAULT_TARGET_LANGUAGES
    """
    Translate text with retry logic for handling transient failures.
    
    Args:
        text: Input text to translate
        target_languages: List of target language codes
        source_language: Source language code (auto-detect if None)
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
    
    Returns:
        Translation result dictionary
    """
    for attempt in range(max_retries):
        result = translate_text(text, target_languages, source_language)
        
        if result["success"]:
            return result
        
        if attempt < max_retries - 1:
            time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
            print(f"⚠️ Retry attempt {attempt + 2}/{max_retries}...")
    
    return result


def save_translation(translation_result: Dict[str, any], transcript_id: Optional[str] = None) -> str:
    """
    Save translation result to JSON file.
    
    Args:
        translation_result: Result dictionary from translate_text()
        transcript_id: Optional ID to include in filename
    
    Returns:
        Path to saved file
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    if transcript_id:
        filename = f"translation_{transcript_id}.json"
    else:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"translation_{timestamp}.json"
    
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(translation_result, f, ensure_ascii=False, indent=2)
    
    return filepath


def test_translator():
    """Test function to verify Azure Translator setup."""
    print("🧪 Testing Azure Translator...")
    print("=" * 50)
    
    test_text = "Hello, how are you today?"
    print(f"📝 Test text: {test_text}\n")
    
    result = translate_text(test_text, target_languages=["hi", "te", "es"])
    
    if result["success"]:
        print(f"✅ Translation successful!")
        print(f"🌐 Source language: {result['source_language']}")
        print(f"📅 Timestamp: {result['timestamp']}\n")
        print("🌍 Translations:")
        for lang, translated in result["translations"].items():
            print(f"   {lang}: {translated}")
    else:
        print(f"❌ Translation failed: {result['error']}")
    
    return result


if __name__ == "__main__":
    test_translator()

