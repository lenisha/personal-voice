#!/usr/bin/env python3
"""
Azure AI Services - Text-to-Speech with Personal Voice
This script demonstrates how to use Azure AI Speech Service to convert text to speech
using both standard voices and personal voice capabilities.

Requirements:
- See requirements.txt for dependencies
"""

import os
import sys
import argparse
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk
from azure.cognitiveservices.speech import SpeechSynthesisOutputFormat

# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)


# Get credentials from environment variables
# These should be set in .env file or system environment
SPEECH_KEY = os.environ.get('AZURE_SPEECH_KEY')
SPEECH_REGION = os.environ.get('AZURE_SPEECH_REGION')
AZURE_SPEAKER_PROFILE_ID = os.environ.get('AZURE_SPEAKER_PROFILE_ID',None)

print("Using Azure Speech Service with the following configuration:")
print(f"  Speech Region: {'***' if SPEECH_REGION else 'Not set'}")
# Print speaker profile ID if available
if AZURE_SPEAKER_PROFILE_ID:
    print(f"  Speaker Profile ID: {'***' if AZURE_SPEAKER_PROFILE_ID else 'Not set'}")

# Check if credentials are available
if not SPEECH_KEY or not SPEECH_REGION:
    print("Warning: Azure Speech credentials not found in environment variables.")
    print("Please set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION in your .env file.")
    print("Using default region (eastus). You will need to provide a valid key to use the service.")
    if not SPEECH_REGION:
        SPEECH_REGION = "eastus"

def text_to_speech_basic(text, output_filename="output.wav", voice_name="en-US-JennyNeural"):
    """
    Convert text to speech using a standard voice
    """
    # Configure speech synthesis
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    
    # Set the voice name
    speech_config.speech_synthesis_voice_name = voice_name
    
    # Configure audio output
    audio_config = speechsdk.audio.AudioOutputConfig(filename=output_filename)
    
    # Create speech synthesizer
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    
    # Synthesize speech
    result = synthesizer.speak_text_async(text).get()
    
    # Check result
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print(f"Speech synthesized for text [{text}] and saved to [{output_filename}]")
        return True
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print(f"Speech synthesis canceled: {cancellation_details.reason}")
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print(f"Error details: {cancellation_details.error_details}")
        return False
    return False

def text_to_speech_with_ssml(ssml, output_filename="output.wav"):
    """
    Convert text to speech using SSML (Speech Synthesis Markup Language)
    Allows for more control over speech synthesis including using personal voice via speakerProfileId
    """
    # Configure speech synthesis
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    
    # Configure audio output
    audio_config = speechsdk.audio.AudioOutputConfig(filename=output_filename)
    
    # Create speech synthesizer
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    
    # Synthesize speech from SSML
    result = synthesizer.speak_ssml_async(ssml).get()
    
    # Check result
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print(f"Speech synthesized from SSML and saved to [{output_filename}]")
        return True
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print(f"Speech synthesis canceled: {cancellation_details.reason}")
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print(f"Error details: {cancellation_details.error_details}")
        return False
    return False

def personal_voice_text_to_speech(text, speaker_profile_id, output_filename="personal_voice_output.wav", 
                          rate="1.0", reduce_pauses=False):
    """
    Convert text to speech using a personal voice
    
    Args:
        text (str): The text to convert to speech
        speaker_profile_id (str): The speaker profile ID for the personal voice
        output_filename (str): The filename to save the audio to
        rate (str): The speaking rate (e.g., "1.0", "1.2", "fast")
        reduce_pauses (bool): Whether to minimize pauses between sentences/phrases
    """
    # Process text to reduce pauses if requested
    if reduce_pauses:
        # Replace periods and other punctuation that might cause longer pauses
        # with break tags that have minimal pause
        text = text.replace(". ", '.<break strength="weak"/> ')
        text = text.replace("? ", '?<break strength="weak"/> ')
        text = text.replace("! ", '!<break strength="weak"/> ')
        text = text.replace(", ", ',<break strength="none"/> ')
    
    # Create SSML with speaker profile ID for personal voice
    ssml = f"""
    <speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xmlns:mstts='http://www.w3.org/2001/mstts' xml:lang='en-US'>
        <voice name='DragonLatestNeural'> 
            <mstts:ttsembedding speakerProfileId='{speaker_profile_id}'>
                <prosody rate="{rate}">
                    {text}
                </prosody>
            </mstts:ttsembedding> 
        </voice> 
    </speak>
    """
    
    return text_to_speech_with_ssml(ssml, output_filename)

