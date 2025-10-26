import azure.cognitiveservices.speech as speechsdk
import threading
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def recognize_from_microphone_enhanced():
    """
    Enhanced real-time speech recognition with voice stop and multiple features
    """
    # Azure configuration from environment variables
    speech_key = os.getenv('SPEECH_KEY')
    service_region = os.getenv('SERVICE_REGION', 'centralindia')
    
    if not speech_key:
        raise ValueError("❌ SPEECH_KEY not found in environment variables")
    
    # Create speech config
    speech_config = speechsdk.SpeechConfig(
        subscription=speech_key, 
        region=service_region
    )
    
    # Create recognizer
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)
    
    print("🎤 VOICE RECORDER WITH AUTO-STOP")
    print("=" * 40)
    print("💬 Voice Commands to stop:")
    print("   - 'end recording'")
    print("\n⏹️  Manual: Press Ctrl+C to stop")
    print("⏰ Auto-stop: 2 minutes maximum")
    print("-" * 40)
    
    # Store the recognition results
    recognized_text = []
    stop_phrases = ["end recording"]
    start_time = time.time()
    max_duration = 120  # 2 minutes maximum
    
    # Event to signal when to stop
    stop_event = threading.Event()
    
    def recognized_cb(evt):
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            text = evt.result.text.strip().lower()
            recognized_text.append(evt.result.text)
            print(f"🎯 {evt.result.text}")
            
            # Check if user said any stop phrase
            if any(phrase in text for phrase in stop_phrases):
                print("\n🛑 Stop command detected! Ending recording...")
                stop_event.set()
    
    def canceled_cb(evt):
        print(f"❌ Recognition canceled: {evt.result.reason}")
        stop_event.set()
    
    # Connect callbacks
    speech_recognizer.recognized.connect(recognized_cb)
    speech_recognizer.canceled.connect(canceled_cb)
    
    # Start continuous recognition
    speech_recognizer.start_continuous_recognition_async().get()
    print("\n🔴 Recording started... Speak now!\n")
    
    try:
        # Wait for stop event with timeout
        while not stop_event.is_set():
            if time.time() - start_time > max_duration:
                print("\n⏰ Maximum time limit reached (2 minutes)")
                stop_event.set()
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Manual stop requested...")
    finally:
        # Stop recognition
        speech_recognizer.stop_continuous_recognition_async().get()
        print("🟢 Recording stopped")
        
        duration = time.time() - start_time
        print(f"⏱️  Total recording time: {duration:.1f} seconds")
    
    # Process and display final results
    if recognized_text:
        # Filter out stop commands
        final_transcript = []
        for text in recognized_text:
            text_lower = text.strip().lower()
            if not any(phrase in text_lower for phrase in stop_phrases):
                final_transcript.append(text)
        
        if final_transcript:
            full_text = " ".join(final_transcript)
            print(f"\n" + "=" * 50)
            print("🎉 FINAL TRANSCRIPTION:")
            print("=" * 50)
            print(f"📝 {full_text}")
            print(f"📊 Words: {len(full_text.split())}")
            print(f"🔢 Characters: {len(full_text)}")
            print("=" * 50)
        else:
            print("\n❌ Only stop commands were detected")
    else:
        print("\n❌ No speech recognized")

if __name__ == "__main__":
    recognize_from_microphone_enhanced()