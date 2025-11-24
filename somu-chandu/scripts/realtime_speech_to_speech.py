"""
Milestone 3: Full Real-Time Speech-to-Speech Pipeline
Combines STT → Translation → TTS in a real-time streaming system
"""

import os
import time
import threading
import uuid
import json
from datetime import datetime
from typing import Dict, List, Optional
from queue import Queue
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk

from translator import translate_with_retry
from language_config import (
    DEFAULT_TARGET_LANGUAGES, SUPPORTED_LANGUAGES,
    SPEECH_LANGUAGES, TTS_VOICES, get_speech_language_code, get_tts_voice
)

load_dotenv()

# Azure credentials
SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
SPEECH_REGION = os.getenv("AZURE_REGION")
TRANSLATOR_KEY = os.getenv("AZURE_TRANSLATOR_KEY")
TRANSLATOR_REGION = os.getenv("AZURE_TRANSLATOR_REGION") or os.getenv("AZURE_REGION")

# Base directories
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "realtime_output")
AUDIO_OUTPUT_DIR = os.path.join(OUTPUT_DIR, "audio")
TRANSCRIPTS_OUTPUT_DIR = os.path.join(OUTPUT_DIR, "transcripts")
TRANSLATIONS_OUTPUT_DIR = os.path.join(OUTPUT_DIR, "translations")

# Configuration
TARGET_LANGUAGES = DEFAULT_TARGET_LANGUAGES  # 15+ target languages
SOURCE_LANGUAGE = "en-US"  # Source language for STT
CHUNK_DURATION = 3.0  # Process chunks every 3 seconds
SILENCE_TIMEOUT = 2.0  # Stop after 2 seconds of silence


