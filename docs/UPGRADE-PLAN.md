# Upgrade plan — book-grant-data

Current state: **7/10** (pass 1: 5 -> 7; pass 2: 7, consumer-facing CLI fix). Offline contract, adapters and CLI are tested and linted in CI; live capture, source permission and consumers remain unverified by design.

## Backlog

- P0: Push this branch and confirm the new GitHub Actions `CI` workflow is green on both Python versions.
- P1: Strengthen drift markers for `sba-small-business-grants` — their `required_markers` are only fragments of the title, so a challenge or error page that repeats the title would pass. Pick body phrases from a captured page (needs a reviewed live capture; not done offline).
- P1: Replace the copy of `cli.py`/`capture.py` scaffolding shared by the sibling `book-*-data` repos with the shared runtime package once it is independently installable (README gate 3).
- P1: ZEVI 2 deadline (2026-09-16) has passed; add the next reviewed competition as a new source record ID rather than editing history.
- P2: `depa` directory stays status `unknown`; add a round-specific parser only when an exact window is published.
- P2: Add a live-capture smoke job only behind an explicit manual trigger and reviewed source permission (never on push).

## Done in this pass (pass 1)

- Added `.github/workflows/ci.yml`: `ruff check`, `pytest` and an offline CLI smoke (`contract`, `validate demo.json`, `demo --open-only`) on Python 3.10 and 3.13.
- Added `[project.optional-dependencies] dev` (pytest, pinned ruff), `[tool.ruff]` and `[tool.pytest.ini_options]` to `pyproject.toml`; fixed import-order lint.
- Added `tests/test_registry.py`: `sources.json` ↔ packaged `source*.json` consistency (product, domain, category in contract, https URLs, interval), source-ID selector rejects traversal/unknown IDs, every marker-driven adapter normalizes a synthetic page into a valid live record and rejects a challenge page, JSON adapters reject non-object payloads, CLI `validate` exit codes do not echo input.
- Removed dead GitHub-Education and Chevening template branches; unknown sources now fail closed (`unknown grant source`).
- GOV.UK Content API adapter rejects non-object JSON with `ValueError`.
- README source list now names all seven sources; stale GitHub/Chevening attribution removed.

## Done in this pass (pass 2)

- `contract --version {v1,v2}` (default v1, output unchanged) prints `schema-v2.json`, the
  contract every captured record uses; before, consumers of live data could only get v1.
  Unknown versions exit 2. Registry test, CI smoke and README updated (same change as the
  sibling scholarship/freebie/grant/benefit CLIs).
- Weak drift markers left unchanged: stronger phrases need a reviewed live capture.
- Drift guard: the HTML text extractor now also ignores `<noscript>` and `<svg>` (matching
  the sibling creator/deal/learning/mobility/paid-study/partnership/startup adapters), so
  markers hidden there cannot pass a challenge page; `tests/test_text_extraction.py`.
