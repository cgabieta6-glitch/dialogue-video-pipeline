# Dialogue Video Pipeline

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
| 3 | `search_provider.py` | Downloads relevant images for each dialogue segment using the `image_search` field in the JSON |
| 4 | `make_video.py` | Renders all segments into 1280×720 landscape videos in parallel, stitches them into a final `.mp4`, exports to Google Drive, and auto-cleans all intermediate files |

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

## Requirements

- **Python 3.10+**
- **FFmpeg** (included locally for Windows, pre-installed on Colab)
- **tqdm** (`pip install tqdm` — auto-installed by the script if missing)
- Local image search services (Degoog/SearXNG) for `search_provider.py`
