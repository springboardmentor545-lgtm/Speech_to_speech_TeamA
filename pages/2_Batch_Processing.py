# pages/2_Batch_Processing.py

import os
import sys
from pathlib import Path
from typing import List, Dict

import streamlit as st
import pandas as pd
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = BASE_DIR / "scripts"
sys.path.append(str(SCRIPTS_DIR))

from language_config import (
    LANGUAGE_NAMES,
    SUPPORTED_LANGUAGES,
    DEFAULT_TARGET_LANGUAGES,
    get_speech_language_code,
    get_language_name,
)
from translator import translate_with_retry
from transcribe_files import transcribe_file, get_language_info

load_dotenv()

st.set_page_config(page_title="Batch Processing", page_icon="📂", layout="wide")

st.title("📂 Batch Processing")
st.caption("Transcribe multiple WAV files and translate transcript CSVs in one go.")

tab_wav, tab_csv = st.tabs(["🎧 Batch WAV → Transcript", "🌐 Batch CSV Translation"])


# ---- TAB 1: Batch WAV transcription ----------------------------------------


with tab_wav:
    st.subheader("🎧 Batch WAV → Transcript CSV")

    st.markdown(
        "Upload one or more `.wav` audio files. "
        "Transcripts will be generated using Azure Speech-to-Text."
    )

    uploaded_files = st.file_uploader(
        "Upload WAV files",
        type=["wav"],
        accept_multiple_files=True,
        help="You can select multiple files at once.",
        key="wav_uploader"
    )

    infer_language = st.checkbox(
        "Infer language from filename prefix (e.g., `hi_*.wav`, `te_*.wav`)",
        value=True,
        key="infer_lang_checkbox"
    )

    if not infer_language:
        default_lang_short = st.selectbox(
            "Default STT language for all files",
            options=SUPPORTED_LANGUAGES,
            index=SUPPORTED_LANGUAGES.index("en") if "en" in SUPPORTED_LANGUAGES else 0,
            format_func=lambda code: f"{LANGUAGE_NAMES[code]} ({code})",
            key="default_lang_selector"
        )
        default_lang_code = get_speech_language_code(default_lang_short)
        default_lang_name = get_language_name(default_lang_short)
    else:
        default_lang_code = None
        default_lang_name = None

    # ---------------- FIXED BUTTON (unique key and used only once) ----------------
    run_button = st.button("🚀 Run Batch Transcription", key="run_batch_stt")
    # ------------------------------------------------------------------------------

    if run_button:
        if not uploaded_files:
            st.error("Please upload at least one WAV file before running transcription.")
        else:
            rows = []
            work_dir = BASE_DIR / "temp_batch_wav"
            work_dir.mkdir(parents=True, exist_ok=True)

            with st.spinner("Transcribing audio files..."):
                for up in uploaded_files:
                    file_name = up.name
                    file_path = work_dir / file_name

                    # Save uploaded file
                    with open(file_path, "wb") as f:
                        f.write(up.read())

                    # Determine language
                    if infer_language:
                        lang_code, lang_name = get_language_info(file_name)
                    else:
                        lang_code, lang_name = default_lang_code, default_lang_name

                    # Convert using Azure STT
                    transcript = transcribe_file(str(file_path), language=lang_code or "en-US")

                    rows.append(
                        {
                            "filename": file_name,
                            "language": lang_code or "en-US",
                            "language_name": lang_name or "English",
                            "transcript": transcript,
                        }
                    )

            df = pd.DataFrame(rows)
            st.success("Batch transcription completed!")
            st.dataframe(df, use_container_width=True)

            csv_data = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "💾 Download transcripts CSV",
                data=csv_data,
                file_name="batch_transcripts.csv",
                mime="text/csv",
            )

# ---- TAB 2: Batch CSV translation ------------------------------------------


with tab_csv:
    st.subheader("🌐 Batch Translation of Transcript CSV")

    st.markdown(
        "Upload a CSV file containing transcripts. The app will translate each row into multiple languages.\n\n"
        "**Expected columns:**\n"
        "- `transcript` (or choose any text column below)\n"
        "- optional: `language` (e.g., `en-US`, `hi-IN`)"
    )

    uploaded_csv = st.file_uploader(
        "Upload transcript CSV",
        type=["csv"],
        key="csv_uploader",
    )

    if uploaded_csv is not None:
        df_input = pd.read_csv(uploaded_csv)
        st.markdown("#### Preview of uploaded CSV")
        st.dataframe(df_input.head(), use_container_width=True)

        text_column = None
        if "transcript" in df_input.columns:
            text_column = "transcript"
        else:
            text_column = st.selectbox(
                "Select the column that contains the text to translate",
                options=list(df_input.columns),
            )

        target_langs = st.multiselect(
            "Target languages",
            options=SUPPORTED_LANGUAGES,
            default=[code for code in DEFAULT_TARGET_LANGUAGES if code in SUPPORTED_LANGUAGES][:5],
            format_func=lambda code: f"{get_language_name(code)} ({code})",
        )

        if st.button("🚀 Translate CSV"):
            if not text_column:
                st.error("Please select a valid text column.")
            elif not target_langs:
                st.error("Please choose at least one target language.")
            else:
                rows_out: List[Dict] = []
                with st.spinner("Translating rows..."):
                    for idx, row in df_input.iterrows():
                        text = str(row[text_column])
                        source_lang_raw = row.get("language", "")

                        if "-" in str(source_lang_raw):
                            source_lang_base = str(source_lang_raw).split("-")[0]
                        else:
                            source_lang_base = source_lang_raw or None

                        result = translate_with_retry(
                            text,
                            target_languages=target_langs,
                            source_language=source_lang_base,
                        )

                        out_row = dict(row)  # keep original columns
                        out_row["detected_language"] = result.get("source_language")
                        out_row["translation_timestamp"] = result.get("timestamp")
                        out_row["translation_error"] = result.get("error")

                        translations = result.get("translations", {})
                        for lang_code in target_langs:
                            col_name = f"translation_{lang_code}"
                            out_row[col_name] = translations.get(lang_code, "")

                        rows_out.append(out_row)

                df_out = pd.DataFrame(rows_out)
                st.success("CSV translation completed.")
                st.dataframe(df_out.head(), use_container_width=True)

                csv_result = df_out.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "💾 Download translated CSV",
                    data=csv_result,
                    file_name="translated_transcripts.csv",
                    mime="text/csv",
                )
