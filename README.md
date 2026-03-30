# Automated Dialogue Video Pipeline

A powerful, automated FFmpeg pipeline that converts audio dialogues into dynamic, landscape-oriented videos with synchronized scene images. 

## Workflow Features:
1. **auto_segment.py**: Processes raw transcripts into structured JSON dialogue trees, mapping characters and timestamps.
2. **cut_audio.py**: Parses JSON timestamps and uses FFmpeg to deeply slice continuous audio files into individual phrase-level audio segments correctly identified by speaker.
3. **search_provider.py**: Executes local or third-party reverse image searches based on dialogue context constraints to gather perfectly matched visual assets.
4. **make_video.py**: Features an extraordinarily fast `ThreadPoolExecutor` async loop to render hundreds of 1280x720 `.mp4` video clips in parallel. Overlays properly-scaled images on white canvas padding. It successfully stitches them fully intact in perfectly sequential timestamps and saves the final result locally.
5. **Colab Friendly**: Auto-detects Google Colab's Linux environment to switch seamlessly from `ffmpeg.exe` to native `ffmpeg`. Seamlessly exports to a `Dialogue_Project_Outputs` Google Drive folder when mounted. Includes auto-cleanup logic.

## Usage
Simply drop raw audio + `.txt` into the root directory and step through the automated python scripts!
