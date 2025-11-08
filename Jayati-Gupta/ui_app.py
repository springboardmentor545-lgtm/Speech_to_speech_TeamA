import streamlit as st
import tempfile, os
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

from scripts.stt_helper_file import speech_to_text
from scripts.translate_helper import translate_text
from scripts.tts_helper import synthesize_speech

# Load env
load_dotenv()
SPEECH_KEY = os.getenv("SPEECH_KEY") or os.getenv("AZURE_SPEECH_KEY")
SERVICE_REGION = os.getenv("SERVICE_REGION") or os.getenv("AZURE_REGION")

# Page settings
st.set_page_config(page_title="Speech Translator", page_icon="🎤", layout="centered")

# Custom CSS 👇 for clean UI
st.markdown("""
<style>
    .main {background-color:#fafafa;}
    .stButton>button {
        border-radius: 10px;
        font-size: 15px;
        padding: 0.6rem 1.2rem;
    }
    .upload-box {padding: 10px; background: #ffffff; border-radius: 10px; border: 1px solid #ddd;}
    .result-box {background:#ffffff;padding:10px;border-radius:10px;border:1px solid #ddd;}
</style>
""", unsafe_allow_html=True)

# Title
st.markdown("<h2 style='text-align:center;'>🎤 Real-Time AI Speech Translator</h2>", unsafe_allow_html=True)
st.caption("Powered by Azure Speech Services")

# Language Options
LANGUAGE_MAP = {
    "Hindi": ("hi", "hi-IN-SwaraNeural"),
    "French": ("fr", "fr-FR-DeniseNeural"),
    "Spanish": ("es", "es-ES-ElviraNeural"),
    "German": ("de", "de-DE-KatjaNeural"),
    "Tamil": ("ta", "ta-IN-PallaviNeural"),
    "Telugu": ("te", "te-IN-ShrutiNeural"),
    "Marathi": ("mr", "mr-IN-AarohiNeural"),
    "Bengali": ("bn", "bn-IN-TanishaaNeural"),
    "Gujarati": ("gu", "gu-IN-NiranjanNeural"),
    "Punjabi": ("pa", "pa-IN-AmritNeural"),
    "Kannada": ("kn", "kn-IN-SapnaNeural"),
    "Malayalam": ("ml", "ml-IN-SobhanaNeural"),
}

with st.sidebar:
    st.header("⚙️ Settings")
    target_lang = st.selectbox("Target Language", list(LANGUAGE_MAP.keys()))
    st.info("🎙️ Speak or upload to translate.\n\n🌍 Powered by Microsoft Azure")

# Session text variable
if "recognized_text" not in st.session_state:
    st.session_state.recognized_text = ""

# Input options
st.markdown("#### 🎙️ Input Method")

col1, col2 = st.columns(2)

with col1:
    mic_btn = st.button("🎤 Speak Now")

with col2:
    st.markdown("<div class='upload-box'>", unsafe_allow_html=True)
    file = st.file_uploader("Upload WAV", type=["wav"], label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)

# Microphone STT
if mic_btn:
    if not SPEECH_KEY:
        st.error("❌ Azure keys missing in .env")
    else:
        st.info("🎧 Listening...")
        speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SERVICE_REGION)
        audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
        recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
        result = recognizer.recognize_once_async().get()

        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            st.session_state.recognized_text = result.text
            st.success("✅ Voice captured successfully!")
        else:
            st.warning("⚠️ No speech detected")

# File Upload STT
if file:
    st.audio(file)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp:
        temp.write(file.read())
        temp_path = temp.name
    with st.spinner("🎧 Transcribing audio..."):
        st.session_state.recognized_text = speech_to_text(temp_path)
    st.success("✅ Audio transcribed!")

# Display recognized text
if st.session_state.recognized_text:
    st.markdown("#### 📝 Recognized Text")
    st.text_area("", st.session_state.recognized_text, height=90)

    tgt_code, voice = LANGUAGE_MAP[target_lang]

    if st.button(f"🌐 Translate → {target_lang}"):
        with st.spinner("🔄 Translating..."):
            translated_text = translate_text(st.session_state.recognized_text, tgt_code)

        st.markdown("#### 🌍 Translated Text")
        st.text_area("", translated_text, height=90)

        # TTS disabled but ready
        out_file = f"tts_{tgt_code}.wav"
        synthesize_speech(translated_text, voice, out_file)

        st.audio(open(out_file, "rb").read(), format="audio/wav")
        st.success("✅ Translation & Speech Complete")
