#!/usr/bin/env python3
"""
Audio Conversion Module for Azure AI Speech Service
This module provides functions to convert audio files to WAV format suitable for Azure AI Speech Service

Requirements:
- See requirements.txt for dependencies
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

# Import pydub for audio processing
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    # We keep this try/except since pydub is optional with ffmpeg fallback
    PYDUB_AVAILABLE = False

def check_ffmpeg(quiet=False):
    """
    Check if FFmpeg is installed
    
    Args:
        quiet (bool): Whether to suppress console output
        
    Returns:
        bool: True if FFmpeg is installed, False otherwise
    """
    try:
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        if not quiet:
            print("✓ FFmpeg is installed")
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        if not quiet:
            print("✗ FFmpeg is not installed")
        return False

def convert_to_wav(input_file, output_file=None, quiet=False):
    """
    Convert an audio file to WAV format (16-bit PCM, 16kHz, mono)
    
    Args:
        input_file (str): Path to the input audio file
        output_file (str, optional): Path to save the output WAV file.
                                    If not provided, a temp file will be created.
        quiet (bool): Whether to suppress console output
        
    Returns:
        tuple: (success (bool), output_file_path (str))
    """
    if not os.path.exists(input_file):
        if not quiet:
            print(f"Input file not found: {input_file}")
        return False, None
    
    # Get the file extension
    file_extension = Path(input_file).suffix.lower()
    
    # If already a WAV file, return the path
    if file_extension == '.wav':
        return True, input_file
    
    # Create output file path if not provided
    if not output_file:
        fd, output_file = tempfile.mkstemp(suffix='.wav')
        os.close(fd)
    
    if not quiet:
        print(f"Converting {os.path.basename(input_file)} to WAV format...")
    
    # Try with pydub if available
    if PYDUB_AVAILABLE:
        try:
            if not quiet:
                print("Using pydub for conversion...")
            audio = AudioSegment.from_file(input_file)
            audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
            audio.export(output_file, format="wav")
            if not quiet:
                print(f"✓ Conversion successful: {os.path.basename(output_file)}")
                print(f"  - Duration: {len(audio)/1000:.2f} seconds")
                print(f"  - Channels: {audio.channels}")
                print(f"  - Sample rate: {audio.frame_rate} Hz")
                print(f"  - Sample width: {audio.sample_width} bytes")
            return True, output_file
        except Exception as e:
            if not quiet:
                print(f"⚠️ Pydub conversion failed: {e}")
                print("Falling back to FFmpeg...")
            # If pydub failed, try FFmpeg if available
            return convert_to_wav_with_ffmpeg(input_file, output_file, quiet)
    else:
        # If pydub is not available, try FFmpeg
        return convert_to_wav_with_ffmpeg(input_file, output_file, quiet)

def convert_to_wav_with_ffmpeg(input_file, output_file, quiet=False):
    """
    Convert an audio file to WAV format using FFmpeg
    
    Args:
        input_file (str): Path to the input audio file
        output_file (str): Path to save the output WAV file
        quiet (bool): Whether to suppress console output
        
    Returns:
        tuple: (success (bool), output_file_path (str))
    """
    # Check if FFmpeg is installed
    if not check_ffmpeg(quiet):
        if not quiet:
            print("⚠️ FFmpeg is not installed. Please install FFmpeg to enable audio conversion.")
            print("   For Ubuntu/Debian: sudo apt-get install ffmpeg")
            print("   For macOS: brew install ffmpeg")
            print("   For Windows: Download from https://ffmpeg.org/download.html")
        return False, None
    
    try:
        if not quiet:
            print("Using FFmpeg for conversion...")
        
        # Use FFmpeg to convert to WAV format (16-bit PCM, 16kHz)
        subprocess.run([
            'ffmpeg',
            '-i', input_file,
            '-acodec', 'pcm_s16le',
            '-ac', '1',
            '-ar', '16000',
            output_file
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        
        if not quiet:
            print(f"✓ Conversion successful: {os.path.basename(output_file)}")
            
            # Get information about the converted file
            try:
                info = subprocess.run([
                    'ffprobe',
                    '-v', 'error',
                    '-select_streams', 'a:0',
                    '-show_entries', 'stream=duration,channels,sample_rate,bits_per_sample',
                    '-of', 'default=noprint_wrappers=1:nokey=0',
                    output_file
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                print(info.stdout.decode('utf-8'))
            except:
                pass
        
        return True, output_file
    except subprocess.CalledProcessError as e:
        if not quiet:
            print(f"✗ FFmpeg conversion failed: {e}")
        if os.path.exists(output_file):
            os.remove(output_file)
        return False, None

def get_audio_info(audio_file, quiet=False):
    """
    Get information about an audio file using FFmpeg
    
    Args:
        audio_file (str): Path to the audio file
        quiet (bool): Whether to suppress console output
        
    Returns:
        dict: Audio file information or None if error
    """
    if not check_ffmpeg(True):
        return None
    
    try:
        result = subprocess.run([
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'a:0',
            '-show_entries', 'stream=duration,channels,sample_rate,bits_per_sample',
            '-of', 'json',
            audio_file
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        
        import json
        info = json.loads(result.stdout.decode('utf-8'))
        return info
    except Exception as e:
        if not quiet:
            print(f"Error getting audio info: {e}")
        return None

def convert_files_to_wav(file_list, quiet=False):
    """
    Convert multiple files to WAV format
    
    Args:
        file_list (list): List of file paths to convert
        quiet (bool): Whether to suppress console output
        
    Returns:
        tuple: (converted_files (list), temp_files (list))
    """
    converted_files = []
    temp_files = []
    
    for file_path in file_list:
        success, converted_file = convert_to_wav(file_path, quiet=quiet)
        if success:
            converted_files.append(converted_file)
            # Track temporary files for cleanup
            if converted_file != file_path:
                temp_files.append(converted_file)
        else:
            if not quiet:
                print(f"Error converting {file_path}")
    
    return converted_files, temp_files

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Convert audio files to WAV format suitable for Azure AI Speech Service")
    parser.add_argument("input", help="Path to input audio file")
    parser.add_argument("--output", help="Path to output WAV file (optional)")
    parser.add_argument("--quiet", action="store_true", help="Suppress detailed output")
    
    args = parser.parse_args()
    
    if not args.quiet:
        print("\nAudio Conversion")
        print("===============")
        
        # Check for pydub
        if PYDUB_AVAILABLE:
            print("pydub library: Available")
        else:
            print("pydub library: Not installed (you can install with 'pip install pydub')")
        
        # Check for FFmpeg
        check_ffmpeg()
    
    # Convert the file
    success, output_file = convert_to_wav(args.input, args.output, quiet=args.quiet)
    
    if success:
        if not args.quiet:
            print(f"\n✓ Audio conversion successful: {output_file}")
        else:
            print(output_file)
        return 0
    else:
        if not args.quiet:
            print("\n✗ Audio conversion failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
