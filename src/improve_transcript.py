#!/usr/bin/env python3
"""
Transcript Improvement Tool
This script takes a text transcript and improves it using Azure OpenAI's services.
It fixes grammar, clarifies sentences, and improves readability while preserving 
the main points and approximate length of the original transcript.

Requirements:
- See requirements.txt for dependencies
"""

import os
import sys
import argparse
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from openai import AzureOpenAI

# Load environment variables from .env file
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
    print(f"Loaded environment variables from {env_path}")



# Get Azure OpenAI credentials from environment variables
AZURE_OPENAI_KEY = os.environ.get('AZURE_OPENAI_KEY')
AZURE_OPENAI_ENDPOINT = os.environ.get('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_DEPLOYMENT = os.environ.get('AZURE_OPENAI_DEPLOYMENT')
AZURE_OPENAI_API_VERSION = os.environ.get('AZURE_OPENAI_API_VERSION', '2023-05-15')

# Fallback to regular OpenAI API if Azure not configured
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', None)

def load_transcript(input_file):
    """
    Load a transcript from a file
    
    Args:
        input_file (str): Path to the transcript file
        
    Returns:
        str or dict: The loaded transcript
    """
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Try to parse as JSON if it appears to be JSON
            if content.strip().startswith('{') or content.strip().startswith('['):
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    # Not valid JSON, treat as plain text
                    return content
            return content
    except Exception as e:
        print(f"Error loading transcript: {e}")
        return None

def format_transcript_for_gpt(transcript):
    """
    Format the transcript for sending to GPT
    
    Args:
        transcript (str or dict): The transcript to format
        
    Returns:
        str: Formatted transcript ready for the API
    """
    # If transcript is a dictionary or list (JSON format)
    if isinstance(transcript, dict):
        # Handle different JSON structures based on what's available
        if 'text' in transcript:
            return transcript['text']
        else:
            # Return a JSON string if we don't understand the structure
            return json.dumps(transcript, indent=2)
    elif isinstance(transcript, list):
        # Handle list of utterances
        if all(isinstance(item, dict) for item in transcript):
            # Check if these are utterances with speaker info
            if all('text' in item for item in transcript):
                formatted_text = ""
                for item in transcript:
                    speaker = f"Speaker {item.get('speaker', 'Unknown')}: " if 'speaker' in item else ""
                    formatted_text += f"{speaker}{item.get('text', '')}\n"
                return formatted_text
            else:
                # Return a JSON string if we don't understand the structure
                return json.dumps(transcript, indent=2)
        else:
            # Just join the list items with newlines
            return "\n".join(transcript)
    else:
        # Assume it's already a string
        return transcript

def improve_transcript_with_gpt(transcript_text, model="gpt-35-turbo", 
                                preserve_speakers=True, 
                                formality_level="neutral",
                                max_tokens=4000):
    """
    Improve a transcript using Azure OpenAI
    
    Args:
        transcript_text (str): The transcript text to improve
        model (str): The GPT model deployment name to use
        preserve_speakers (bool): Whether to preserve speaker annotations
        formality_level (str): Desired formality level (casual, neutral, formal)
        max_tokens (int): Maximum number of tokens to process at once
        
    Returns:
        str: The improved transcript
    """
    # Check for Azure OpenAI credentials
    if not AZURE_OPENAI_KEY or not AZURE_OPENAI_ENDPOINT or not AZURE_OPENAI_DEPLOYMENT:
        if not OPENAI_API_KEY:
            print("Error: Neither Azure OpenAI nor OpenAI credentials are properly configured")
            print("Please check your .env file and ensure either:")
            print("- AZURE_OPENAI_KEY, AZURE_OPENAI_ENDPOINT, and AZURE_OPENAI_DEPLOYMENT are set for Azure OpenAI")
            print("- OPENAI_API_KEY is set for standard OpenAI API")
            return None
        
        # Fall back to standard OpenAI API if Azure credentials are missing
        from openai import OpenAI
        print("Warning: Azure OpenAI credentials not found, falling back to standard OpenAI API")
        client = OpenAI(api_key=OPENAI_API_KEY)
        deployment_model = model  # Use the model parameter directly
    else:
        # Use Azure OpenAI
        client = AzureOpenAI(
            api_key=AZURE_OPENAI_KEY,
            api_version=AZURE_OPENAI_API_VERSION,
            azure_endpoint=AZURE_OPENAI_ENDPOINT
        )
        deployment_model = AZURE_OPENAI_DEPLOYMENT  # Use deployment name from env var
    
    # Create the system prompt based on the options
    system_prompt = f"""You are an expert transcript editor. Your task is to improve a transcript by:
1. Fixing grammar and spelling errors
2. Making sentences clearer and more coherent
3. Removing filler words and verbal tics (um, uh, like, you know)
4. Maintaining a {formality_level} tone
5. IMPORTANT: Preserving the main points and meaning of the original text
6. IMPORTANT: Keeping approximately the same length as the original

The transcript should sound natural and flow well when read aloud.
"""

    if preserve_speakers:
        system_prompt += "\nMaintain all speaker labels and turns of speech exactly as in the original."
    
    try:
        # For long transcripts, we need to process in chunks
        if len(transcript_text) > max_tokens * 2:  # Rough character estimate
            return improve_long_transcript(transcript_text, system_prompt, deployment_model, max_tokens, client)
        
        # For shorter transcripts, process all at once
        response = client.chat.completions.create(
            model=deployment_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Please improve this transcript:\n\n{transcript_text}"}
            ],
            temperature=0.3,  # Lower temperature for more consistent editing
            max_tokens=max_tokens
        )
        
        # Extract the improved transcript from the response
        improved_text = response.choices[0].message.content
        return improved_text
    
    except Exception as e:
        print(f"Error improving transcript with Azure OpenAI: {e}")
        return None

