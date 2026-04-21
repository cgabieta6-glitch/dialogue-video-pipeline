# Technology Stack

**Analysis Date:** 2026-04-22

## Languages

**Primary:**
- Python 3.x - Core logic, data processing, and automation scripts.
- HTML5 / JavaScript / CSS3 - Frontend "playable web video" and preview tools.

**Secondary:**
- Shell (PowerShell/Bash) - Utility scripts and environment setup.

## Runtime

**Environment:**
- Python 3.x Interpreter
- Browser (for HTML-based video player and preview)
- .venv (Virtual Environment) present in root

**Package Manager:**
- Pip (inferred from .venv)
- No `requirements.txt` or `pyproject.toml` found in root (manual dependency management)

## Frameworks

**Core:**
- Vanilla Python (scripts)
- Vanilla HTML/JS/CSS (frontend)

**Testing:**
- None detected

**Build/Dev:**
- ffmpeg - Critical for audio/video processing and rendering.

## Key Dependencies

**Critical:**
- `spacy` - NLP for smart keyword extraction in `auto_segment.py`.
- `rake-nltk` / `yake` / `keybert` - Keyword extraction libraries.
- `playwright` - Browser automation for image search scraping in `search_provider.py`.
- `sentence-transformers` - Semantic similarity boosting for keyword extraction.
- `pdf.js` - PDF rendering in the web player.

**Infrastructure:**
- `os`, `shutil`, `json`, `argparse`, `urllib` - Standard Python libraries for file and network operations.
- `ffmpeg` (external binary) - Used via subprocess for media manipulation.

## Configuration

**Environment:**
- Environment variables: `SEARXNG_BASE_URL`, `KLIPY_API_KEY`, `GIPHY_API_KEY`, `DEGOOG_BASE_URL`.
- Hardcoded API keys in `search_provider.py`.

**Build:**
- No formal build system (script-based execution).

## Platform Requirements

**Development:**
- Windows (Current environment)
- Python 3.x
- Docker (required for local Degoog/SearXNG services)

**Production:**
- Any platform with Python 3.x and browser access.

---

*Stack analysis: 2026-04-22*
*Update after major dependency changes*
