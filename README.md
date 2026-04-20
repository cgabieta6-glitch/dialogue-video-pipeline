# Dialogue Video Pipeline

> ⚠️ **Early Development Stage** — This project is still in its early stages. I will be updating this whenever I'm not busy with schoolwork. Contributions, suggestions, and feedback are welcome!

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
| 3 | `search_provider.py` | Downloads relevant images using a **18-tier fallback system** (see below) |
| 3.5a | `preview_page.py` | *(Optional)* Generates a static HTML preview page showing each dialogue paragraph alongside its image |
| 3.5b | `preview_editor.py` | *(Optional)* Interactive editor — click any image to search all 18 tiers and swap it. Changes save directly to the JSON |
| 4a | `make_video.py` | Renders all segments into 1280x720 landscape videos in parallel, stitches them into a final `.mp4`, exports to Google Drive, and auto-cleans all intermediate files |
| 4b | `make_website.py`| *(Alternative)* Generates a zero-render **Interactive Web Video Player**. Bundles audio, images, and HTML into a portable website folder you can send to anyone for instant playback in their browser. |

## 📖 Manual Execution Master Guide

If you record a new audio file (e.g., `stats_2a.m4a`) and generate a transcript (`stats_2a.m4a.txt`), follow this exact flow to process it:

### Step 1: `auto_segment.py`
**What it does:** Converts raw transcript text files into structured `.json` dialogue files with intelligent image search query generation.
```powershell
# Auto-discovers all unprocessed .txt files in the current directory (default: spaCy Smart mode)
python auto_segment.py

# Or specify files explicitly
python auto_segment.py "done stats 2a.m4a.txt" "done chem ch4.m4a.txt"

# Use KeyBERT BERT-embedding extraction (high quality semantic keywords)
python auto_segment.py --use-keybert

# Use Google Gemini Cloud LLM for best-quality queries (requires API key)
python auto_segment.py --use-gemini --gemini-api-key "YOUR_KEY"

# Use local Ollama LLM (requires Ollama running locally)
python auto_segment.py --use-llm

# Add semantic similarity boost to Smart mode (appends best visual category)
python auto_segment.py --use-semantic

# Use the full paragraph as the image search query (no processing)
python auto_segment.py --use-paragraph
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

### Step 3.5a: `preview_page.py` *(Optional — Static Preview)*
**What it does:** Generates a self-contained HTML page for quick visual review of all dialogues and their images.
```powershell
python preview_page.py
```

### Step 3.5b: `preview_editor.py` *(Optional — Interactive Editor)*
**What it does:** Launches a local web server with an **invideo.ai-style media editor**. Click any image to search all 5 tiers and swap it — changes save directly to the JSON.
```powershell
# Auto-opens in your browser
python preview_editor.py

# Specify a file & port
python preview_editor.py "done exercise no 10.json" --port 9000
```
*(Runs at `http://127.0.0.1:8090`. Press Ctrl+C to stop.)*

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

### 🧠 Image Search Query Generation (`auto_segment.py`)

`auto_segment.py` supports multiple extraction modes for generating image search queries from dialogue text. Each mode offers a different quality/speed tradeoff:

