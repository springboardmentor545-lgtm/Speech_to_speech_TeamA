import azure.cognitiveservices.speech as speechsdk
import threading
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
speech_key = os.getenv("AZURE_SPEECH_KEY")
service_region = os.getenv("AZURE_REGION")

def recognize_from_microphone_enhanced():
    """
    Enhanced real-time speech recognition with voice stop and multiple features
    """
    if not speech_key or not service_region:
        print("❌ Azure credentials missing. Check your .env file.")
        return
    
    # Create speech config
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)
    
    print("🎤 VOICE RECORDER WITH AUTO-STOP")
    print("=" * 40)
    print("💬 Say 'end recording' to stop, or press Ctrl+C manually.")
    print("-" * 40)
    
    recognized_text = []
    stop_phrases = ["end recording"]
    start_time = time.time()
    max_duration = 120  # 2 minutes
    
    stop_event = threading.Event()
    
    def recognized_cb(evt):
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            text = evt.result.text.strip().lower()
            recognized_text.append(evt.result.text)
            print(f"🎯 {evt.result.text}")
            if any(phrase in text for phrase in stop_phrases):
                print("\n🛑 Stop command detected!")
                stop_event.set()
    
    def canceled_cb(evt):
        print(f"❌ Recognition canceled: {evt.result.reason}")
        stop_event.set()
    
    speech_recognizer.recognized.connect(recognized_cb)
    speech_recognizer.canceled.connect(canceled_cb)
    
    speech_recognizer.start_continuous_recognition_async().get()
    print("\n🔴 Recording started... Speak now!\n")
    
    try:
        while not stop_event.is_set():
            if time.time() - start_time > max_duration:
                print("\n⏰ 2 minutes limit reached.")
                stop_event.set()
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n⏹️  Manual stop requested...")
    finally:
        speech_recognizer.stop_continuous_recognition_async().get()
        print("🟢 Recording stopped")
    
    if recognized_text:
        final_transcript = [t for t in recognized_text if not any(p in t.lower() for p in stop_phrases)]
        if final_transcript:
            full_text = " ".join(final_transcript)
            print("\n🎉 FINAL TRANSCRIPTION:\n")
            print(full_text)
        else:
            print("❌ Only stop command detected.")
    else:
        print("❌ No speech recognized.")

if __name__ == "__main__":
    recognize_from_microphone_enhanced()
