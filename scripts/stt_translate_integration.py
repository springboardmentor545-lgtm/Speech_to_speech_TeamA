"""
Milestone 2: STT + Translation Integration
Feeds STT transcripts into the translation module
"""

import os
import csv
import json
from datetime import datetime
from dotenv import load_dotenv
from translator import translate_with_retry, save_translation

try:
    from language_config import DEFAULT_TARGET_LANGUAGES
except ImportError:
    DEFAULT_TARGET_LANGUAGES = ["hi", "te", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh", "ar", "nl", "pl", "tr"]

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
TRANSCRIPTS_DIR = os.path.join(BASE_DIR, "transcripts")
TRANSLATIONS_DIR = os.path.join(BASE_DIR, "translations")
OUTPUT_CSV = os.path.join(TRANSLATIONS_DIR, "translated_transcripts.csv")


def translate_transcripts_from_csv(
    input_csv: str = None,
    target_languages: list = None
):
    if target_languages is None:
        target_languages = DEFAULT_TARGET_LANGUAGES
    """
    Read transcripts from CSV and translate them.
    
    Args:
        input_csv: Path to input CSV file (defaults to transcripts/transcripts.csv)
        target_languages: List of target language codes
    """
    if input_csv is None:
        input_csv = os.path.join(TRANSCRIPTS_DIR, "transcripts.csv")
    
    if not os.path.exists(input_csv):
        print(f"❌ Input file not found: {input_csv}")
        return
    
    print("🔄 STT + TRANSLATION INTEGRATION")
    print("=" * 50)
    print(f"📂 Reading transcripts from: {input_csv}")
    print(f"🌍 Target languages: {', '.join(target_languages)}\n")
    
    os.makedirs(TRANSLATIONS_DIR, exist_ok=True)
    
    translated_rows = []
    
    # Read transcripts
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    if not rows:
        print("❌ No transcripts found in CSV file.")
        return
    
    # Translate each transcript
    for idx, row in enumerate(rows, 1):
        transcript = row.get("transcript", "").strip()
        filename = row.get("filename", f"transcript_{idx}")
        source_lang = row.get("language", "en-US")
        
        if not transcript or transcript.startswith("[") and transcript.endswith("]"):
            print(f"⏭️  Skipping {filename}: {transcript}")
            continue
        
        print(f"\n[{idx}/{len(rows)}] Translating: {filename}")
        print(f"   Original: {transcript[:80]}...")
        
        # Convert language code format (en-US -> en)
        source_lang_code = source_lang.split("-")[0] if "-" in source_lang else source_lang
        
        # Translate
        result = translate_with_retry(
            transcript,
            target_languages=target_languages,
            source_language=source_lang_code
        )
        
        if result["success"]:
            # Save individual translation JSON
            translation_file = save_translation(result, transcript_id=f"{filename}_{idx}")
            print(f"   ✅ Saved: {os.path.basename(translation_file)}")
            
            # Prepare CSV row
            csv_row = {
                "filename": filename,
                "source_language": source_lang,
                "original_text": transcript,
                "detected_language": result["source_language"],
                "timestamp": result["timestamp"]
            }
            
            # Add translations
            for lang in target_languages:
                csv_row[f"translation_{lang}"] = result["translations"].get(lang, "")
            
            translated_rows.append(csv_row)
            
            # Print sample translations
            for lang in target_languages[:2]:  # Show first 2
                if lang in result["translations"]:
                    trans_text = result["translations"][lang]
                    print(f"   🌐 {lang}: {trans_text[:60]}...")
        else:
            print(f"   ❌ Failed: {result['error']}")
            csv_row = {
                "filename": filename,
                "source_language": source_lang,
                "original_text": transcript,
                "detected_language": "",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "error": result["error"]
            }
            for lang in target_languages:
                csv_row[f"translation_{lang}"] = ""
            translated_rows.append(csv_row)
    
    # Save combined CSV
    if translated_rows:
        fieldnames = ["filename", "source_language", "original_text", "detected_language", "timestamp"]
        for lang in target_languages:
            fieldnames.append(f"translation_{lang}")
        if any("error" in row for row in translated_rows):
            fieldnames.append("error")
        
        with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(translated_rows)
        
        print(f"\n💾 All translations saved to: {OUTPUT_CSV}")
        print(f"📊 Total transcripts translated: {len([r for r in translated_rows if 'error' not in r or not r.get('error')])}/{len(translated_rows)}")
    else:
        print("\n❌ No translations to save.")


def translate_single_transcript(text: str, target_languages: list = None):
    if target_languages is None:
        target_languages = DEFAULT_TARGET_LANGUAGES
    """
    Translate a single transcript text (useful for real-time pipeline).
    
    Args:
        text: Text to translate
        target_languages: List of target language codes
    
    Returns:
        Translation result dictionary
    """
    return translate_with_retry(text, target_languages=target_languages)


if __name__ == "__main__":
    translate_transcripts_from_csv()

