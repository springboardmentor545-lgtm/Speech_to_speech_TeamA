# streamlit_app.py

import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="Speech-to-Speech Studio",
    page_icon="🎙️",
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parent

# ---------------------- CLEAN + FIXED CSS -------------------------
st.markdown(
    """
    <style>
    .big-title {
        font-size: 2.4rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }
    .subtitle {
        font-size: 1.05rem;
        color: #aaa;
        margin-bottom: 1.5rem;
    }
    .feature-card {
        padding: 1.4rem 1.4rem;
        border-radius: 0.9rem;
        border: 1px solid rgba(255,255,255,0.15);
        background: #1f1f1f;
        box-shadow: 0 3px 10px rgba(0,0,0,0.25);
        height: 220px;
    }
    .feature-card-light {
        padding: 1.4rem 1.4rem;
        border-radius: 0.9rem;
        border: 1px solid #eee;
        background: white;
        box-shadow: 0 3px 10px rgba(0,0,0,0.06);
        height: 220px;
    }
    @media (prefers-color-scheme: light) {
        .feature-card { background: white; border: 1px solid #eee; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)
# ------------------------------------------------------------------

st.markdown('<div class="big-title">🎙️ Speech-to-Speech Studio</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Real-time speech recognition, translation, and text-to-speech, all powered by Azure.</div>',
    unsafe_allow_html=True,
)

st.write("Use the navigation sidebar to switch between pages.")

col1, col2, col3, col4 = st.columns(4)

# ---------------- FEATURE CARDS ------------------

with col2:
    st.markdown("### 🎤 Real-Time & Text Translation")
    st.write(
        "- Live microphone speech-to-text\n"
        "- Instant translation into multiple languages\n"
        "- Text → Speech playback per language"
    )

with col3:
    st.markdown("### 📂 Batch Processing")
    st.write(
        "- Upload `.wav` audio for batch transcription\n"
        "- Translate transcript CSV into many languages\n"
        "- Download processed CSV files"
    )

with col4:
    st.markdown("### 🧪 Diagnostics")
    st.write(
        "- Test microphone & audio stack\n"
        "- Validate Azure credentials\n"
        "- Run pipeline component tests"
    )

with col1:
    st.markdown("### 🎬 Video Speech Translation")
    st.write(
        "- Upload a video file\n"
        "- Extract audio commentary\n"
        "- Translate into 12+ languages\n"
        "- Generate multilingual speech tracks"
    )

# -----------------------------------------------------------

st.markdown("---")
st.markdown("#### ℹ️ Setup Checklist")

st.write(
    "1. Create a `.env` file at the project root containing your Azure API keys:\n"
    "   - `AZURE_SPEECH_KEY`\n"
    "   - `AZURE_REGION`\n"
    "   - `AZURE_TRANSLATOR_KEY`\n"
    "   - `AZURE_TRANSLATOR_REGION`\n\n"
    "2. Install required packages:\n"
    "   - `pip install streamlit azure-cognitiveservices-speech python-dotenv pyaudio requests`\n\n"
    "3. Start the app using:\n"
    "   `streamlit run streamlit_app.py`"
)
