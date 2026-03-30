# Dialogue Video Pipeline

> ⚠️ **Early Development Stage** — This project is still in its early stages. I'm a college student and will be updating this whenever I'm not busy with schoolwork. Contributions, suggestions, and feedback are welcome!

An automated pipeline that transforms **NotebookLM Audio Overview** `.m4a` files into polished, landscape-oriented dialogue videos with synchronized scene images — powered by FFmpeg and parallel processing.

## How It Works

### Source Material
1. **Generate audio** using [Google NotebookLM](https://notebooklm.google.com/) Audio Overview feature — this produces a `.m4a` dialogue file between two AI speakers.
2. **Transcribe the audio** using the included **[WhisperX for Transcribing NotebookLM Audio Overview.ipynb](https://colab.research.google.com/)** Colab notebook — this generates a timestamped `.txt` transcript with speaker labels.

### Pipeline Scripts (Run in Order)

| # | Script | What It Does |
|---|--------|-------------|
| 1 | `auto_segment.py` | Converts raw `.txt` transcripts into structured `.json` dialogue files with speaker IDs, paragraphs, and image search terms |
| 2 | `cut_audio.py` | Uses FFmpeg to slice the full `.m4a` audio into individual speaker segments based on timestamps |
| 3 | `search_provider.py` | Downloads relevant images using a **3-tier fallback system** (see below) |
| 4 | `make_video.py` | Renders all segments into 1280×720 landscape videos in parallel, stitches them into a final `.mp4`, exports to Google Drive, and auto-cleans all intermediate files |

## 📖 Manual Execution Master Guide

If you record a new audio file (e.g., `stats_2a.m4a`) and generate a transcript (`stats_2a.m4a.txt`), follow this exact flow to process it:

### Step 1: `auto_segment.py`
**What it does:** Converts raw transcript text files into structured `.json` dialogue files.
```powershell
python auto_segment.py
```

### Step 2: `cut_audio.py`
**What it does:** Slices your single audio file into hundreds of tiny speaker-specific `.mp3` clips.
```powershell
python cut_audio.py
```
*(Creates a folder called `stats 2a/` for the segments).*

### Step 3: `search_provider.py`
**What it does:** Downloads relevant images for every sentence and updates the `.json`.
```powershell
# Optional: use --tiers to customize search providers
python search_provider.py --tiers 1,2,3
```
*(Images are saved in `done stats 2a.m4a_images/`).*

### Step 4: `make_video.py`
**What it does:** The final step. Renders and stitches everything into an `.mp4`.
```powershell
python make_video.py
```
*(On Google Colab, this runs in parallel for maximum speed).*

### Step 5: `cleanup.py` (Optional)
**What it does:** This is now mostly **automated**! `make_video.py` will automatically shred the leftover assets (JSON, audio folders, etc.) once the video is finished. You only need to run `cleanup.py` if you want to manually wipe files that were interrupted.

## 🐳 Local Search Provider Setup (Docker)

To enable image downloading, you must run the local search providers (Degoog and SearXNG). The easiest way to do this is using **Docker Desktop**.

### 1. Prerequisites
- **Docker Desktop** installed and running on your machine.
- **Port 8080** (SearXNG) and **Port 8082** (Degoog) must be available.

### 2. Start Services
Run the following command in your project root:
```powershell
docker-compose up -d
```
This will start both search providers in the background.

### 3. Verify Connections
- **SearXNG**: [http://localhost:8080](http://localhost:8080)
- **Degoog**: [http://127.0.0.1:8082](http://127.0.0.1:8082)

Once started, `search_provider.py` will automatically detect and use these services to download your images.

### 💡 Pro Tip: Using AI for Better Image Search Terms
For the best visual storytelling, your `image_search` terms should be **descriptive, specific, and unique**. Instead of just "data", use "Data Visualization Abstract Glowing Grid".

You can use ChatGPT, Gemini, or Claude to **"Level Up"** these terms. While `auto_segment.py` provides a great baseline (as seen in [**done stats 2a.m4a.json**](./done%20stats%202a.m4a.json)), using a dedicated LLM can generate much more creative and visually impactful terms.

**Example "Polishing" Prompt:**
> "I have a JSON file with dialogue and basic image search terms. For each entry, please rewrite the 'image_search' field to be more cinematic and professional (e.g., instead of 'data chart', use 'Holographic 3D Data Visualization'). Keep the other fields the same."

### ⚠️ Troubleshooting Port Conflicts
If you encounter a "Port is already in use" error:
1. Open Task Manager and stop any applications using those ports.
2. Or, modify the `docker-compose.yml` and `search_provider.py` to use different ports.

### Image Search: 3-Tier Fallback System (`search_provider.py`)

The image downloader uses a triple-tier search strategy to maximize the chances of finding a relevant image for every dialogue segment:

| Tier | Provider | Description |
|------|----------|-------------|
| 🥇 Tier 1 | **Degoog** (local) | Primary search engine. Appends `"meme funny"` to queries for more engaging, visual results. Runs locally via `http://127.0.0.1:8082`. |
| 🥈 Tier 2 | **Wikimedia Commons** | Falls back to Wikimedia's free image library if Degoog fails or returns no results. Great for educational/scientific diagrams. |
| 🥉 Tier 3 | **SearXNG** (local) | Last resort fallback. Queries the local SearXNG meta-search engine at `http://localhost:8080` for broader web image results. |

If one tier fails or returns no usable images, the system automatically tries the next tier before moving on.

### ⚙️ Configuring Search Tiers (Tier Changer)
You can manually choose which search providers to use and in what order by using the `--tiers` flag:

```bash
# Default: Try Degoog, then Wikimedia, then SearXNG
python search_provider.py --tiers 1,2,3

# Only use Wikimedia (Tier 2)
python search_provider.py --tiers 2

# Try SearXNG (Tier 3) first, then Degoog (Tier 1)
python search_provider.py --tiers 3,1
```

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
- [ ] **Custom Voice & Character Visuals** — Since NotebookLM Audio Overview and free Google Gemini TTS don't offer custom voice options, add support for custom TTS engines (e.g., Coqui XTTSv2, ElevenLabs, Chatterbox) so users can clone any voice. Pair this with **character speaker images** (PNG/transparent) displayed on screen — similar to the viral AI Peter Griffin & Stewie Griffin shorts where two characters talk to each other. The layout would feature character PNGs at the bottom, **b-roll images floating on top** for visual context, and a **gameplay or background video** playing behind everything to keep viewers engaged.
- [ ] **PDF / PPTX Image Extraction** — Allow `search_provider.py` to search for and extract relevant images directly from PDF or PowerPoint files provided as input, instead of (or in addition to) downloading from the web. Perfect for educational content where the source material already contains the best diagrams.
- [ ] **Batch Processing UI** — A simple web interface or CLI menu for drag-and-drop batch processing of multiple audio files.
- [ ] **Smart Image Caching** — Cache previously downloaded images to avoid redundant searches across similar topics.
- [ ] **Subtitle / Caption Overlay** — Burn speaker subtitles directly into the video for accessibility.
- [ ] **One-Click Automator** — A single script that takes just a raw NotebookLM Audio Overview `.m4a` file as input and automatically runs the entire pipeline end-to-end (transcribe → segment → search images → render video) with zero manual steps. Just drop in your `.m4a` and get a finished video out.
- [ ] **Remotion / Revideo Integration** — Migrate the video rendering engine from raw FFmpeg commands to [Remotion](https://remotion.dev/) or [Revideo](https://re.video/) for more powerful, React-based video composition. This would unlock features like animated text overlays, smooth transitions between scenes, dynamic layouts, and much more polished visual output.

> 💡 *If you have ideas or want to contribute, feel free to open an issue or pull request!*
