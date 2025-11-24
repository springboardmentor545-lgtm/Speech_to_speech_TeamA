# app.py
"""
Final Streamlit app.py with robust process control and safe audio playback.
"""

import streamlit as st
import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk
import psutil
import subprocess
import sys

# Import project modules
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
except ImportError:
    import importlib.util
    spec = importlib.util.spec_from_file_location("translator", os.path.join(SCRIPTS_DIR, "translator.py"))
    translator_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(translator_module)
    translate_with_retry = translator_module.translate_with_retry
    translate_text = translator_module.translate_text

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

load_dotenv()

st.set_page_config(page_title="Speech-to-Speech Translation", page_icon="🎤", layout="wide")

# helper: safe rerun
def maybe_rerun():
    try:
        st.experimental_rerun()
    except Exception:
        st.session_state["_needs_rerender"] = not st.session_state.get("_needs_rerender", False)

# session state defaults
for k, v in {
    'live_recognition_running': False,
    'live_transcripts': [],
    'audio_files': [],
    'file_upload_results': None,
    'last_translation_result': None,
    'last_refresh': time.time()
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

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

def transcribe_audio_file(audio_file, language="en-US"):
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
        speech_key = os.getenv("AZURE_SPEECH_KEY")
        speech_region = os.getenv("AZURE_REGION")
        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
        speech_config.speech_recognition_language = language
        audio_config = speechsdk.audio.AudioConfig(filename=str(temp_path))
        recognizer = speechsdk.SpeechRecognizer(speech_config, audio_config)
        result = recognizer.recognize_once_async().get()
        recognizer = None
        audio_config = None
        time.sleep(0.2)
        for attempt in range(5):
            try:
                if temp_path and temp_path.exists():
                    temp_path.unlink()
                break
            except (PermissionError, OSError):
                time.sleep(0.3)
        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return {"success": True, "text": result.text}
        else:
            return {"success": False, "error": "No speech recognized"}
    except Exception as e:
        try:
            if temp_path and temp_path.exists():
                time.sleep(0.2)
                temp_path.unlink()
        except:
            pass
        return {"success": False, "error": str(e)}

def generate_tts_audio(text, language_code, transcript_id):
    try:
        speech_key = os.getenv("AZURE_SPEECH_KEY")
        speech_region = os.getenv("AZURE_REGION")
        voice_name = get_tts_voice(language_code)
        tts_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
        tts_config.speech_synthesis_voice_name = voice_name
        output_dir = Path("temp_audio_output")
        output_dir.mkdir(exist_ok=True)
        audio_file = output_dir / f"tts_{transcript_id}_{language_code}.wav"
        audio_config = speechsdk.audio.AudioOutputConfig(filename=str(audio_file))
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=tts_config, audio_config=audio_config)
        result = synthesizer.speak_text_async(text).get()
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

# UI
st.markdown('<h1 style="text-align:center">🎤 Speech-to-Speech Translation</h1>', unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Configuration")
    creds = check_credentials()
    if creds["all_configured"]:
        st.success("✅ All credentials configured")
    else:
        st.error("❌ Missing credentials")
        missing = []
        if not creds["speech_key"]: missing.append("AZURE_SPEECH_KEY")
        if not creds["speech_region"]: missing.append("AZURE_REGION")
        if not creds["translator_key"]: missing.append("AZURE_TRANSLATOR_KEY")
        st.info(f"Please configure your .env file with: {', '.join(missing)}")
        st.stop()
    st.divider()
    st.subheader("🌍 Language Settings")
    source_lang_selected = st.selectbox("Source Language", options=SUPPORTED_LANGUAGES, format_func=lambda x: f"{get_language_name(x)} ({x})", index=0, key="sidebar_source_lang")
    source_language = get_speech_language_code(source_lang_selected)
    target_languages = st.multiselect("Target Languages", options=[c for c in SUPPORTED_LANGUAGES if c != source_lang_selected], format_func=lambda x: f"{get_language_name(x)} ({x})", default=[], key="sidebar_target_langs")
    if not target_languages:
        st.warning("Please select at least one target language")
    st.divider()
    page = st.radio("Choose a page", ["🏠 Home", "🎤 Real-Time Pipeline", "📁 File Upload", "📊 Results", "🧪 Test Components"], key="sidebar_page")

# Pages
if page == "🏠 Home":
    st.header("Welcome")
    st.write("Go to 🎤 Real-Time Pipeline to start live translation.")

elif page == "🎤 Real-Time Pipeline":
    st.header("🎤 Real-Time Speech Recognition")
    if not target_languages:
        st.warning("⚠️ Please select at least one target language in the sidebar")
        st.stop()
    status_info = get_recognition_status()
    c1,c2,c3,c4 = st.columns(4)
    with c1:
        st.metric("Recognition Status", f"{'🟢' if status_info['is_running'] else '🔴'} {status_info['status'].title()}")
    with c2:
        st.metric("Transcripts", len(st.session_state.live_transcripts))
    with c3:
        st.metric("Target Languages", len(target_languages))
    with c4:
        st.metric("Memory Usage", f"{psutil.virtual_memory().percent:.1f}%")
    col1,col2,col3 = st.columns([1,1,1])
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

    # Auto-refresh transcripts
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
                    st.markdown(f"<div style='background:#f8f9fa;padding:1rem;border-radius:10px;border-left:4px solid #007bff;margin:0.5rem 0;'><p style='margin:0;font-size:1.1rem;color:#333;'><strong>{transcript['text']}</strong></p><p style='margin:0;font-size:0.8rem;color:#666;'>{time.strftime('%H:%M:%S', time.localtime(transcript['timestamp']))}</p></div>", unsafe_allow_html=True)
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
                                    tts_result = generate_tts_audio(trans_text, lang, transcript['id'])
                                    if tts_result["success"] and os.path.exists(tts_result["file_path"]):
                                        st.success("✅ Audio generated!")
                                        st.session_state.audio_files.append({"transcript_id": transcript['id'], "language": lang, "file": tts_result["file_path"], "text": trans_text, "original_text": transcript['text']})
                                        # show player immediately
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
                                    tts_result = generate_tts_audio(translated_text, lang, res['transcript_id'])
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
            result = generate_tts_audio(tts_test_text, tts_test_lang, test_id)
            if result["success"] and os.path.exists(result["file_path"]):
                st.success("✅ Audio generated!")
                st.audio(result["file_path"])
            else:
                st.error(f"❌ TTS failed: {result.get('error','Unknown error')}")
