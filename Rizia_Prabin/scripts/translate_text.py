import requests
import uuid
import json
import csv
import os

# ------------------------------------------
# CONFIGURATION SECTION
# ------------------------------------------
# Replace with your Azure Translator details
key = "3eJE0mhTu0Fc02Nj2Eq1jc5AhpDwDudAAtkmP9M9CoetoZQQQAbqJQQJ99BJACGhslBXJ3w3AAAbACOGDW0R"
endpoint = "https://api.cognitive.microsofttranslator.com/"
location = "centralindia"  # Your resource location (e.g., "centralindia")

# --- M1 INTEGRATION ---
# This automatically finds your 'transcripts.csv' file
# It assumes 'scripts' and 'transcripts' are in the same parent folder (Rizia_Prabin)
try:
    # Gets the path to the 'scripts' folder, then goes up one level
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    stt_output_file = os.path.join(base_dir, 'transcripts', 'transcripts.csv')
except NameError:
    # Fallback if __file__ is not defined (e.g., in some interactive shells)
    stt_output_file = r"C:\Users\HP\Desktop\Speech_to_speech_TeamA\Rizia_Prabin\transcripts\transcripts.csv" # <-- Change this path if needed

# ------------------------------------------
# TRANSLATION FUNCTION (This is your "module" - unchanged)
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
# EXECUTION (This is the new "Integration" part)
# ------------------------------------------
print(f"--- Starting Full Integration ---")
print(f"Reading STT Output from: {stt_output_file}\n")

try:
    with open(stt_output_file, mode='r', encoding='utf-8') as f:
        # Use DictReader to read the CSV by its column names
        reader = csv.DictReader(f)
        
        for row in reader:
            original_text = row['transcript']
            original_lang = row['language']
            
            # Skip any empty rows from the CSV
            if not original_text:
                continue

            print("==================================================")
            print(f"Original Text ({original_lang}): {original_text}")
            
            # Intelligently set the target languages
            if original_lang == 'hi':
                # If original is Hindi, translate to English, French, etc.
                target_languages = ['en', 'fr', 'es', 'de']
            else:
                # If original is English, translate to Hindi, French, etc.
                target_languages = ['hi', 'fr', 'es', 'de']

            # Call your translation module
            result = translate_text(original_text, target_languages)
            
            print("\nTranslated Outputs:")
            for i, lang in enumerate(target_languages):
                translated_text = result[0]['translations'][i]['text']
                print(f"   {lang.upper()}: {translated_text}")
            print("==================================================\n")

except FileNotFoundError:
    print(f"ERROR: Could not find transcripts file at {stt_output_file}")
    print("Please make sure you have run Milestone 1 and the transcripts.csv file exists.")
except Exception as e:
    print(f"Error during translation: {e}")