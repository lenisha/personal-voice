# Azure Personal Voice Creation Tool

This utility helps you create a personal voice using Azure AI Speech Services. It creates a voice profile that you can use for text-to-speech synthesis that sounds like your own voice.

## Requirements

1. An Azure Speech resource with Personal Voice feature enabled
2. Python 3.6+ with the following libraries:
   - `requests` for API communication
   - `pydub` for audio conversion
   - FFmpeg installed on your system for use by pydub for audio conversion (on Windows, run `choco install ffmpeg`)
3. Audio files:
   - One consent recording (clear statement giving consent to use your voice)
   - At least two sample audio recordings of your voice (clear, high-quality recordings)

## Audio Recording Requirements

- Format: WAV, M4A, MP3, or other common audio formats (will be converted to the proper format automatically)
- Consent file: Recording of you saying the required consent statement (see below)
- Sample files: Clear recordings of your natural speech (20+ seconds each recommended)
- Record in a quiet environment with minimal background noise
- on Windows use Sound Recorder or Audacity to record your voice


### Audio Format Conversion

The script will automatically convert your audio files to the required format (16-bit PCM WAV, 16kHz, mono):

1. If `pydub` is installed, it will be used for the conversion
2. If `pydub` fails or isn't available, FFmpeg will be used as a fallback
3. If neither is available, the script will provide installation instructions
4. Ensure you have FFmpeg installed (e.g., using Chocolatey: `choco install ffmpeg` , `apt install ffmpeg` on Linux, or download from [FFmpeg's official site](https://ffmpeg.org/download.html))

## Consent Statement

For the consent recording, you should record yourself clearly saying:

```
I [state your name], am aware that [state company name] will use recordings of my voice to create and use a synthetic version of my voice.
```
## Create an Azure Speech Service
Currently EastUS and WestEurope regions support Personal Voice.

- Create an Azure Speech resource in the Azure portal or AI Service in AI Foundry portal
- Copy the `AZURE_SPEECH_KEY` and `AZURE_SPEECH_REGION` from the Azure portal to your environment variables or `src/.env` file


## Create Personal Voice
- Install the required Python packages:
```bash
pip install -r src/requirements.txt
```
- Create personal voice using the provided script:

```bash
# Basic usage
python src/create_personal_voice.py --consent /path/to/consent.wav --samples /path/to/sample1.wav /path/to/sample2.wav --name "Your Name"
```

- Advanced usage with all parameters
```bash
python create_personal_voice.py \
    --consent /path/to/consent.wav \
    --samples /path/to/sample1.wav /path/to/sample2.wav /path/to/sample3.wav \
    --name "Your Name" \
    --company "Your Company" \
    --locale "en-US" \
    --project-id "YourProjectID" \
    --consent-id "YourConsentID" 
```

### My Example

```bash
python create_personal_voice.py --consent voice/consent2.wav --samples voice/sample3.wav voice/sample4.wav --name "Elena Neroslavskaya"
```

- You will see similar output:
```
✓ Conversion successful: sample3-converted.wav
  - Duration: 7.83 seconds
  - Channels: 1
  - Sample rate: 16000 Hz
  - Sample width: 2 bytes

[1/4] Creating project 'Project-xxxx'...
✓ Project created successfully: Project-xxxx

[2/4] Uploading consent for 'Elena Neroslaskaya'... from file 'consent-converted.wav'
✓ Consent uploaded successfully: Consent-xxxx
Operation ID: 9f24fdce-f4c5-4d87-
Monitoring operation 9f24fdce-f4c5-4d87-a979-...
Attempt 1/10... status code: 200
Operation in progress: running (attempt 1/10)
Attempt 2/10... status code: 200
✓ Operation completed successfully

[3/4] Creating personal voice 'Voice-xxx' with 3 sample(s)...
✓ Personal voice created successfully!
✓ Speaker Profile ID: 160faee9-0bc5-4221-8463-xxxxx

[4/4] Checking status of voice 'Voice-xxx'...
Voice Status: Running
Speaker Profile ID: 160faee9-0bc5-4221-8463-xxxxx

============================================================
 PERSONAL VOICE DETAILS 
============================================================
Voice ID:           Voice-xxx
Display Name:       Voice-xxxx
Project ID:         Project-xxx
Consent ID:         Consent-xxx
Speaker Profile ID: 160faee9-0bc5-4221-8463-xxxxxx
Created:            2025-06-18 22:23:57 UTC
Last Action:        2025-06-18 22:23:57 UTC
============================================================

To use this voice in text-to-speech applications, use the Speaker Profile ID:

160faee9-0bc5-4221-8463-xxxx

Example SSML:

<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xmlns:mstts='http://www.w3.org/2001/mstts' xml:lang='en-US'>
    <voice name='DragonLatestNeural'> 
        <mstts:ttsembedding speakerProfileId='160faee9-0bc5-4221-8463-xxxxxx'> 
            This is my personal voice created with Azure AI Speech Service.
        </mstts:ttsembedding> 
    </voice> 
</speak>

✓ Personal Voice Creation Process Completed
Save your Speaker Profile ID for future use: 160faee9-0bc5-4221-8463-xxxxxxx
```

## Using Your Personal Voice to Synthesize Speech

Once your personal voice is created, you'll receive a Speaker Profile ID that you can use in your text-to-speech applications with the Azure Speech Service.

To use it with the existing `text_to_speech.py` script:

```python

```

- `DragonLatestNeural` provides superior voice cloning similarity
- `PhoenixLatestNeural` offers more accurate pronunciation with lower latency

## Improving Transcripts with OpenAI

## References

- [Create a project for personal voice](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/personal-voice-create-project)
- [Add user consent to the project](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/personal-voice-create-consent)
- [Get a speaker profile ID](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/personal-voice-create-voice)
- [Use personal voice in your application](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/personal-voice-how-to-use)
- [Speech SDK documentation](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/get-started-text-to-speech)
