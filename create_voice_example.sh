#!/bin/bash
# Example script to create a personal voice using the files in the workspace

echo "Creating personal voice profile for Elena..."

# Run the Python script with the required parameters
# This example shows that you can use WAV files directly
python src/create_personal_voice.py \
    --consent "audio/consent2.wav" \
    --samples "audio/sample3.wav" "audio/sample4.wav" \
    --name "Elena Neroslavskaya" \
    --company "Microsoft" \
    --project-id "ElenaProject" \
    --consent-id "ElenaConsent3" \
    --voice-id "ElenaNerosVoice$(date +%m%d)"

echo ""
echo "Example with different audio formats (if you have m4a files):"
echo "./create_personal_voice.py \\"
echo "    --consent \"voice_recording.m4a\" \\"
echo "    --samples \"sample_recording1.m4a\" \"sample_recording2.m4a\" \\"
echo "    --name \"Your Name\" \\"
echo "    --company \"Your Company\""
echo ""
echo "Once you have your Speaker Profile ID, you can use it with text_to_speech.py"
echo "Example:"
echo "python src/text_to_speech.py"
