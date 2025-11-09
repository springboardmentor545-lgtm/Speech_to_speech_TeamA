# Path to your Milestone 1 transcript
import requests
import uuid
import json
import csv
import os
import time

# ------------------------------------------
# CONFIGURATION
# ------------------------------------------
key = "3eJE0mhTu0Fc02Nj2Eq1jc5AhpDwDudAAtkmP9M9CoetoZQQQAbqJQQJ99BJACGhslBXJ3w3AAAbACOGDW0R"
endpoint = "https://api.cognitive.microsofttranslator.com/"
location = "centralindia"

# Path to your Milestone 1 transcripts.csv
CSV_PATH = "/Users/shrehithasureddy/Documents/Shrehitha/transcripts/transcripts.csv"

# Path to save your translated output
OUTPUT_PATH = "/Users/shrehithasureddy/Documents/Shrehitha/transcripts/translations.csv"

# Target languages for translation
target_languages = ["hi", "fr", "es", "de"]  # Hindi, French, Spanish, German


# ------------------------------------------
# TRANSLATION FUNCTION
# ------------------------------------------
def translate_text(text, target_langs):
    path = "/translate?api-version=3.0"
    params = "&".join([f"to={lang}" for lang in target_langs])
    constructed_url = endpoint + path + "&" + params

    headers = {
        "Ocp-Apim-Subscription-Key": key,
        "Ocp-Apim-Subscription-Region": location,
        "Content-type": "application/json",
        "X-ClientTraceId": str(uuid.uuid4()),
    }

    body = [{"text": text}]
    response = requests.post(constructed_url, headers=headers, json=body)
    response.raise_for_status()
    return response.json()[0]["translations"]


# ------------------------------------------
# EXECUTION
# ------------------------------------------
if not os.path.exists(CSV_PATH):
    print("Transcript file not found!")
    exit()

# Read all rows from transcripts.csv
with open(CSV_PATH, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# Prepare output CSV
with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as outcsv:
    fieldnames = ["filename", "language", "original_text"] + target_languages
    writer = csv.DictWriter(outcsv, fieldnames=fieldnames)
    writer.writeheader()

    # Process each transcript
    for row in rows:
        filename = row["filename"]
        text = row["transcript"]
        lang = row["language"]

        if not text.strip():
            continue

        print(f"\nTranslating {filename} ({lang}) ...")

        try:
            translations = translate_text(text, target_languages)

            row_data = {"filename": filename, "language": lang, "original_text": text}

            for tr in translations:
                row_data[tr["to"]] = tr["text"]

            writer.writerow(row_data)
            print(f"✅ Done: {filename}")
            time.sleep(1)  # Prevents rate limit errors

        except Exception as e:
            print(f"⚠️ Error translating {filename}: {e}")

print(f"\n🎉 All translations saved to: {OUTPUT_PATH}")
