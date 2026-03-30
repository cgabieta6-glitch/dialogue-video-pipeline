import os
import shutil
import json
import subprocess
import platform
import time
import concurrent.futures

try:
    from tqdm import tqdm
except ImportError:
    # Fallback if tqdm is not installed (auto-install on Colab)
    os.system("pip install tqdm -q")
    from tqdm import tqdm

# ============================================================
# CONFIGURATION
# ============================================================

# Cross-platform FFmpeg detection (Colab-ready)
if platform.system() == "Windows":
    FFMPEG_PATH = os.path.join(os.getcwd(), "ffmpeg", "bin", "ffmpeg.exe")
    FFPROBE_PATH = os.path.join(os.getcwd(), "ffmpeg", "bin", "ffprobe.exe")
else:
    FFMPEG_PATH = "ffmpeg"
    FFPROBE_PATH = "ffprobe"

OUTPUT_DIR = "output_videos"
TEMP_DIR = "temp_segments"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

if platform.system() == "Windows" and not os.path.exists(FFMPEG_PATH):
    print(f"❌ Error: FFmpeg not found at {FFMPEG_PATH}")
    exit(1)

# Oversubscribe workers to saturate CPU (great for Colab's multi-core)
NUM_WORKERS = (os.cpu_count() or 4) * 4

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_audio_duration(path):
    """Get audio duration in seconds using ffprobe."""
    try:
        result = subprocess.run(
            [FFPROBE_PATH, "-v", "quiet", "-show_entries", "format=duration",
             "-of", "csv=p=0", path],
            capture_output=True, text=True, timeout=10
        )
        return float(result.stdout.strip())
    except Exception:
        return 5.0  # Safe fallback


def generate_chunk(args):
    """Render one dialogue segment as a video chunk. Designed for parallel execution."""
    item, segment_idx, audio_folder, raw_name, images_folder = args

    segment_id = item.get("id")
    if segment_id is None:
        return segment_idx, None

    char_str = item.get("character", "00")
    speaker_id = char_str.split("_")[1] if "_" in char_str else "00"

    counter = segment_id + 1
    audio_file = os.path.join(audio_folder, f"speaker{int(speaker_id)}_audio_{counter}.mp3")

    if not os.path.exists(audio_file):
        return segment_idx, None

    image_file = item.get("image")
    if image_file and not os.path.exists(image_file):
        image_file = None

    output_seg = os.path.join(TEMP_DIR, f"{raw_name}_seg_{segment_id}.mp4")

    # Skip if already rendered (resume support)
    if os.path.exists(output_seg) and os.path.getsize(output_seg) > 0:
        return segment_idx, output_seg

    # Get precise duration from audio
    duration = get_audio_duration(audio_file)

    if image_file:
        command = [
            FFMPEG_PATH, "-y", "-hide_banner", "-loglevel", "error",
            "-loop", "1",
            "-i", image_file,
            "-i", audio_file,
            "-t", str(duration + 0.1),
            "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2:white,format=yuv420p",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
            "-r", "30",
            "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
            "-shortest", output_seg
        ]
    else:
        # White screen fallback
        command = [
            FFMPEG_PATH, "-y", "-hide_banner", "-loglevel", "error",
            "-f", "lavfi", "-i", f"color=c=white:s=1280x720:r=30:d={duration + 0.1}",
            "-i", audio_file,
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
            "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
            "-shortest", output_seg
        ]

    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            return segment_idx, None
        return segment_idx, output_seg
    except Exception:
        return segment_idx, None


# ============================================================
# MAIN PIPELINE
# ============================================================

# Find all JSON guide files
json_files = sorted([f for f in os.listdir('.') if f.startswith('done ') and f.endswith('.json')])

if not json_files:
    print("❌ No JSON files found starting with 'done '")
    exit(0)

print(f"📋 Found {len(json_files)} JSON files to process")
print(f"⚡ Using {NUM_WORKERS} parallel workers\n")

overall_start = time.time()

