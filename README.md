# Dialogue Video Pipeline

> ⚠️ **Early Development Stage** — This project is still in its early stages. I'm a college student and will be updating this whenever I'm not busy with schoolwork. Contributions, suggestions, and feedback are welcome!

An automated pipeline that transforms **NotebookLM Audio Overview** `.m4a` files into polished, landscape-oriented dialogue videos with synchronized scene images — powered by FFmpeg and parallel processing.

## How It Works

### Source Material
1. **Generate audio** using [Google NotebookLM](https://notebooklm.google.com/) Audio Overview feature — this produces a `.m4a` dialogue file between two AI speakers.
2. **Transcribe the audio** using the included **[Chatterbox Turbo for Transcribing NotebookLM Audio Overview.ipynb](https://colab.research.google.com/)** Colab notebook — this generates a timestamped `.txt` transcript with speaker labels.

### Pipeline Scripts (Run in Order)

| # | Script | What It Does |
|---|--------|-------------|
| 1 | `auto_segment.py` | Converts raw `.txt` transcripts into structured `.json` dialogue files with speaker IDs, paragraphs, and image search terms |
| 2 | `cut_audio.py` | Uses FFmpeg to slice the full `.m4a` audio into individual speaker segments based on timestamps |
| 3 | `search_provider.py` | Downloads relevant images using a **3-tier fallback system** (see below) |
| 4 | `make_video.py` | Renders all segments into 1280×720 landscape videos in parallel, stitches them into a final `.mp4`, exports to Google Drive, and auto-cleans all intermediate files |

### Image Search: 3-Tier Fallback System (`search_provider.py`)

The image downloader uses a triple-tier search strategy to maximize the chances of finding a relevant image for every dialogue segment:

| Tier | Provider | Description |
|------|----------|-------------|
| 🥇 Tier 1 | **Degoog** (local) | Primary search engine. Appends `"meme funny"` to queries for more engaging, visual results. Runs locally via `http://127.0.0.1:8082`. |
| 🥈 Tier 2 | **Wikimedia Commons** | Falls back to Wikimedia's free image library if Degoog fails or returns no results. Great for educational/scientific diagrams. |
| 🥉 Tier 3 | **SearXNG** (local) | Last resort fallback. Queries the local SearXNG meta-search engine at `http://localhost:8080` for broader web image results. |

If one tier fails or returns no usable images, the system automatically tries the next tier before moving on.

## File Naming Convention

The pipeline uses a **`done` prefix** to track which files have been processed:

| File | Meaning |
|------|---------|
| `stats 2a.m4a` | ❌ Raw, unprocessed audio |
| `done stats 2a.m4a` | ✅ Audio has been processed (segmented) |
| `stats 2a.m4a.txt` | ❌ Raw, unprocessed transcript |
| `done stats 2a.m4a.txt` | ✅ Transcript has been processed |
| `done stats 2a.m4a.json` | ✅ Structured JSON guide (generated from transcript) |

## Example: Processing `stats 2a`

Here is what the project directory looks like at each stage, using `stats 2a` as a sample:

### After running all scripts (before cleanup):
```
project/
├── done stats 2a.m4a              # Original audio (marked as processed)
├── done stats 2a.m4a.txt          # Original transcript (marked as processed)
├── done stats 2a.m4a.json         # JSON dialogue guide
├── stats 2a/                      # Audio segments folder
│   ├── speaker0_audio_1.mp3
│   ├── speaker1_audio_2.mp3
│   ├── speaker0_audio_3.mp3
│   └── ...
├── done stats 2a.m4a_images/      # Downloaded scene images
│   ├── probability_distribution.jpg
│   ├── sampling_bias_chart.png
│   └── ...
└── output_videos/
    └── stats 2a.mp4               # ✅ Final rendered video
```

### After auto-cleanup (automatic):
```
project/
└── output_videos/
    └── stats 2a.mp4               # ✅ Only the final video remains
```

> **Auto-cleanup:** As soon as `make_video.py` successfully generates the final `.mp4` output, it automatically deletes all intermediate files — the `.m4a`, `.txt`, `.json`, audio segments folder, and images folder. Only the finished video survives.

## Google Colab Support

The `make_video.py` script is designed to run on **Google Colab** for faster rendering:

- **Cross-platform:** Automatically detects Windows (local FFmpeg) vs Linux (Colab's built-in FFmpeg)
- **Parallel rendering:** Uses `ThreadPoolExecutor` with `CPU cores × 4` workers for maximum speed
- **Auto-export to Drive:** If Google Drive is mounted, finished videos are automatically copied to `My Drive/Dialogue_Project_Outputs/`

### Quick Start on Colab
```python
from google.colab import drive
drive.mount('/content/drive')

import os, zipfile

zip_path = "/content/drive/MyDrive/project.zip"
extract_path = "/content/project_work"

with zipfile.ZipFile(zip_path, 'r') as z:
    z.extractall(extract_path)

# Find and run the script
for root, dirs, files in os.walk(extract_path):
    if "make_video.py" in files:
        %cd {root}
        !python make_video.py
        break
```

## Setup & Requirements

### 1. Install FFmpeg
The pipeline requires FFmpeg to handle all video and audio processing.
- **Windows:** [Download FFmpeg (Builds by gyan.dev)](https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z). Extract it and ensure the `ffmpeg/bin` folder is in your project root or your system PATH.
- **Google Colab:** Pre-installed (the script handles the setup automatically).

### 2. Python Dependencies
- **Python 3.10+**
- **tqdm** (`pip install tqdm` — auto-installed by the script if missing)

### 3. Image Search
- Local image search services (Degoog/SearXNG) are required for `search_provider.py`.

## Roadmap / Planned Updates

This project is actively being developed. Here are the features I'm planning to add:

- [ ] **Improved Pacing & Dynamic Scene Changes** — Currently, if a character speaks a long paragraph (e.g., 20+ seconds), the video stays on a single image, which can feel slow and less dynamic. The fix: generate a new image (with a new `image_search` query) for every *sentence* instead of every paragraph, so the visuals change more frequently and keep viewers engaged.
- [ ] **Custom Voice Options** — Add support for custom TTS voices (e.g., Coqui XTTSv2, ElevenLabs) so users can replace the default NotebookLM speakers with their own character voices.
- [ ] **PDF / PPTX Image Extraction** — Allow `search_provider.py` to search for and extract relevant images directly from PDF or PowerPoint files provided as input, instead of (or in addition to) downloading from the web. Perfect for educational content where the source material already contains the best diagrams.
- [ ] **Batch Processing UI** — A simple web interface or CLI menu for drag-and-drop batch processing of multiple audio files.
- [ ] **Smart Image Caching** — Cache previously downloaded images to avoid redundant searches across similar topics.
- [ ] **Subtitle / Caption Overlay** — Burn speaker subtitles directly into the video for accessibility.
- [ ] **One-Click Automator** — A single script that takes just a raw NotebookLM Audio Overview `.m4a` file as input and automatically runs the entire pipeline end-to-end (transcribe → segment → search images → render video) with zero manual steps. Just drop in your `.m4a` and get a finished video out.
- [ ] **Remotion / Revideo Integration** — Migrate the video rendering engine from raw FFmpeg commands to [Remotion](https://remotion.dev/) or [Revideo](https://re.video/) for more powerful, React-based video composition. This would unlock features like animated text overlays, smooth transitions between scenes, dynamic layouts, and much more polished visual output.

> 💡 *If you have ideas or want to contribute, feel free to open an issue or pull request!*
