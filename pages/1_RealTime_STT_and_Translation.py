# pages/1_RealTime_STT_and_Translation.py

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import List, Dict

import streamlit as st
from dotenv import load_dotenv

import azure.cognitiveservices.speech as speechsdk

# Import your helper modules from scripts/
BASE_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = BASE_DIR / "scripts"
sys.path.append(str(SCRIPTS_DIR))  # allow importing scripts as modules

from language_config import (
    LANGUAGE_NAMES,
    SUPPORTED_LANGUAGES,
    DEFAULT_TARGET_LANGUAGES,
    get_speech_language_code,
    get_language_name,
    get_tts_voice,
)
from translator import translate_with_retry

load_dotenv()

TEMP_DIR = BASE_DIR / "temp_audio_output"
TRANSCRIPT_FILE = TEMP_DIR / "live_transcripts.json"
PARTIAL_FILE = TEMP_DIR / "partial_transcript.txt"
PROCESS_FILE = TEMP_DIR / "recognition_process.pid"
LOG_FILE = TEMP_DIR / "live_recognition.log"
TTS_OUTPUT_DIR = BASE_DIR / "tts_output"
TTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

st.set_page_config(page_title="Real-Time STT & Translation", page_icon="🎤", layout="wide")

st.title("🎤 Real-Time STT + 🌐 Translation")
st.caption("Listen via microphone, capture transcripts, translate them, and generate speech audio.")

# ---- Helper functions -------------------------------------------------------


def is_stt_process_running() -> bool:
    """Check if the live recognition helper process is running via PID file."""
    return PROCESS_FILE.exists()


def start_stt_process(source_language_code: str):
    """Start live_recognition_helper.py as a separate process."""
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    cmd = [sys.executable, str(SCRIPTS_DIR / "live_recognition_helper.py"), source_language_code]
    # Use subprocess without blocking
    try:
        subprocess.Popen(cmd, cwd=str(SCRIPTS_DIR))
    except Exception as e:
        st.error(f"Failed to start live recognition process: {e}")


def stop_stt_process():
    """Signal helper process to stop by removing the PID file."""
    try:
        if PROCESS_FILE.exists():
            PROCESS_FILE.unlink()
    except Exception as e:
        st.warning(f"Error while trying to stop STT process: {e}")


def load_live_transcripts() -> List[Dict]:
    """Load all saved transcripts from JSON file."""
    if not TRANSCRIPT_FILE.exists():
        return []
    try:
        with open(TRANSCRIPT_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except Exception:
        return []


def load_partial_transcript() -> str:
    """Read current partial transcript (if any)."""
    if not PARTIAL_FILE.exists():
        return ""
    try:
        return PARTIAL_FILE.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def synthesize_speech(text: str, lang_code: str, gender: str = "female") -> Path:
    """
    Use Azure TTS to synthesize speech to a WAV file for the given language code.
    Returns path to the generated audio file.
    """
    speech_key = os.getenv("AZURE_SPEECH_KEY")
    speech_region = os.getenv("AZURE_REGION")
    if not speech_key or not speech_region:
        raise RuntimeError("Missing Azure Speech credentials")

    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)

    # Map 2-letter language to Azure voice name using your language_config helper
    voice_name = get_tts_voice(lang_code, gender=gender)
    speech_config.speech_synthesis_voice_name = voice_name

    TTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    safe_lang = lang_code.replace("-", "_")
    audio_file = TTS_OUTPUT_DIR / f"tts_{safe_lang}.wav"

    audio_config = speechsdk.audio.AudioOutputConfig(filename=str(audio_file))
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    result = synthesizer.speak_text_async(text).get()
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        return audio_file
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation = speechsdk.CancellationDetails(result)
        raise RuntimeError(f"TTS canceled: {cancellation.reason} ({cancellation.error_details})")
    else:
        raise RuntimeError(f"TTS failed with reason: {result.reason}")


# ---- Session state ----------------------------------------------------------

if "current_text" not in st.session_state:
    st.session_state.current_text = ""

if "last_source_lang" not in st.session_state:
    st.session_state.last_source_lang = "en"

# ---- Layout -----------------------------------------------------------------

top_col1, top_col2 = st.columns([2, 1])