| Flag | Mode | Description | Requirements |
|------|------|-------------|--------------|
| *(default)* | **Smart** | spaCy NLP noun-chunk extraction + Named Entity Recognition. Falls back to RAKE/YAKE if spaCy is unavailable. | `pip install spacy` |
| `--use-keybert` | **KeyBERT** | BERT-embedding keyword extraction using Maximal Marginal Relevance for diverse, semantically relevant keywords. | `pip install keybert` |
| `--use-semantic` | **Semantic Boost** | Enhancement for Smart mode — appends the best-matching visual category from 48 predefined categories using cosine similarity. | `pip install sentence-transformers` |
| `--use-gemini` | **Gemini Cloud** | Google Gemini API for highest quality, context-aware query generation. Requires API key via `--gemini-api-key` or `GEMINI_API_KEY` env var. | API key only (no extra pip installs) |
| `--use-llm` | **Ollama LLM** | Local Ollama LLM for offline intelligent query generation. | [Ollama](https://ollama.ai/) running locally |
| `--use-paragraph` | **Paragraph** | Uses raw dialogue text as-is with no processing. | None |

> 💡 **Recommended for best results:** `--use-gemini` for cloud-quality queries, or the default Smart mode + `--use-semantic` for fully offline, high-quality extraction.

#### Installing NLP Dependencies
```powershell
# Full NLP stack (recommended)
pip install spacy rake-nltk yake keybert sentence-transformers

# Download spaCy's English model (auto-downloaded on first run if missing)
python -m spacy download en_core_web_sm
```

### Image Search: 3-Tier Fallback System (`search_provider.py`)

The image downloader uses a triple-tier search strategy to maximize the chances of finding a relevant image for every dialogue segment:

| Tier | Provider | Description |
|------|----------|-------------|
| 🥇 Tier 1 | **Degoog** (local) | Primary search engine. Appends `"meme funny"` to queries for more engaging, visual results. Runs locally via `http://127.0.0.1:8082`. |
| 🥈 Tier 2 | **Wikimedia Commons** | Falls back to Wikimedia's free image library if Degoog fails or returns no results. Great for educational/scientific diagrams. |
| 🥉 Tier 3 | **SearXNG** (local) | Queries the local SearXNG meta-search engine at `http://localhost:8888` for broader web image results. |
| 🎞️ Tier 4 | **Klipy** (GIF) | Searches the Klipy GIF API for animated GIFs. Requires `KLIPY_API_KEY` env variable. |
| 🎞️ Tier 5 | **Giphy** (GIF) | Searches the Giphy API for animated GIFs. Requires `GIPHY_API_KEY` env variable. |
| 📸 Tier 6 | **Unsplash** (API) | Direct Unsplash integration using provided access key. |
| 📸 Tier 7 | **Pexels** (API) | Direct Pexels integration using provided auth token. |
| 📸 Tier 8 | **Pixabay** (API) | Direct Pixabay integration using provided API key. |
| 📸 Tier 9 | **Openverse** (API) | Openly-licensed media search engine via OAuth token. |
| 🏛️ Tier 10 | **Int. Archive** (REST API) | Direct API integration with the Internet Archive image library. |
| 🌿 Tier 11 | **iNaturalist** (Botany/Bio) | Search community-verified biological research photos via iNaturalist API. |
| 🫀 Tier 12 | **Smart Servier** (Medical) | Scrapes high-quality biology, anatomy, and medical diagrams from Servier Medical Art. |
| 🏛️ Tier 13 | **PDImageArchive** (Playwright) | Utilizes a headless Chromium browser to scrape public domain historical/biological images safely from behind JS firewalls. |
| 🦜 Tier 14 | **GBIF Repo** (API) | Direct scientific integration via the Global Biodiversity Information Facility. |

If one tier fails or returns no usable images, the system automatically tries the next tier before moving on.

### ⚙️ Configuring Search Tiers (Tier Changer)
You can manually choose which search providers to use and in what order by using the `--tiers` flag:

```bash
# Default: Try all tiers in order
python search_provider.py --tiers 1,2,3,4,5

# Only use Wikimedia (Tier 2)
python search_provider.py --tiers 2

# Try SearXNG (Tier 3) first, then Degoog (Tier 1)
python search_provider.py --tiers 3,1

# Only use GIF providers (Klipy + Giphy)
python search_provider.py --tiers 4,5
```

### 🎞️ GIF Search Setup (Klipy & Giphy)
To enable GIF search via Klipy and/or Giphy, set the following environment variables with your API keys:

```powershell
# Klipy (get a free key from https://docs.klipy.com)
$env:KLIPY_API_KEY = "your_klipy_api_key_here"

# Giphy (get a free key from https://developers.giphy.com/)
$env:GIPHY_API_KEY = "your_giphy_api_key_here"
```

If the API key for a GIF tier is not set, that tier is **silently skipped** (no errors, it just moves to the next tier).

### 🖼️ Disabling "Meme" Suffix
By default, the script appends `"meme funny"` to all Degoog searches to get more expressive results. If you want cleaner, more professional images, you can disable this:

```bash
# Disable the 'meme funny' suffix
python search_provider.py --no-meme
```

### 📝 Using Paragraph Text for Search
Sometimes generating a short search query isn't enough, or you want to see what images standard providers return for the full dialogue text. You can tell the script to use the raw `paragraph` field instead of `image_search` by using the `--use-paragraph` flag:

```bash
# Use raw paragraph text for image searches
python search_provider.py --use-paragraph
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
- **NLP Libraries** *(optional but recommended for `auto_segment.py`)*:
  - `spacy` — Smart noun-chunk extraction + NER (default mode)
  - `rake-nltk` + `yake` — Statistical keyword extraction (fallback)
  - `keybert` — BERT-embedding keyword extraction
  - `sentence-transformers` — Semantic similarity visual category matching

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