def read_sample_text(file_path):
    """
    Read sample text from a file
    """
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None

if __name__ == "__main__":
    # Add command-line argument parsing
    import argparse
    
    parser = argparse.ArgumentParser(description="Convert text to speech using Azure AI Speech Service")
    parser.add_argument("--input", help="Path to text file to convert to speech (optional)")
    parser.add_argument("--output", default="audio/personal_output.wav", help="Path to save the audio output (default: output.wav)")
    parser.add_argument("--voice", default="en-US-JennyNeural", help="Voice to use (default: en-US-JennyNeural)")
    parser.add_argument("--personal-voice", help="Speaker profile ID for personal voice (optional)")
    parser.add_argument("--rate", default="1.0", help="Speaking rate (default: 1.0)")
    parser.add_argument("--reduce-pauses", action="store_true", help="Reduce pauses between sentences")
    parser.add_argument("--variants", action="store_true", help="Use variants for personal voice synthesis (optional)")

    args = parser.parse_args()
    
    # Read from input file if provided, otherwise use sample text
    text_to_convert = None
    if args.input:
        text_to_convert = read_sample_text(args.input)
        if not text_to_convert:
            print(f"Error reading input file: {args.input}")
            sys.exit(1)
        print(f"Using input file: {args.input}")    
    else:  
          # Example 2: Read from sample file and convert to speech
        text_to_convert = read_sample_text("sample_text.txt")
        print(f"Using sample text: {text_to_convert[:50]}...")  # Print first 50 characters for brevity


    personal_voice_id = args.personal_voice if args.personal_voice else AZURE_SPEAKER_PROFILE_ID
    # If personal voice ID is provided, use it for synthesis
    if personal_voice_id:
        print(f"Using personal voice with ID: {personal_voice_id}")
        if not args.variants:
            # Use personal voice
            print(f"Using standard personal voice synthesis without variants. rate {args.rate} and reduce pauses {args.reduce_pauses} can be adjusted.")
            personal_voice_text_to_speech(
                text_to_convert, 
                personal_voice_id, 
                args.output,
                rate=args.rate,
                reduce_pauses=args.reduce_pauses
            )
        else:
            # Use personal voice with variants
            # Note: Variants are not supported in the current version of the SDK, 
            # so this is a placeholder for future implementation.
            print("Using variants for personal voice synthesis is not yet implemented in this SDK version.")
            # Example 3: Using personal voice (you need to provide speaker_profile_id)
            # To get a speaker profile ID, follow the steps in:
            # https://learn.microsoft.com/en-us/azure/ai-services/speech-service/personal-voice-create-voice
            
                       
            # Option 1: Standard personal voice synthesis
            personal_voice_text_to_speech(text_to_convert, 
                                            personal_voice_id, 
                                            "audio/personal_voice_output.wav")
            
            # Option 2: Faster speech rate (20% faster)
            personal_voice_text_to_speech(text_to_convert,
                                            personal_voice_id,
                                            "audio/personal_voice_faster.wav",
                                            rate="1.2")
                                            
            # Option 3: Reduced pauses between sentences
            personal_voice_text_to_speech(text_to_convert,
                                            personal_voice_id,
                                            "audio/personal_voice_fewer_pauses.wav",
                                            reduce_pauses=True)
                                            
            # Option 4: Both faster and reduced pauses
            personal_voice_text_to_speech(text_to_convert,
                                            personal_voice_id,
                                            "audio/personal_voice_faster_fewer_pauses.wav",
                                            rate="1.2",
                                            reduce_pauses=True)
    else:
        print("No personal voice ID provided. Using standard voice synthesis.")
        # Example 1: Basic text-to-speech with standard voice
        text_to_speech_basic(text_to_convert, 
                             output_filename="audio/standard_voice_output.wav",
                             voice_name=args.voice)

     

  
    