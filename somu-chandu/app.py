"""
Final Streamlit app.py with robust process control and enhanced UI.
Merged: original robust logic + enhanced UI from second version.
"""

import streamlit as st
import os
import json
import time
import html
from urllib.error import HTTPError
from pathlib import Path
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk
import psutil
import subprocess
import sys
import importlib.util
from pytube import YouTube, Search
import yt_dlp

# Import project modules - support both normal import and running from different cwd
BASE_DIR = os.path.dirname(__file__)
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

try:
    from translator import translate_with_retry, translate_text
    from language_config import (
        SUPPORTED_LANGUAGES, LANGUAGE_NAMES, SPEECH_LANGUAGES,
        TTS_VOICES, get_speech_language_code, get_language_name, get_tts_voice
    )
except Exception:
    # Fallback when running from different directory
    try:
        spec = importlib.util.spec_from_file_location("translator", os.path.join(SCRIPTS_DIR, "translator.py"))
        translator_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(translator_module)
        translate_with_retry = translator_module.translate_with_retry
        translate_text = translator_module.translate_text
    except Exception as e:
        translate_with_retry = lambda *a, **k: {"success": False, "error": f"translator import error: {e}"}
        translate_text = lambda *a, **k: {"success": False, "error": f"translator import error: {e}"}

    try:
        lang_spec = importlib.util.spec_from_file_location("language_config", os.path.join(SCRIPTS_DIR, "language_config.py"))
        lang_module = importlib.util.module_from_spec(lang_spec)
        lang_spec.loader.exec_module(lang_module)
        SUPPORTED_LANGUAGES = lang_module.SUPPORTED_LANGUAGES
        LANGUAGE_NAMES = lang_module.LANGUAGE_NAMES
        SPEECH_LANGUAGES = lang_module.SPEECH_LANGUAGES
        TTS_VOICES = lang_module.TTS_VOICES
        get_speech_language_code = lang_module.get_speech_language_code
        get_language_name = lang_module.get_language_name
        get_tts_voice = lang_module.get_tts_voice
    except Exception as e:
        # Fallback minimal defaults to avoid crashes during UI design (user should have proper file)
        SUPPORTED_LANGUAGES = ["en", "hi"]
        LANGUAGE_NAMES = {"en": "English", "hi": "Hindi"}
        SPEECH_LANGUAGES = {}
        TTS_VOICES = {}
        get_speech_language_code = lambda x: x
        get_language_name = lambda x: LANGUAGE_NAMES.get(x, x)
        get_tts_voice = lambda x, gender="female": (TTS_VOICES.get(x) or {}).get(gender) if isinstance(TTS_VOICES.get(x), dict) else TTS_VOICES.get(x, None)

load_dotenv()

st.set_page_config(page_title="Speech-to-Speech Translation", page_icon="🎤", layout="wide", initial_sidebar_state="expanded")

# helper: safe rerun (keeps original maybe_rerun behavior)
def maybe_rerun():
    try:
        st.experimental_rerun()
    except Exception:
        st.session_state["_needs_rerender"] = not st.session_state.get("_needs_rerender", False)

# --- Session state defaults (kept from first file, with a few additional keys) ---
for k, v in {
    'live_recognition_running': False,
    'live_transcripts': [],
    'audio_files': [],
    'file_upload_results': None,
    'youtube_results': None,
    'last_translation_result': None,
    'last_refresh': time.time(),
    'pipeline_running': False,
    'transcripts': [],
    'translations': [],
    'recognizer': None,
    'recognition_thread': None,
    'transcript_queue': [],
    'recognition_error': None,
    'voice_gender': 'female',
    'voice_rate': 0,
    'voice_pitch': 0,
    'yt_search_results': [],
    'video_outputs': [],
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# --- Core helpers (kept from your first file, with minor restructuring) ---

def check_credentials():
    speech_key = os.getenv("AZURE_SPEECH_KEY")
    speech_region = os.getenv("AZURE_REGION")
    translator_key = os.getenv("AZURE_TRANSLATOR_KEY")
    translator_region = os.getenv("AZURE_TRANSLATOR_REGION") or os.getenv("AZURE_REGION")
    return {
        "speech_key": bool(speech_key),
        "speech_region": bool(speech_region),
        "translator_key": bool(translator_key),
        "translator_region": bool(translator_region),
        "all_configured": bool(speech_key and speech_region and translator_key and translator_region)
    }

def transcribe_audio_path(file_path: Path, language="en-US"):
    """Transcribe an existing audio file on disk."""
    try:
        speech_key = os.getenv("AZURE_SPEECH_KEY")
        speech_region = os.getenv("AZURE_REGION")
        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
        speech_config.speech_recognition_language = language
        audio_config = speechsdk.audio.AudioConfig(filename=str(file_path))
        recognizer = speechsdk.SpeechRecognizer(speech_config, audio_config)
        result = recognizer.recognize_once_async().get()
        recognizer = None
        audio_config = None
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return {"success": True, "text": result.text}
        else:
            return {"success": False, "error": "No speech recognized"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# --- Audio helpers for format safety (ensure WAV 16 kHz mono) ---

def convert_to_wav_16k(input_path: Path) -> dict:
    """Convert any audio file to 16 kHz mono WAV using ffmpeg."""
    try:
        output_dir = input_path.parent
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f"{input_path.stem}_16k.wav"
        if output_path.exists():
            output_path.unlink()
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(input_path),
            "-acodec",
            "pcm_s16le",
            "-ac",
            "1",
            "-ar",
            "16000",
            str(output_path),
        ]
        completed = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if completed.returncode != 0 or not output_path.exists():
            return {"success": False, "error": f"ffmpeg conversion failed: {completed.stderr.decode(errors='ignore')[:500]}"}
        return {"success": True, "file_path": output_path}
    except FileNotFoundError:
        return {"success": False, "error": "ffmpeg not found. Please install ffmpeg and ensure it is on PATH."}
    except Exception as e:
        return {"success": False, "error": f"Audio conversion error: {e}"}


def transcribe_audio_file(audio_file, language="en-US"):
    """Transcribe uploaded file-like object by saving to disk temporarily."""
    temp_path = None
    try:
        temp_dir = Path("temp_audio")
        temp_dir.mkdir(exist_ok=True)
        unique_id = f"{int(time.time() * 1000)}_{abs(hash(audio_file.name)) % 10000}"
        file_ext = Path(audio_file.name).suffix or ".wav"
        temp_path = temp_dir / f"temp_{unique_id}{file_ext}"
        with open(temp_path, "wb") as f:
            f.write(audio_file.getbuffer())
        del f
        time.sleep(0.1)
        result = transcribe_audio_path(temp_path, language)
        time.sleep(0.1)
        for attempt in range(5):
            try:
                if temp_path and temp_path.exists():
                    temp_path.unlink()
                break
            except (PermissionError, OSError):
                time.sleep(0.3)
        return result
    except Exception as e:
        try:
            if temp_path and temp_path.exists():
                time.sleep(0.2)
                temp_path.unlink()
        except:
            pass
        return {"success": False, "error": str(e)}


def normalize_youtube_url(url: str) -> str:
    """Normalize common YouTube URL formats to a standard watch URL."""
    url = url.strip()
    if "youtu.be/" in url:
        video_id = url.split("youtu.be/")[-1].split("?")[0]
        return f"https://www.youtube.com/watch?v={video_id}"
    if "/shorts/" in url:
        video_id = url.split("/shorts/")[-1].split("?")[0]
        return f"https://www.youtube.com/watch?v={video_id}"
    return url


def download_with_yt_dlp(url: str, output_dir: Path):
    """Fallback downloader using yt_dlp for tougher cases."""
    output_dir.mkdir(exist_ok=True)
    out_template = str(output_dir / "yt_%(id)s.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": out_template,
        "quiet": True,
        "nocheckcertificate": True,
        "noprogress": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
                "preferredquality": "192",
            }
        ],
        "postprocessor_args": ["-ar", "16000", "-ac", "1"],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        wav_path = Path(filename).with_suffix(".wav")
        final_path = wav_path if wav_path.exists() else Path(filename)
        return {
            "success": True,
            "file_path": final_path,
            "title": info.get("title"),
            "length": info.get("duration"),
        }


