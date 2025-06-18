#!/usr/bin/env python3
"""
Azure AI Services - Speech-to-Text Transcription
This script converts audio or video files to text transcripts using Azure AI Speech Services.
It supports various audio formats (WAV, MP3, M4A, etc.) and provides options for formatting.

Requirements:
- See requirements.txt for dependencies
"""

import os
import sys
import argparse
import tempfile
import time
import json
from pathlib import Path
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk
# Import our audio conversion module
from audio_conversion import convert_to_wav

# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)




# Get credentials from environment variables
# These should be set in .env file or system environment
SPEECH_KEY = os.environ.get('AZURE_SPEECH_KEY')
SPEECH_REGION = os.environ.get('AZURE_SPEECH_REGION')

# Check if credentials are available
if not SPEECH_KEY or not SPEECH_REGION:
    print("Warning: Azure Speech credentials not found in environment variables.")
    print("Please set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION in your .env file.")
    print("Using default region (eastus). You will need to provide a valid key to use the service.")
    if not SPEECH_REGION:
        SPEECH_REGION = "eastus"

def transcribe_from_file(audio_file_path, language="en-US", profanity_option="masked", 
                          output_format="simple", show_timestamps=False):
    """
    Transcribe speech from an audio file using Azure AI Speech Services
    
    Args:
        audio_file_path (str): Path to the audio file
        language (str): Language code (e.g., "en-US")
        profanity_option (str): How to handle profanity ("masked", "removed", or "raw")
        output_format (str): Format of the output ("simple", "detailed", or "json")
        show_timestamps (bool): Whether to include timestamps in the output
        
    Returns:
        dict or str: Transcription result based on the specified output format
    """
    print(f"Transcribing audio file: {audio_file_path}")
    
    # Ensure audio file is in WAV format (required for some Azure Speech features)
    wav_file_path = convert_to_wav(audio_file_path)
    temp_file = wav_file_path != audio_file_path
    
    try:
        # Configure speech recognition
        speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
        speech_config.speech_recognition_language = language
        
        # Set profanity option
        if profanity_option == "masked":
            speech_config.set_profanity(speechsdk.ProfanityOption.Masked)
        elif profanity_option == "removed":
            speech_config.set_profanity(speechsdk.ProfanityOption.Removed)
        elif profanity_option == "raw":
            speech_config.set_profanity(speechsdk.ProfanityOption.Raw)
        
        # Enable word-level timestamps if requested
        if show_timestamps:
            speech_config.request_word_level_timestamps()
        
        # Configure audio input
        audio_config = speechsdk.audio.AudioConfig(filename=wav_file_path)
        
        # Standard speech recognition
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
        
        # Start the recognition
        print("Starting transcription... (this may take a while)")
        
        # Process the entire audio file
        all_results = []
        done = False

        def recognized_cb(evt):
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                all_results.append(evt.result)
            elif evt.result.reason == speechsdk.ResultReason.NoMatch:
                print(f"NOMATCH: Speech could not be recognized.")

        def stop_cb(evt):
            print('CLOSING on {}'.format(evt))
            nonlocal done
            done = True

        # Connect callbacks
        speech_recognizer.recognized.connect(recognized_cb)
        speech_recognizer.session_stopped.connect(stop_cb)
        speech_recognizer.canceled.connect(stop_cb)

        # Start continuous recognition
        speech_recognizer.start_continuous_recognition()

        # Wait for completion
        start_time = time.time()  # Initialize start_time for the timeout
        while not done:
            time.sleep(0.5)
            # Force stop after a timeout (you may need to adjust this for long files)
            # In a real system, we'd calculate this based on audio duration
            if len(all_results) > 0 and (time.time() - start_time) > 300:  # 5 minute timeout
                print("Timeout reached, stopping recognition")
                break

        # Stop recognition
        speech_recognizer.stop_continuous_recognition()

        # Process results based on output format
        if output_format == "json":
            json_results = []
            for result in all_results:
                if show_timestamps and hasattr(result, 'result.properties'):
                    json_results.append({
                        'text': result.text,
                        'offset': result.offset // 10000,  # Convert to milliseconds
                        'duration': result.duration // 10000  # Convert to milliseconds
                    })
                else:
                    json_results.append({'text': result.text})
            return json_results
        elif output_format == "detailed":
            result_text = ""
            for result in all_results:
                if show_timestamps:
                    timestamp = f"[{result.offset/10000000:.2f}s]"
                    result_text += f"{timestamp} {result.text}\n"
                else:
                    result_text += f"{result.text}\n"
            return result_text
        else:  # simple format
            return " ".join([result.text for result in all_results])
            
    except Exception as e:
        print(f"Error during transcription: {e}")
        import traceback
        traceback.print_exc()
        return f"Transcription failed: {str(e)}"
    finally:
        # Clean up the temporary WAV file if created during conversion
        if temp_file and os.path.exists(wav_file_path) and wav_file_path != audio_file_path:
            try:
                os.remove(wav_file_path)
                print(f"Removed temporary file: {wav_file_path}")
            except Exception as e:
                print(f"Warning: Could not remove temporary file {wav_file_path}: {e}")

def save_transcript(transcript, output_file=None, input_file=None):
    """
    Save transcript to a file
    
    Args:
        transcript (str or dict): The transcript to save
        output_file (str): Path to save the transcript to
        input_file (str): Original input file (used to generate default output path)
        
    Returns:
        str: Path to the saved transcript file
    """
    # Generate default output filename if not provided
    if not output_file and input_file:
        input_path = Path(input_file)
        output_file = str(input_path.with_suffix('.txt'))
    
    # Use a default name if we still don't have one
    if not output_file:
        output_file = "transcript.txt"
    
    try:
        # Handle dict/json output
        if isinstance(transcript, (dict, list)):
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(transcript, f, indent=2, ensure_ascii=False)
        else:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(transcript)
        
        print(f"Transcript saved to: {output_file}")
        return output_file
    except Exception as e:
        print(f"Error saving transcript: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Transcribe speech from audio/video files")
    
    parser.add_argument("input", help="Path to the audio/video file to transcribe")
    parser.add_argument("--output", "-o", help="Path to save the transcript (default: same as input with .txt extension)")
    parser.add_argument("--language", "-l", default="en-US", help="Language code (default: en-US)")
    parser.add_argument("--profanity", choices=["masked", "removed", "raw"], default="masked",
                        help="How to handle profanity (default: masked)")
    parser.add_argument("--format", choices=["simple", "detailed", "json"], default="simple",
                        help="Output format (default: simple)")
    parser.add_argument("--timestamps", action="store_true", help="Include timestamps in the output")
    
    args = parser.parse_args()
    
    # Check that the input file exists
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        return 1
    
    # Start timing
    start_time = time.time()
    
    # Transcribe the audio file
    transcript = transcribe_from_file(
        args.input, 
        language=args.language,
        profanity_option=args.profanity,
        output_format=args.format,
        show_timestamps=args.timestamps
    )
    
    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    print(f"Transcription completed in {elapsed_time:.2f} seconds")
    
    # Save the transcript
    if transcript:
        save_transcript(transcript, args.output, args.input)
        
        # Print a preview of the transcript
        if isinstance(transcript, (dict, list)):
            print("\nTranscript preview (JSON):")
            print(json.dumps(transcript[:2] if isinstance(transcript, list) else transcript, indent=2))
        else:
            preview_lines = transcript.split('\n')[:5]
            print("\nTranscript preview:")
            for line in preview_lines:
                print(line)
            if len(preview_lines) < transcript.count('\n') + 1:
                print("...")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
