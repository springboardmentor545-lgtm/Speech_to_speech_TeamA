import requests
import uuid
import json
import csv
import os
from dotenv import load_dotenv

# ------------------------------------------
# LOAD ENVIRONMENT VARIABLES
# ------------------------------------------
load_dotenv()
key = os.getenv("TRANSLATION_KEY")
location = os.getenv("TRANSLATION_REGION")
endpoint = "https://api.cognitive.microsofttranslator.com/"

# ------------------------------------------
# AUTOMATICALLY FIND transcripts.csv
# ------------------------------------------
try:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    stt_output_file = os.path.join(base_dir, 'transcripts', 'transcripts.csv')
except NameError:
    stt_output_file = r"C:\Users\HP\Documents\SPEECH_TO_SPEECH_TEAMA\transcripts\transcripts.csv"

translated_output_file = os.path.join(base_dir, 'transcripts', 'translated_output.csv')

# ------------------------------------------
# TRANSLATION FUNCTION
# ------------------------------------------
def translate_text(text, target_langs):
    path = '/translate?api-version=3.0'
    params = '&'.join([f"to={lang}" for lang in target_langs])
    constructed_url = endpoint + path + "&" + params

    headers = {
        'Ocp-Apim-Subscription-Key': key,
        'Ocp-Apim-Subscription-Region': location,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }

    body = [{'text': text}]
    response = requests.post(constructed_url, headers=headers, json=body)
    response.raise_for_status()
    return response.json()

# ------------------------------------------
# MAIN EXECUTION
# ------------------------------------------
print(f"--- Starting Translation Integration ---")
print(f"Reading STT Output from: {stt_output_file}\n")

try:
    with open(stt_output_file, mode='r', encoding='utf-8') as f_in, \
         open(translated_output_file, mode='w', encoding='utf-8', newline='') as f_out:

        reader = csv.DictReader(f_in)
        fieldnames = ['original_language', 'original_text', 'target_language', 'translated_text']
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            original_text = row.get('transcript', '').strip()
            original_lang = row.get('language', '').strip()

            if not original_text:
                continue

            print("==================================================")
            print(f"Original Text ({original_lang}): {original_text}")

            if original_lang == 'hi':
                target_languages = ['en', 'fr', 'es', 'de']
            else:
                target_languages = ['hi', 'fr', 'es', 'de']

            result = translate_text(original_text, target_languages)

            print("\nTranslated Outputs:")
            for i, lang in enumerate(target_languages):
                translated_text = result[0]['translations'][i]['text']
                print(f"   {lang.upper()}: {translated_text}")
                writer.writerow({
                    'original_language': original_lang,
                    'original_text': original_text,
                    'target_language': lang,
                    'translated_text': translated_text
                })
            print("==================================================\n")

    print(f"\n✅ Translation Completed! Output saved to:\n{translated_output_file}")

except FileNotFoundError:
    print(f"❌ ERROR: transcripts.csv not found at {stt_output_file}")
    print("Please make sure you have run Milestone 1 and that the file exists.")
except Exception as e:
    print(f"⚠️ Error during translation: {e}")
