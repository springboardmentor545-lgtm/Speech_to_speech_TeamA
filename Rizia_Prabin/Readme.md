# AI-Powered Real-Time Speech Translation-Milestone 1

This folder contains all the deliverables for **Milestone 1: Speech Recognition and Data Collection**.

The objective of this milestone was to set up the Azure Speech-to-Text service, gather audio samples in English and Hindi, and use the Azure SDK to transcribe them into a CSV file.

## Folder Contents

* `/speech_samples`
    * Contains **10 audio samples** (5 English, 5 Hindi) used for transcription.
    * All audio files have been converted to the required `.wav` format (16 kHz, mono) using ffmpeg.

* `/scripts`
    * `transcribe_files.py`: The Python script used to process the audio. This script reads each file from `/speech_samples`, sends it to the Azure Speech-to-Text service, and saves the transcription.

* `/transcripts`
    * `transcripts.csv`: The final output. This file contains the filename, language (`en` or `hi`), and the recognized text for each audio sample.

## Technologies Used

* **Python**
* **Azure Cognitive Services Speech SDK** (for speech-to-text)
* **ffmpeg** (for audio conversion)
