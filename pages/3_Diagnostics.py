# pages/3_Diagnostics.py

import os
import sys
import subprocess
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = BASE_DIR / "scripts"

load_dotenv()

st.set_page_config(page_title="Diagnostics", page_icon="🧪", layout="wide")

st.title("🧪 Diagnostics & System Tests")
st.caption("Check microphone access, Azure credentials, and pipeline components.")

st.markdown("### 🔐 Azure Credentials Check")

cols = st.columns(4)
env_vars = [
    ("AZURE_SPEECH_KEY", cols[0]),
    ("AZURE_REGION", cols[1]),
    ("AZURE_TRANSLATOR_KEY", cols[2]),
    ("AZURE_TRANSLATOR_REGION", cols[3]),
]

for var_name, col in env_vars:
    with col:
        value = os.getenv(var_name)
        if value:
            st.success(var_name)
        else:
            st.error(var_name)

st.info(
    "Green = environment variable found. "
    "Red = missing variable (set it in your `.env` file at project root)."
)

st.markdown("---")

st.markdown("### 🎧 Microphone & Audio Test")

st.write(
    "Runs `scripts/test_microphone.py` which uses PyAudio to enumerate devices and checks Azure Speech SDK."
)

if st.button("▶️ Run Microphone Test"):
    script_path = SCRIPTS_DIR / "test_microphone.py"
    if not script_path.exists():
        st.error(f"Test script not found at {script_path}")
    else:
        with st.spinner("Running microphone test script..."):
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(SCRIPTS_DIR),
                capture_output=True,
                text=True,
            )

        st.markdown("#### Output")
        st.code(result.stdout + "\n" + result.stderr, language="bash")

        if result.returncode == 0:
            st.success("Microphone test script completed.")
        else:
            st.warning("Microphone test script exited with a non-zero status.")

st.markdown("---")

st.markdown("### 🧪 Full Pipeline Component Tests")

st.write(
    "Runs `scripts/test_pipeline.py` which checks:\n"
    "- Azure credentials\n"
    "- Translator module\n"
    "- Speech-to-Text initialization\n"
    "- Text-to-Speech initialization"
)

if st.button("▶️ Run Pipeline Tests"):
    script_path = SCRIPTS_DIR / "test_pipeline.py"
    if not script_path.exists():
        st.error(f"Test script not found at {script_path}")
    else:
        with st.spinner("Running pipeline test script..."):
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(SCRIPTS_DIR),
                capture_output=True,
                text=True,
            )

        st.markdown("#### Output")
        st.code(result.stdout + "\n" + result.stderr, language="bash")

        if result.returncode == 0:
            st.success("All tests passed according to test_pipeline.py.")
        else:
            st.warning("Some tests failed. Check the output above for details.")
