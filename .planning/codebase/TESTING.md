# Testing

**Analysis Date:** 2026-04-22

## Frameworks

- **No formal testing framework** (e.g., `pytest`, `unittest`) is currently in use.
- No `tests/` directory exists in the codebase.

## Testing Strategy

### Manual Verification
Testing is performed manually by running the scripts on sample transcripts and inspecting the outputs:
- Checking if `auto_segment.py` produces valid JSON.
- Verifying `search_provider.py` downloads expected images.
- Opening `make_website.py` outputs in a browser to check playback.
- Watching rendered videos from `make_video.py`.

### Logging-based Debugging
Scripts use `print()` statements heavily to report progress, successful downloads, and failures (e.g., `[SearXNG] Found image...`, `[Error] ALL media providers failed...`).

## Potential Improvements

- Implement unit tests for `search_provider.py` mock responses.
- Add regression tests for `auto_segment.py` keyword extraction logic.
- Use E2E tests (e.g., Playwright) for the web player.

---

*Testing analysis: 2026-04-22*
*Update after implementing testing tools*
