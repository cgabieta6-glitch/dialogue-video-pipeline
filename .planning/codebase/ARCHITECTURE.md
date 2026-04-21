# Architecture

**Analysis Date:** 2026-04-22

## System Overview

The project is a **Dialogue-to-Video Pipeline** that converts audio transcripts (dialogues) into interactive web-based players and rendered videos. It follows a sequential pipeline architecture.

## Core Patterns

### Pipeline Pattern
Work flows through several stages, often mediated by JSON files:
1. **Segmentation**: `auto_segment.py` processes raw transcripts into structured JSON segments with keywords.
2. **Asset Procurement**: `search_provider.py` downloads images/videos based on keywords from the JSON.
3. **Audio Processing**: `cut_audio.py` (and potentially others) manages audio slicing.
4. **Presentation**: `make_website.py` generates a static HTML player using the assets.
5. **Rendering**: `make_video.py` stitches everything into a final MP4.

### Abstract Base Class (ABC)
Used in `search_provider.py` to define a common interface for `ImageSearchProvider`, allowing multiple fallback tiers (Wikimedia, Degoog, etc.) to be swapped or combined easily.

## Data Flow

1. **Input**: `.txt` transcript files.
2. **Intermediate**: `.json` files (e.g., `done exercise no 12.json`) containing text, speaker IDs, and media paths.
3. **Output**: `.html` files (in `output_websites/`) and `.mp4` videos (in `output_videos/`).

## Key Abstractions

- **Segment**: The fundamental unit of data, representing a single line of dialogue with associated audio and visual metadata.
- **Provider**: A service (local or remote) that fulfills a specific need, such as image search or LLM processing.

## Entry Points

- `auto_segment.py`: Start here to process a new transcript.
- `search_provider.py`: Run to download missing images for existing JSON segments.
- `make_website.py`: Run to generate the interactive player.
- `make_video.py`: Run to render the final video.

---

*Architecture analysis: 2026-04-22*
*Update after major structural changes*