class RealtimeSpeechToSpeech:
    """
    Real-time Speech-to-Speech pipeline orchestrator.
    Handles: STT → Translation → TTS
    """
    
    def __init__(self, target_languages: List[str] = None, source_language: str = "en-US"):
        """Initialize the pipeline."""
        if not SPEECH_KEY or not SPEECH_REGION:
            raise ValueError("Missing Azure Speech credentials. Check .env file.")
        if not TRANSLATOR_KEY or not TRANSLATOR_REGION:
            raise ValueError("Missing Azure Translator credentials. Check .env file.")
        
        self.target_languages = target_languages or TARGET_LANGUAGES
        self.source_language = source_language
        
        # Create output directories
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        os.makedirs(AUDIO_OUTPUT_DIR, exist_ok=True)
        os.makedirs(TRANSCRIPTS_OUTPUT_DIR, exist_ok=True)
        os.makedirs(TRANSLATIONS_OUTPUT_DIR, exist_ok=True)
        
        # State management
        self.transcript_queue = Queue()  # Queue for final transcripts
        self.translation_queue = Queue()  # Queue for translations
        self.transcript_id_counter = 0
        self.transcript_map = {}  # Maps transcript_id -> transcript_data
        self.translation_map = {}  # Maps transcript_id -> translation_data
        
        # Timing metrics
        self.stt_timings = []
        self.translation_timings = []
        self.tts_timings = []
        
        # Control flags
        self.is_running = False
        self.stop_event = threading.Event()
        
        # Initialize Azure services
        self._init_speech_config()
        self._init_tts_config()
    
    def _init_speech_config(self):
        """Initialize Azure Speech-to-Text configuration."""
        self.speech_config = speechsdk.SpeechConfig(
            subscription=SPEECH_KEY,
            region=SPEECH_REGION
        )
        self.speech_config.speech_recognition_language = self.source_language
        self.speech_config.set_property_by_name(
            speechsdk.PropertyId.Speech_SegmentationSilenceTimeoutMs, "2000"
        )
    
    def _init_tts_config(self):
        """Initialize Azure Text-to-Speech configuration."""
        self.tts_config = speechsdk.SpeechConfig(
            subscription=SPEECH_KEY,
            region=SPEECH_REGION
        )
        # Use neural voices for better quality
        self.tts_config.speech_synthesis_voice_name = "en-US-JennyNeural"
    
    def _stt_recognized_callback(self, evt):
        """Callback for STT recognition events."""
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            text = evt.result.text.strip()
            if text:
                transcript_id = f"transcript_{self.transcript_id_counter}_{int(time.time())}"
                self.transcript_id_counter += 1
                
                transcript_data = {
                    "id": transcript_id,
                    "text": text,
                    "timestamp": datetime.now().isoformat(),
                    "stt_time": time.time()
                }
                
                self.transcript_map[transcript_id] = transcript_data
                self.transcript_queue.put(transcript_data)
                
                # Save transcript to file
                transcript_file = os.path.join(
                    TRANSCRIPTS_OUTPUT_DIR,
                    f"{transcript_id}.json"
                )
                with open(transcript_file, 'w', encoding='utf-8') as f:
                    json.dump(transcript_data, f, ensure_ascii=False, indent=2)
                
                print(f"\n🎯 [STT] {transcript_id}: {text}")
        
        elif evt.result.reason == speechsdk.ResultReason.NoMatch:
            print("⚠️ [STT] No speech could be recognized")
    
    def _stt_recognizing_callback(self, evt):
        """Callback for partial STT results."""
        if evt.result.reason == speechsdk.ResultReason.RecognizingSpeech:
            text = evt.result.text.strip()
            if text:
                print(f"🔄 [STT Partial] {text}", end="\r")
    
    def _stt_canceled_callback(self, evt):
        """Callback for STT cancellation."""
        print(f"❌ [STT] Canceled: {evt.result.reason}")
        if evt.result.reason == speechsdk.CancellationReason.Error:
            print(f"   Error details: {evt.result.error_details}")
        self.stop_event.set()
    
    def _process_translations(self):
        """Background thread to process translations."""
        while not self.stop_event.is_set():
            try:
                if not self.transcript_queue.empty():
                    transcript_data = self.transcript_queue.get(timeout=1)
                    self._translate_transcript(transcript_data)
                else:
                    time.sleep(0.1)
            except Exception as e:
                print(f"❌ [Translation Thread] Error: {e}")
                time.sleep(0.5)
    
    def _translate_transcript(self, transcript_data: Dict):
        """Translate a transcript and queue for TTS."""
        transcript_id = transcript_data["id"]
        text = transcript_data["text"]
        
        print(f"🌐 [Translation] Translating: {text[:50]}...")
        translation_start = time.time()
        
        # Translate to all target languages
        result = translate_with_retry(
            text,
            target_languages=self.target_languages,
            source_language=self.source_language.split("-")[0] if "-" in self.source_language else self.source_language
        )
        
        translation_time = time.time() - translation_start
        self.translation_timings.append(translation_time)
        
        if result["success"]:
            translation_data = {
                "transcript_id": transcript_id,
                "original_text": text,
                "translations": result["translations"],
                "source_language": result["source_language"],
                "timestamp": result["timestamp"],
                "translation_time": translation_time
            }
            
            self.translation_map[transcript_id] = translation_data
            self.translation_queue.put(translation_data)
            
            # Save translation JSON
            translation_file = os.path.join(
                TRANSLATIONS_OUTPUT_DIR,
                f"translation_{transcript_id}.json"
            )
            with open(translation_file, 'w', encoding='utf-8') as f:
                json.dump(translation_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ [Translation] Completed in {translation_time:.2f}s")
            for lang, trans_text in result["translations"].items():
                print(f"   {lang}: {trans_text[:60]}...")
            
            # Generate TTS for each translation
            self._generate_tts(translation_data)
        else:
            print(f"❌ [Translation] Failed: {result.get('error', 'Unknown error')}")
    
    def _generate_tts(self, translation_data: Dict):
        """Generate TTS audio for translated text."""
        transcript_id = translation_data["transcript_id"]
        
        for lang, translated_text in translation_data["translations"].items():
            if not translated_text.strip():
                continue
            
            tts_start = time.time()
            # Use language config for voice mapping
            voice_name = get_tts_voice(lang)
            
            print(f"🔊 [TTS] Generating audio for {lang}: {translated_text[:40]}...")
            
            try:
                # Update TTS config for this language
                self.tts_config.speech_synthesis_voice_name = voice_name
                
                # Prepare audio file path
                audio_file = os.path.join(
                    AUDIO_OUTPUT_DIR,
                    f"tts_{transcript_id}_{lang}.wav"
                )
                
                # Create audio output config to save directly to file
                audio_config = speechsdk.audio.AudioOutputConfig(filename=audio_file)
                
                # Create synthesizer with file output
                synthesizer = speechsdk.SpeechSynthesizer(
                    speech_config=self.tts_config,
                    audio_config=audio_config
                )
                
                # Synthesize speech directly to file
                result = synthesizer.speak_text_async(translated_text).get()
                
                tts_time = time.time() - tts_start
                self.tts_timings.append(tts_time)
                
                if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                    print(f"✅ [TTS] Saved {lang} audio: {os.path.basename(audio_file)} ({tts_time:.2f}s)")
                elif result.reason == speechsdk.ResultReason.Canceled:
                    cancellation = speechsdk.CancellationDetails(result)
                    print(f"❌ [TTS] {lang} canceled: {cancellation.reason}")
                    if cancellation.reason == speechsdk.CancellationReason.Error:
                        print(f"   Error: {cancellation.error_details}")
                else:
                    print(f"⚠️ [TTS] {lang} audio generation issue: {result.reason}")
            
            except Exception as e:
                print(f"❌ [TTS] {lang} error: {e}")
    
    def _process_tts(self):
        """Background thread to process TTS (already handled in _generate_tts)."""
        pass  # TTS is handled synchronously in _translate_transcript for simplicity
    
    def start(self):
        """Start the real-time Speech-to-Speech pipeline."""
        print("🚀 REAL-TIME SPEECH-TO-SPEECH PIPELINE")
        print("=" * 60)
        print(f"🌍 Source Language: {self.source_language}")
        print(f"🌍 Target Languages: {', '.join(self.target_languages)}")
        print("=" * 60)
        print("\n💬 Speak into your microphone...")
        print("⏹️  Press Ctrl+C to stop\n")
        
        # Create speech recognizer
        audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config,
            audio_config=audio_config
        )
        
        # Set up callbacks
        speech_recognizer.recognized.connect(self._stt_recognized_callback)
        speech_recognizer.recognizing.connect(self._stt_recognizing_callback)
        speech_recognizer.canceled.connect(self._stt_canceled_callback)
        
        # Start background threads
        translation_thread = threading.Thread(target=self._process_translations, daemon=True)
        translation_thread.start()
        
        self.is_running = True
        
        try:
            # Start continuous recognition
            speech_recognizer.start_continuous_recognition_async().get()
            print("🔴 Recording started...\n")
            
            # Keep running until stopped
            while not self.stop_event.is_set():
                time.sleep(0.1)
        
        except KeyboardInterrupt:
            print("\n⏹️  Stopping pipeline...")
        finally:
            # Stop recognition
            speech_recognizer.stop_continuous_recognition_async().get()
            self.is_running = False
            self.stop_event.set()
            
            # Wait for threads to finish
            translation_thread.join(timeout=5)
            
            # Print summary
            self._print_summary()
    
    def _print_summary(self):
        """Print pipeline execution summary."""
        print("\n" + "=" * 60)
        print("📊 PIPELINE SUMMARY")
        print("=" * 60)
        
        total_transcripts = len(self.transcript_map)
        total_translations = len(self.translation_map)
        
        print(f"📝 Transcripts processed: {total_transcripts}")
        print(f"🌐 Translations completed: {total_translations}")
        
        if self.translation_timings:
            avg_translation = sum(self.translation_timings) / len(self.translation_timings)
            print(f"⏱️  Avg translation time: {avg_translation:.2f}s")
        
        if self.tts_timings:
            avg_tts = sum(self.tts_timings) / len(self.tts_timings)
            print(f"⏱️  Avg TTS time: {avg_tts:.2f}s")
        
        print(f"\n💾 Output saved to: {OUTPUT_DIR}")
        print("=" * 60)


def main():
    """Main entry point."""
    try:
        pipeline = RealtimeSpeechToSpeech(
            target_languages=TARGET_LANGUAGES,
            source_language=SOURCE_LANGUAGE
        )
        pipeline.start()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

