
import os
import csv
import time
import requests
import uuid
from dotenv import load_dotenv

load_dotenv()  # load .env from current working dir 


INPUT_CSV = "C:/Users/linga/OneDrive/Desktop/speech_project/transcripts/transcripts.csv"
OUTPUT_CSV = "C:/Users/linga/OneDrive/Desktop/speech_project/transcripts/transcripts_translated.csv"

TRANSLATOR_KEY = os.getenv("TRANSLATOR_KEY", "YOUR_TRANSLATOR_KEY")
TRANSLATOR_REGION = os.getenv("TRANSLATOR_REGION", "")
TRANSLATOR_ENDPOINT = os.getenv("TRANSLATOR_ENDPOINT", "https://api.cognitive.microsofttranslator.com")

# Languages you want the transcripts translated into
TARGET_LANGS = ["hi", "fr", "es", "de"]  # Hindi, French, Spanish, German
# ----------------------------

if TRANSLATOR_KEY == "YOUR_TRANSLATOR_KEY" or not TRANSLATOR_KEY:
    raise SystemExit("Please set TRANSLATOR_KEY in your .env file")

# Construct base URL and parameters
PATH = "/translate?api-version=3.0"
PARAMS = "&".join([f"to={lang}" for lang in TARGET_LANGS])
URL = TRANSLATOR_ENDPOINT.rstrip("/") + PATH + "&" + PARAMS

HEADERS = {
    "Ocp-Apim-Subscription-Key": TRANSLATOR_KEY,
    "Content-type": "application/json",
    "X-ClientTraceId": str(uuid.uuid4())
}
# Include region header if provided (required for some resource types)
if TRANSLATOR_REGION:
    HEADERS["Ocp-Apim-Subscription-Region"] = TRANSLATOR_REGION

def translate_text(text):
    """Send one request to translate `text` into TARGET_LANGS.
       Returns a list of translated strings in the same order as TARGET_LANGS.
    """
    if not text:
        return [""] * len(TARGET_LANGS)
    body = [{"Text": text}]  # Azure accepts 'Text' key
    try:
        resp = requests.post(URL, headers=HEADERS, json=body, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        # data is a list where data[0]['translations'] is list of translations in the same order
        translations = data[0].get("translations", [])
        # safe-extract texts in order
        out = []
        for i, lang in enumerate(TARGET_LANGS):
            if i < len(translations):
                out.append(translations[i].get("text", ""))
            else:
                out.append("")
        return out
    except requests.RequestException as e:
        # For transient failures, caller can decide to retry
        raise

def main():
    if not os.path.exists(INPUT_CSV):
        print(f"Input CSV not found: {INPUT_CSV}")
        return

    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)

    with open(INPUT_CSV, newline="", encoding="utf-8") as inf, \
         open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as outf:

        reader = csv.DictReader(inf)
        # Build header: existing fields plus language columns
        fieldnames = reader.fieldnames[:] if reader.fieldnames else ["filename", "language", "transcript"]
        for lang in TARGET_LANGS:
            fieldnames.append(f"translated_{lang}")
        writer = csv.DictWriter(outf, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            fname = row.get("filename", "")
            transcript = row.get("transcript", "") or ""
            print(f"Translating {fname}...")

            # Retry logic for transient errors
            for attempt in range(3):
                try:
                    translated_texts = translate_text(transcript)
                    break
                except Exception as e:
                    print(f"  attempt {attempt+1} failed: {e}")
                    time.sleep(1 + attempt*2)
                    translated_texts = [""] * len(TARGET_LANGS)
            # attach translations to row
            for lang, ttext in zip(TARGET_LANGS, translated_texts):
                row[f"translated_{lang}"] = ttext
            writer.writerow(row)
            
            time.sleep(0.1)

    print("Done. Translated CSV written to:", OUTPUT_CSV)

if __name__ == "__main__":
    main()
