#!/usr/bin/env python3
"""
Azure AI Services - Personal Voice Creation Utility
This script creates a personal voice profile in Azure AI Speech Service using:
1. A consent audio file (recorded consent statement)
2. Two sample audio files of the speaker's voice

Based on the Azure Speech Service Personal Voice API

Requirements:
- See requirements.txt for dependencies
"""

import os
import sys
import json
import argparse
import requests
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from .audio_conversion import convert_to_wav, convert_files_to_wav

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

# API version
API_VERSION = "2024-02-01-preview"

def create_project(project_id, description="Personal Voice Project"):
    """
    Create a new personal voice project
    """
    print(f"\n[1/4] Creating project '{project_id}'...")
    
    url = f"https://{SPEECH_REGION}.api.cognitive.microsoft.com/customvoice/projects/{project_id}?api-version={API_VERSION}"
    
    headers = {
        "Ocp-Apim-Subscription-Key": SPEECH_KEY,
        "Content-Type": "application/json"
    }
    
    data = {
        "description": description,
        "kind": "PersonalVoice"
    }
    
    response = requests.put(url, headers=headers, json=data)
    
    if response.status_code in [200, 201]:
        print(f"✓ Project created successfully: {project_id}")
        return True, response.json()
    else:
        print(f"✗ Failed to create project: {response.status_code}")
        print(response.text)
        return False, None

def upload_consent(project_id, consent_id, consent_file_path, voice_talent_name, company_name="My Company", locale="en-US"):
    """
    Upload a consent audio file
    """
    print(f"\n[2/4] Uploading consent for '{voice_talent_name}'...")
    
    url = f"https://{SPEECH_REGION}.api.cognitive.microsoft.com/customvoice/consents/{consent_id}?api-version={API_VERSION}"
    
    headers = {
        "Ocp-Apim-Subscription-Key": SPEECH_KEY,
    }
    
    # Ensure the consent file exists
    if not os.path.exists(consent_file_path):
        print(f"✗ Consent file not found: {consent_file_path}")
        return False, None
    
    # Create multipart form data
    files = {
        'audiodata': (os.path.basename(consent_file_path), open(consent_file_path, 'rb'), 'audio/wav')
    }
    
    data = {
        'description': f"Consent for {voice_talent_name}",
        'projectId': project_id,
        'voiceTalentName': voice_talent_name,
        'companyName': company_name,
        'locale': locale
    }
    
    response = requests.post(url, headers=headers, files=files, data=data)
    
    if response.status_code in [200, 201, 202]:
        print(f"✓ Consent uploaded successfully: {consent_id}")
        
        # Check if there's an operation ID to monitor
        operation_id = None
        response_json = {}
        
        try:
            response_json = response.json()
            if 'id' in response_json:
                operation_id = response_json.get('id')
        except:
            pass
        
        # If there's an operation ID, monitor it
        if operation_id:
            print(f"Operation ID: {operation_id}")
            success, operation_result = monitor_operation(operation_id)
            if success:
                return True, operation_result
        
        return True, response_json
    else:
        print(f"✗ Failed to upload consent: {response.status_code}")
        print(response.text)
        return False, None

def monitor_operation(operation_id, max_attempts=10, delay=5):
    """
    Monitor an asynchronous operation
    """
    print(f"Monitoring operation {operation_id}...")
    
    url = f"https://{SPEECH_REGION}.api.cognitive.microsoft.com/customvoice/operations/{operation_id}?api-version={API_VERSION}"
    
    headers = {
        "Ocp-Apim-Subscription-Key": SPEECH_KEY
    }
    
    for attempt in range(max_attempts):
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            operation_status = response.json()
            status = operation_status.get('status', '').lower()
            
            if status == 'succeeded':
                print(f"✓ Operation completed successfully")
                return True, operation_status
            elif status in ['failed', 'canceled']:
                print(f"✗ Operation failed: {status}")
                return False, operation_status
            else:
                print(f"Operation in progress: {status} (attempt {attempt+1}/{max_attempts})")
                time.sleep(delay)
                continue
                
    print(f"✗ Timed out waiting for operation to complete")
    return False, None

def create_personal_voice(project_id, consent_id, voice_id, sample_files):
    """
    Create a personal voice using sample files
    """
    print(f"\n[3/4] Creating personal voice '{voice_id}' with {len(sample_files)} sample(s)...")
    
    url = f"https://{SPEECH_REGION}.api.cognitive.microsoft.com/customvoice/personalvoices/{voice_id}?api-version={API_VERSION}"
    
    headers = {
        "Ocp-Apim-Subscription-Key": SPEECH_KEY
    }
    
    # Verify sample files exist
    for sample_file in sample_files:
        if not os.path.exists(sample_file):
            print(f"✗ Sample file not found: {sample_file}")
            return False, None
    
    # Create multipart form data
    files = []
    for sample_file in sample_files:
        files.append(('audiodata', (os.path.basename(sample_file), open(sample_file, 'rb'), 'audio/wav')))
    
    data = {
        'projectId': project_id,
        'consentId': consent_id
    }
    
    response = requests.post(url, headers=headers, files=files, data=data)
    
    if response.status_code in [200, 201, 202]:
        result = response.json()
        speaker_profile_id = result.get('speakerProfileId')
        
        if speaker_profile_id:
            print(f"✓ Personal voice created successfully!")
            print(f"✓ Speaker Profile ID: {speaker_profile_id}")
            return True, result
        else:
            print(f"✗ Failed to get speaker profile ID from response")
            return False, result
    else:
        print(f"✗ Failed to create personal voice: {response.status_code}")
        print(response.text)
        return False, None

