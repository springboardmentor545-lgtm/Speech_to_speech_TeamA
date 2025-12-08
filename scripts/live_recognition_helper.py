"""
Enhanced helper script for live recognition that runs in a separate process
This avoids Streamlit's threading limitations and provides reliable speech recognition
"""

import os
import json
import time
import sys
import signal
from pathlib import Path
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk

load_dotenv()

# File paths
BASE_DIR = Path(__file__).parent.parent
TRANSCRIPT_FILE = BASE_DIR / "temp_audio_output" / "live_transcripts.json"
PARTIAL_FILE = BASE_DIR / "temp_audio_output" / "partial_transcript.txt"
PROCESS_FILE = BASE_DIR / "temp_audio_output" / "recognition_process.pid"
STATUS_FILE = BASE_DIR / "temp_audio_output" / "recognition_status.json"
LOG_FILE = BASE_DIR / "temp_audio_output" / "live_recognition.log"

def cleanup_files():
    """Clean up temporary files"""
    try:
        if PARTIAL_FILE.exists():
            PARTIAL_FILE.unlink()
        if STATUS_FILE.exists():
            STATUS_FILE.unlink()
        # Note: do not remove TRANSCRIPT_FILE by default
        with open(LOG_FILE, 'a', encoding='utf-8') as lf:
            lf.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Cleanup completed\n")
        print("Cleanup completed", file=sys.stderr)
    except Exception as e:
        print(f"Error during cleanup: {e}", file=sys.stderr)
        try:
            with open(LOG_FILE, 'a', encoding='utf-8') as lf:
                lf.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Cleanup error: {e}\n")
        except:
            pass

def signal_handler(sig, frame):
    """Handle cleanup on interrupt"""
    print("Received interrupt signal, cleaning up...", file=sys.stderr)
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as lf:
            lf.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Received signal {sig}, cleaning up\n")
    except:
        pass
    cleanup_files()
    # Remove PID file if present
    try:
        if PROCESS_FILE.exists():
            PROCESS_FILE.unlink()
    except:
        pass
    sys.exit(0)

def update_status(status, error=None):
    """Update status file for monitoring"""
    try:
        status_data = {
            "status": status,
            "timestamp": time.time(),
            "error": error
        }
        STATUS_FILE.parent.mkdir(exist_ok=True, parents=True)
        with open(STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, ensure_ascii=False, indent=2)
        # also log
        with open(LOG_FILE, 'a', encoding='utf-8') as lf:
            lf.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Status updated: {status} {('error: ' + str(error)) if error else ''}\n")
    except Exception as e:
        print(f"Error updating status: {e}", file=sys.stderr)
        try:
            with open(LOG_FILE, 'a', encoding='utf-8') as lf:
                lf.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Status update error: {e}\n")
        except:
            pass

def create_pid_file():
    """Create PID file to indicate process is running (atomic-ish and flushed)."""
    try:
        PROCESS_FILE.parent.mkdir(exist_ok=True, parents=True)
        # Write pid atomically via a .tmp -> rename
        tmp = PROCESS_FILE.with_suffix(".pid.tmp")
        with open(tmp, 'w', encoding='utf-8') as f:
            f.write(str(os.getpid()))
            f.flush()
            try:
                os.fsync(f.fileno())
            except:
                pass
        tmp.replace(PROCESS_FILE)  # atomic on most OSes
        # Also create/append to a logfile
        with open(LOG_FILE, 'a', encoding='utf-8') as lf:
            lf.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] PID file created: {PROCESS_FILE} (pid={os.getpid()})\n")
        print(f"✓ PID file created: {PROCESS_FILE}", file=sys.stderr)
        return True
    except Exception as e:
        # try writing to log file as fallback
        try:
            with open(LOG_FILE, 'a', encoding='utf-8') as lf:
                lf.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ✗ Failed to create PID file: {e}\n")
        except:
            pass
        print(f"✗ Failed to create PID file: {e}", file=sys.stderr)
        return False