for jf in json_files:
    print(f"\n{'=' * 60}")
    print(f"🎬  Processing: {jf}")
    print(f"{'=' * 60}")

    with open(jf, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Determine the audio folder
    raw_name = jf.replace('done ', '').replace('.json', '')
    if raw_name.endswith('.m4a'):
        raw_name = raw_name[:-4]

    audio_folder = raw_name.replace('_', ' ')

    if not os.path.isdir(audio_folder) and os.path.isdir(raw_name):
        audio_folder = raw_name

    if not os.path.isdir(audio_folder):
        print(f"  ⚠️  Skipping {jf}: Audio folder '{audio_folder}' not found.")
        continue

    # Determine images folder
    images_folder = jf.replace('.json', '_images')

    final_video = os.path.join(OUTPUT_DIR, f"{raw_name}.mp4")

    # Skip if already fully rendered
    if os.path.exists(final_video) and os.path.getsize(final_video) > 1000:
        print(f"  ⏭️  Already complete: {final_video}, skipping.")
        continue

    total_count = len(data)
    print(f"  📊 {total_count} segments to render")
    print(f"  🎙️ Audio folder: {audio_folder}/")
    print(f"  🖼️ Images folder: {images_folder}/")

    # ── PARALLEL RENDERING ──────────────────────────────────
    start_time = time.time()

    # Prepare argument tuples for the worker function
    task_args = [
        (item, idx, audio_folder, raw_name, images_folder)
        for idx, item in enumerate(data)
    ]

    # Results array indexed by position to preserve order
    chunk_results = [None] * total_count

    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = {
            executor.submit(generate_chunk, arg): arg[1]
            for arg in task_args
        }

        for future in tqdm(
            concurrent.futures.as_completed(futures),
            total=total_count,
            desc=f"  ⚡ Rendering {raw_name}",
            unit="chunk"
        ):
            idx = futures[future]
            try:
                result_idx, result_path = future.result()
                chunk_results[result_idx] = result_path
            except Exception as e:
                print(f"\n  ❌ Chunk {idx} error: {e}")

    # Count successes
    successful = [r for r in chunk_results if r is not None]
    elapsed = time.time() - start_time
    print(f"\n  ✅ {len(successful)}/{total_count} chunks rendered in {elapsed:.1f}s")

    if not successful:
        print(f"  ❌ No valid segments for {jf}")
        continue

    # ── CONCATENATION ───────────────────────────────────────
    print(f"  🔗 Stitching into final video...")
    concat_file_path = os.path.join(TEMP_DIR, f"concat_{raw_name}.txt")

    with open(concat_file_path, "w", encoding="utf-8") as cf:
        for seg in chunk_results:
            if seg and os.path.exists(seg):
                safe_path = os.path.abspath(seg).replace('\\', '/')
                cf.write(f"file '{safe_path}'\n")

    concat_cmd = [
        FFMPEG_PATH, "-y", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0",
        "-i", concat_file_path,
        "-c", "copy", final_video
    ]

    try:
        subprocess.run(concat_cmd, check=True, capture_output=True)
        size_mb = os.path.getsize(final_video) / (1024 * 1024)
        print(f"  🏁 SUCCESS: {final_video} ({size_mb:.1f} MB)")

        # ── AUTO-EXPORT TO GOOGLE DRIVE (IF MOUNTED) ──────
        drive_output_path = "/content/drive/MyDrive/Dialogue_Project_Outputs"
        if os.path.exists("/content/drive/MyDrive"):
            os.makedirs(drive_output_path, exist_ok=True)
            dest_path = os.path.join(drive_output_path, f"{raw_name}.mp4")
            print(f"  💾 Exporting to Google Drive: {dest_path}...")
            shutil.copy2(final_video, dest_path)
            print("  ✅ Export complete.")

        # Clean up concat list
        os.remove(concat_file_path)

        # Clean up temp segment files for this video
        for seg in chunk_results:
            if seg and os.path.exists(seg):
                try:
                    os.remove(seg)
                except:
                    pass

        # ── AUTO-CLEANUP ────────────────────────────────────
        print(f"  🧹 Cleaning up source files for {raw_name}...")
        base_space = raw_name.replace('_', ' ')
        base_under = raw_name.replace(' ', '_')

        files_to_delete = [
            jf,
            f"done {base_space}.m4a", f"done {base_under}.m4a",
            f"done {base_space}.m4a.txt", f"done {base_under}.m4a.txt",
            f"done {base_space}.json", f"done {base_under}.json",
            f"done {base_space}.m4a.json", f"done {base_under}.m4a.json"
        ]

        dirs_to_delete = [
            audio_folder,
            jf.replace('.json', '_images'),
            f"done {base_space}_images", f"done {base_under}_images",
            f"done {base_space}.m4a_images", f"done {base_under}.m4a_images"
        ]

        for f_path in files_to_delete:
            if os.path.exists(f_path) and os.path.isfile(f_path):
                try:
                    os.remove(f_path)
                    print(f"    🗑️ Deleted: {f_path}")
                except Exception as e:
                    print(f"    ⚠️ Could not delete {f_path}: {e}")

        for d_path in dirs_to_delete:
            if os.path.exists(d_path) and os.path.isdir(d_path):
                try:
                    shutil.rmtree(d_path)
                    print(f"    🗑️ Deleted: {d_path}/")
                except Exception as e:
                    print(f"    ⚠️ Could not delete {d_path}: {e}")

        print(f"  ✅ Cleanup for {raw_name} finished.")

    except Exception as e:
        print(f"  ❌ FAILED to concatenate final video: {e}")

# ============================================================
# FINAL SUMMARY
# ============================================================
total_elapsed = time.time() - overall_start
print(f"\n{'=' * 60}")
print(f"🏁  ALL VIDEOS RENDERED!")
print(f"    Total time: {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")
print(f"    Output folder: {os.path.abspath(OUTPUT_DIR)}")
print(f"{'=' * 60}")

# List final videos
for vid in os.listdir(OUTPUT_DIR):
    vid_path = os.path.join(OUTPUT_DIR, vid)
    if os.path.isfile(vid_path):
        sz = os.path.getsize(vid_path) / (1024 * 1024)
        print(f"    🎬 {vid} ({sz:.1f} MB)")
