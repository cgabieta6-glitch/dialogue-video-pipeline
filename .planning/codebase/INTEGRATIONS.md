# External Integrations

**Analysis Date:** 2026-04-22

## External APIs

### Image Search Providers
The project implements a multi-tier fallback system for image and GIF search in `search_provider.py`.

**Configured Providers:**
1. **Wikimedia Commons** - Public API for royalty-free images.
2. **Klipy** - GIF search (requires `KLIPY_API_KEY`).
3. **Giphy** - GIF search (requires `GIPHY_API_KEY`).
4. **Unsplash** - High-quality photo search (API Key hardcoded).
5. **Pexels** - Photo/Video search (API Key hardcoded).
6. **Pixabay** - Photo/Video search (API Key hardcoded).
7. **Openverse** - Creative Commons search (Client ID/Secret hardcoded).
8. **Internet Archive** - Public domain image search.
9. **iNaturalist** - Biology-focused image search.
10. **Desmos** - Graph rendering (direct image URL construction).

### LLM Providers
Used in `auto_segment.py` for keyword extraction.

- **Ollama** (Local) - Default: `http://localhost:11434`.
- **Google Gemini API** - Cloud-based LLM (requires `GEMINI_API_KEY`).

## Databases

- **File System** - Primary "database" for segment data (JSON files) and media assets (images, audio, videos).

## Local Services

- **Degoog** - Local Docker container at `http://127.0.0.1:8082` for aggregated search.
- **SearXNG** - Local Docker container at `http://localhost:8888` for evasive search scraping.

## Auth Providers

- **None** - Authentication is handled via static API keys/tokens for external services.

---

*Integrations analysis: 2026-04-22*
*Update when adding new external services*
