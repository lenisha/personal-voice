#!/bin/bash
# Example script demonstrating the complete transcription and improvement pipeline

# Check for the .env file
ENV_FILE="$(dirname $0)/.env"
if [ ! -f "$ENV_FILE" ]; then
  echo "Warning: .env file not found at $ENV_FILE"
  echo "Creating a template .env file. Please edit it with your API keys."
  
  cat > "$ENV_FILE" << EOL
# Azure Speech Services configuration
AZURE_SPEECH_KEY=your_azure_speech_key_here
AZURE_SPEECH_REGION=eastus

# OpenAI API configuration
OPENAI_API_KEY=your_openai_api_key_here
EOL

  echo "Created template .env file at $ENV_FILE"
  echo "Please edit this file and add your API keys before running this script."
  exit 1
fi

# Check if requirements are installed
SRC_DIR="$(dirname $0)/src"
MAIN_REQ="$(dirname $0)/requirements.txt"
SRC_REQ="$SRC_DIR/requirements.txt"

if [ -f "$SRC_REQ" ]; then
  REQUIREMENTS="$SRC_REQ"
  echo "Using requirements.txt from src directory..."
elif [ -f "$MAIN_REQ" ]; then 
  REQUIREMENTS="$MAIN_REQ"
  echo "Using requirements.txt from main directory..."
else
  echo "Error: requirements.txt file not found in either $(dirname $0) or $SRC_DIR"
  exit 1
fi

echo "Checking dependencies from $REQUIREMENTS..."
pip install -r "$REQUIREMENTS" --quiet
if [ $? -ne 0 ]; then
  echo "Error installing dependencies. Please check requirements.txt"
  exit 1
fi

# Check if API keys are set in .env file
source "$ENV_FILE"

if [ -z "$AZURE_SPEECH_KEY" ] || [ "$AZURE_SPEECH_KEY" == "your_azure_speech_key_here" ]; then
  echo "Error: AZURE_SPEECH_KEY not properly set in $ENV_FILE"
  echo "Please edit the .env file and add your Azure Speech key."
  exit 1
fi

if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" == "your_openai_api_key_here" ]; then
  echo "Warning: OPENAI_API_KEY not properly set in $ENV_FILE"
  echo "Transcript improvement will not work without a valid OpenAI API key."
  echo "Please edit the .env file to add your OpenAI API key if you want to use the improvement feature."
fi

# Create a transcripts directory if it doesn't exist
mkdir -p transcripts

echo "=========================================================="
echo "STEP 1: Speech-to-Text Transcription"
echo "=========================================================="
echo "Transcribing audio file: audio/sample1.wav"

# Run the speech-to-text transcription with timestamps
python src/get_transcript.py audio/sample1.wav \
  --output transcripts/sample1_transcript.txt \
  --timestamps

echo ""
echo "=========================================================="
echo "STEP 2: Transcript Improvement"
echo "=========================================================="
echo "Improving transcript using GPT..."

# Run the transcript improvement (if OpenAI API key is set)
if [ -n "$OPENAI_API_KEY" ]; then
  python src/improve_transcript.py transcripts/sample1_transcript.txt \
    --output transcripts/sample1_improved.txt \
    --formality neutral
else
  echo "Skipping transcript improvement (no OpenAI API key)"
fi

echo ""
echo "=========================================================="
echo "STEP 3: Text-to-Speech Conversion"
echo "=========================================================="
echo "Converting improved transcript back to speech..."

# Convert the improved transcript back to speech
python src/text_to_speech.py \
  --input transcripts/sample1_improved.txt \
  --output audio/sample1_narration.wav

echo ""
echo "Pipeline complete!"
echo "Check the following files:"
echo "- Original transcript: transcripts/sample1_transcript.txt"
echo "- Improved transcript: transcripts/sample1_improved.txt"
echo "- Narrated audio: audio/sample1_narration.wav"
