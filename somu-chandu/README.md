# 🎤 Speech-to-Speech Translation Pipeline

A real-time Speech-to-Speech translation system built with Azure Cognitive Services. This project implements a complete pipeline that captures speech, transcribes it, translates it to multiple languages, and generates speech output.

## 📋 Project Overview

This project is divided into three milestones:

- **Milestone 1**: Speech-to-Text (STT) - ✅ Completed
- **Milestone 2**: Translation Module - ✅ Completed  
- **Milestone 3**: Full Real-Time Speech-to-Speech Pipeline - ✅ Completed

## 🏗️ Architecture

```
Microphone Input
    ↓
[Azure Speech-to-Text] → Transcript (with IDs)
    ↓
[Azure Translator] → Translations (multiple languages)
    ↓
[Azure Text-to-Speech] → Audio Output (per language)
```

## 🚀 Features

- **Real-time Speech Recognition**: Continuous microphone input with partial and final results
- **Multi-language Translation**: Translate to Hindi, Telugu, Spanish, French (configurable)
- **Text-to-Speech**: Generate natural-sounding audio in target languages
- **Transcript Management**: Track transcripts with unique IDs
- **Error Handling**: Retry logic for API failures
- **Performance Metrics**: Track STT, translation, and TTS latencies

## 📦 Prerequisites

- Python 3.8+
- Azure account with the following services:
  - **Azure Speech Service** (for STT and TTS)
  - **Azure Translator Service**
- Microphone access

## 🔧 Installation

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd somu-chandu
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   Create a `.env` file in the root directory:
   ```env
   AZURE_SPEECH_KEY=your_speech_key_here
   AZURE_REGION=your_region_here
   AZURE_TRANSLATOR_KEY=your_translator_key_here
   AZURE_TRANSLATOR_REGION=your_region_here
   ```

   > **Note**: You can use the same region for both services, or specify `AZURE_TRANSLATOR_REGION` separately.

## 📁 Project Structure

```
somu-chandu/
├── app.py                            # Streamlit web interface
├── scripts/
│   ├── transcribe_files.py          # Milestone 1: File transcription
│   ├── recognize_once.py            # Milestone 1: Real-time STT
│   ├── auto_convert_transcribe.py   # Milestone 1: Auto-convert + transcribe
│   ├── translator.py                # Milestone 2: Translation module
│   ├── stt_translate_integration.py # Milestone 2: STT + Translation
│   ├── realtime_speech_to_speech.py # Milestone 3: Full pipeline
│   └── test_pipeline.py             # Component testing script
├── speech_samples/                   # Input audio files
├── transcripts/                      # STT output
├── translations/                     # Translation output
├── realtime_output/                  # Milestone 3 output
│   ├── audio/                        # TTS audio files
│   ├── transcripts/                  # Real-time transcripts
│   └── translations/                 # Real-time translations
├── requirements.txt
├── README.md
└── QUICKSTART.md
```

## 🎯 Usage

### 🌐 Web Interface (Streamlit)

**Launch the web interface:**
```bash
streamlit run app.py
```

The web interface provides:
- 🏠 **Home**: Overview and quick start guide
- 🎤 **Real-Time Pipeline**: Instructions for running the live pipeline
- 📁 **File Upload**: Upload and process audio files with transcription and translation
- 📊 **Results**: View and download generated audio files
- 🧪 **Test Components**: Test individual components (STT, Translation, TTS)

**Features:**
- User-friendly interface
- Real-time processing feedback
- Audio playback in browser
- Download generated audio files
- Component testing tools

### Milestone 1: Speech-to-Text

#### Transcribe audio files:
```bash
python scripts/transcribe_files.py
```

#### Real-time microphone transcription:
```bash
python scripts/recognize_once.py
```
Say "end recording" to stop, or press Ctrl+C.

#### Auto-convert and transcribe:
```bash
python scripts/auto_convert_transcribe.py
```

### Milestone 2: Translation

#### Test translation module:
```bash
python scripts/translator.py
```

#### Translate transcripts from CSV:
```bash
python scripts/stt_translate_integration.py
```

### Milestone 3: Real-Time Speech-to-Speech

