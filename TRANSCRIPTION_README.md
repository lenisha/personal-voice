# Audio Transcription and Improvement Utilities

This directory contains several utilities for working with speech and text:

## 1. Text-to-Speech (`text_to_speech.py`)
Convert text to speech using Azure AI Speech Service, with support for standard voices and personal voices.

## 2. Personal Voice Creation (`create_personal_voice.py`)
Create a personal voice profile in Azure AI Speech Service using recorded audio samples.

## 3. Speech-to-Text Transcription (`get_transcript.py`)
Transcribe audio and video files to text using Azure AI Speech-to-Text services.

## 4. Transcript Improvement (`improve_transcript.py`)
Improve transcripts using OpenAI's GPT models to fix grammar, improve clarity, and enhance readability.

## Audio Conversion Utilities
The `audio_conversion.py` module provides support for converting between different audio formats.

---

## Setup

### Installation

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables in a `.env` file:
   ```
   # Azure Speech Services configuration
   AZURE_SPEECH_KEY=your_azure_speech_key_here
   AZURE_SPEECH_REGION=eastus

   # Azure OpenAI configuration
   AZURE_OPENAI_KEY=your_azure_openai_key_here
   AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
   AZURE_OPENAI_DEPLOYMENT=your-deployment-name
   AZURE_OPENAI_API_VERSION=2023-05-15

   # OpenAI API configuration (backup)
   OPENAI_API_KEY=your_openai_api_key_here
   ```

### Dependencies

The required packages are listed in `requirements.txt`:
- azure-cognitiveservices-speech - For Azure Speech-to-Text and Text-to-Speech
- openai - For transcript improvement with language models
- python-dotenv - For loading environment variables
- pydub - For audio format conversion (optional, will fall back to ffmpeg)
- requests - Used by personal voice creation API calls
- azure-identity - Used for Azure OpenAI authentication (optional)

---

## Usage Examples

### Transcribing an Audio File

```bash
# Basic transcription
python get_transcript.py audio/sample1.wav

# Save to specific output file
python get_transcript.py audio/sample1.wav --output transcripts/meeting_transcript.txt

# With timestamps
python get_transcript.py audio/sample1.wav --timestamps

# Specify language
python get_transcript.py audio/sample1.wav --language es-ES
```

### Improving a Transcript

```bash
# Basic improvement with default parameters
python improve_transcript.py transcript.txt

# Specify formality level
python improve_transcript.py transcript.txt --formality formal

# Use a more powerful model for better results
python improve_transcript.py transcript.txt --model gpt-4

# Save to specific output file
python improve_transcript.py transcript.txt --output transcripts/improved_transcript.txt
```

### Complete Pipeline Example

```bash
# 1. Transcribe audio file
python get_transcript.py audio/meeting_recording.m4a --timestamps

# 2. Improve the transcript
python improve_transcript.py meeting_recording.txt --formality formal

# 3. Convert improved transcript to speech
python text_to_speech.py --input meeting_recording_improved.txt --output audio/meeting_narration.wav
```

## Requirements

- Azure Speech Service subscription key and region
- OpenAI API key (for transcript improvement)
- Python libraries: azure-cognitiveservices-speech, openai, pydub (optional)