def download_youtube_video_mp4(url: str):
    """Download best-available MP4 video with audio using yt_dlp."""
    try:
        temp_dir = Path("temp_video")
        temp_dir.mkdir(exist_ok=True)
        normalized_url = normalize_youtube_url(url)
        out_template = str(temp_dir / "yt_%(id)s.%(ext)s")
        ydl_opts = {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "outtmpl": out_template,
            "quiet": True,
            "nocheckcertificate": True,
            "merge_output_format": "mp4",
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(normalized_url, download=True)
            filename = ydl.prepare_filename(info)
            mp4_path = Path(filename)
            if mp4_path.suffix.lower() != ".mp4":
                alt_path = mp4_path.with_suffix(".mp4")
                if alt_path.exists():
                    mp4_path = alt_path
            if not mp4_path.exists():
                return {"success": False, "error": "Video download failed: file not found after download."}
            return {
                "success": True,
                "file_path": mp4_path,
                "title": info.get("title"),
                "length": info.get("duration"),
            }
    except Exception as e:
        return {"success": False, "error": f"Video download failed: {e}"}


def mux_video_with_audio(video_path: Path, audio_path: Path, transcript_id: str, lang: str):
    """Replace video's audio track with provided audio using ffmpeg."""
    try:
        output_dir = Path("temp_video_output")
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f"dub_{transcript_id}_{lang}.mp4"
        if output_path.exists():
            output_path.unlink()
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-i",
            str(audio_path),
            "-c:v",
            "copy",
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-shortest",
            str(output_path),
        ]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if proc.returncode != 0 or not output_path.exists():
            return {"success": False, "error": f"ffmpeg mux failed: {proc.stderr.decode(errors='ignore')[:500]}"}
        return {"success": True, "file_path": output_path}
    except FileNotFoundError:
        return {"success": False, "error": "ffmpeg not found. Please install ffmpeg and ensure it is on PATH."}
    except Exception as e:
        return {"success": False, "error": f"Mux error: {e}"}


def download_youtube_audio(url: str):
    """Download YouTube audio-only stream and return local path."""
    try:
        temp_dir = Path("temp_audio")
        temp_dir.mkdir(exist_ok=True)
        normalized_url = normalize_youtube_url(url)
        try:
            yt = YouTube(normalized_url, use_oauth=False, allow_oauth_cache=True)
            try:
                yt.bypass_age_gate()
            except Exception:
                pass

            def _download_best_stream(yt_obj):
                # Prefer audio-only, fallback to progressive mp4 if audio-only fails.
                audio_stream = yt_obj.streams.filter(only_audio=True).order_by('abr').desc().first()
                progressive_stream = yt_obj.streams.filter(progressive=True, file_extension="mp4").order_by('abr').desc().first()
                return audio_stream or progressive_stream

            stream = _download_best_stream(yt)
            if not stream:
                raise RuntimeError("No downloadable stream found for this video.")

            safe_title = "".join(c for c in yt.title if c.isalnum() or c in (" ", "-", "_")).strip() or "youtube_audio"
            filename = f"yt_{int(time.time() * 1000)}_{safe_title[:24].replace(' ', '_')}"
            file_path = Path(stream.download(output_path=str(temp_dir), filename=filename))
            # ensure WAV 16k
            conv = convert_to_wav_16k(file_path)
            if conv["success"]:
                file_path = conv["file_path"]
            else:
                return {"success": False, "error": conv.get("error", "Conversion failed")}

            return {
                "success": True,
                "file_path": file_path,
                "title": yt.title,
                "length": yt.length
            }
        except Exception as primary_err:
            # Fallback to yt_dlp for stubborn URLs (age/region/shorts/etc.)
            try:
                dl = download_with_yt_dlp(normalized_url, temp_dir)
                return dl
            except Exception as fallback_err:
                return {
                    "success": False,
                    "error": f"YouTube download failed. Primary: {primary_err}; Fallback: {fallback_err}"
                }
    except Exception as e:
        return {"success": False, "error": f"YouTube download failed: {e}"}


