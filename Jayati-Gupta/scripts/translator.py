import os
import uuid
import csv
import time
import requests
from dotenv import load_dotenv
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()

translator_key = os.getenv("TRANSLATOR_KEY")
translator_region = os.getenv("TRANSLATOR_REGION")

if not translator_key or not translator_region:
    raise ValueError("Translator API key or region missing in .env")

endpoint = "https://api.cognitive.microsofttranslator.com/"
path = "/translate?api-version=3.0"

input_csv = "transcripts/transcripts.csv"
output_csv = "transcripts/translations.csv"

# Languages to translate into
target_languages = ["hi", "fr", "es", "de"]  # Hindi, French, Spanish, German

# --- Replace with a transcript from Milestone 1 ---
input_text = "Welcome everyone, this is a sample commentary for our AI translation demo."

def translate_text(text, languages):
    params = "&".join([f"to={lang}" for lang in languages])
    url = endpoint + path + "&" + params

    headers = {
        "Ocp-Apim-Subscription-Key": translator_key,
        "Ocp-Apim-Subscription-Region": translator_region,
        "Content-Type": "application/json",
        "X-ClientTraceId": str(uuid.uuid4())
    }

    body = [{"text": text}]
    
    # Track latency
    start = time.time()
    response = requests.post(url, headers=headers, json=body)
    latency = time.time() - start

    response.raise_for_status()  # Will throw error if request fails
    return response.json(), latency


# Run Translation
with open(input_csv, "r", encoding="utf-8") as infile, \
     open(output_csv, "w", encoding="utf-8", newline="") as outfile:

    reader = csv.DictReader(infile)
    fieldnames = ["filename", "original_text"] + [f"{lang}_translation" for lang in target_languages] + ["latency"]
    writer = csv.DictWriter(outfile, fieldnames=fieldnames)
    writer.writeheader()

    for row in reader:
        text = row["transcript"]

        # Skip blank lines
        if not text.strip():
            continue

        result, latency = translate_text(text, target_languages)

        output_row = {
            "filename": row["filename"],
            "original_text": text,
            "latency": round(latency, 3)
        }

        # Extract translations
        for item in result[0]["translations"]:
            output_row[f"{item['to']}_translation"] = item["text"]

        writer.writerow(output_row)

print("\nTranslation completed! Check:", output_csv)