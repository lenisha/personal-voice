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
- Consent file: Recording of you saying the required consent statement
- Sample files: Clear recordings of your natural speech (30+ seconds each recommended)
- Record in a quiet environment with minimal background noise

## Audio Format Conversion

The script will automatically convert your audio files to the required format (16-bit PCM WAV, 16kHz, mono):

1. If `pydub` is installed, it will be used for the conversion
2. If `pydub` fails or isn't available, FFmpeg will be used as a fallback
3. If neither is available, the script will provide installation instructions

## Create Personal Voice

```bash
# Basic usage
python create_personal_voice.py --consent /path/to/consent.wav --samples /path/to/sample1.wav /path/to/sample2.wav --name "Your Name"

# Advanced usage with all parameters
python create_personal_voice.py \
    --consent /path/to/consent.wav \
    --samples /path/to/sample1.wav /path/to/sample2.wav /path/to/sample3.wav \
    --name "Your Name" \
    --company "Your Company" \
    --locale "en-US" \
    --project-id "YourProjectID" \
    --consent-id "YourConsentID" \
    --voice-id "YourVoiceID"
```

## Example

```bash
python create_personal_voice.py --consent voice/consent2.wav --samples voice/sample3.wav voice/sample4.wav --name "Elena Neroslavskaya"
```

## Consent Statement

For the consent recording, you should record yourself clearly saying:

"I [state your name], am aware that [state company name] will use recordings of my voice to create and use a synthetic version of my voice."

## After Creating Your Voice

Once your personal voice is created, you'll receive a Speaker Profile ID that you can use in your text-to-speech applications with the Azure Speech Service.

To use it with the existing `text_to_speech.py` script:

```python
speaker_profile_id = "your_speaker_profile_id_here"
personal_voice_text_to_speech("This is my personal voice.", speaker_profile_id, "my_voice_output.wav")
```


## References

- [Create a project for personal voice](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/personal-voice-create-project)
- [Add user consent to the project](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/personal-voice-create-consent)
- [Get a speaker profile ID](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/personal-voice-create-voice)
- [Use personal voice in your application](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/personal-voice-how-to-use)
- [Speech SDK documentation](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/get-started-text-to-speech)
