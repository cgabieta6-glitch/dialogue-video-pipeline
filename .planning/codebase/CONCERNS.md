# Concerns

**Analysis Date:** 2026-04-22

## Critical Issues

### [HIGH] Hardcoded Secrets
Multiple API keys and client secrets are hardcoded in `search_provider.py`. 
- **Impact**: High risk of credential leakage if the code is shared or pushed to a public repository.
- **Remediation**: Move all keys to a `.env` file and use `python-dotenv` to load them.

## Technical Debt

### [MED] Script Complexity
Core scripts like `make_website.py` (1900+ lines) and `auto_segment.py` (950+ lines) have grown very large.
- **Impact**: Difficult to maintain and test.
- **Remediation**: Refactor large functions into smaller modules or separate utility files.

### [MED] Dependency Management
Lack of a `requirements.txt` or `pyproject.toml` file.
- **Impact**: Difficult for new developers to set up the environment; risk of version mismatches.
- **Remediation**: Generate a `requirements.txt` from the current `.venv`.

## Fragility

### [MED] Web Scrapers
Heavy reliance on scraping services (SearXNG, Degoog) and specific website structures (Wikimedia, Pixabay, etc.).
- **Impact**: Frequent breakage if target sites update their layout or implement stricter bot protection.
- **Remediation**: Use official APIs where possible; implement more robust error recovery.

### [LOW] Local Service Dependency
Requires local Docker services (SearXNG, Degoog) for optimal performance.
- **Impact**: Complex local setup.
- **Remediation**: Provide a `docker-compose.yml` (Note: one exists, but verify it covers all needs).

---

*Concerns analysis: 2026-04-22*
*Update as issues are resolved*
