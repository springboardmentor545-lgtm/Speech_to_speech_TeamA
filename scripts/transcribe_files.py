import os
import csv
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("🚀 FIXED AZURE SPEECH-TO-TEXT")
print("=" * 50)

# Configuration from environment variables
BASE_DIR = os.getenv('BASE_DIR', r"C:\Users\csomu\Desktop\Speech_to_speech_TeamA\somu-chandu")
INPUT_DIR = os.path.join(BASE_DIR, os.getenv('INPUT_DIR', 'speech_samples'))
OUTPUT_DIR = os.path.join(BASE_DIR, os.getenv('OUTPUT_DIR', 'transcripts'))
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "transcripts.csv")

# Azure credentials from environment variables
SPEECH_KEY = os.getenv('SPEECH_KEY')
SERVICE_REGION = os.getenv('SERVICE_REGION', 'centralindia')

if not SPEECH_KEY:
    raise ValueError("❌ SPEECH_KEY not found in environment variables")

# ... rest of your existing functions remain the same ...
def transcribe_file(file_path, language="en-US"):
    try:
        print(f"🎯 Processing: {os.path.basename(file_path)}")
        
        # Configure speech recognition
        speech_config = speechsdk.SpeechConfig(
            subscription=SPEECH_KEY, 
            region=SERVICE_REGION
        )
        speech_config.speech_recognition_language = language
        
        # Create audio config
        audio_config = speechsdk.audio.AudioConfig(filename=file_path)
        
        # Create recognizer
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config, 
            audio_config=audio_config
        )
        
        print(f"   🔊 Sending to Azure ({language})...")
        result = recognizer.recognize_once_async().get()
        
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            print("   ✅ Transcription successful!")
            return result.text
        elif result.reason == speechsdk.ResultReason.NoMatch:
            print("   ❌ No speech could be recognized")
            return "[No speech detected]"
        else:
            print("   ❌ Recognition failed")
            return "[Recognition failed]"
            
    except Exception as e:
        print(f"   💥 Error: {str(e)}")
        return f"[Error: {str(e)}]"

def get_language_info(filename):
    """
    Determine language based on filename prefix
    Returns: (language_code, language_name)
    """
    if filename.startswith('te_'):
        return "te-IN", "Telugu"
    elif filename.startswith('hi_'):
        return "hi-IN", "Hindi"
    else:
        return "en-US", "English"

def main():
    # Create directories if they don't exist
    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Check for WAV files
    if not os.path.exists(INPUT_DIR):
        print(f"❌ Directory doesn't exist: {INPUT_DIR}")
        return
        
    wav_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith('.wav')]
    
    if not wav_files:
        print("❌ No WAV files found in speech_samples!")
        print(f"Please add your .wav files to: {INPUT_DIR}")
        return
    
    print(f"📁 Found {len(wav_files)} WAV file(s):")
    for file in wav_files:
        language_code, language_name = get_language_info(file)
        print(f"   - {file} [{language_name}]")
    
    print("\n🎯 Starting transcription...")
    print("Supported languages:")
    print("   🇮🇳 English (default)")
    print("   🇮🇳 Hindi - use 'hi_' prefix")
    print("   🇮🇳 Telugu - use 'te_' prefix")
    
    # Process files
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["filename", "language", "language_name", "transcript"])
        
        for filename in wav_files:
            file_path = os.path.join(INPUT_DIR, filename)
            
            # Determine language based on filename
            language_code, language_name = get_language_info(filename)
            
            print(f"\n🌐 Language detected: {language_name} ({language_code})")
            transcript = transcribe_file(file_path, language_code)
            
            # Write to CSV with UTF-8 encoding to preserve all language characters
            writer.writerow([filename, language_code, language_name, transcript])
            
            print(f"\n📝 RESULT for {filename}:")
            print(f"   Language: {language_name}")
            print(f"   Transcript: {transcript}")
            print("-" * 50)
    
    print(f"\n🎉 Transcription completed!")
    print(f"💾 Results saved to: {OUTPUT_CSV}")
    print("📝 Note: All transcripts are preserved in their native scripts")

if __name__ == "__main__":
    main()