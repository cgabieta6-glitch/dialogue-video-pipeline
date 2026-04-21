# Conventions

**Analysis Date:** 2026-04-22

## Code Style

**Python:**
- Follows standard snake_case for functions and variables.
- PascalCase for Classes (e.g., `ImageSearchProvider`).
- Uses `argparse` for CLI interfaces.
- Heavy use of `try-except` for robust network operations (especially in `search_provider.py`).

**Frontend:**
- Uses CSS Variables for theming (Midnight, Ocean, Sunset, Forest, Lavender, Light).
- Functional JavaScript (not framework-based) embedded directly in generated HTML.

## Naming Patterns

- **Variables**: Descriptive names (e.g., `dialogue_id`, `safe_paragraph`, `tier_order`).
- **Files**: Logic files use functional names (`make_video.py`), data files use status-prefixed names (`done ...`).

## Error Handling

- **Graceful Fallbacks**: Scripts are designed to continue even if a specific sub-task (like downloading one image) fails.
- **Micro-delays**: Used in scrapers to avoid 403 Forbidden errors.
- **Timeouts**: Socket and request timeouts are explicitly set (usually 5-10s).

## Patterns

- **Factory/Provider**: Centralizing search logic into providers.
- **Embedded Assets**: The web player often includes configuration as JSON objects within the `<script>` tags.

---

*Conventions analysis: 2026-04-22*
*Update as new patterns emerge*
