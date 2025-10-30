import os
import csv
import azure.cognitiveservices.speech as speechsdk

# --- Your paths are correct ---
SPEECH_KEY = "7bZ4X8wi4V25K3tR7LoXkUVYgMt9J5WOwRIRn0isIVhV9F23kY4cJQQJ99BJACGhslBXJ3w3AAAYACOGQx9V"
SERVICE_REGION = "centralindia"
INPUT_DIR = r"C:\Users\HP\Desktop\RIZIA_PRABIN\samples"
OUTPUT_CSV = r"C:\Users\HP\Desktop\RIZIA_PRABIN\transcripts\transcripts.csv"

# --- Config is fine ---
speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SERVICE_REGION)

# --- THIS FUNCTION IS NOW FIXED ---
# It now accepts a 'lang_code'
def transcribe_file(file_path, lang_code):
    
    # This maps your simple "hi" or "en" to the full Azure code
    if lang_code == "hi":
        azure_lang_code = "hi-IN"
    else:
        azure_lang_code = "en-US"

    audio_input = speechsdk.AudioConfig(filename=file_path)
    
    # --- THIS IS THE CRITICAL FIX ---
    # We now tell the recognizer WHAT LANGUAGE to listen for
    recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config, 
        language=azure_lang_code,  # <-- This line fixes everything
        audio_config=audio_input
    )
    
    result = recognizer.recognize_once_async().get()
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return result.text
    else:
        return None

# --- This part is fine ---
os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)

with open(OUTPUT_CSV, mode='w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["filename", "language", "transcript"])
    
    for fname in sorted(os.listdir(INPUT_DIR)):
        if not fname.lower().endswith(".wav"):
            continue
        
        # This logic is correct and matches your files
        lang = "en" if fname.startswith("en_") else ("hi" if fname.startswith("hi_") else "unknown")
        
        # Skip any file it doesn't recognize
        if lang == "unknown":
            continue
            
        path = os.path.join(INPUT_DIR, fname)
        
        # This print message is new, so you can see it's working
        print(f"Transcribing {fname} as language: {lang}") 
        
        # --- THIS IS THE OTHER HALF OF THE FIX ---
        # We now pass the 'lang' variable into the function
        text = transcribe_file(path, lang) 
        
        writer.writerow([fname, lang, text or ""])
        print("->", text)

print("\nDone! Check your transcripts.csv file.")