import streamlit as st
import yt_dlp
import os
from pathlib import Path
from transcribe_files import transcribe_file
from translator import translate_with_retry

st.set_page_config(page_title="YouTube Speech Translation", page_icon="📺")

st.title("📺 YouTube Speech Translation")
st.write("Enter any YouTube video link. The system will extract audio → run STT → translate into 12+ languages.")

BASE_DIR = Path(__file__).resolve().parents[1]
TEMP_DIR = BASE_DIR / "temp_youtube"
TEMP_DIR.mkdir(exist_ok=True)

import azure.cognitiveservices.speech as speechsdk
from language_config import get_tts_voice

def synthesize_speech(text, lang_code):
    try:
        speech_key = os.getenv("AZURE_SPEECH_KEY")
        region = os.getenv("AZURE_REGION")

        speech_config = speechsdk.SpeechConfig(
            subscription=speech_key,
            region=region
        )

        # Pick correct Azure neural voice
        voice_name = get_tts_voice(lang_code)
        speech_config.speech_synthesis_voice_name = voice_name

        # Save output to memory stream
        audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=False)
        synthesizer = speechsdk.SpeechSynthesizer(speech_config, audio_config)

        result = synthesizer.speak_text_async(text).get()

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return result.audio_data
        else:
            return None

    except Exception as e:
        return None

# -------------------- YOUTUBE URL INPUT --------------------
url = st.text_input("🔗 Enter YouTube URL")

if st.button("🎬 Process Video"):
    if not url.strip():
        st.error("Please enter a YouTube URL.")
        st.stop()

    st.info("Downloading audio from YouTube… please wait.")

    audio_path = TEMP_DIR / "video_audio.wav"

    # -------------------- YT-DLP DOWNLOAD --------------------
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": str(TEMP_DIR / "downloaded"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "wav",
            "preferredquality": "192"
        }]
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Find audio file
        for f in TEMP_DIR.glob("*.wav"):
            audio_path = f
            break

        st.success("Audio extracted successfully!")
        st.audio(str(audio_path))

    except Exception as e:
        st.error(f"YouTube download failed: {e}")
        st.stop()

    # -------------------- STT --------------------
    st.info("Running Speech-to-Text…")

    transcript = transcribe_file(str(audio_path))

    if not transcript or transcript.startswith("["):
        st.error(f"STT failed: {transcript}")
        st.stop()

    st.success("Transcription complete!")
    st.write("### 📝 Transcript")
    st.write(transcript)

    # -------------------- TRANSLATION --------------------
    st.info("Translating transcript into all languages…")

    result = translate_with_retry(transcript)

    if not result["success"]:
        st.error("Translation failed.")
        st.write(result["error"])
        st.stop()

    st.success("Translations ready!")

    st.write("### 🔊 Listen to Translations")

    for lang, text in result["translations"].items():
        st.markdown(f"**🌐 {lang}:** {text}")

        if st.button(f"▶ Speak {lang}", key=f"tts_{lang}"):
            audio_bytes = synthesize_speech(text, lang)

            if audio_bytes:
                st.audio(audio_bytes, format="audio/wav")
            else:
                st.error(f"TTS failed for {lang}.")