def run_recognition(source_language="en-US"):
    """Run continuous recognition and save transcripts to file."""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        speech_key = os.getenv("AZURE_SPEECH_KEY")
        speech_region = os.getenv("AZURE_REGION")
        
        if not speech_key or not speech_region:
            error_msg = "Missing Azure credentials"
            print(f"ERROR: {error_msg}", file=sys.stderr)
            update_status("error", error_msg)
            sys.exit(1)
        
        # Create output directory and PID file immediately
        TRANSCRIPT_FILE.parent.mkdir(exist_ok=True, parents=True)
        
        if not create_pid_file():
            error_msg = "Failed to create PID file"
            update_status("error", error_msg)
            sys.exit(1)
        
        # Initialize files
        transcripts = []
        try:
            with open(TRANSCRIPT_FILE, 'w', encoding='utf-8') as f:
                json.dump(transcripts, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error initializing transcript file: {e}", file=sys.stderr)
            try:
                with open(LOG_FILE, 'a', encoding='utf-8') as lf:
                    lf.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Error initializing transcript file: {e}\n")
            except:
                pass
        
        update_status("initializing")
        
        print(f"Starting recognition for language: {source_language}", file=sys.stderr)
        with open(LOG_FILE, 'a', encoding='utf-8') as lf:
            lf.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting recognition for language: {source_language}\n")
        
        # Configure speech recognition
        speech_config = speechsdk.SpeechConfig(
            subscription=speech_key,
            region=speech_region
        )
        speech_config.speech_recognition_language = source_language
        
        # Configure audio with error handling
        audio_config = None
        try:
            print("Configuring microphone...", file=sys.stderr)
            audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
            print("✓ Microphone configured successfully", file=sys.stderr)
            with open(LOG_FILE, 'a', encoding='utf-8') as lf:
                lf.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Microphone configured\n")
        except Exception as e:
            error_msg = f"Microphone configuration failed: {e}"
            print(f"✗ {error_msg}", file=sys.stderr)
            update_status("error", error_msg)
            with open(LOG_FILE, 'a', encoding='utf-8') as lf:
                lf.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Microphone configuration failed: {e}\n")
            sys.exit(1)
        
        # Create recognizer
        try:
            recognizer = speechsdk.SpeechRecognizer(speech_config, audio_config)
            print("✓ Speech recognizer created", file=sys.stderr)
            with open(LOG_FILE, 'a', encoding='utf-8') as lf:
                lf.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Recognizer created\n")
        except Exception as e:
            error_msg = f"Failed to create recognizer: {e}"
            print(f"✗ {error_msg}", file=sys.stderr)
            update_status("error", error_msg)
            with open(LOG_FILE, 'a', encoding='utf-8') as lf:
                lf.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Recognizer creation failed: {e}\n")
            sys.exit(1)
        
        update_status("running")
        
        # Track if we should keep running
        keep_running = True
        
        def recognized_cb(evt):
            """Callback for recognized speech"""
            try:
                if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                    text = evt.result.text.strip()
                    if text and len(text) > 2:  # Filter out very short segments
                        transcript_data = {
                            "id": f"live_{int(time.time() * 1000)}",
                            "text": text,
                            "timestamp": time.time(),
                            "language": source_language
                        }
                        
                        # Load existing transcripts
                        existing_transcripts = []
                        if TRANSCRIPT_FILE.exists():
                            try:
                                with open(TRANSCRIPT_FILE, 'r', encoding='utf-8') as f:
                                    content = f.read().strip()
                                    if content:
                                        existing_transcripts = json.loads(content)
                            except Exception as e:
                                print(f"Error loading existing transcripts: {e}", file=sys.stderr)
                                existing_transcripts = []
                        
                        # Add new transcript
                        existing_transcripts.append(transcript_data)
                        
                        # Save to file
                        try:
                            with open(TRANSCRIPT_FILE, 'w', encoding='utf-8') as f:
                                json.dump(existing_transcripts, f, ensure_ascii=False, indent=2)
                            print(f"✓ Saved: {text}", file=sys.stderr)
                            with open(LOG_FILE, 'a', encoding='utf-8') as lf:
                                lf.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Saved transcript: {text}\n")
                        except Exception as e:
                            print(f"Error saving transcript: {e}", file=sys.stderr)
                            
                elif evt.result.reason == speechsdk.ResultReason.NoMatch:
                    print("No speech recognized", file=sys.stderr)
                    
            except Exception as e:
                print(f"Error in recognition callback: {e}", file=sys.stderr)
        
        def recognizing_cb(evt):
            """Callback for partial recognition results"""
            try:
                if evt.result.reason == speechsdk.ResultReason.RecognizingSpeech:
                    text = evt.result.text.strip()
                    if text:
                        try:
                            with open(PARTIAL_FILE, 'w', encoding='utf-8') as f:
                                f.write(text)
                        except Exception as e:
                            print(f"Error saving partial transcript: {e}", file=sys.stderr)
            except Exception as e:
                print(f"Error in partial recognition: {e}", file=sys.stderr)
        
        def canceled_cb(evt):
            """Callback for canceled recognition"""
            print(f"Recognition canceled: {evt.reason}", file=sys.stderr)
            if evt.reason == speechsdk.CancellationReason.Error:
                error_details = f"Error: {evt.error_details}"
                print(f"Error details: {error_details}", file=sys.stderr)
                update_status("error", error_details)
                with open(LOG_FILE, 'a', encoding='utf-8') as lf:
                    lf.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Cancellation error: {error_details}\n")
        
        def session_started_cb(evt):
            print("✓ Session started successfully", file=sys.stderr)
            update_status("listening")
        
        def session_stopped_cb(evt):
            print("Session stopped", file=sys.stderr)
            update_status("stopped")
        
        # Connect event handlers
        recognizer.recognized.connect(recognized_cb)
        recognizer.recognizing.connect(recognizing_cb)
        recognizer.canceled.connect(canceled_cb)
        recognizer.session_started.connect(session_started_cb)
        recognizer.session_stopped.connect(session_stopped_cb)
        
        # Start recognition
        print("Starting continuous recognition...", file=sys.stderr)
        try:
            # start_continuous_recognition_async returns a future; offload to background
            recognizer.start_continuous_recognition_async()
            print("✓ Continuous recognition started", file=sys.stderr)
            with open(LOG_FILE, 'a', encoding='utf-8') as lf:
                lf.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Continuous recognition started\n")
        except Exception as e:
            error_msg = f"Failed to start recognition: {e}"
            print(f"✗ {error_msg}", file=sys.stderr)
            update_status("error", error_msg)
            with open(LOG_FILE, 'a', encoding='utf-8') as lf:
                lf.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Failed to start recognition: {e}\n")
            sys.exit(1)
        
        # Keep running until stopped
        print("🎤 Listening... Speak now! (Process will stop when PID file is removed)", file=sys.stderr)
        try:
            while keep_running:
                time.sleep(0.5)
                # Check if we should stop (PID file removed)
                if not PROCESS_FILE.exists():
                    print("Process file removed, stopping...", file=sys.stderr)
                    with open(LOG_FILE, 'a', encoding='utf-8') as lf:
                        lf.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] PID file removed; stopping\n")
                    keep_running = False
                    break
                    
        except KeyboardInterrupt:
            print("Interrupted by user", file=sys.stderr)
        except Exception as e:
            print(f"Unexpected error in main loop: {e}", file=sys.stderr)
            with open(LOG_FILE, 'a', encoding='utf-8') as lf:
                lf.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Unexpected error in main loop: {e}\n")
            
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        update_status("error", str(e))
        try:
            with open(LOG_FILE, 'a', encoding='utf-8') as lf:
                lf.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Fatal error: {e}\n")
        except:
            pass
    finally:
        try:
            # Stop recognition
            if 'recognizer' in locals():
                print("Stopping continuous recognition...", file=sys.stderr)
                try:
                    recognizer.stop_continuous_recognition_async().get()
                except Exception:
                    try:
                        recognizer.stop_continuous_recognition_async()
                    except:
                        pass
                print("✓ Recognition stopped", file=sys.stderr)
                with open(LOG_FILE, 'a', encoding='utf-8') as lf:
                    lf.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Recognition stopped\n")
            # Cleanup
            cleanup_files()
            update_status("stopped")
            print("Recognition stopped and cleaned up", file=sys.stderr)
        except Exception as e:
            print(f"Error during cleanup: {e}", file=sys.stderr)
            try:
                with open(LOG_FILE, 'a', encoding='utf-8') as lf:
                    lf.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Error during cleanup: {e}\n")
            except:
                pass

if __name__ == "__main__":
    source_lang = sys.argv[1] if len(sys.argv) > 1 else "en-US"
    run_recognition(source_lang)
