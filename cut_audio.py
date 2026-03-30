import re
import subprocess
import os
import shutil

# Explicitly set the path to the ffmpeg executable we just downloaded
FFMPEG_PATH = os.path.join(os.getcwd(), "ffmpeg", "bin", "ffmpeg.exe")

def cut_audio(audio_file, transcript_file):
    # Get filename without extension for the folder name
    base_folder = os.path.splitext(audio_file)[0]
    
    # Create the target directory if it doesn't exist
    if not os.path.exists(base_folder):
        print(f"\nCreating directory: {base_folder}")
        os.makedirs(base_folder)
    
    # Check if files exist
    if not os.path.exists(audio_file) or not os.path.exists(transcript_file):
        print(f"Error: {audio_file} or {transcript_file} not found.")
        return False

    with open(transcript_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Regex to match the timestamps and speaker
    pattern = r'\[([\d\.]+)s - ([\d\.]+)s\] \[(SPEAKER_(\d+))\]:'
    matches = list(re.finditer(pattern, content))
    
    print(f"File: {audio_file} - Total segments found: {len(matches)}")
    
    counter = 1
    error_occurred = False
    for match in matches:
        start_time = match.group(1)
        end_time = match.group(2)
        speaker_id = match.group(4)
        
        output_filename = f"speaker{int(speaker_id)}_audio_{counter}.mp3"
        full_output_path = os.path.join(base_folder, output_filename)
        
        if os.path.exists(full_output_path):
            counter += 1
            continue
            
        print(f"Cutting {output_filename} ({start_time}s to {end_time}s)...")
        
        # Using the explicit FFMPEG_PATH
        command = [
            FFMPEG_PATH,
            "-y",
            "-i", audio_file,
            "-ss", start_time,
            "-to", end_time,
            "-q:a", "0",
            "-map", "a",
            full_output_path
        ]
        
        try:
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"Error cutting {output_filename}: {e}")
            error_occurred = True
            break
        
        counter += 1

    if not error_occurred:
        print(f"Successfully processed {audio_file}. Segments are in: {base_folder}")
        
        # Rename the original files with "done " prefix
        done_audio = f"done {audio_file}"
        done_transcript = f"done {transcript_file}"
        
        try:
            os.rename(audio_file, done_audio)
            print(f"Renamed {audio_file} -> {done_audio}")
            
            os.rename(transcript_file, done_transcript)
            print(f"Renamed {transcript_file} -> {done_transcript}")
            return True
        except Exception as e:
            print(f"Error renaming files: {e}")
            return False
    return False

if __name__ == "__main__":
    if not os.path.exists(FFMPEG_PATH):
        print(f"Error: FFmpeg not found at {FFMPEG_PATH}")
    else:
        # Get all .m4a files that don't start with "done"
        files = [f for f in os.listdir('.') if f.endswith('.m4a') and not f.startswith('done')]
        
        if not files:
            print("No new audio files to process.")
        else:
            print(f"Found {len(files)} files to process: {', '.join(files)}")
            for audio_file in files:
                transcript_file = f"{audio_file}.txt"
                if os.path.exists(transcript_file):
                    cut_audio(audio_file, transcript_file)
                else:
                    # Special check for user-mentioned potential typo (stats 2b using stats 1 transcript)
                    # Although we saw stats 2b.m4a.txt in the list_dir earlier
                    print(f"Skipping {audio_file} - No transcript file found.")
            print("\nAll tasks completed!")
