import re
import subprocess
import os
import shutil
from concurrent.futures import ThreadPoolExecutor

# Explicitly set the path to the ffmpeg executable we just downloaded
FFMPEG_PATH = os.path.join(os.getcwd(), "ffmpeg", "bin", "ffmpeg.exe")

def to_seconds(t_str):
    h, m, s = t_str.split(':')
    s, ms = s.split(',')
    return int(h)*3600 + int(m)*60 + int(s) + int(ms)/1000.0

def process_segment(match_data, audio_file, base_folder, counter):
    start_time = match_data['start_time']
    end_time = match_data['end_time']
    speaker_id = match_data['speaker_id']
    
    output_filename = f"speaker{int(speaker_id)}_audio_{counter}.mp3"
    full_output_path = os.path.join(base_folder, output_filename)
    
    if os.path.exists(full_output_path):
        return True
        
    duration = float(end_time) - float(start_time)
    
    # Using the explicit FFMPEG_PATH with fast seeking (-ss before -i)
    command = [
        FFMPEG_PATH,
        "-y",
        "-ss", str(start_time),
        "-i", audio_file,
        "-t", str(duration),
        "-q:a", "0",
        "-map", "a",
        full_output_path
    ]
    
    try:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        print(f"Error cutting {output_filename}: {e}")
        return False

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

    # Try multiple encodings (some Windows apps save as UTF-16 with BOM)
    content = None
    for enc in ['utf-8-sig', 'utf-16', 'utf-8']:
        try:
            with open(transcript_file, 'r', encoding=enc) as f:
                content = f.read()
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    if content is None:
        print(f"Error: Could not decode {transcript_file} with any known encoding.")
        return False
    
    # Regex to match the old format
    pattern_old = r'\[([\d\.]+)s - ([\d\.]+)s\] \[(SPEAKER_(\d+))\]:'
    matches_old = list(re.finditer(pattern_old, content))
    
    # Regex to match the new format
    pattern_new = r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})\s*\n(?:\[.*?\]\s*)?\[(SPEAKER_(\d+))\]:'
    matches_new = list(re.finditer(pattern_new, content))
    
    parsed_matches = []
    if matches_old:
        for m in matches_old:
            parsed_matches.append({
                'start_time': m.group(1),
                'end_time': m.group(2),
                'speaker_id': m.group(4)
            })
    elif matches_new:
        for m in matches_new:
            parsed_matches.append({
                'start_time': str(to_seconds(m.group(1))),
                'end_time': str(to_seconds(m.group(2))),
                'speaker_id': m.group(4)
            })
    
    print(f"File: {audio_file} - Total segments found: {len(parsed_matches)}")
    
    if len(parsed_matches) == 0:
        return False
        
    error_occurred = False
    print(f"Slicing segments for {audio_file} in parallel...")
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = []
        for i, match in enumerate(parsed_matches, start=1):
            futures.append(executor.submit(process_segment, match, audio_file, base_folder, i))
            
        for future in futures:
            if not future.result():
                error_occurred = True
                
    if not error_occurred:
        print(f"Successfully processed {audio_file}. Segments are in: {base_folder}")
        
        # Rename the original files with "done " prefix
        done_audio = f"done {audio_file}"
        transcript_basename = os.path.basename(transcript_file)
        # Avoid double 'done '
        if not transcript_basename.startswith('done '):
            done_transcript = os.path.join(os.path.dirname(transcript_file), f"done {transcript_basename}")
        else:
            done_transcript = transcript_file
            
        try:
            os.rename(audio_file, done_audio)
            print(f"Renamed {audio_file} -> {done_audio}")
            
            if transcript_file != done_transcript:
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
        # Auto-discover all unprocessed .m4a files (no "done" prefix)
        files = [f for f in os.listdir('.') if f.endswith('.m4a') and not f.startswith('done ')]
        
        if not files:
            print("No new audio files to process.")
        else:
            print(f"Found {len(files)} files to process.")
            for audio_file in files:
                base_name = os.path.splitext(audio_file)[0]
                # Check for both .m4a.txt and .txt
                transcript_file_1 = f"{audio_file}.txt"
                transcript_file_2 = f"{base_name}.txt"
                
                if os.path.exists(transcript_file_1):
                    cut_audio(audio_file, transcript_file_1)
                elif os.path.exists(transcript_file_2):
                    cut_audio(audio_file, transcript_file_2)
                else:
                    print(f"Skipping {audio_file} - No transcript file found.")
            print("\nAll tasks completed!")

