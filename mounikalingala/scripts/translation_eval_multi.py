import os
import csv
import uuid
import time
import requests
import json
import sacrebleu
from dotenv import load_dotenv


# LOAD ENVIRONMENT VARIABLES

load_dotenv()

TRANSLATOR_KEY = os.getenv("TRANSLATOR_KEY")
TRANSLATOR_REGION = os.getenv("TRANSLATOR_REGION")
TRANSLATOR_ENDPOINT = os.getenv("TRANSLATOR_ENDPOINT", "https://api.cognitive.microsofttranslator.com")

# Input and output files
INPUT_CSV = "C:/Users/linga/OneDrive/Desktop/speech_project/transcripts/transcripts.csv"
OUTPUT_CSV = "C:/Users/linga/OneDrive/Desktop/speech_project/transcripts/translation_eval_multi.csv"

# Target languages — edit or add your choices
TARGET_LANGS = [ "fr", "es", "de", "te"]  #  French, Spanish, German, Telugu



# TRANSLATE FUNCTION (handles multiple languages)

def translate_text(text, target_langs):
    path = "/translate?api-version=3.0"
    params = "&".join([f"to={lang}" for lang in target_langs])
    url = TRANSLATOR_ENDPOINT.rstrip("/") + path + "&" + params

    headers = {
        "Ocp-Apim-Subscription-Key": TRANSLATOR_KEY,
        "Ocp-Apim-Subscription-Region": TRANSLATOR_REGION,
        "Content-type": "application/json",
        "X-ClientTraceId": str(uuid.uuid4())
    }

    body = [{"Text": text}]

    start_time = time.time()
    response = requests.post(url, headers=headers, json=body)
    response.raise_for_status()
    elapsed = time.time() - start_time

    data = response.json()
    translations = {t["to"]: t["text"] for t in data[0]["translations"]}
    return translations, elapsed



# MAIN EVALUATION LOGIC

if __name__ == "__main__":
    if not os.path.exists(INPUT_CSV):
        print(f"❌ Input file not found: {INPUT_CSV}")
        exit()

    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)

    with open(INPUT_CSV, newline='', encoding='utf-8') as infile, \
         open(OUTPUT_CSV, mode='w', newline='', encoding='utf-8') as outfile:

        reader = csv.DictReader(infile)
        fieldnames = ["filename", "original_text", "translation_time(s)"]
        for lang in TARGET_LANGS:
            fieldnames.append(f"{lang}_translation")
            fieldnames.append(f"{lang}_BLEU")

        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            original = row["transcript"]
            fname = row["filename"]

            if not original.strip():
                continue

            try:
                translations, elapsed = translate_text(original, TARGET_LANGS)
                row_data = {
                    "filename": fname,
                    "original_text": original,
                    "translation_time(s)": f"{elapsed:.2f}"
                }

                for lang in TARGET_LANGS:
                    translated_text = translations.get(lang, "")
                    bleu = sacrebleu.sentence_bleu(translated_text, [original]).score
                    row_data[f"{lang}_translation"] = translated_text
                    row_data[f"{lang}_BLEU"] = f"{bleu:.2f}"

                writer.writerow(row_data)

                print(f"{fname} | Time: {elapsed:.2f}s")

            except Exception as e:
                print(f"Error translating {fname}:", e)
                continue

    print("\n✅ Multi-language translation evaluation complete!")
    print(f"Results saved to: {OUTPUT_CSV}")