def improve_long_transcript(transcript_text, system_prompt, deployment_model, max_tokens, client):
    """
    Process a long transcript in chunks
    
    Args:
        transcript_text (str): The full transcript text
        system_prompt (str): The system prompt to use
        deployment_model (str): The deployment model name to use
        max_tokens (int): Maximum tokens per chunk
        client: The OpenAI client (Azure or standard)
        
    Returns:
        str: The improved full transcript
    """
    print(f"Transcript is long ({len(transcript_text)} chars). Processing in chunks...")
    
    # Split by paragraphs or lines
    if "\n\n" in transcript_text:
        chunks = transcript_text.split("\n\n")
    else:
        chunks = transcript_text.split("\n")
    
    # Combine chunks to fit within token limits (rough estimate)
    processed_chunks = []
    current_chunk = []
    current_length = 0
    chunk_size = max_tokens * 2  # Rough character to token ratio
    
    for chunk in chunks:
        if current_length + len(chunk) > chunk_size and current_chunk:
            # Process the current combined chunk
            chunk_text = "\n".join(current_chunk)
            improved_chunk = process_chunk(chunk_text, system_prompt, deployment_model, client)
            processed_chunks.append(improved_chunk)
            
            # Reset for next chunk
            current_chunk = [chunk]
            current_length = len(chunk)
        else:
            current_chunk.append(chunk)
            current_length += len(chunk)
    
    # Process any remaining content
    if current_chunk:
        chunk_text = "\n".join(current_chunk)
        improved_chunk = process_chunk(chunk_text, system_prompt, deployment_model, client)
        processed_chunks.append(improved_chunk)
    
    # Combine all improved chunks
    return "\n\n".join(processed_chunks)

