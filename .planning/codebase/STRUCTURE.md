# Structure

**Analysis Date:** 2026-04-22

## Directory Layout

```text
/
├── .agent/              # GSD skills and instructions
├── .planning/           # Project planning and codebase mapping docs
├── .venv/               # Python virtual environment
├── app_data/            # Internal application data
├── downloaded_images/   # Repository for downloaded search assets
├── ffmpeg/              # ffmpeg binaries
├── output_videos/       # Rendered MP4 outputs
├── output_websites/     # Generated HTML player outputs
├── tools/               # Utility scripts and tools
├── scratch/             # Temporary workspace for experiments
└── [Root Files]         # Core pipeline scripts and data files
```

## Key Locations

| Location | Purpose |
|----------|---------|
| `auto_segment.py` | Main script for transcript processing |
| `search_provider.py` | Core image/video search logic |
| `make_website.py` | Web player generator |
| `make_video.py` | Video renderer |
| `*.json` | Segment data (input/output of various stages) |
| `*.m4a` / `*.txt` | Source audio and transcripts |

## Naming Conventions

- **Data Files**: Completed segments use the prefix `done ` (e.g., `done exercise no 12.json`).
- **Asset Folders**: Images for a specific exercise are stored in `done [exercise]_images/`.
- **Scripts**: Snake case for Python files (`make_website.py`, `auto_segment.py`).

---

*Structure analysis: 2026-04-22*
*Update after directory reorganizations*