#### Run the full pipeline:
```bash
python scripts/realtime_speech_to_speech.py
```

**How it works:**
1. Start speaking into your microphone
2. The system will:
   - Transcribe your speech in real-time
   - Translate to target languages (hi, te, es, fr)
   - Generate audio output for each translation
3. Press **Ctrl+C** to stop

**Output:**
- Transcripts saved to `realtime_output/transcripts/`
- Translations saved to `realtime_output/translations/`
- Audio files saved to `realtime_output/audio/`

## ⚙️ Configuration

### Target Languages

Edit `scripts/realtime_speech_to_speech.py` to change target languages:

```python
TARGET_LANGUAGES = ["hi", "te", "es", "fr"]  # Add/remove languages
```

### Source Language

Change the source language for STT:

```python
SOURCE_LANGUAGE = "en-US"  # Change to your source language
```

### TTS Voices

The system uses neural voices for each language:
- Hindi: `hi-IN-SwaraNeural`
- Telugu: `te-IN-MohanNeural`
- Spanish: `es-ES-ElviraNeural`
- French: `fr-FR-DeniseNeural`

You can modify voice mappings in `_generate_tts()` method.

## 📊 Output Format

### Transcripts CSV
```csv
filename,language,language_name,transcript
en_commentary1.wav,en-US,English,"Communication technology has evolved..."
```

### Translations JSON
```json
{
  "transcript_id": "transcript_0_1234567890",
  "original_text": "Hello, how are you?",
  "translations": {
    "hi": "नमस्ते, आप कैसे हैं?",
    "te": "నమస్కారం, మీరు ఎలా ఉన్నారు?",
    "es": "Hola, ¿cómo estás?",
    "fr": "Bonjour, comment allez-vous?"
  },
  "source_language": "en",
  "timestamp": "2024-01-15 10:30:45",
  "translation_time": 0.85
}
```

## 🔍 Troubleshooting

### "Missing Azure credentials"
- Ensure your `.env` file exists and contains all required keys
- Check that variable names match exactly (case-sensitive)

### "No speech recognized"
- Check microphone permissions
- Ensure microphone is working
- Try speaking louder or closer to the microphone

### Translation failures
- Verify Azure Translator service is active
- Check API key and region are correct
- Ensure you have sufficient quota

### TTS audio not generated
- Verify Azure Speech service includes TTS (usually included)
- Check voice names are valid for your region
- Review error messages in console output

## 📈 Performance Metrics

The pipeline tracks:
- **STT Latency**: Time to recognize speech
- **Translation Latency**: Time to translate text
- **TTS Latency**: Time to generate audio

These are displayed in the summary at the end of each session.

## 🛠️ Development

### Adding New Languages

1. Add language code to `TARGET_LANGUAGES`
2. Add voice mapping in `_generate_tts()`:
   ```python
   voice_map = {
       "new_lang": "new-lang-Locale-VoiceNeural"
   }
   ```

### Extending Functionality

- **VAD (Voice Activity Detection)**: Can be added using Azure Speech SDK's silence detection
- **Streaming TTS**: Can be enhanced to stream audio directly to speakers
- **Web Interface**: Can be wrapped in Flask/FastAPI for web access

## 📝 Sample Input/Output

### Input (Speech)
> "Hello, how are you today? I hope you're doing well."

### Output (Translations)
- **Hindi**: "नमस्ते, आज आप कैसे हैं? मुझे आशा है कि आप अच्छा कर रहे हैं।"
- **Telugu**: "నమస్కారం, మీరు ఈరోజు ఎలా ఉన్నారు? మీరు బాగా చేస్తున్నారని నేను ఆశిస్తున్నాను."
- **Spanish**: "Hola, ¿cómo estás hoy? Espero que lo estés haciendo bien."
- **French**: "Bonjour, comment allez-vous aujourd'hui ? J'espère que vous allez bien."

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is for educational purposes.

## 🙏 Acknowledgments

- Azure Cognitive Services for Speech and Translation APIs
- Python community for excellent libraries

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review Azure service documentation
3. Open an issue on GitHub

---

**Built with ❤️ using Azure Cognitive Services**