def process_youtube_url(url: str, source_language: str, target_languages):
    """End-to-end YouTube pipeline: download -> transcribe -> translate."""
    download_result = download_youtube_audio(url)
    if not download_result["success"]:
        return download_result

    video_dl = download_youtube_video_mp4(url)
    if not video_dl["success"]:
        return video_dl

    file_path = download_result["file_path"]
    transcript = transcribe_audio_path(file_path, source_language)
    if not transcript["success"]:
        return {"success": False, "error": transcript.get("error", "Transcription failed")}

    translation_result = translate_with_retry(
        transcript["text"],
        target_languages=target_languages,
        source_language=None  # Let translator auto-detect if needed
    )
    if not translation_result["success"]:
        return {"success": False, "error": translation_result.get("error", "Translation failed")}

    transcript_id = f"yt_{int(time.time())}"
    return {
        "success": True,
        "file_path": str(file_path),
        "video_title": download_result.get("title"),
        "video_length": download_result.get("length"),
        "transcript_text": transcript["text"],
        "video_file": str(video_dl.get("file_path")),
        "translation_result": translation_result,
        "transcript_id": transcript_id,
        "url": url
    }

def generate_tts_audio(text, language_code, transcript_id, voice_gender="female", rate_percent=0, pitch_percent=0):
    try:
        speech_key = os.getenv("AZURE_SPEECH_KEY")
        speech_region = os.getenv("AZURE_REGION")
        voice_name = get_tts_voice(language_code, gender=voice_gender)
        tts_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
        if voice_name:
            tts_config.speech_synthesis_voice_name = voice_name
        output_dir = Path("temp_audio_output")
        output_dir.mkdir(exist_ok=True)
        audio_file = output_dir / f"tts_{transcript_id}_{language_code}.wav"
        audio_config = speechsdk.audio.AudioOutputConfig(filename=str(audio_file))
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=tts_config, audio_config=audio_config)
        # Use SSML so we can adjust pitch/rate even when defaults are zero.
        ssml = f"""
<speak version="1.0" xml:lang="{language_code}">
  <voice name="{voice_name}">
    <prosody rate="{rate_percent:+d}%" pitch="{pitch_percent:+d}%">{html.escape(text)}</prosody>
  </voice>
</speak>
""".strip()
        result = synthesizer.speak_ssml_async(ssml).get()
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return {"success": True, "file_path": str(audio_file)}
        else:
            return {"success": False, "error": f"TTS failed: {result.reason}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def is_process_running(pid):
    try:
        process = psutil.Process(pid)
        return process.is_running() and process.status() != psutil.STATUS_ZOMBIE
    except (psutil.NoSuchProcess, psutil.AccessDenied, ValueError):
        return False

def get_recognition_status():
    process_file = Path("temp_audio_output") / "recognition_process.pid"
    status_file = Path("temp_audio_output") / "recognition_status.json"
    is_running = False
    status_text = "Stopped"
    error_msg = None
    if process_file.exists():
        try:
            with open(process_file, 'r') as f:
                pid = int(f.read().strip())
            if is_process_running(pid):
                is_running = True
                if status_file.exists():
                    try:
                        with open(status_file, 'r') as f:
                            status_data = json.load(f)
                        status_text = status_data.get('status', 'Running')
                        error_msg = status_data.get('error')
                    except:
                        status_text = "Running"
                else:
                    status_text = "Running"
            else:
                try:
                    process_file.unlink()
                except:
                    pass
        except:
            try:
                if process_file.exists():
                    process_file.unlink()
            except:
                pass
    return {"is_running": is_running, "status": status_text, "error": error_msg}

# --- Enhanced UI CSS (from second app.py) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
    * { font-family: 'Poppins', sans-serif; }
    .main-header { font-size: 3.5rem; font-weight: 700; text-align: center;
                   background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                   margin-bottom: 2rem; animation: fadeInDown 0.8s ease-out; }
    @keyframes fadeInDown { from { opacity: 0; transform: translateY(-20px);} to { opacity: 1; transform: translateY(0);} }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }
    .status-box { padding: 1.5rem; border-radius: 15px; margin: 1rem 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: transform 0.3s ease; }
    .status-box:hover { transform: translateY(-2px); box-shadow: 0 6px 12px rgba(0,0,0,0.15); }
    .success-box { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; }
    .error-box { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; border: none; }
    .info-box { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; border: none; }
    .card { background: white; border-radius: 15px; padding: 2rem; box-shadow: 0 10px 30px rgba(0,0,0,0.1); margin: 1rem 0; transition: all 0.3s ease; }
    .card:hover { box-shadow: 0 15px 40px rgba(0,0,0,0.15); transform: translateY(-5px); }
    .recording-indicator { display:inline-block; width:12px; height:12px; background:#f5576c; border-radius:50%; margin-right:8px; animation: pulse 1.5s infinite; }
    .stButton>button { border-radius:25px; padding:0.5rem 2rem; font-weight:600; transition:all 0.3s ease; border:none; }
    .stButton>button:hover { transform: scale(1.05); box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
    .metric-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color:white; padding:1.5rem; border-radius:15px; text-align:center; box-shadow:0 5px 15px rgba(102,126,234,0.3); }
    .transcript-card { background:#f7fafc; border-left:4px solid #667eea; padding:1rem; margin:0.5rem 0; border-radius:8px; transition: all 0.3s ease; }
    .transcript-card:hover { background:#edf2f7; transform: translateX(5px); }
</style>
""", unsafe_allow_html=True)

# --- Main UI (structure adapted from second app.py but using functions from first) ---

st.markdown('<h1 class="main-header">🎤 Speech-to-Speech Translation</h1>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")

    creds = check_credentials()
    if creds["all_configured"]:
        st.success("✅ All credentials configured")
    else:
        st.error("❌ Missing credentials")
        missing = []
        if not creds["speech_key"]:
            missing.append("AZURE_SPEECH_KEY")
        if not creds["speech_region"]:
            missing.append("AZURE_REGION")
        if not creds["translator_key"]:
            missing.append("AZURE_TRANSLATOR_KEY")
        st.info(f"Please configure your .env file with: {', '.join(missing)}")
        st.stop()

    st.divider()
    st.subheader("🌍 Language Settings")

    # Source language selection
    try:
        source_lang_selected = st.selectbox(
            "Source Language",
            options=SUPPORTED_LANGUAGES,
            format_func=lambda x: f"{get_language_name(x)} ({x})",
            index=0,
            key="sidebar_source_lang"
        )
    except Exception:
        # fallback if SUPPORTED_LANGUAGES isn't well-formed
        source_lang_selected = st.selectbox("Source Language", options=["en"], format_func=lambda x: f"{x} ({x})", index=0, key="sidebar_source_lang")

    source_language = get_speech_language_code(source_lang_selected)

    # Target languages
    try:
        target_languages = st.multiselect(
            "Target Languages",
            options=[c for c in SUPPORTED_LANGUAGES if c != source_lang_selected],
            format_func=lambda x: f"{get_language_name(x)} ({x})",
            default=[],
            key="sidebar_target_langs"
        )
    except Exception:
        target_languages = st.multiselect("Target Languages", options=[], default=[], key="sidebar_target_langs")

    if not target_languages:
        st.warning("Please select at least one target language")

    st.divider()
    st.subheader("🔊 Voice Settings")
    st.session_state.voice_gender = st.radio(
        "Voice gender",
        options=["female", "male"],
        format_func=lambda x: "Female" if x == "female" else "Male",
        index=0,
        key="voice_gender_select",
        horizontal=True,
    )
    st.session_state.voice_rate = st.slider(
        "Speech speed (rate)",
        min_value=-50,
        max_value=50,
        value=0,
        help="Negative = slower, Positive = faster",
        key="voice_rate_slider"
    )
    st.session_state.voice_pitch = st.slider(
        "Pitch adjustment",
        min_value=-20,
        max_value=20,
        value=0,
        help="Negative = deeper, Positive = brighter",
        key="voice_pitch_slider"
    )

    st.divider()
    page = st.radio("Choose a page", ["🏠 Home", "🎤 Real-Time Pipeline", "📁 File Upload", "📺 YouTube URL", "📊 Results", "🧪 Test Components"], key="sidebar_page")


# --- Pages (kept behaviors from first file, UI from second) ---

if page == "🏠 Home":
    st.header("Welcome to Speech-to-Speech Translation")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        ### 🎤 Speech-to-Text
        - Real-time microphone input
        - File upload support
        - Multiple language support
        """)
    with col2:
        st.markdown("""
        ### 🌐 Translation
        - Multi-language translation
        - Azure Translator API
        - Retry logic for reliability
        """)
    with col3:
        st.markdown("""
        ### 🔊 Text-to-Speech
        - Neural voice synthesis
        - Multiple language voices
        - High-quality audio output
        """)
    st.divider()
    st.markdown("""
    ### 🚀 Quick Start
    
    1. **Real-Time Pipeline**: Go to "🎤 Real-Time Pipeline" to start live translation
    2. **File Upload**: Upload audio files in "📁 File Upload" for batch processing
    3. **Test Components**: Use "🧪 Test Components" to verify your setup
    
    ### 📝 Features
    
    - ✅ Real-time speech recognition
    - ✅ Multi-language translation
    - ✅ Text-to-speech synthesis
    - ✅ Batch file processing
    - ✅ Performance metrics
    - ✅ Error handling and retries
    """)

elif page == "🎤 Real-Time Pipeline":
    st.header("🎤 Real-Time Speech Recognition")

    if not target_languages:
        st.warning("⚠️ Please select at least one target language in the sidebar")
        st.info("💡 Go to the sidebar → Language Settings → Select Target Languages")
        st.stop()

    status_info = get_recognition_status()
    status_col1, status_col2, status_col3, status_col4 = st.columns(4)
    with status_col1:
        status_color = "🟢" if status_info["is_running"] else "🔴"
        st.metric("Recognition Status", f"{status_color} {status_info['status'].title()}")
    with status_col2:
        transcript_count = len(st.session_state.live_transcripts)
        st.metric("Transcripts", transcript_count)
    with status_col3:
        st.metric("Target Languages", len(target_languages))
    with status_col4:
        memory_usage = psutil.virtual_memory().percent
        st.metric("Memory Usage", f"{memory_usage:.1f}%")

    col1, col2, col3 = st.columns([1,1,1])
    with col1:
        if not status_info["is_running"]:
            if st.button("🟢 Start Recording", key="start_recording_btn", use_container_width=True):
                with st.spinner("Starting recognition process..."):
                    try:
                        output_dir = Path("temp_audio_output")
                        output_dir.mkdir(exist_ok=True, parents=True)
                        script_path = Path(__file__).parent / "scripts" / "live_recognition_helper.py"
                        log_path = output_dir / "live_recognition_streamlit.log"
                        if not script_path.exists():
                            st.error(f"❌ Recognition script not found: {script_path}")
                        else:
                            # open log file
                            log_fd = open(str(log_path), "a", buffering=1, encoding="utf-8", errors="ignore")
                            popen_args = [sys.executable, str(script_path), source_language]
                            popen_kwargs = {"cwd": str(Path(__file__).parent), "stdout": log_fd, "stderr": log_fd, "stdin": subprocess.DEVNULL, "close_fds": True}
                            if os.name=='nt':
                                popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
                            else:
                                popen_kwargs["start_new_session"] = True
                            process = subprocess.Popen(popen_args, **popen_kwargs)
                            process_file = output_dir / "recognition_process.pid"
                            startup_timeout = 10.0
                            poll_interval = 0.25
                            waited = 0.0
                            helper_started = False
                            while waited < startup_timeout:
                                if process.poll() is not None:
                                    log_fd.flush()
                                    log_fd.close()
                                    try:
                                        with open(log_path,'r',encoding='utf-8',errors='ignore') as lf:
                                            content = lf.read()[-2000:]
                                    except:
                                        content = "<could not read log>"
                                    st.error(f"❌ Recognition process exited prematurely. See logs:\n\n{content}")
                                    helper_started = False
                                    break
                                if process_file.exists():
                                    helper_started = True
                                    break
                                time.sleep(poll_interval)
                                waited += poll_interval
                            if helper_started:
                                st.session_state.live_recognition_running = True
                                st.session_state.live_transcripts = []
                                st.success("✅ Recording started! Speak into your microphone.")
                                try:
                                    log_fd.close()
                                except:
                                    pass
                                maybe_rerun()
                            else:
                                try:
                                    process.terminate()
                                except:
                                    pass
                                try:
                                    log_fd.flush()
                                    log_fd.close()
                                except:
                                    pass
                                st.error("❌ Failed to start recognition process within timeout. Check logs in temp_audio_output/")
                    except Exception as e:
                        st.error(f"❌ Error starting process: {str(e)}")
        else:
            if st.button("🔴 Stop Recording", key="stop_recording_btn", use_container_width=True):
                with st.spinner("Stopping recognition..."):
                    process_file = Path("temp_audio_output") / "recognition_process.pid"
                    status_file = Path("temp_audio_output") / "recognition_status.json"
                    killed = False
                    if process_file.exists():
                        try:
                            with open(process_file,'r') as f:
                                pid = int(f.read().strip())
                            try:
                                process_file.unlink()
                            except:
                                pass
                            if is_process_running(pid):
                                try:
                                    proc = psutil.Process(pid)
                                    proc.terminate()
                                    proc.wait(timeout=5)
                                    killed = True
                                except Exception:
                                    try:
                                        proc.kill()
                                        killed = True
                                    except Exception:
                                        killed = False
                        except Exception:
                            try:
                                if process_file.exists():
                                    process_file.unlink()
                            except:
                                pass
                    try:
                        if status_file.exists():
                            status_file.unlink()
                    except:
                        pass
                    st.session_state.live_recognition_running = False
                    if killed:
                        st.success("✅ Recording stopped.")
                    else:
                        st.warning("⚠️ Recording stop requested. Process may still be running; check process list or logs.")
                    maybe_rerun()

    with col2:
        if st.button("🔄 Refresh", key="refresh_btn", use_container_width=True):
            maybe_rerun()

    with col3:
        if st.button("🗑️ Clear Transcripts", key="clear_transcripts_btn", use_container_width=True):
            st.session_state.live_transcripts = []
            transcript_file = Path("temp_audio_output") / "live_transcripts.json"
            try:
                if transcript_file.exists():
                    transcript_file.unlink()
            except:
                pass
            st.success("✅ Transcripts cleared.")
            maybe_rerun()

    # Banner
    if status_info["is_running"]:
        if status_info["error"]:
            st.error(f"❌ Error: {status_info['error']}")
        else:
            st.markdown("""<div style='background:linear-gradient(135deg,#00b09b 0%,#96c93d 100%);padding:1rem;border-radius:10px;color:white;text-align:center;margin:1rem 0;'><strong>🎤 LIVE - Recording Active - Speak Now!</strong></div>""", unsafe_allow_html=True)
    else:
        st.info("🔴 Recording stopped. Click 'Start Recording' to begin.")

    # Auto-refresh transcripts (kept from first)
    if status_info["is_running"]:
        if time.time() - st.session_state.last_refresh > 2.0:
            st.session_state.last_refresh = time.time()
            transcript_file = Path("temp_audio_output") / "live_transcripts.json"
            if transcript_file.exists():
                try:
                    with open(transcript_file,'r',encoding='utf-8') as f:
                        content = f.read().strip()
                        if content:
                            file_transcripts = json.loads(content)
                            current_ids = {t['id'] for t in st.session_state.live_transcripts}
                            new_transcripts = [t for t in file_transcripts if t['id'] not in current_ids]
                            if new_transcripts:
                                st.session_state.live_transcripts.extend(new_transcripts)
                                maybe_rerun()
                except Exception as e:
                    st.caption(f"⚠️ Error reading transcripts: {str(e)[:100]}")
        time_since_refresh = time.time() - st.session_state.last_refresh
        st.caption(f"🔄 Auto-refreshing in {max(0.0,2.0 - time_since_refresh):.1f}s...")

    st.subheader("📝 Live Transcripts")
    if st.session_state.live_transcripts:
        st.info(f"📊 Found {len(st.session_state.live_transcripts)} transcript(s)")
        for transcript in reversed(st.session_state.live_transcripts[-10:]):
            with st.container():
                c1,c2 = st.columns([4,1])
                with c1:
                    st.markdown(f"<div class='transcript-card'><p style='margin:0;font-size:1.1rem;color:#333;'><strong>{transcript['text']}</strong></p><p style='margin:0;font-size:0.8rem;color:#666;'>{time.strftime('%H:%M:%S', time.localtime(transcript['timestamp']))}</p></div>", unsafe_allow_html=True)
                with c2:
                    if st.button("🌐 Translate", key=f"translate_btn_{transcript['id']}", use_container_width=True):
                        with st.spinner("Translating..."):
                            translation_result = translate_with_retry(transcript['text'], target_languages=target_languages, source_language=source_lang_selected)
                            if translation_result["success"]:
                                st.success("✅ Translation completed!")
                                st.session_state.last_translation_result = {"transcript_id": transcript['id'], "translations": translation_result["translations"], "original_text": transcript['text']}
                                maybe_rerun()
                            else:
                                st.error(f"❌ Translation failed: {translation_result.get('error','Unknown error')}")
            # show translations if available
            if st.session_state.get('last_translation_result') and st.session_state.last_translation_result.get('transcript_id') == transcript['id']:
                translations_for_this = st.session_state.last_translation_result.get('translations', {})
                with st.expander("View Translations", expanded=False):
                    for lang in target_languages:
                        trans_text = translations_for_this.get(lang)
                        if not trans_text:
                            st.info(f"No translation for {get_language_name(lang)}")
                            continue
                        st.markdown(f"**{get_language_name(lang)}:**")
                        st.write(trans_text)
                        existing_audio = next((af for af in st.session_state.audio_files if af.get('transcript_id') == transcript['id'] and af.get('language') == lang), None)
                        if existing_audio and os.path.exists(existing_audio.get('file','')):
                            st.audio(existing_audio['file'])
                            st.download_button(f"📥 Download {lang.upper()}", data=open(existing_audio['file'],'rb').read(), file_name=f"translation_{transcript['id']}_{lang}.wav", mime="audio/wav", key=f"download_{transcript['id']}_{lang}")
                        else:
                            if st.button(f"🔊 Generate {lang.upper()} Audio", key=f"generate_tts_{transcript['id']}_{lang}", use_container_width=True):
                                with st.spinner(f"Generating {get_language_name(lang)} audio..."):
                                    tts_result = generate_tts_audio(
                                        trans_text,
                                        lang,
                                        transcript['id'],
                                        voice_gender=st.session_state.voice_gender,
                                        rate_percent=st.session_state.voice_rate,
                                        pitch_percent=st.session_state.voice_pitch,
                                    )
                                    if tts_result["success"] and os.path.exists(tts_result["file_path"]):
                                        st.success("✅ Audio generated!")
                                        st.session_state.audio_files.append({"transcript_id": transcript['id'], "language": lang, "file": tts_result["file_path"], "text": trans_text, "original_text": transcript['text']})
                                        st.audio(tts_result["file_path"])
                                        st.download_button(f"📥 Download {lang.upper()}", data=open(tts_result["file_path"],'rb').read(), file_name=f"translation_{transcript['id']}_{lang}.wav", mime="audio/wav", key=f"dl_{transcript['id']}_{lang}")
                                        maybe_rerun()
                                    else:
                                        st.error(f"❌ TTS failed: {tts_result.get('error','Unknown error')}")
    else:
        st.info("🎤 No transcripts yet. Start recording and speak into your microphone.")

    with st.expander("🔍 Debug Information"):
        d1,d2 = st.columns(2)
        with d1:
            st.write("**File Status:**")
            st.write(f"- Process File: {Path('temp_audio_output/recognition_process.pid').exists()}")
            st.write(f"- Transcript File: {Path('temp_audio_output/live_transcripts.json').exists()}")
            st.write(f"- Status File: {Path('temp_audio_output/recognition_status.json').exists()}")
        with d2:
            st.write("**Session State:**")
            st.write(f"- Live Recognition Running: {st.session_state.live_recognition_running}")
            st.write(f"- Transcript Count: {len(st.session_state.live_transcripts)}")

elif page == "📁 File Upload":
    st.header("Upload Audio File")
    uploaded_file = st.file_uploader("Choose an audio file", type=['wav','mp3','m4a','mp4'], key="file_upload_input")
    if uploaded_file:
        st.audio(uploaded_file, format='audio/wav')
        if st.button("🚀 Process File", type="primary", key="process_file_btn"):
            with st.spinner("Processing audio file..."):
                transcript_result = transcribe_audio_file(uploaded_file, source_language)
                if transcript_result["success"]:
                    transcript_text = transcript_result["text"]
                    if target_languages:
                        translation_result = translate_with_retry(transcript_text, target_languages=target_languages, source_language=source_lang_selected)
                        if translation_result["success"]:
                            transcript_id = f"file_{int(time.time())}"
                            st.session_state.file_upload_results = {"transcript_text": transcript_text, "translation_result": translation_result, "transcript_id": transcript_id, "uploaded_file_name": uploaded_file.name}
                            st.session_state.last_translation_result = st.session_state.file_upload_results
                            st.success("✅ Processing completed! Scroll down to see translations and generate audio.")
                            maybe_rerun()
                        else:
                            st.error(f"❌ Translation failed: {translation_result.get('error','Unknown error')}")
                    else:
                        st.warning("⚠️ Please select target languages in the sidebar")
                else:
                    st.error(f"❌ Transcription failed: {transcript_result.get('error','Unknown error')}")
    if st.session_state.file_upload_results:
        res = st.session_state.file_upload_results
        st.divider()
        st.subheader("📝 Transcription Result")
        st.success(f"✅ Transcribed: {res['transcript_text']}")
        if res['translation_result']["success"]:
            st.subheader("🌐 Translation Results")
            st.success("✅ Translation completed!")
            st.subheader("🔊 Generate Audio Files")
            cols = st.columns(min(len(target_languages),3) or 1)
            for idx, lang in enumerate(target_languages):
                with cols[idx % 3]:
                    lang_name = get_language_name(lang)
                    st.markdown(f"**{lang_name} ({lang.upper()})**")
                    translated_text = res['translation_result']["translations"].get(lang,"")
                    if translated_text:
                        st.text_area("", translated_text, height=120, key=f"trans_display_file_{lang}", disabled=True, label_visibility="collapsed")
                        existing_audio = next((af for af in st.session_state.audio_files if af.get('transcript_id') == res['transcript_id'] and af.get('language') == lang), None)
                        if existing_audio and os.path.exists(existing_audio.get('file','')):
                            st.audio(existing_audio['file'])
                            st.download_button(f"📥 Download {lang.upper()}", data=open(existing_audio['file'],'rb').read(), file_name=f"translation_{res['transcript_id']}_{lang}.wav", mime="audio/wav", key=f"download_file_{res['transcript_id']}_{lang}")
                        else:
                            if st.button(f"🔊 Generate {lang.upper()} Audio", key=f"generate_file_tts_{res['transcript_id']}_{lang}", use_container_width=True):
                                with st.spinner(f"Generating {lang_name} audio..."):
                                    tts_result = generate_tts_audio(
                                        translated_text,
                                        lang,
                                        res['transcript_id'],
                                        voice_gender=st.session_state.voice_gender,
                                        rate_percent=st.session_state.voice_rate,
                                        pitch_percent=st.session_state.voice_pitch,
                                    )
                                    if tts_result["success"] and os.path.exists(tts_result["file_path"]):
                                        st.success(f"✅ {lang_name} audio generated!")
                                        st.session_state.audio_files.append({"transcript_id": res['transcript_id'], "language": lang, "file": tts_result["file_path"], "text": translated_text, "original_text": res['transcript_text']})
                                        st.audio(tts_result["file_path"])
                                        st.download_button(f"📥 Download {lang.upper()}", data=open(tts_result["file_path"],'rb').read(), file_name=f"translation_{res['transcript_id']}_{lang}.wav", mime="audio/wav", key=f"dl_file_{res['transcript_id']}_{lang}")
                                        maybe_rerun()
                                    else:
                                        st.error(f"❌ {tts_result.get('error','Unknown error')}")
                    else:
                        st.info("No translation available")
            if st.button("🗑️ Clear Results", key="clear_upload_results_btn"):
                st.session_state.file_upload_results = None
                st.session_state.last_translation_result = None
                maybe_rerun()

elif page == "📺 YouTube URL":
    st.header("YouTube URL → Translate & Voice")
    st.caption("Paste a YouTube link, we will pull the audio, transcribe it, translate, and generate voice with your selected settings.")

    yt_url = st.text_input("Paste YouTube link", key="yt_url_input", placeholder="https://www.youtube.com/watch?v=...")
    col_dl, col_clear = st.columns([2,1])
    with col_dl:
        if st.button("🚀 Fetch & Translate", type="primary", key="yt_process_btn"):
            if not yt_url:
                st.warning("Please paste a valid YouTube URL.")
            elif not target_languages:
                st.warning("Please select target languages in the sidebar first.")
            else:
                with st.spinner("Downloading audio and processing..."):
                    yt_result = process_youtube_url(yt_url, source_language, target_languages)
                    if yt_result["success"]:
                        st.session_state.youtube_results = yt_result
                        st.session_state.last_translation_result = yt_result
                        st.success("✅ YouTube audio processed!")
                        maybe_rerun()
                    else:
                        st.error(f"❌ {yt_result.get('error','Failed to process YouTube URL')}")
    with col_clear:
        if st.button("🗑️ Clear", key="yt_clear_btn"):
            st.session_state.youtube_results = None
            st.session_state.last_translation_result = None
            st.experimental_set_query_params()  # clean state in browser
            st.info("Cleared YouTube results.")

    st.divider()
    st.subheader("🔎 Search YouTube")
    search_query = st.text_input("Search keyword or phrase", key="yt_search_query", placeholder="e.g., technology news in English")
    if st.button("🔍 Search", key="yt_search_btn"):
        if not search_query.strip():
            st.warning("Enter a keyword to search.")
        else:
            with st.spinner("Searching YouTube..."):
                try:
                    search = Search(search_query)
                    results = search.results[:6] if search.results else []
                    st.session_state.yt_search_results = [
                        {
                            "title": v.title,
                            "url": v.watch_url,
                            "length": v.length,
                        }
                        for v in results
                    ]
                    if not st.session_state.yt_search_results:
                        st.info("No results found. Try a different query.")
                except Exception as e:
                    st.error(f"❌ Search failed: {e}")

    if st.session_state.yt_search_results:
        st.markdown("**Select a result and press Fetch & Translate**")
        options = [f"{r['title']} ({int(r['length']//60)}m {int(r['length']%60)}s)" for r in st.session_state.yt_search_results]
        urls = [r['url'] for r in st.session_state.yt_search_results]
        selected_idx = st.selectbox("Search results", options=list(range(len(options))), format_func=lambda i: options[i], key="yt_search_select")
        if st.button("Use Selected Result", key="yt_use_selected_btn"):
            st.session_state.yt_url_input = urls[selected_idx]
            st.experimental_set_query_params()  # force UI refresh
            maybe_rerun()

    yt_data = st.session_state.youtube_results
    if yt_data:
        st.divider()
        st.subheader("🖥️ Video Info")
        info_cols = st.columns(3)
        info_cols[0].metric("Title", yt_data.get("video_title", ""))
        info_cols[1].metric("Length", f"{int(yt_data.get('video_length',0)//60)}m {int(yt_data.get('video_length',0)%60)}s")
        info_cols[2].metric("Source", "YouTube")
        if yt_data.get("video_file") and os.path.exists(yt_data["video_file"]):
            st.video(yt_data["video_file"])

        st.subheader("📝 Transcript")
        st.success(yt_data.get("transcript_text",""))

        if yt_data.get("translation_result", {}).get("success"):
            st.subheader("🌐 Translation Results")
            cols = st.columns(min(len(target_languages),3) or 1)
            for idx, lang in enumerate(target_languages):
                with cols[idx % 3]:
                    lang_name = get_language_name(lang)
                    st.markdown(f"**{lang_name} ({lang.upper()})**")
                    translated_text = yt_data["translation_result"]["translations"].get(lang,"")
                    if translated_text:
                        st.text_area("", translated_text, height=140, key=f"yt_trans_display_{lang}", disabled=True, label_visibility="collapsed")
                        existing_audio = next((af for af in st.session_state.audio_files if af.get('transcript_id') == yt_data['transcript_id'] and af.get('language') == lang), None)
                        if existing_audio and os.path.exists(existing_audio.get('file','')):
                            st.audio(existing_audio['file'])
                            st.download_button(f"📥 Download {lang.upper()}", data=open(existing_audio['file'],'rb').read(), file_name=f"yt_translation_{yt_data['transcript_id']}_{lang}.wav", mime="audio/wav", key=f"yt_download_{yt_data['transcript_id']}_{lang}")
                        else:
                            if st.button(f"🔊 Generate {lang.upper()} Audio", key=f"yt_generate_tts_{yt_data['transcript_id']}_{lang}", use_container_width=True):
                                with st.spinner(f"Generating {lang_name} voice..."):
                                    tts_result = generate_tts_audio(
                                        translated_text,
                                        lang,
                                        yt_data['transcript_id'],
                                        voice_gender=st.session_state.voice_gender,
                                        rate_percent=st.session_state.voice_rate,
                                        pitch_percent=st.session_state.voice_pitch,
                                    )
                                    if tts_result["success"] and os.path.exists(tts_result["file_path"]):
                                        st.success(f"✅ {lang_name} audio ready!")
                                        new_audio = {"transcript_id": yt_data['transcript_id'], "language": lang, "file": tts_result["file_path"], "text": translated_text, "original_text": yt_data['transcript_text']}
                                        st.session_state.audio_files.append(new_audio)
                                        existing_audio = new_audio
                                        st.audio(tts_result["file_path"])
                                        st.download_button(f"📥 Download {lang.upper()}", data=open(tts_result["file_path"],'rb').read(), file_name=f"yt_translation_{yt_data['transcript_id']}_{lang}.wav", mime="audio/wav", key=f"yt_dl_{yt_data['transcript_id']}_{lang}")
                                    else:
                                        st.error(f"❌ {tts_result.get('error','Unknown error')}")
                        if existing_audio and os.path.exists(existing_audio.get('file','')) and yt_data.get("video_file"):
                            if st.button(f"🎬 Render video with {lang.upper()} audio", key=f"yt_render_video_{yt_data['transcript_id']}_{lang}", use_container_width=True):
                                with st.spinner("Muxing video and audio..."):
                                    mux_result = mux_video_with_audio(Path(yt_data["video_file"]), Path(existing_audio['file']), yt_data['transcript_id'], lang)
                                    if mux_result["success"] and os.path.exists(mux_result["file_path"]):
                                        st.success("✅ Dubbed video ready!")
                                        st.session_state.video_outputs.append({
                                            "transcript_id": yt_data["transcript_id"],
                                            "language": lang,
                                            "file": str(mux_result["file_path"]),
                                            "source_url": yt_data.get("url"),
                                            "title": yt_data.get("video_title"),
                                        })
                                        st.video(str(mux_result["file_path"]))
                                        st.download_button(
                                            f"📥 Download Dubbed ({lang.upper()})",
                                            data=open(mux_result["file_path"], 'rb').read(),
                                            file_name=f"dub_{yt_data['transcript_id']}_{lang}.mp4",
                                            mime="video/mp4",
                                            key=f"yt_dub_download_{yt_data['transcript_id']}_{lang}"
                                        )
                                    else:
                                        st.error(f"❌ {mux_result.get('error','Mux failed')}")
                    else:
                        st.info("No translation available")

elif page == "📊 Results":
    st.header("Results & History")
    if st.session_state.audio_files:
        st.subheader("Generated Audio Files")
        for idx, audio_data in enumerate(st.session_state.audio_files):
            with st.expander(f"Audio {idx+1} - {audio_data['language'].upper()}"):
                st.text(f"Original: {audio_data.get('original_text','N/A')}")
                st.text(f"Translated: {audio_data['text']}")
                if os.path.exists(audio_data['file']):
                    st.audio(audio_data['file'])
                    st.download_button("📥 Download Audio", data=open(audio_data['file'],'rb').read(), file_name=f"translation_{audio_data['language']}_{idx}.wav", mime="audio/wav", key=f"results_download_{idx}")
                else:
                    st.warning("Audio file not found")
        if st.button("🗑️ Clear History", key="clear_history_btn"):
            st.session_state.audio_files = []
            maybe_rerun()
    else:
        st.info("No results yet. Process some files to see results here.")

    st.divider()
    if st.session_state.video_outputs:
        st.subheader("Dubbed Videos")
        for idx, vdata in enumerate(st.session_state.video_outputs):
            with st.expander(f"Video {idx+1} - {vdata.get('language','').upper()}"):
                st.text(f"Title: {vdata.get('title','')}")
                st.text(f"Source: {vdata.get('source_url','')}")
                if os.path.exists(vdata.get("file","")):
                    st.video(vdata["file"])
                    st.download_button(
                        "📥 Download Dubbed Video",
                        data=open(vdata["file"], 'rb').read(),
                        file_name=f"{Path(vdata['file']).name}",
                        mime="video/mp4",
                        key=f"results_video_download_{idx}"
                    )
                else:
                    st.warning("Video file not found")
        if st.button("🗑️ Clear Videos", key="clear_videos_btn"):
            st.session_state.video_outputs = []
            maybe_rerun()

elif page == "🧪 Test Components":
    st.header("Test Pipeline Components")
    st.subheader("🌐 Test Translation")
    test_text = st.text_input("Enter text to translate", value="Hello, how are you today?", key="test_translate_input")
    if st.button("Test Translation", key="test_translate_btn"):
        if test_text and target_languages:
            with st.spinner("Translating..."):
                result = translate_text(test_text, target_languages=target_languages)
                if result["success"]:
                    st.success("✅ Translation successful!")
                    st.markdown("**Original Text:**")
                    st.write(result["original_text"])
                    st.markdown("**Translations:**")
                    for lang, trans in result["translations"].items():
                        st.markdown(f"**{lang.upper()}**: {trans}")
                else:
                    st.error(f"❌ Translation failed: {result.get('error','Unknown error')}")
        else:
            st.warning("Please enter text and select target languages")
    st.divider()
    st.subheader("🎤 Test Speech-to-Text")
    st.info("Upload an audio file to test transcription")
    test_audio = st.file_uploader("Upload test audio", type=['wav','mp3'], key="test_stt_audio")
    if test_audio and st.button("Test STT", key="test_stt_btn"):
        with st.spinner("Transcribing..."):
            result = transcribe_audio_file(test_audio, source_language)
            if result["success"]:
                st.success("✅ Transcription successful!")
                st.write(f"**Transcribed Text:** {result['text']}")
            else:
                st.error(f"❌ Transcription failed: {result.get('error','Unknown error')}")
    st.divider()
    st.subheader("🔊 Test Text-to-Speech")
    tts_test_text = st.text_input("Enter text for TTS", value="Hello, this is a test of text to speech.", key="test_tts_input")
    tts_test_lang = st.selectbox("Select language", options=SUPPORTED_LANGUAGES, format_func=lambda x: f"{get_language_name(x)} ({x})", index=0, key="test_tts_lang")
    if st.button("Test TTS", key="test_tts_btn") and tts_test_text:
        with st.spinner("Generating audio..."):
            test_id = f"test_{int(time.time())}"
            result = generate_tts_audio(
                tts_test_text,
                tts_test_lang,
                test_id,
                voice_gender=st.session_state.voice_gender,
                rate_percent=st.session_state.voice_rate,
                pitch_percent=st.session_state.voice_pitch,
            )
            if result["success"] and os.path.exists(result["file_path"]):
                st.success("✅ Audio generated!")
                st.audio(result["file_path"])
            else:
                st.error(f"❌ TTS failed: {result.get('error','Unknown error')}")

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem;'>
    <p>Built with ❤️ using Azure Cognitive Services</p>
    <p>Speech-to-Speech Translation Pipeline</p>
</div>
""", unsafe_allow_html=True)