def process_chunk(chunk_text, system_prompt, deployment_model, client):
    """Process a single chunk of the transcript"""
    try:
        print(f"Processing chunk of {len(chunk_text)} characters...")
        
        # Add context for partial processing
        chunk_prompt = system_prompt + "\nNote: This is part of a longer transcript. Focus on improving this section while maintaining its consistency with the whole."
        
        response = client.chat.completions.create(
            model=deployment_model,
            messages=[
                {"role": "system", "content": chunk_prompt},
                {"role": "user", "content": f"Please improve this transcript section:\n\n{chunk_text}"}
            ],
            temperature=0.3
        )
        
        improved_chunk = response.choices[0].message.content
        return improved_chunk
    
    except Exception as e:
        print(f"Error processing chunk: {e}")
        # Return original if processing fails
        return chunk_text

def save_improved_transcript(improved_text, output_file=None, input_file=None):
    """
    Save the improved transcript to a file
    
    Args:
        improved_text (str): The improved transcript
        output_file (str): Path to save the transcript to
        input_file (str): Original input file (used to generate default output path)
        
    Returns:
        str: Path to the saved transcript file
    """
    # Generate default output filename if not provided
    if not output_file and input_file:
        input_path = Path(input_file)
        stem = input_path.stem
        output_file = str(input_path.with_name(f"{stem}_improved{input_path.suffix}"))
    
    # Use a default name if we still don't have one
    if not output_file:
        output_file = "improved_transcript.txt"
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(improved_text)
        
        print(f"Improved transcript saved to: {output_file}")
        return output_file
    except Exception as e:
        print(f"Error saving improved transcript: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Improve transcripts using Azure OpenAI")
    
    parser.add_argument("input", help="Path to the transcript file to improve")
    parser.add_argument("--output", "-o", help="Path to save the improved transcript")
    parser.add_argument("--model", default="gpt-35-turbo", 
                        help="Model deployment name (default: gpt-35-turbo)")
    parser.add_argument("--no-preserve-speakers", action="store_true", 
                        help="Don't preserve speaker annotations")
    parser.add_argument("--formality", choices=["casual", "neutral", "formal"], 
                        default="neutral", help="Formality level of the output")
    
    args = parser.parse_args()
    
    # Check that the input file exists
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        return 1
    
    # Check for API credentials
    if not AZURE_OPENAI_KEY and not OPENAI_API_KEY:
        print("Error: Neither AZURE_OPENAI_KEY nor OPENAI_API_KEY environment variables are set")
        print("Please configure Azure OpenAI credentials in your .env file:")
        print("AZURE_OPENAI_KEY=your_azure_openai_key")
        print("AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/")
        print("AZURE_OPENAI_DEPLOYMENT=your-deployment-name")
        return 1
    
    # Start timing
    start_time = time.time()
    
    # Load the transcript
    transcript = load_transcript(args.input)
    if not transcript:
        return 1
    
    # Format the transcript for GPT
    formatted_transcript = format_transcript_for_gpt(transcript)
    
    # Determine if we're using Azure OpenAI or standard OpenAI
    api_type = "Azure OpenAI" if (AZURE_OPENAI_KEY and AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_DEPLOYMENT) else "standard OpenAI"
    
    # Improve the transcript
    print(f"Improving transcript using {api_type} with model {args.model}...")
    improved_transcript = improve_transcript_with_gpt(
        formatted_transcript,
        model=args.model,
        preserve_speakers=not args.no_preserve_speakers,
        formality_level=args.formality
    )
    
    if not improved_transcript:
        return 1
    
    # Calculate elapsed time
    elapsed_time = time.time() - start_time
    print(f"Transcript improvement completed in {elapsed_time:.2f} seconds")
    
    # Save the improved transcript
    save_improved_transcript(improved_transcript, args.output, args.input)
    
    # Print a preview of the improved transcript
    preview_lines = improved_transcript.split('\n')[:5]
    print("\nImproved transcript preview:")
    for line in preview_lines:
        print(line)
    if len(preview_lines) < improved_transcript.count('\n') + 1:
        print("...")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