with top_col1:
    st.subheader("🎧 Live Microphone Capture")

    source_lang_short = st.selectbox(
        "Source language (for speech recognition)",
        options=SUPPORTED_LANGUAGES,
        format_func=lambda code: f"{LANGUAGE_NAMES[code]} ({code})",
        index=SUPPORTED_LANGUAGES.index("en") if "en" in SUPPORTED_LANGUAGES else 0,
        key="source_lang_short",
    )
    st.session_state.last_source_lang = source_lang_short
    source_language_code = get_speech_language_code(source_lang_short)

    st.write(f"Azure STT language code: `{source_language_code}`")

    st.markdown("---")

    stt_col1, stt_col2 = st.columns(2)
    with stt_col1:
        if not is_stt_process_running():
            if st.button("▶️ Start Listening"):
                start_stt_process(source_language_code)
                st.success("Live recognition started. Speak into your microphone.")
        else:
            st.info("Live recognition is currently **running**.")

    with stt_col2:
        if is_stt_process_running():
            if st.button("⏹️ Stop Listening"):
                stop_stt_process()
                st.success("Requested live recognition to stop.")
        else:
            st.caption("Start listening to enable live speech recognition.")

    st.markdown("---")

    partial = load_partial_transcript()
    if partial:
        st.markdown("**📝 Live partial transcript:**")
        st.info(partial)
    else:
        st.caption("No partial transcript yet.")

with top_col2:
    st.subheader("🗂 Live Transcript History")

    transcripts = load_live_transcripts()
    if transcripts:
        last_n = transcripts[-10:]  # show last 10
        for item in reversed(last_n):
            st.markdown(
                f"- `{item.get('language', '')}` · "
                f"{item.get('text', '')}"
            )
        last_text = transcripts[-1].get("text", "")
        if last_text and not st.session_state.current_text:
            st.session_state.current_text = last_text
    else:
        st.caption("No transcripts recorded yet. Start listening to capture speech.")

st.markdown("---")

# ---- Translation & TTS section ----------------------------------------------

st.subheader("🌐 Translate & 🔊 Speak")

col_text, col_settings = st.columns([2, 1])

with col_text:
    st.markdown("**Input text** (pre-filled from last transcript if available):")
    st.session_state.current_text = st.text_area(
        "",
        value=st.session_state.current_text,
        height=150,
        key="text_input_area",
    )

with col_settings:
    st.markdown("**Translation settings**")

    target_langs = st.multiselect(
        "Target languages",
        options=SUPPORTED_LANGUAGES,
        default=[code for code in DEFAULT_TARGET_LANGUAGES if code in SUPPORTED_LANGUAGES][:4],
        format_func=lambda code: f"{get_language_name(code)} ({code})",
    )

    tts_gender = st.radio(
        "Preferred TTS voice gender",
        options=["female", "male"],
        index=0,
        horizontal=True,
    )

    st.caption("You can pick multiple target languages. TTS will use Azure Neural voices for each.")

st.markdown("---")

if st.button("🚀 Translate & Generate Speech"):
    text = (st.session_state.current_text or "").strip()
    if not text:
        st.error("Please provide some text to translate.")
    elif not target_langs:
        st.error("Please choose at least one target language.")
    else:
        with st.spinner("Translating..."):
            # Use source language’s base code (e.g., en-US -> en)
            src_lang_code = st.session_state.last_source_lang
            result = translate_with_retry(
                text,
                target_languages=target_langs,
                source_language=src_lang_code,
            )

        if not result["success"]:
            st.error(f"Translation failed: {result['error']}")
        else:
            st.success("Translation successful!")

            st.markdown("### 📝 Original text")
            st.info(result["original_text"])

            st.markdown("### 🌍 Translations")
            for lang_code, translated in result["translations"].items():
                lang_name = get_language_name(lang_code)
                with st.expander(f"{lang_name} ({lang_code})"):
                    st.write(translated)
                    try:
                        with st.spinner(f"Generating TTS for {lang_name}..."):
                            audio_path = synthesize_speech(translated, lang_code, gender=tts_gender)
                        audio_bytes = audio_path.read_bytes()
                        st.audio(audio_bytes, format="audio/wav")
                    except Exception as e:
                        st.warning(f"TTS error for {lang_code}: {e}")