def get_voice_status(voice_id):
    """
    Get the status of a voice creation request
    """
    print(f"\n[4/4] Checking status of voice '{voice_id}'...")
    
    url = f"https://{SPEECH_REGION}.api.cognitive.microsoft.com/customvoice/personalvoices/{voice_id}?api-version={API_VERSION}"
    
    headers = {
        "Ocp-Apim-Subscription-Key": SPEECH_KEY
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        status = result.get('status')
        speaker_profile_id = result.get('speakerProfileId')
        
        print(f"Voice Status: {status}")
        print(f"Speaker Profile ID: {speaker_profile_id}")
        
        return True, result
    else:
        print(f"✗ Failed to get voice status: {response.status_code}")
        print(response.text)
        return False, None

def display_voice_details(voice_details):
    """
    Display the details of a personal voice in a formatted way
    """
    print("\n" + "="*60)
    print(" PERSONAL VOICE DETAILS ")
    print("="*60)
    
    if not voice_details:
        print("No voice details available.")
        return
    
    # Format the output
    print(f"Voice ID:           {voice_details.get('id', 'N/A')}")
    print(f"Display Name:       {voice_details.get('displayName', 'N/A')}")
    print(f"Project ID:         {voice_details.get('projectId', 'N/A')}")
    print(f"Consent ID:         {voice_details.get('consentId', 'N/A')}")
    print(f"Speaker Profile ID: {voice_details.get('speakerProfileId', 'N/A')}")
    print(f"Status:             {voice_details.get('status', 'N/A')}")
    
    # Format dates if available
    created_date = voice_details.get('createdDateTime')
    last_action_date = voice_details.get('lastActionDateTime')
    
    if created_date:
        created_date = created_date.replace('Z', '+00:00')
        try:
            dt = datetime.fromisoformat(created_date)
            print(f"Created:            {dt.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        except:
            print(f"Created:            {created_date}")
            
    if last_action_date:
        last_action_date = last_action_date.replace('Z', '+00:00')
        try:
            dt = datetime.fromisoformat(last_action_date)
            print(f"Last Action:        {dt.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        except:
            print(f"Last Action:        {last_action_date}")
    
    print("="*60)
    print(f"\nTo use this voice in text-to-speech applications, use the Speaker Profile ID:")
    print(f"\n{voice_details.get('speakerProfileId', 'N/A')}")
    print("\nExample SSML:")
    print(f"""
<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xmlns:mstts='http://www.w3.org/2001/mstts' xml:lang='en-US'>
    <voice name='DragonLatestNeural'> 
        <mstts:ttsembedding speakerProfileId='{voice_details.get('speakerProfileId', 'YOUR_SPEAKER_PROFILE_ID')}'> 
            This is my personal voice created with Azure AI Speech Service.
        </mstts:ttsembedding> 
    </voice> 
</speak>
""")

# Note: This function is now imported from audio_conversion module

def generate_unique_id(prefix):
    """Generate a unique ID with prefix and timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{prefix}-{timestamp}"

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Create a personal voice profile in Azure AI Speech Service")
    
    parser.add_argument("--consent", required=True, help="Path to consent audio file (WAV, M4A, or other audio formats)")
    parser.add_argument("--samples", required=True, nargs='+', help="Paths to sample audio files (WAV, M4A, or other audio formats)")
    parser.add_argument("--name", required=True, help="Voice talent name")
    parser.add_argument("--company", default="My Company", help="Company name")
    parser.add_argument("--locale", default="en-US", help="Locale (e.g., en-US)")
    parser.add_argument("--project-id", help="Project ID (generated if not provided)")
    parser.add_argument("--consent-id", help="Consent ID (generated if not provided)")
    parser.add_argument("--voice-id", help="Voice ID (generated if not provided)")
    
    args = parser.parse_args()
    
    # Generate IDs if not provided
    project_id = args.project_id or generate_unique_id("Project")
    consent_id = args.consent_id or generate_unique_id("Consent")
    voice_id = args.voice_id or generate_unique_id("Voice")
    
    # Verify at least 2 samples are provided
    if len(args.samples) < 2:
        print("Error: Please provide at least 2 sample audio files")
        sys.exit(1)
    
    # Convert audio files if needed
    print("\nChecking audio file formats...")
    
    # Convert consent file if needed
    converted_consent_file = convert_to_wav(args.consent)
    
    # Convert sample files if needed
    converted_sample_files = []
    temp_files = []
    
    for sample_file in args.samples:
        converted_file = convert_to_wav(sample_file)
        converted_sample_files.append(converted_file)
        # Keep track of temporary files for cleanup
        if converted_file != sample_file:
            temp_files.append(converted_file)
    
    # Create project
    project_success, project_details = create_project(project_id)
    if not project_success:
        sys.exit(1)
    
    # Upload consent
    consent_success, consent_details = upload_consent(
        project_id, 
        consent_id, 
        converted_consent_file, 
        args.name, 
        args.company, 
        args.locale
    )
    if not consent_success:
        sys.exit(1)
    
    # Create personal voice
    voice_success, voice_details = create_personal_voice(
        project_id,
        consent_id,
        voice_id,
        converted_sample_files
    )
    if not voice_success:
        sys.exit(1)
    
    # Get final status
    status_success, final_details = get_voice_status(voice_id)
    
    # Display the details
    display_voice_details(voice_details if voice_details else final_details)
    
    # Clean up any temporary files
    for temp_file in temp_files:
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except Exception as e:
            print(f"Warning: Could not remove temporary file {temp_file}: {e}")
    
    print("\n✓ Personal Voice Creation Process Completed")
    print(f"Save your Speaker Profile ID for future use: {voice_details.get('speakerProfileId', 'N/A')}")

if __name__ == "__main__":
    main()
